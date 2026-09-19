# AI Customer Support & Intelligent Ticket Resolution Agent

**PranavX Labs | 15-Day AI Automation Internship Project**

An end-to-end AI support automation system: a customer submits a question, the system understands intent, retrieves trusted information via RAG, generates a grounded response, evaluates its own confidence, and either answers automatically or escalates to a human — with real email notifications either way. Built to demonstrate practical, production-minded AI automation, not a toy chatbot demo.

## Status: Complete (Day 15 of 15)

Every phase of the 15-day roadmap is built, tested, and verified end-to-end — including full n8n orchestration and real email delivery.

## The business problem this solves

Support teams get flooded with repetitive questions. Manual handling causes slow response times, inconsistent answers, missed tickets, and no clear way to separate "easy, instantly answerable" queries from "needs a human, urgently." This system automates the repetitive majority of queries while keeping a human firmly in the loop for anything low-confidence, sensitive, or high-priority — the AI never resolves payment, refund, or complaint issues on its own, regardless of how confident it appears.

## How it works

```
Customer submits a question (customer.html)
  -> n8n webhook receives it
  -> Ticket created immediately (status: Processing) -- nothing is lost on failure
  -> Backend: intent + priority + sentiment classification (Groq)
  -> Backend: RAG retrieval from knowledge base (pgvector)
  -> Backend: grounded response generation (Groq, strictly answers from
     retrieved content, honestly says "I don't know" otherwise)
  -> Backend: confidence scoring (retrieval relevance + intent confidence,
     capped low on any uncertainty signal)
  -> Decision: auto-resolve OR escalate
       - Escalates automatically on: low confidence, HIGH/CRITICAL priority,
         Complaint intent, Negative sentiment, or a detected prompt-injection
         attempt -- regardless of how "confident" the AI's answer looks
  -> n8n: emails the customer (answer, or "a specialist will follow up")
  -> n8n: if escalated, also emails the internal team with full ticket context
  -> Ticket visible on the password-protected staff dashboard, with
     analytics (status/priority breakdown)
```

## Tech stack

| Layer | Choice |
|---|---|
| Orchestration | n8n (self-hosted, Docker) |
| Backend | Python + FastAPI |
| LLM | Groq (`openai/gpt-oss-120b`) |
| Embeddings | sentence-transformers (`all-MiniLM-L6-v2`), local, free |
| Database + vector store | PostgreSQL + pgvector (Docker) |
| Frontend | Plain HTML/CSS/JS (no build tooling) |
| Email | Gmail API via OAuth2 (n8n native node) |
| Version control | GitHub |

Every substitution from the originally suggested stack (Groq instead of OpenAI, pgvector instead of a separate vector DB, Gmail OAuth2 instead of raw SMTP) was a deliberate, evidence-based decision — see `docs/architecture.md` for the reasoning behind each.

## Key design decisions worth knowing

- **Ticket-first reliability**: a ticket is created the instant a query arrives, before any AI processing — so a crash mid-pipeline never loses a customer's question.
- **Confidence threshold (0.70)** was not guessed — it was calibrated using real evidence from a 36-query test run across Normal, Difficult, Ambiguous, and Sensitive/failure categories (`tests/test_results.md`).
- **Escalation is multi-layered**: confidence score, priority, intent, and sentiment can each independently trigger escalation. A "confident-sounding" answer to a complaint still escalates — confidence alone never overrides a safety rule.
- **Prompt-injection defense**: both a system-prompt-level instruction and a pattern-based detector flag suspicious input and force human review.
- **Everything fails safely**: a failed LLM call, a failed retrieval, or a database hiccup all degrade to "escalate to a human" rather than crashing or guessing.

## Project structure

```
backend/
  app/
    routers/       Ticket endpoints, dashboard, auth
    services/      Intent, RAG, response generation, confidence, guardrails
    db/             SQLAlchemy models (Ticket, KnowledgeChunk)
  scripts/          Ingestion, retrieval/response test tools, full test suite
n8n/workflows/      Importable n8n orchestration workflow
knowledge_base/docs/  Source company content (mock data, see note below)
frontend/
  customer.html      Public-facing "ask a question" form
  index.html          Password-protected staff dashboard
tests/               36-query test suite + results report
docs/                 Architecture notes, n8n setup guide
```

## Running it locally

This project is deployed **locally only**, by deliberate choice — not as a limitation. See "Deployment scope" below for why.

1. `cp .env.example .env` and fill in real values (Groq API key, a database password, a dashboard password) — never commit `.env`
2. `docker-compose up -d postgres`
3. `python -m venv venv && venv\Scripts\activate` (Windows) then `pip install -r backend/requirements.txt`
4. `python backend/scripts/ingest_knowledge_base.py` (first time only, or after editing `knowledge_base/docs/`)
5. `uvicorn app.main:app --app-dir backend --reload`
6. Import `n8n/workflows/ai_support_agent_workflow.json` into your n8n instance, attach a Gmail OAuth2 credential (see `docs/n8n-workflow-setup.md`), and publish/activate it
7. Open `frontend/customer.html` to submit a question, `frontend/index.html` to view the staff dashboard

## Testing

`backend/scripts/run_test_suite.py` runs 36 queries across Normal, Difficult, Ambiguous, and Sensitive/failure categories against the live system and generates `tests/test_results.md` automatically — a real, evidence-backed report rather than a claim. Includes deliberate edge cases: a knowledge-base gap (refund question with no matching policy), duplicate-submission detection, and two different prompt-injection phrasings.

## Deployment scope: local, by choice

A live, publicly-hosted version was considered and deliberately declined for two concrete reasons:
1. **n8n's always-on hosting isn't genuinely free** — free-tier options either sleep (breaking the "instant" demo experience) or require ongoing cost.
2. **A public form with no rate-limiting would let strangers consume the Groq API quota** — not a security leak (the API key was never exposed to the frontend to begin with — it's server-side only, in `.env`, never committed), but unwanted usage of the account regardless.

A confident local walkthrough demonstrates the same capability without either tradeoff.

## Knowledge base content

All company information (`knowledge_base/docs/`) is realistic **mock data** for demonstration purposes — this is a portfolio/capability-demo project, not a real deployment for an operating company.

## Security notes

- API keys and passwords live only in `.env` (git-ignored), never in code or committed files
- The dashboard is password-protected
- Prompt-injection attempts are detected and force human review
- The AI never autonomously resolves payments, refunds, or complaints — these always escalate

## Roadmap (as built)

| Day | Delivered |
|---|---|
| 1-2 | Architecture, tech stack, repo scaffold |
| 3-4 | Knowledge base content + ingestion pipeline |
| 5-6 | RAG retrieval, tested against real queries |
| 7-8 | Intent/priority/sentiment classification, structured tickets |
| 9-10 | Grounded response generation, conversation memory |
| 11 | Confidence scoring, escalation logic |
| 12 | Staff dashboard, authentication, analytics |
| 13 | Error handling, retries, logging, prompt-injection guardrails |
| 14 | 36-query test suite, evidence-based threshold calibration |
| 15 | Full n8n orchestration, customer-facing form, real email delivery, deployment |
