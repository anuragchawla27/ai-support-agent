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
/tickets/{id}              -> GET, fetch current ticket state (used by
                              the dashboard, Day 12).

Later (Day 9-11) these get chained together into one /process endpoint
for n8n to call in a single request -- until then they stay separate and
independently testable, which is deliberate: each day's work can be
verified on its own before the next piece is wired in.
"""

import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlalchemy.exc import SQLAlchemyError

from app.db.session import SessionLocal
from app.db.models import Ticket
from app.services.intent import classify_query

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
