"""
Priority + sentiment classification.

Implemented together with intent classification in
app/services/intent.py::classify_query() -- one Groq call covers intent,
priority, and sentiment at once (they're all "read this query" tasks over
the same input, so splitting them into separate calls would just double
or triple latency and cost for no benefit).

Kept as a separate module/name here for clarity against the architecture
diagram and repo structure, but this is a thin re-export, not a second
implementation.
"""

from app.services.intent import classify_query  # noqa: F401
