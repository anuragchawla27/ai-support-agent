"""
FastAPI entrypoint for the AI Customer Support & Ticket Resolution Agent.

Built for: PranavX Labs 15-Day AI Automation Internship Project.

This app is called by n8n (the orchestration layer) over plain HTTP.
It does NOT talk to end customers directly -- n8n's webhook handles intake,
and this backend does the "thinking": intent detection, RAG retrieval,
response generation, confidence scoring, and ticket persistence.

Routers are added incrementally, day by day, per the project roadmap:
  Day 3-4  -> knowledge_base ingestion endpoints
  Day 5-6  -> /retrieve  (RAG)
  Day 7-8  -> /classify  (intent, priority, sentiment) + ticket creation
  Day 9-10 -> /respond   (grounded response generation)
  Day 11   -> confidence scoring folded into /process
  Day 12   -> dashboard read endpoints + auth
"""

from fastapi import FastAPI

from app.db.session import engine, Base
from app.db import models  # noqa: F401  (import registers models with Base)
from app.routers import tickets

app = FastAPI(
    title="PranavX Labs - AI Support Agent",
    description="End-to-end AI customer support & ticket resolution backend.",
    version="0.1.0",
)


@app.on_event("startup")
def on_startup():
    """Ensures all tables (KnowledgeChunk, Ticket) exist. Safe to run
    every startup -- create_all only creates tables that don't already
    exist, it never touches existing data."""
    Base.metadata.create_all(bind=engine)


@app.get("/health")
def health_check():
    """Simple liveness check n8n / docker-compose can ping."""
    return {"status": "ok"}


app.include_router(tickets.router, prefix="/tickets", tags=["tickets"])

# --- Routers added in later days ---
# from app.routers import process, dashboard, auth
# app.include_router(process.router, prefix="/process", tags=["ai-processing"])
# app.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
# app.include_router(auth.router, prefix="/auth", tags=["auth"])
