"""
Grounded response generation (Day 9-10).

Takes a customer's query, retrieved knowledge base context (from
app/services/rag.py), and prior conversation history for this ticket
(conversation memory), and generates a response via Groq that is
strictly grounded in the retrieved context -- it must not invent
information beyond what was retrieved (Section 15: hallucination
prevention).

If the retrieved context doesn't actually answer the question, the
prompt instructs the model to say so honestly rather than guess. That
honesty (or lack of it) is also useful signal for confidence scoring
later (Day 11).
"""

from typing import List, Optional

from groq import Groq

from app.config import GROQ_API_KEY, GROQ_MODEL

_client = None


def _get_client():
    global _client
    if _client is None:
        _client = Groq(api_key=GROQ_API_KEY)
    return _client


SYSTEM_PROMPT = """You are a customer support assistant for PranavX Labs, \
an AI automation studio. Answer the customer's question using ONLY the \
information in the "Knowledge base context" section below.

Rules:
- Do not invent, assume, or add information not present in the context, \
even if it seems reasonable.
- If the context does not contain enough information to answer the \
question, say so honestly and briefly -- do not guess. For example: \
"I don't have that specific information -- I'm passing this to a \
specialist who can help."
- Keep responses concise, friendly, and professional -- 2-4 sentences \
for most questions.
- Never promise refunds, discounts, or payment changes yourself -- \
always say those go through a human team member, per policy.
- Use the conversation history (if provided) to understand follow-up \
questions in context, but still ground every factual claim in the \
knowledge base context below, not in memory of earlier turns.
"""


def generate_response(
    query_text: str,
    context_chunks: List[dict],
    conversation_history: Optional[List[dict]] = None,
) -> str:
    """
    query_text: the current customer message to respond to.
    context_chunks: output of app.services.rag.retrieve() -- list of
        { source_file, section_title, content, distance }.
    conversation_history: prior turns for this ticket, oldest first,
        each { "role": "customer" | "assistant", "content": str }.

    Returns the generated response text. Falls back to a safe
    escalation message if the LLM call fails -- must never crash the
    pipeline just because a response couldn't be generated.
    """
    context_text = "\n\n".join(
        f"[{c['section_title']}]\n{c['content']}" for c in context_chunks
    ) or "(no relevant information found in the knowledge base)"

    messages = [
        {"role": "system", "content": f"{SYSTEM_PROMPT}\n\nKnowledge base context:\n{context_text}"}
    ]

    for turn in (conversation_history or []):
        role = "assistant" if turn.get("role") == "assistant" else "user"
        messages.append({"role": role, "content": turn["content"]})

    messages.append({"role": "user", "content": query_text})

    client = _get_client()
    try:
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=messages,
            temperature=0.2,
            max_tokens=300,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"[generate_response] LLM call failed: {e}")
        return (
            "I'm having trouble generating a response right now. "
            "I've passed this along to a specialist who will follow up with you shortly."
        )
