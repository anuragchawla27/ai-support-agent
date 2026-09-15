"""
Full pipeline dry-run test (Day 11).

Chains classify -> retrieve -> respond -> confidence -> escalation
decision, all without touching the database or ticket endpoints. Useful
for quickly seeing the whole decision end-to-end, and for calibrating
CONFIDENCE_AUTO_RESOLVE_THRESHOLD (in .env) before Day 14's full test
suite runs 30-50 queries through the real system.

Run:
    python backend/scripts/test_full_pipeline.py
"""

import sys
from pathlib import Path

from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parents[2]
BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))
load_dotenv(REPO_ROOT / ".env")

from app.services.intent import classify_query  # noqa: E402
from app.services.rag import retrieve  # noqa: E402
from app.services.response import generate_response  # noqa: E402
from app.services.confidence import compute_confidence, decide_escalation, assign_team  # noqa: E402


def main():
    print("Full pipeline test. Type a question (or 'quit' to exit).\n")
    while True:
        query = input("> ").strip()
        if not query or query.lower() in ("quit", "exit"):
            break

        classification = classify_query(query)
        chunks = retrieve(query, top_k=3)
        response = generate_response(query, chunks)
        confidence = compute_confidence(classification["intent_confidence"], chunks, response)
        escalate = decide_escalation(
            confidence["confidence_score"], classification["priority"], classification["intent"]
        )
        team = assign_team(classification["intent"]) if escalate else None

        print(f"\n  intent:      {classification['intent']}  (confidence={classification['intent_confidence']:.2f})")
        print(f"  priority:    {classification['priority']}")
        print(f"  sentiment:   {classification['sentiment']}")
        print(f"  response:    {response}")
        if chunks:
            print(f"  retrieval:   closest distance={chunks[0]['distance']:.4f}")
        else:
            print("  retrieval:   no chunks found")
        print(f"  confidence:  {confidence['confidence_score']:.4f}  (uncertainty_detected={confidence['uncertainty_detected']})")
        print(f"  decision:    {'ESCALATE -> ' + team if escalate else 'AUTO-RESOLVE'}")
        print()


if __name__ == "__main__":
    main()
