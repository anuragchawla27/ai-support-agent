"""
RAG retrieval (Day 5-6).

Embeds an incoming query with the same sentence-transformers model used
during ingestion, then searches the knowledge_chunks table in pgvector
for the most semantically similar chunks (cosine distance -- lower is
more relevant, 0 = identical).

The embedding model is loaded once per process (module-level cache),
not per request -- loading it from disk takes a couple seconds, so we
don't want to repeat that on every call.
"""

from app.config import EMBEDDING_MODEL
from app.db.session import SessionLocal
from app.db.models import KnowledgeChunk

_model = None


def _get_model():
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer  # imported late: slow import
        _model = SentenceTransformer(EMBEDDING_MODEL)
    return _model


def retrieve(query: str, top_k: int = 3):
    """
    Returns the top_k most relevant knowledge chunks for `query`.

    Each result: { source_file, section_title, content, distance }
    distance is cosine distance (0.0 = identical meaning, 2.0 = opposite).
    Used later (Day 11) as one input to the confidence score.
    """
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
