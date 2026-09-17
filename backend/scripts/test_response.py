"""
Interactive test for the full Day 9-11 pipeline: retrieval -> grounded
response -> confidence scoring -> escalation decision.

Doesn't touch tickets or the database -- fast iteration on response
quality AND on confidence threshold calibration. Keeps conversation
history across turns in this session (conversation memory).

This is also a useful preview of Day 14's testing process: try a mix of
normal, ambiguous, and nonsense queries and watch where the confidence
score and escalate/resolve decision land.

Run:
    python backend/scripts/test_response.py
"""

import sys
from pathlib import Path

from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parents[2]
BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))
load_dotenv(REPO_ROOT / ".env")

from app.services.rag import retrieve  # noqa: E402
from app.services.response import generate_response  # noqa: E402
from app.services.confidence import compute_confidence, decide_outcome  # noqa: E402
from app.services.intent import classify_query  # noqa: E402


def main():
    print("Full pipeline test. Type a question (or 'quit' to exit).")
    print("Conversation memory is kept across turns in this session.\n")

    history = []
    while True:
        query = input("> ").strip()
        if not query or query.lower() in ("quit", "exit"):
            break

        classification = classify_query(query)
        chunks = retrieve(query, top_k=4)
        generation = generate_response(query, chunks, history)

        confidence = compute_confidence(
            chunks, generation["self_confidence"], classification["intent_confidence"]
        )
        decision = decide_outcome(
            confidence, classification["intent"], classification["priority"], classification["sentiment"]
        )

        print(f"\n  {generation['response']}\n")
        print(
            f"  intent: {classification['intent']} ({classification['intent_confidence']:.2f})"
            f"  priority: {classification['priority']}  sentiment: {classification['sentiment']}"
        )
        if chunks:
            print(f"  closest retrieval distance: {chunks[0]['distance']:.4f}")
        print(
            f"  self-reported grounded: {generation['grounded']}"
            f"  self_confidence: {generation['self_confidence']:.2f}"
        )

        outcome_label = "ESCALATE" if decision["escalate"] else "AUTO-RESOLVE"
        team_note = f" (team: {decision['assigned_team']})" if decision["escalate"] else ""
        print(f"  >>> final confidence: {confidence}  ->  {outcome_label}{team_note}")
        print(f"      reason: {decision['reason']}\n")

        history.append({"role": "customer", "content": query})
        history.append({"role": "assistant", "content": generation["response"]})


if __name__ == "__main__":
    main()
