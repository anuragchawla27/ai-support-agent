"""
RAG retrieval (Day 5-6).

Embeds an incoming query with the same sentence-transformers model used
during ingestion, then searches the knowledge_chunks table in pgvector
for the most semantically similar chunks (cosine distance -- lower is
more relevant, 0 = identical).

The embedding model is loaded once per process (module-level cache),
not per request -- loading it from disk takes a couple seconds, so we
don't want to repeat that on every call.

Day 13: if the database is unreachable or the query fails, returns an
empty list instead of raising -- app.services.response then correctly
tells the customer it has no information, and app.services.confidence
scores that as low confidence, which routes to a human. A missing
knowledge base becomes "safely uncertain," never a crash.
"""

import logging

from app.config import EMBEDDING_MODEL
from app.db.session import SessionLocal
from app.db.models import KnowledgeChunk

logger = logging.getLogger("app")

_model = None


def _get_model():
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer  # imported late: slow import
        _model = SentenceTransformer(EMBEDDING_MODEL)
    return _model


def retrieve(query: str, top_k: int = 4):
    """
    Returns the top_k most relevant knowledge chunks for `query`, or an
    empty list if retrieval fails for any reason (DB unreachable,
    embedding failure, etc.) -- callers must treat an empty list as a
    valid "no information available" result, not an error.

    Each result: { source_file, section_title, content, distance }
    distance is cosine distance (0.0 = identical meaning, 2.0 = opposite).
    """
    try:
        model = _get_model()
        query_vector = model.encode(query).tolist()

        db = SessionLocal()
        try:
            distance_col = KnowledgeChunk.embedding.cosine_distance(query_vector).label("distance")
            rows = (
                db.query(KnowledgeChunk, distance_col)
                .order_by(distance_col)
                .limit(top_k)
                .all()
            )
            return [
                {
                    "source_file": chunk.source_file,
                    "section_title": chunk.section_title,
                    "content": chunk.content,
                    "distance": float(distance),
                }
                for chunk, distance in rows
            ]
        finally:
            db.close()
    except Exception as e:
        logger.error(f"[retrieve] Retrieval failed, returning no results: {e}")
        return []
