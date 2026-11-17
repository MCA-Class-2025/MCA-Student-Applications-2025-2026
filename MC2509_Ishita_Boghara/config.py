"""
BookMuse 2.0 - Configuration
"""

import os
import streamlit as st
from dotenv import load_dotenv

# Load .env only for local development
load_dotenv()

# Read API keys safely
# Local development uses .env.
# Streamlit Cloud can use .streamlit/secrets.toml.
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# Only access Streamlit secrets when a local secrets file actually exists.
secrets_path = os.path.join(".streamlit", "secrets.toml")

if os.path.isfile(secrets_path):
    try:
        GROQ_API_KEY = st.secrets.get("GROQ_API_KEY", GROQ_API_KEY)
        OPENAI_API_KEY = st.secrets.get("OPENAI_API_KEY", OPENAI_API_KEY)
    except Exception:
        pass
    
if not GROQ_API_KEY:
    print("⚠️ WARNING: GROQ_API_KEY not found")
    
# LLM Config
# Fast model for normal conversation and lightweight tasks
LLM_FAST_MODEL = "openai/gpt-oss-20b"

# Powerful model for complex literary analysis
LLM_MODEL = "qwen/qwen3.8-27b"

# Generation settings
LLM_TEMP = 0.7

# Keep normal responses reasonably short for faster generation
LLM_MAX_TOKENS = 1024

# Maximum tokens for deep-analysis tasks
LLM_DEEP_MAX_TOKENS = 1536

# Voice Config
VOICE_LANGUAGES = ["en-US", "hi-IN"]

# Image Config
IMAGE_MODEL = "dall-e-3"
IMAGE_SIZE = "1024x1024"

# Embedding Config
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
EMBEDDING_DIM = 384

# Genre Categories
GENRES = [
    "Mystery",
    "Romance",
    "Science Fiction",
    "Fantasy",
    "Thriller",
    "Historical Fiction",
    "Self-Help",
    "Memoir",
    "Comedy",
    "Drama",
    "Horror",
    "Adventure",
]

# Supported Languages
LANGUAGES = {
    "English": "en-US",
    "Hindi": "hi-IN",
}