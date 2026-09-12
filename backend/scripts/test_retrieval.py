"""
Interactive test for the RAG retrieval function (Day 5-6).

Run locally the same way as ingest_knowledge_base.py:
    python backend/scripts/test_retrieval.py

Type a question, see the top matching knowledge base chunks and their
distance scores (lower = more relevant). Type 'quit' to exit.
"""

import sys
from pathlib import Path

from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parents[2]
BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))
load_dotenv(REPO_ROOT / ".env")

from app.services.rag import retrieve  # noqa: E402


def main():
    print("RAG retrieval test. Type a question (or 'quit' to exit).\n")
    while True:
        query = input("> ").strip()
        if not query or query.lower() in ("quit", "exit"):
            break

        results = retrieve(query, top_k=3)
        if not results:
            print("  No results found.\n")
            continue

        for i, r in enumerate(results, 1):
            preview = r["content"][:150] + ("..." if len(r["content"]) > 150 else "")
            print(f"  [{i}] {r['source_file']} -> {r['section_title']}  (distance={r['distance']:.4f})")
            print(f"      {preview}")
        print()


if __name__ == "__main__":
    main()
