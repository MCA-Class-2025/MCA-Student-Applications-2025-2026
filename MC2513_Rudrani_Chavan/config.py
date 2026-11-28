import os

# Base Directories
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
DOCS_DIR = os.path.join(DATA_DIR, "documents")
DB_DIR = os.path.join(DATA_DIR, "db")

# Ensure directories exist
for directory in [DATA_DIR, DOCS_DIR, DB_DIR]:
    os.makedirs(directory, exist_ok=True)

# RAG Pipeline Configuration
EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
# Default Ollama LLM model. Gemma is lightweight and fits CPU-based local runs.
# The user can pull this using: ollama pull gemma:2b
OLLAMA_MODEL = os.environ.get("NUTRIMATE_LLM_MODEL", "gemma:2b")
OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")

# Text chunking configuration
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200
RETRIEVER_K = 6

# Pinterest UI styling config
PINTEREST_THEME = {
    "primary_color": "#3A5A40",      # Deep sage green
    "secondary_color": "#588157",    # Lighter green accent
    "background_color": "#F4F1DE",   # Warm beige background
    "card_background": "#FFFFFF",    # Soft white for cards
    "text_color": "#2F3E46",         # Charcoal gray for readability
    "accent_beige": "#E9D8A6"        # Sand/Beige highlights
}
