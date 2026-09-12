"""
RAG pipeline:
  1. Embed the incoming query (sentence-transformers, local, free)
  2. Similarity search against pgvector (knowledge_base embeddings)
  3. Return top-k relevant chunks as grounding context

Built: Day 5-6. Knowledge base itself is prepared Day 3-4.
"""
