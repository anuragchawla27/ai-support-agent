"""
Grounded response generation via Groq LLM. Takes: raw query + intent +
retrieved KB context + conversation history + company policy notes.
Must not answer beyond what's grounded in retrieved context
(hallucination prevention, Section 15).

Built: Day 9-10
"""
