"""
Interactive test for grounded response generation (Day 9-10).

Chains retrieve() + generate_response() directly, without touching
tickets or the database -- fast iteration on prompt/response quality.

Keeps conversation history across turns in this session, so you can test
follow-up questions and see if conversation memory actually helps (e.g.
ask about "standard support automation pricing", then ask "what about
the enterprise tier?" and see if it understands the follow-up).

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


def main():
    print("Response generation test. Type a question (or 'quit' to exit).")
    print("Conversation memory is kept across turns in this session.\n")

    history = []
    while True:
        query = input("> ").strip()
        if not query or query.lower() in ("quit", "exit"):
            break

        chunks = retrieve(query, top_k=3)
        response = generate_response(query, chunks, history)

        print(f"\n  {response}\n")
        if chunks:
            print(f"  (grounded in {len(chunks)} chunks, closest distance={chunks[0]['distance']:.4f})")
        else:
            print("  (no chunks retrieved -- response should be an honest 'I don't know')")
        print()

        history.append({"role": "customer", "content": query})
        history.append({"role": "assistant", "content": response})


if __name__ == "__main__":
    main()
