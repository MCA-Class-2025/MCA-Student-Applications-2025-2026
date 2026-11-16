"""
settings.py — Centralised configuration for the Medicine Safety Intelligence AI.

All configuration is sourced from environment variables or .env file.
No secrets are hardcoded.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# ── Load .env from project root ──────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

# ── Streamlit Secrets compatibility ──────────────────────────────────────────
try:
    import streamlit as st
    # Access secrets safely — may not be available outside Streamlit context
    try:
        _secrets = st.secrets
    except Exception:
        _secrets = {}
except ImportError:
    _secrets = {}


def _get(key: str, default: str = "") -> str:
    """Read from env → Streamlit secrets → default."""
    env_val = os.getenv(key)
    if env_val:
        return env_val
    try:
        secret_val = _secrets.get(key, default)
        return secret_val if secret_val else default
    except Exception:
        return default


# ── LLM ──────────────────────────────────────────────────────────────────────
OPENAI_API_KEY: str = _get("OPENAI_API_KEY", "")
OPENAI_MODEL: str = _get("OPENAI_MODEL", "gpt-4o-mini")
# Optional — point the LLM client at another OpenAI-compatible provider
# (e.g. https://api.groq.com/openai/v1, https://openrouter.ai/api/v1, or a local
# Ollama/LM-Studio endpoint). Leave empty to use the default OpenAI API.
OPENAI_BASE_URL: str = _get("OPENAI_BASE_URL", "")
# Groq free tier (https://console.groq.com/keys) — preferred provider.
# When set, the LLM layer uses Groq automatically (model: GROQ_MODEL).
GROQ_API_KEY: str = _get("GROQ_API_KEY", "")
GROQ_MODEL: str = _get("GROQ_MODEL", "openai/gpt-oss-120b")

# ── API Keys ─────────────────────────────────────────────────────────────────
OPENFDA_API_KEY: str = _get("OPENFDA_API_KEY", "")
PUBMED_EMAIL: str = _get("PUBMED_EMAIL", "medicine-safety-ai@example.com")

# ── API Base URLs ─────────────────────────────────────────────────────────────
OPENFDA_BASE_URL = "https://api.fda.gov"
RXNORM_BASE_URL = "https://rxnav.nlm.nih.gov/REST"
DAILYMED_BASE_URL = "https://dailymed.nlm.nih.gov/dailymed/services/v2"
PUBMED_BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
CLINICALTRIALS_BASE_URL = "https://clinicaltrials.gov/api/v2"

# ── Cache ─────────────────────────────────────────────────────────────────────
CACHE_TTL: int = int(_get("CACHE_TTL", "3600"))

# ── Data directories ──────────────────────────────────────────────────────────
DATA_DIR = BASE_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
FUSED_DIR = DATA_DIR / "fused"

for _d in [RAW_DIR, PROCESSED_DIR, FUSED_DIR]:
    _d.mkdir(parents=True, exist_ok=True)

# ── API Timeouts / Retry ──────────────────────────────────────────────────────
REQUEST_TIMEOUT = 30          # seconds
MAX_RETRIES = 3
RETRY_BACKOFF_FACTOR = 1.0

# ── RAG / Embedding ───────────────────────────────────────────────────────────
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
CHUNK_SIZE = 512
CHUNK_OVERLAP = 64
TOP_K_RETRIEVAL = 6

# ── openFDA limits ────────────────────────────────────────────────────────────
OPENFDA_ADVERSE_LIMIT = 50
OPENFDA_LABEL_LIMIT = 5
OPENFDA_RECALL_LIMIT = 20

# ── PubMed limits ─────────────────────────────────────────────────────────────
PUBMED_MAX_RESULTS = 20

# ── ClinicalTrials limits ─────────────────────────────────────────────────────
CT_PAGE_SIZE = 20

# ── Logging ───────────────────────────────────────────────────────────────────
LOG_LEVEL = _get("APP_LOG_LEVEL", "INFO")
