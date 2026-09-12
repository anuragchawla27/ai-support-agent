"""
SQLAlchemy models. Ticket model fields (per project doc, Section F):
ticket_id, customer_name, query_text, intent, priority, sentiment,
ai_response, confidence_score, status, assigned_team, created_at,
updated_at, resolution_time, escalation_status.

Also: KnowledgeChunk model (text + pgvector embedding column) for RAG.

Built: Day 3-4 (KnowledgeChunk) and Day 7-8 (Ticket)
"""
