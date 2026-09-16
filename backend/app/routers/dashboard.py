"""
Dashboard read endpoints (Day 12). Powers the ticket list, filters, and
basic analytics shown in frontend/index.html.

Every endpoint here requires the dashboard password (Section 15:
"Protect the ticket dashboard"), enforced by require_dashboard_auth
(app/routers/auth.py) via the X-Dashboard-Password header.
"""

from typing import Optional

from fastapi import APIRouter, Depends, Query

from app.db.session import SessionLocal
from app.db.models import Ticket
from app.routers.auth import require_dashboard_auth

router = APIRouter()


@router.get("/tickets")
def list_tickets(
    status: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    _auth: None = Depends(require_dashboard_auth),
):
    """Lists tickets, most recent first. Optional filters: status, priority."""
    db = SessionLocal()
    try:
        query = db.query(Ticket)
        if status:
            query = query.filter(Ticket.status == status)
        if priority:
            query = query.filter(Ticket.priority == priority)
        tickets = query.order_by(Ticket.created_at.desc()).all()
        return [
            {
                "ticket_id": t.ticket_id,
                "customer_name": t.customer_name,
                "query_text": t.query_text,
                "intent": t.intent,
                "priority": t.priority,
                "sentiment": t.sentiment,
                "status": t.status,
                "assigned_team": t.assigned_team,
                "confidence_score": t.confidence_score,
                "created_at": t.created_at,
            }
            for t in tickets
        ]
    finally:
        db.close()


@router.get("/analytics")
def get_analytics(_auth: None = Depends(require_dashboard_auth)):
    """Basic counts by status, priority, and assigned team -- enough for
    an at-a-glance operational view without a full BI tool."""
    db = SessionLocal()
    try:
        tickets = db.query(Ticket).all()
        by_status, by_priority, by_team = {}, {}, {}
        for t in tickets:
            by_status[t.status] = by_status.get(t.status, 0) + 1
            if t.priority:
                by_priority[t.priority] = by_priority.get(t.priority, 0) + 1
            if t.assigned_team:
                by_team[t.assigned_team] = by_team.get(t.assigned_team, 0) + 1
        return {
            "total_tickets": len(tickets),
            "by_status": by_status,
            "by_priority": by_priority,
            "by_team": by_team,
        }
    finally:
        db.close()
