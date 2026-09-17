"""
Ticket endpoints, called by n8n (and directly by our own test scripts
before n8n is wired up).

/tickets/create           -> called at intake. Creates the ticket
                              immediately with status "Processing" (Day
                              1-2 reliability pattern), before any AI
                              work happens, so nothing is lost if a later
                              step fails. Day 13: validates input and
                              returns the existing ticket instead of a
                              duplicate if the same customer submits the
                              same query again within a short window.
/tickets/{id}/classify     -> Day 7-8: runs intent + priority + sentiment
                              classification and updates the ticket.
/tickets/{id}/respond      -> Day 9-10/11: retrieves knowledge base
                              context, generates a grounded response,
                              computes confidence, and decides whether
                              to auto-resolve or escalate to a human.
                              Supports follow-up messages via stored
                              conversation history (memory). Day 13:
                              flags likely prompt-injection attempts and
                              forces escalation on them.
/tickets/{id}              -> GET, fetch current ticket state (used by
                              the dashboard, Day 12).

Day 13: every endpoint here now returns a clean 503 (rather than a raw
500 crash) when the database is unreachable, so a DB outage degrades
gracefully instead of surfacing a stack trace to the caller.

Later (this gets folded into one /process endpoint for the n8n
workflow) -- until then it stays separate and independently testable,
which is deliberate: each day's work can be verified on its own before
the next piece is wired in.
"""

import json
import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.exc import SQLAlchemyError

from app.db.session import SessionLocal
from app.db.models import Ticket
from app.services.intent import classify_query
from app.services.rag import retrieve
from app.services.response import generate_response
from app.services.confidence import compute_confidence, decide_escalation, assign_team
from app.services.guardrails import contains_injection_attempt

logger = logging.getLogger("app")
router = APIRouter()

DUPLICATE_WINDOW_MINUTES = 5


class CreateTicketRequest(BaseModel):
    query_text: str = Field(..., min_length=1, max_length=5000)
    customer_name: Optional[str] = Field(None, max_length=255)
    customer_email: Optional[str] = Field(None, max_length=255)


class CreateTicketResponse(BaseModel):
    ticket_id: str
    status: str
    duplicate_of_existing: bool = False


@router.post("/create", response_model=CreateTicketResponse)
def create_ticket(payload: CreateTicketRequest):
    """
    Creates a ticket immediately, status 'Processing'. Input is
    validated by Pydantic (non-empty, length-capped) before this runs.

    Duplicate handling: if the same customer_email submitted the exact
    same query_text within the last few minutes (e.g. an accidental
    double-submit from a slow form), returns the existing ticket instead
    of creating a second one.
    """
    query_text = payload.query_text.strip()
    if not query_text:
        raise HTTPException(status_code=422, detail="query_text cannot be empty or whitespace-only.")

    db = SessionLocal()
    try:
        if payload.customer_email:
            cutoff = datetime.now(timezone.utc) - timedelta(minutes=DUPLICATE_WINDOW_MINUTES)
            existing = (
                db.query(Ticket)
                .filter(
                    Ticket.customer_email == payload.customer_email,
                    Ticket.query_text == query_text,
                    Ticket.created_at >= cutoff,
                )
                .order_by(Ticket.created_at.desc())
                .first()
            )
            if existing:
                logger.info(f"[create_ticket] Duplicate submission detected, returning existing ticket {existing.ticket_id}")
                return {
                    "ticket_id": existing.ticket_id,
                    "status": existing.status,
                    "duplicate_of_existing": True,
                }

        ticket_id = str(uuid.uuid4())
        ticket = Ticket(
            ticket_id=ticket_id,
            customer_name=payload.customer_name,
            customer_email=payload.customer_email,
            query_text=query_text,
            status="Processing",
        )
        db.add(ticket)
        db.commit()
        logger.info(f"[create_ticket] Created ticket {ticket_id}")
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"[create_ticket] Database error: {e}")
        raise HTTPException(status_code=503, detail="Database temporarily unavailable. Please try again shortly.")
    finally:
        db.close()
    return {"ticket_id": ticket_id, "status": "Processing", "duplicate_of_existing": False}


class ClassifyResponse(BaseModel):
    ticket_id: str
    intent: str
    intent_confidence: float
    priority: str
    sentiment: str


@router.post("/{ticket_id}/classify", response_model=ClassifyResponse)
def classify_ticket(ticket_id: str):
    """Runs intent/priority/sentiment classification on an existing
    ticket's query_text and updates the ticket record."""
    db = SessionLocal()
    try:
        try:
            ticket = db.query(Ticket).filter(Ticket.ticket_id == ticket_id).first()
        except SQLAlchemyError as e:
            logger.error(f"[classify_ticket] Database error: {e}")
            raise HTTPException(status_code=503, detail="Database temporarily unavailable. Please try again shortly.")

        if not ticket:
            raise HTTPException(status_code=404, detail="Ticket not found")

        result = classify_query(ticket.query_text)

        ticket.intent = result["intent"]
        ticket.intent_confidence = result["intent_confidence"]
        ticket.priority = result["priority"]
        ticket.sentiment = result["sentiment"]
        ticket.updated_at = datetime.now(timezone.utc)
        db.commit()

        return {
            "ticket_id": ticket_id,
            "intent": ticket.intent,
            "intent_confidence": ticket.intent_confidence,
            "priority": ticket.priority,
            "sentiment": ticket.sentiment,
        }
    finally:
        db.close()


class RespondRequest(BaseModel):
    message: Optional[str] = Field(None, max_length=5000)
    # If omitted, responds to the ticket's original query_text (first
    # response). If provided, treats it as a new follow-up message on
    # this ticket, using conversation_history for context (memory).


class RespondResponse(BaseModel):
    ticket_id: str
    response: str
    retrieved_chunks: list
    confidence_score: float
    status: str
    assigned_team: Optional[str] = None
    flagged_for_review: bool = False


@router.post("/{ticket_id}/respond", response_model=RespondResponse)
def respond_to_ticket(ticket_id: str, payload: RespondRequest):
    """
    Retrieves relevant knowledge base context, generates a grounded
    response, scores confidence, and decides whether to auto-resolve or
    escalate (Day 11). Appends this exchange to the ticket's stored
    conversation history so a later follow-up call has memory of it.

    If the ticket hasn't been classified yet (no /classify call made),
    this runs classification automatically first -- confidence scoring
    and the escalation decision both depend on intent/priority.

    Day 13: if the message looks like a prompt-injection attempt, the
    ticket is force-escalated for human review regardless of what
    confidence scoring would otherwise decide.
    """
    db = SessionLocal()
    try:
        try:
            ticket = db.query(Ticket).filter(Ticket.ticket_id == ticket_id).first()
        except SQLAlchemyError as e:
            logger.error(f"[respond_to_ticket] Database error: {e}")
            raise HTTPException(status_code=503, detail="Database temporarily unavailable. Please try again shortly.")

        if not ticket:
            raise HTTPException(status_code=404, detail="Ticket not found")

        if ticket.intent is None:
            classification = classify_query(ticket.query_text)
            ticket.intent = classification["intent"]
            ticket.intent_confidence = classification["intent_confidence"]
            ticket.priority = classification["priority"]
            ticket.sentiment = classification["sentiment"]

        current_message = payload.message or ticket.query_text
        history = json.loads(ticket.conversation_history) if ticket.conversation_history else []

        injection_flagged = contains_injection_attempt(current_message)
        if injection_flagged:
            logger.warning(f"[respond_to_ticket] Possible prompt injection on ticket {ticket_id} -- forcing escalation")

        # Retrieval and generation are individually fault-tolerant
        # (see app.services.rag / app.services.response) -- a failure in
        # either still produces a safe, low-confidence result here rather
        # than a 500.
        context_chunks = retrieve(current_message, top_k=4)
        response_text = generate_response(current_message, context_chunks, history)

        confidence_result = compute_confidence(ticket.intent_confidence, context_chunks, response_text)
        confidence_score = confidence_result["confidence_score"]

        should_escalate = injection_flagged or decide_escalation(
            confidence_score, ticket.priority, ticket.intent, ticket.sentiment
        )

        history.append({"role": "customer", "content": current_message})
        history.append({"role": "assistant", "content": response_text})

        ticket.conversation_history = json.dumps(history)
        ticket.ai_response = response_text
        ticket.confidence_score = confidence_score
        ticket.escalation_status = should_escalate
        ticket.updated_at = datetime.now(timezone.utc)

        if should_escalate:
            ticket.status = "Escalated"
            ticket.assigned_team = "Security Review" if injection_flagged else assign_team(ticket.intent)
        else:
            ticket.status = "Resolved"
            ticket.resolution_time = datetime.now(timezone.utc)

        db.commit()
        logger.info(f"[respond_to_ticket] Ticket {ticket_id} -> {ticket.status} (confidence={confidence_score})")

        return {
            "ticket_id": ticket_id,
            "response": response_text,
            "retrieved_chunks": context_chunks,
            "confidence_score": confidence_score,
            "status": ticket.status,
            "assigned_team": ticket.assigned_team,
            "flagged_for_review": injection_flagged,
        }
    finally:
        db.close()


@router.get("/{ticket_id}")
def get_ticket(ticket_id: str):
    db = SessionLocal()
    try:
        try:
            ticket = db.query(Ticket).filter(Ticket.ticket_id == ticket_id).first()
        except SQLAlchemyError as e:
            logger.error(f"[get_ticket] Database error: {e}")
            raise HTTPException(status_code=503, detail="Database temporarily unavailable. Please try again shortly.")

        if not ticket:
            raise HTTPException(status_code=404, detail="Ticket not found")
        return {
            "ticket_id": ticket.ticket_id,
            "customer_name": ticket.customer_name,
            "customer_email": ticket.customer_email,
            "query_text": ticket.query_text,
            "intent": ticket.intent,
            "intent_confidence": ticket.intent_confidence,
            "priority": ticket.priority,
            "sentiment": ticket.sentiment,
            "ai_response": ticket.ai_response,
            "conversation_history": json.loads(ticket.conversation_history) if ticket.conversation_history else [],
            "confidence_score": ticket.confidence_score,
            "status": ticket.status,
            "assigned_team": ticket.assigned_team,
            "escalation_status": ticket.escalation_status,
            "created_at": ticket.created_at,
            "updated_at": ticket.updated_at,
            "resolution_time": ticket.resolution_time,
        }
    finally:
        db.close()
