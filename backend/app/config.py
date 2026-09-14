"""
Central configuration. All secrets/config come from environment variables
(.env file) -- never hardcoded, per project security requirement
(Section 15: API-key security).

Loads .env directly here so it doesn't matter how the app is started
(uvicorn, a script, Docker) -- this always runs first, before any value
below is read. In Docker, real env vars are already injected via
docker-compose, so this load_dotenv() call is a harmless no-op there
(it never overrides variables that are already set).
"""

import os
from pathlib import Path

from dotenv import load_dotenv

# app/config.py -> app/ -> backend/ -> repo root
REPO_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(REPO_ROOT / ".env")

# --- Database ---
DATABASE_URL = os.getenv("DATABASE_URL", "")  # postgresql://user:pass@host:5432/dbname

# --- LLM / Groq ---
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")

# --- Embeddings (local, free -- fills the gap Groq leaves for RAG) ---
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")

# --- Confidence thresholds (Day 11: must be configurable, not hardcoded) ---
CONFIDENCE_AUTO_RESOLVE_THRESHOLD = float(os.getenv("CONFIDENCE_AUTO_RESOLVE_THRESHOLD", "0.75"))

# --- Dashboard auth (Section 15: dashboard must be protected) ---
DASHBOARD_PASSWORD = os.getenv("DASHBOARD_PASSWORD", "")
