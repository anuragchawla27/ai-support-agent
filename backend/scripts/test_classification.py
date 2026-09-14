"""
Interactive test for intent/priority/sentiment classification (Day 7-8).

Doesn't need the FastAPI server or the database -- tests classify_query()
directly against Groq, so you get fast feedback on classification quality
before wiring up the full ticket endpoints.

Run:
    python backend/scripts/test_classification.py
"""

import sys
from pathlib import Path

from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parents[2]
BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))
load_dotenv(REPO_ROOT / ".env")

from app.services.intent import classify_query  # noqa: E402


def main():
    print("Classification test. Type a query (or 'quit' to exit).\n")
    while True:
        query = input("> ").strip()
        if not query or query.lower() in ("quit", "exit"):
            break

        result = classify_query(query)
        print(f"  intent:    {result['intent']}  (confidence={result['intent_confidence']:.2f})")
        print(f"  priority:  {result['priority']}")
        print(f"  sentiment: {result['sentiment']}\n")


if __name__ == "__main__":
    main()
