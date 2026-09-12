# Architecture — AI Customer Support & Ticket Resolution Agent

PranavX Labs | 15-Day AI Automation Internship Project

## Pipeline

```
Customer query
  -> n8n webhook (intake)
  -> Ticket created immediately, status "Processing"
  -> FastAPI /process
       -> Intent detection (Groq)
       -> KB retrieval (pgvector + sentence-transformers embeddings)
       -> Grounded response generation (Groq)
       -> Confidence scoring
       -> Priority + sentiment classification
  -> n8n decision (confidence >= threshold?)
       HIGH confidence -> ticket updated "Resolved", AI answer sent to customer
       LOW confidence / sensitive -> ticket updated "Escalated", assigned
         team notified, human resolves
  -> Every interaction stored in Postgres, visible on dashboard
```

## Tech stack and justification

| Component | Doc suggestion | Our choice | Justification |
|---|---|---|---|
| Orchestration | n8n | n8n | Already running locally via Docker |
| Backend | Node.js / Python | Python (FastAPI) | No prior Node.js experience; Python fits RAG/embeddings work naturally |
| LLM | OpenAI / Gemini | Groq (Llama models) | Fast, low-cost, equivalent capability for this use case |
| Embeddings | (not specified) | sentence-transformers (local) | Groq has no embeddings endpoint; free, no extra API dependency |
| Database + vectors | Supabase / PostgreSQL / Sheets | PostgreSQL + pgvector | One database for structured tickets and vector search, avoids running two data stores |
| Frontend | HTML/CSS/JS or React | Plain HTML/CSS/JS | No build tooling required, easy to run and inspect |

## Reliability decisions

- **Ticket-first pattern:** ticket record is created at intake (before any AI
  processing), not after. Prevents lost queries on pipeline failure
  (addresses "missed tickets" business problem and Day 13 error-handling
  requirement).
- **Configurable confidence threshold:** stored as an env var
  (`CONFIDENCE_AUTO_RESOLVE_THRESHOLD`), tuned empirically during Day 14
  testing rather than hardcoded.
- **Dashboard authentication:** required per Section 15 (Security &
  Responsible AI). MVP implementation: shared password + session token.

## n8n workflow (node-level design)

See `n8n/workflows/` once exported. Design:

1. Webhook trigger — `POST /webhook/support-query`
2. Set node — generate `ticket_id`, `created_at`
3. HTTP Request -> `POST /tickets/create` (status: Processing)
4. HTTP Request -> `POST /process` (returns intent, confidence, priority,
   sentiment, ai_response, escalate flag)
5. IF node — branch on confidence + escalate flag
   - High confidence: `PATCH /tickets/{id}/update` (Resolved) -> respond to webhook
   - Low confidence: `PATCH /tickets/{id}/update` (Escalated) -> notify
     assigned team -> respond to webhook
6. Global error-trigger workflow — catches failed HTTP nodes, marks ticket
   "Pending — Retry", retries once, escalates on repeated failure
