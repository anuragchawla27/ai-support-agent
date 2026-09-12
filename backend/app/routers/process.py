"""
/process  -- the single endpoint n8n calls to do all the "thinking":
  1. Intent detection            (Day 7-8)
  2. Knowledge base retrieval    (Day 5-6, RAG)
  3. Grounded response generation (Day 9-10)
  4. Confidence scoring          (Day 11)
  5. Priority + sentiment classification (Day 7-8)

Returns one JSON blob n8n uses to branch (auto-resolve vs escalate).
"""
