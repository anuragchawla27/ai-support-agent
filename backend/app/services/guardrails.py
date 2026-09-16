"""
Guardrails against prompt injection and malicious inputs (Day 13,
Section 15: "Prompt injection & Malicious inputs: Build guardrails
against jailbreaks").

Two layers, since neither alone is reliable:
1. A defensive instruction baked into every system prompt (see
   app.services.intent and app.services.response) telling the model to
   treat the customer's message as data, never as new instructions.
2. A lightweight heuristic here that flags obviously suspicious input
   (not to block it outright -- keyword blocking is easy to evade and
   produces false positives -- but to force a human review instead of
   letting a flagged query auto-resolve, regardless of how confident
   the AI's response looks).
"""

import re

INJECTION_PATTERNS = [
    r"ignore (all |the )?(previous|prior|above) instructions",
    r"disregard (all |the )?(previous|prior|above)",
    r"you are now",
    r"forget (all |your )?(previous |prior )?instructions",
    r"reveal (your |the )?(system prompt|instructions)",
    r"what (is|are) your (system prompt|instructions)",
    r"act as (if you|a| an)",
    r"pretend (you're|you are|to be)",
    r"bypass (your |the )?(guidelines|restrictions|rules)",
    r"developer mode",
    r"jailbreak",
]

_COMPILED_PATTERNS = [re.compile(p, re.IGNORECASE) for p in INJECTION_PATTERNS]


def contains_injection_attempt(text: str) -> bool:
    """Heuristic check for common prompt-injection phrasing. A positive
    match doesn't block the query -- it forces escalation instead, since
    a human reviewing a flagged message is much safer than an automated
    system guessing whether an attempt actually succeeded."""
    if not text:
        return False
    return any(pattern.search(text) for pattern in _COMPILED_PATTERNS)
