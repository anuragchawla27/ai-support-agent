"""
SQLAlchemy models.

KnowledgeChunk -- built Day 3-4/5-6: stores each chunked section of the
knowledge base docs, plus its vector embedding, used for RAG retrieval.

Ticket -- built Day 7-8. Left as a documented stub below so the exact
fields (matching the project doc's ticket structure requirement) are
already planned out.
"""

from datetime import datetime, timezone

from sqlalchemy import Column, Integer, String, Text, DateTime
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


# --- Ticket model: built Day 7-8, matches project doc's required fields ---
# class Ticket(Base):
#     __tablename__ = "tickets"
#     ticket_id = Column(String(36), primary_key=True)
#     customer_name = Column(String(255))
#     query_text = Column(Text)
#     intent = Column(String(100))
#     priority = Column(String(20))
#     sentiment = Column(String(20))
#     ai_response = Column(Text)
#     confidence_score = Column(Integer)
#     status = Column(String(20))          # Processing / Resolved / Escalated / Pending-Retry
#     assigned_team = Column(String(100))
#     created_at = Column(DateTime)
#     updated_at = Column(DateTime)
#     resolution_time = Column(DateTime)
#     escalation_status = Column(String(20))
