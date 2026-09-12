# AI Customer Support & Intelligent Ticket Resolution Agent

PranavX Labs | 15-Day AI Automation Internship Project

An end-to-end AI support automation system: understands customer queries,
retrieves trusted information via RAG, generates grounded responses,
classifies and prioritizes tickets, evaluates its own confidence, and
escalates uncertain or sensitive cases to a human — instead of acting
as a generic chatbot.

## Status

Day 1-2 (Research & Architecture): complete. See `docs/architecture.md`.

## Stack

n8n (orchestration) · Python/FastAPI (backend) · Groq (LLM) ·
sentence-transformers (embeddings) · PostgreSQL + pgvector (DB/vectors) ·
HTML/CSS/JS (dashboard)

## Running locally

1. `cp .env.example .env` and fill in real values (never commit `.env`)
2. `docker-compose up --build`
3. Import the n8n workflow from `n8n/workflows/` into your local n8n instance
4. Backend health check: `http://localhost:8000/health`

## Repo structure

```
backend/        FastAPI app: routers, services (intent/RAG/response/
                confidence/classification), db models
n8n/workflows/  Exported n8n workflow JSON
knowledge_base/ Source company docs (FAQs, policies, pricing, etc.)
frontend/       Static HTML/CSS/JS dashboard
tests/          Test query dataset + results (Day 14)
docs/           Architecture and technical documentation
```
