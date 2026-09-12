"""
Central configuration. All secrets/config come from environment variables
(.env file, loaded via docker-compose) -- never hardcoded, per project
security requirement (Section 15: API-key security).

Filled in properly starting Day 3-4 (DB URL, embedding model) and
Day 11 (confidence threshold).
"""

import os

# --- Database ---
DATABASE_URL = os.getenv("DATABASE_URL", "")  # postgresql://user:pass@host:5432/dbname

# --- LLM / Groq ---
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

# --- Embeddings (local, free -- fills the gap Groq leaves for RAG) ---
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")

# --- Confidence thresholds (Day 11: must be configurable, not hardcoded) ---
CONFIDENCE_AUTO_RESOLVE_THRESHOLD = float(os.getenv("CONFIDENCE_AUTO_RESOLVE_THRESHOLD", "0.75"))

# --- Dashboard auth (Section 15: dashboard must be protected) ---
DASHBOARD_PASSWORD = os.getenv("DASHBOARD_PASSWORD", "")
