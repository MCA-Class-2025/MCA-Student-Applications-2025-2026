import os

# Embedding Model
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

# LLM Model (Ollama)
LLM_MODEL = "phi3:mini"

# Vector Database Folder
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
VECTOR_DB_PATH = str(PROJECT_ROOT / "llm" / "vector_store")

# Chunk Settings
CHUNK_SIZE = 800
CHUNK_OVERLAP = 150

# Supported File Types
SUPPORTED_EXTENSIONS = [
    ".pdf",
    ".txt",
    ".docx",
    ".csv"
]