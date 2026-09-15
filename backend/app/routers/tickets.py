"""
Ticket endpoints, called by n8n (and directly by our own test scripts
before n8n is wired up).

/tickets/create           -> called at intake. Creates the ticket
                              immediately with status "Processing" (Day
                              1-2 reliability pattern), before any AI
                              work happens, so nothing is lost if a later
                              step fails.
/tickets/{id}/classify     -> Day 7-8: runs intent + priority + sentiment
                              classification and updates the ticket.
/tickets/{id}/respond      -> Day 9-10/11: retrieves knowledge base
                              context, generates a grounded response,
                              computes confidence, and decides whether
                              to auto-resolve or escalate to a human.
                              Supports follow-up messages via stored
                              conversation history (memory).
/tickets/{id}              -> GET, fetch current ticket state (used by
                              the dashboard, Day 12).

Later (Day 12) this gets folded into one /process endpoint for n8n to
call in a single request -- until then it stays separate and
independently testable, which is deliberate: each day's work can be
verified on its own before the next piece is wired in.
"""

import json
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlalchemy.exc import SQLAlchemyError

from app.db.session import SessionLocal
from app.db.models import Ticket
from app.services.intent import classify_query
from app.services.rag import retrieve
from app.services.response import generate_response
from app.services.confidence import compute_confidence, decide_escalation, assign_team

router = APIRouter()


class CreateTicketRequest(BaseModel):
    query_text: str
    customer_name: Optional[str] = None
    customer_email: Optional[str] = None


class CreateTicketResponse(BaseModel):
    ticket_id: str
    status: str


@router.post("/create", response_model=CreateTicketResponse)
def create_ticket(payload: CreateTicketRequest):
    """Creates a ticket immediately, status 'Processing'."""
    ticket_id = str(uuid.uuid4())
    db = SessionLocal()
    try:
        ticket = Ticket(
            ticket_id=ticket_id,
            customer_name=payload.customer_name,
            customer_email=payload.customer_email,
            query_text=payload.query_text,
            status="Processing",
        )
        db.add(ticket)
        db.commit()
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create ticket: {e}")
    finally:
        db.close()
    return {"ticket_id": ticket_id, "status": "Processing"}


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
        ticket = db.query(Ticket).filter(Ticket.ticket_id == ticket_id).first()
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
    message: Optional[str] = None
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
    """
    db = SessionLocal()
    try:
        ticket = db.query(Ticket).filter(Ticket.ticket_id == ticket_id).first()
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

        context_chunks = retrieve(current_message, top_k=3)
        response_text = generate_response(current_message, context_chunks, history)

        confidence_result = compute_confidence(ticket.intent_confidence, context_chunks, response_text)
        confidence_score = confidence_result["confidence_score"]
        should_escalate = decide_escalation(confidence_score, ticket.priority, ticket.intent)

        history.append({"role": "customer", "content": current_message})
        history.append({"role": "assistant", "content": response_text})

        ticket.conversation_history = json.dumps(history)
        ticket.ai_response = response_text
        ticket.confidence_score = confidence_score
        ticket.escalation_status = should_escalate
        ticket.updated_at = datetime.now(timezone.utc)

        if should_escalate:
            ticket.status = "Escalated"
            ticket.assigned_team = assign_team(ticket.intent)
        else:
            ticket.status = "Resolved"
            ticket.resolution_time = datetime.now(timezone.utc)

        db.commit()

        return {
            "ticket_id": ticket_id,
            "response": response_text,
            "retrieved_chunks": context_chunks,
            "confidence_score": confidence_score,
            "status": ticket.status,
            "assigned_team": ticket.assigned_team,
        }
    finally:
        db.close()


@router.get("/{ticket_id}")
def get_ticket(ticket_id: str):
    db = SessionLocal()
    try:
        ticket = db.query(Ticket).filter(Ticket.ticket_id == ticket_id).first()
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
