# Frequently asked questions

## General

**Q: What does PranavX Labs actually build?**
A: We build AI-powered automation systems — most commonly customer
support automation, workflow automation, and RAG-based knowledge
retrieval systems — for businesses that want to reduce repetitive manual
work.

**Q: Is this a chatbot company?**
A: No. Our systems are reasoning and decision pipelines: they classify
intent, retrieve trusted information, evaluate their own confidence, and
escalate to a human when appropriate. A chatbot just talks — our systems
make decisions and manage structured outcomes like tickets.

**Q: Do you offer ongoing support after a project is delivered?**
A: Yes, we offer optional monthly maintenance and monitoring plans after
the initial build, covering bug fixes, threshold tuning, and knowledge
base updates.

## Technical

**Q: What tools/tech stack do you typically use?**
A: It depends on the client's existing infrastructure and technical
comfort level. Common choices include n8n for orchestration, Python or
Node.js for backend logic, PostgreSQL or Supabase for storage, and LLM
providers like Groq, OpenAI, or Gemini depending on cost and latency
needs.

**Q: Can you integrate with our existing helpdesk / CRM?**
A: In most cases, yes — our systems are built around webhooks and REST
APIs, so integration depends on whether your existing tool exposes an
API, which most modern helpdesk and CRM tools do.

**Q: How do you prevent the AI from giving wrong or made-up answers?**
A: Every response is grounded in retrieved information from your
knowledge base (RAG), and the system evaluates its own confidence before
answering. Low-confidence or sensitive cases are escalated to a human
instead of guessing.

## Billing and engagement

**Q: How is a project priced?**
A: See `pricing.md` for our standard tiers. Final pricing depends on
scope, integrations, and required customization.

**Q: What's your typical project timeline?**
A: Most automation projects take 2-6 weeks depending on complexity,
similar in structure to our 15-day internal internship build cycle.
