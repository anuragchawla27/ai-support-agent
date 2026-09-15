"""
Confidence scoring and escalation decision (Day 11) -- the primary
guardrail in this system. Combines two signals into one score:

1. Retrieval relevance: how close the retrieved knowledge base chunks
   actually are to the query (from app.services.rag.retrieve()).
2. Intent classification confidence (from app.services.intent).

Then applies a strong override: if the generated response itself
contains an honest "I don't know" signal (per the response generation
prompt in app.services.response), confidence is capped low regardless
of the other two signals -- the model's own admission of uncertainty is
the most reliable signal available.

The auto-resolve threshold is NOT hardcoded -- it's read from
CONFIDENCE_AUTO_RESOLVE_THRESHOLD (app/config.py, backed by .env), so it
can be tuned during Day 14 testing without touching code.

Escalation additionally always triggers for certain intents/priorities
regardless of confidence, per the escalation policy in
knowledge_base/docs/policies.md: payments, refunds, complaints, and
anything HIGH/CRITICAL priority always go to a human, even if the AI is
"confident" about its answer.
"""

from typing import List, Optional

from app.config import CONFIDENCE_AUTO_RESOLVE_THRESHOLD

UNCERTAINTY_PHRASES = [
    "don't have enough information",
    "don't have that specific information",
    "do not have enough information",
    "i'm not sure",
    "i am not sure",
    "cannot find",
    "couldn't find",
    "not certain",
    "passing this to a specialist",
    "specialist who can help",
    "i don't know",
]

# Intents that always escalate to a human regardless of confidence,
# per the escalation policy -- the AI never resolves these on its own.
ALWAYS_ESCALATE_INTENTS = {"Complaint"}
ALWAYS_ESCALATE_PRIORITIES = {"HIGH", "CRITICAL"}

# Which team a ticket is routed to when escalated, by intent.
TEAM_BY_INTENT = {
    "Pricing Enquiry": "Sales",
    "Service Enquiry": "Sales",
    "Internship Enquiry": "Internship Coordination",
    "Application Status": "Internship Coordination",
    "Technical Issue": "Engineering",
    "Partnership": "Business Development",
    "Complaint": "Customer Success",
    "General Enquiry": "Support",
    "Other": "Support",
}


def _contains_uncertainty_phrase(text: str) -> bool:
    text_lower = text.lower()
    return any(phrase in text_lower for phrase in UNCERTAINTY_PHRASES)


def compute_confidence(
    intent_confidence: Optional[float],
    retrieved_chunks: List[dict],
    response_text: str,
) -> dict:
    """
    Returns: { confidence_score, retrieval_score, uncertainty_detected }

    confidence_score is a 0-1 blend: 60% retrieval relevance, 40% intent
    classification confidence -- then capped at 0.3 if the response
    itself signals uncertainty, regardless of what the blend produced.
    """
    intent_confidence = intent_confidence or 0.0

    if retrieved_chunks:
        closest_distance = retrieved_chunks[0]["distance"]
        retrieval_score = max(0.0, min(1.0, 1 - closest_distance))
    else:
        retrieval_score = 0.0

    base_score = 0.6 * retrieval_score + 0.4 * intent_confidence

    uncertainty_detected = _contains_uncertainty_phrase(response_text)
    if uncertainty_detected:
        base_score = min(base_score, 0.3)

    return {
        "confidence_score": round(base_score, 4),
        "retrieval_score": round(retrieval_score, 4),
        "uncertainty_detected": uncertainty_detected,
    }


def decide_escalation(confidence_score: float, priority: Optional[str], intent: Optional[str]) -> bool:
    """
    Returns True if this ticket should be escalated to a human, False if
    it's safe to auto-resolve. Escalates when ANY of:
    - confidence_score is below CONFIDENCE_AUTO_RESOLVE_THRESHOLD
    - priority is HIGH or CRITICAL
    - intent is one that always requires a human (e.g. Complaint)
    """
    if confidence_score < CONFIDENCE_AUTO_RESOLVE_THRESHOLD:
        return True
    if priority in ALWAYS_ESCALATE_PRIORITIES:
        return True
    if intent in ALWAYS_ESCALATE_INTENTS:
        return True
    return False


def assign_team(intent: Optional[str]) -> str:
    """Maps an intent to the human team a ticket is routed to when escalated."""
    return TEAM_BY_INTENT.get(intent, "Support")
