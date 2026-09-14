"""
SQLAlchemy models.

KnowledgeChunk -- built Day 3-4/5-6: stores each chunked section of the
knowledge base docs, plus its vector embedding, used for RAG retrieval.

Ticket -- built Day 7-8: the structured ticket record. Created at intake
with status "Processing" (Day 1-2 reliability pattern), then updated as
classification, response generation, and confidence scoring run.
"""

from datetime import datetime, timezone

from sqlalchemy import Column, Integer, String, Text, DateTime, Float, Boolean
from pgvector.sqlalchemy import Vector

from app.db.session import Base

# Must match the output dimension of EMBEDDING_MODEL (all-MiniLM-L6-v2 = 384).
EMBEDDING_DIM = 384


class KnowledgeChunk(Base):
    __tablename__ = "knowledge_chunks"

    id = Column(Integer, primary_key=True)
    source_file = Column(String(255), nullable=False)      # e.g. "pricing.md"
    section_title = Column(String(255), nullable=False)     # e.g. "Starter automation"
    content = Column(Text, nullable=False)                  # the chunk's raw text
    embedding = Column(Vector(EMBEDDING_DIM), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class Ticket(Base):
    __tablename__ = "tickets"

    ticket_id = Column(String(36), primary_key=True)  # UUID, generated at intake

    # Set at creation (Day 7-8 /tickets/create)
    customer_name = Column(String(255), nullable=True)
    customer_email = Column(String(255), nullable=True)
    query_text = Column(Text, nullable=False)

    # Set by classification (Day 7-8 /tickets/{id}/classify)
    intent = Column(String(100), nullable=True)
    intent_confidence = Column(Float, nullable=True)
    priority = Column(String(20), nullable=True)     # LOW / MEDIUM / HIGH / CRITICAL
    sentiment = Column(String(20), nullable=True)     # Positive / Neutral / Negative

    # Set by response generation + confidence scoring (Day 9-11)
    ai_response = Column(Text, nullable=True)
    confidence_score = Column(Float, nullable=True)

    # Ticket lifecycle
    status = Column(String(20), nullable=False, default="Processing")
    # Processing / Resolved / Escalated / Pending-Retry
    assigned_team = Column(String(100), nullable=True)
    escalation_status = Column(Boolean, default=False)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
    resolution_time = Column(DateTime, nullable=True)
