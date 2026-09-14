"""
Intent classification (Day 7-8), combined with priority and sentiment
classification in a SINGLE Groq call. All three are "read the query and
categorize it" tasks over the same input, so one call covers all three
instead of three separate (slower, costlier) LLM calls.

app/services/classification.py re-exports classify_query() from here --
kept as a separate module name for clarity against the architecture
diagram, but implemented once to avoid duplicate LLM requests.
"""

import json

from groq import Groq

from app.config import GROQ_API_KEY, GROQ_MODEL

_client = None

INTENT_CATEGORIES = [
    "Pricing Enquiry",
    "Service Enquiry",
    "Internship Enquiry",
    "Application Status",
    "Technical Issue",
    "Partnership",
    "Complaint",
    "General Enquiry",
    "Other",
]
PRIORITY_LEVELS = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
SENTIMENT_LEVELS = ["Positive", "Neutral", "Negative"]

SYSTEM_PROMPT = f"""You are a classification engine for a customer support \
system at PranavX Labs, an AI automation studio. Given a customer query, \
classify it.

Return ONLY a JSON object, no other text, with exactly these keys:
- "intent": one of {INTENT_CATEGORIES}
- "intent_confidence": a number between 0 and 1, how confident you are \
in the intent label
- "priority": one of {PRIORITY_LEVELS}. Use HIGH or CRITICAL for anything \
involving payments, refunds, access/login problems, legal issues, or \
strong dissatisfaction. Use LOW for casual or general questions.
- "sentiment": one of {SENTIMENT_LEVELS}

Example:
Query: "I paid two days ago and still don't have access, this is unacceptable"
{{"intent": "Technical Issue", "intent_confidence": 0.88, "priority": "CRITICAL", "sentiment": "Negative"}}
"""


def _get_client():
    global _client
    if _client is None:
        _client = Groq(api_key=GROQ_API_KEY)
    return _client


def classify_query(query_text: str) -> dict:
    """
    Classifies a customer query. Returns:
    { intent, intent_confidence, priority, sentiment }

    Falls back to safe defaults if the LLM call fails or returns
    malformed output -- this must never crash the pipeline. A failed
    classification just means low confidence, which later (Day 11)
    routes the ticket to a human instead of guessing.
    """
    client = _get_client()
    try:
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": query_text},
            ],
            response_format={"type": "json_object"},
            temperature=0.1,
        )
        result = json.loads(response.choices[0].message.content)

        # Defensive validation -- never trust LLM output blindly
        if result.get("intent") not in INTENT_CATEGORIES:
            result["intent"] = "Other"
        if result.get("priority") not in PRIORITY_LEVELS:
            result["priority"] = "MEDIUM"
        if result.get("sentiment") not in SENTIMENT_LEVELS:
            result["sentiment"] = "Neutral"
        try:
            result["intent_confidence"] = float(result.get("intent_confidence", 0.0))
        except (TypeError, ValueError):
            result["intent_confidence"] = 0.0

        return result

    except Exception as e:
        print(f"[classify_query] LLM call failed, using safe defaults: {e}")
        return {
            "intent": "General Enquiry",
            "intent_confidence": 0.0,
            "priority": "MEDIUM",
            "sentiment": "Neutral",
        }
