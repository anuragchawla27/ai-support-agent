"""
Ingestion script (Day 3-4 / Day 5-6 groundwork).

Reads every .md file in knowledge_base/docs/, splits each into chunks by
"## " section headers, embeds each chunk with sentence-transformers, and
loads them into the knowledge_chunks table (pgvector).

Run this locally (not inside Docker) -- it's a one-off/periodic job, not
a running service:

    1. python -m venv venv
       venv\\Scripts\\activate            (Windows)
    2. pip install -r backend/requirements.txt
    3. docker-compose up -d postgres      (from repo root -- just the DB)
    4. python backend/scripts/ingest_knowledge_base.py

Safe to re-run any time the knowledge base docs change -- it clears the
table and re-embeds everything from scratch each time.
"""

import sys
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import text as sql_text

# Repo layout: backend/scripts/this_file.py
#              backend/app/...
#              knowledge_base/docs/...
#              .env
REPO_ROOT = Path(__file__).resolve().parents[2]
BACKEND_DIR = Path(__file__).resolve().parents[1]
KB_DIR = REPO_ROOT / "knowledge_base" / "docs"

# Make "app" importable when running this script directly
sys.path.insert(0, str(BACKEND_DIR))

# Load .env BEFORE importing anything that reads env vars via config.py
load_dotenv(REPO_ROOT / ".env")

from app.db.session import engine, SessionLocal, Base  # noqa: E402
from app.db.models import KnowledgeChunk  # noqa: E402
from app.config import EMBEDDING_MODEL  # noqa: E402


def chunk_markdown(raw_text: str):
    """
    Splits a markdown doc into (title, content) chunks, one per "## "
    section. Any text before the first "## " (usually the intro
    paragraph under the single "# " title) becomes its own chunk too.
    """
    lines = raw_text.splitlines()
    chunks = []
    doc_title = None
    seen_h1 = False
    current_title = None
    current_lines = []
    intro_lines = []

    def flush_intro():
        text = "\n".join(intro_lines).strip()
        if text:
            chunks.append((doc_title or "Overview", text))

    for line in lines:
        if line.startswith("# ") and not seen_h1:
            doc_title = line[2:].strip()
            seen_h1 = True
            continue
        if line.startswith("## "):
            if current_title is not None:
                chunks.append((current_title, "\n".join(current_lines).strip()))
            else:
                flush_intro()
            current_title = line[3:].strip()
            current_lines = []
        else:
            (current_lines if current_title is not None else intro_lines).append(line)

    if current_title is not None:
        chunks.append((current_title, "\n".join(current_lines).strip()))
    else:
        flush_intro()

    return chunks


def main():
    print(f"Loading embedding model: {EMBEDDING_MODEL} (first run downloads it, ~90MB) ...")
    from sentence_transformers import SentenceTransformer  # imported late: slow import
    model = SentenceTransformer(EMBEDDING_MODEL)

    print("Connecting to database and ensuring pgvector extension + tables exist ...")
    with engine.connect() as conn:
        conn.execute(sql_text("CREATE EXTENSION IF NOT EXISTS vector"))
        conn.commit()
    Base.metadata.create_all(engine)

    if not KB_DIR.exists():
        print(f"ERROR: knowledge base folder not found at {KB_DIR}")
        return

    md_files = sorted(KB_DIR.glob("*.md"))
    if not md_files:
        print(f"No markdown files found in {KB_DIR}")
        return

    db = SessionLocal()
    db.query(KnowledgeChunk).delete()  # re-ingest from scratch each run
    db.commit()

    total_chunks = 0
    for md_file in md_files:
        raw = md_file.read_text(encoding="utf-8")
        chunks = chunk_markdown(raw)
        for title, content in chunks:
            if not content:
                continue
            # Embed title + content together so section context is captured
            vector = model.encode(f"{title}\n{content}").tolist()
            db.add(KnowledgeChunk(
                source_file=md_file.name,
                section_title=title,
                content=content,
                embedding=vector,
            ))
            total_chunks += 1
        print(f"  {md_file.name}: {len(chunks)} chunks")

    db.commit()
    db.close()
    print(f"\nDone. Ingested {total_chunks} chunks from {len(md_files)} files.")


if __name__ == "__main__":
    main()
