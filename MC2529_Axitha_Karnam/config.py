import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

CHROMA_DB = os.path.join(BASE_DIR, "chroma_db")

UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")

PDF_FOLDER = os.path.join(BASE_DIR, "data", "pdfs")

MODEL_NAME = "gemma3:1b"

EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

PROJECT_NAME = "Smart Personal Finance Assistant"

PROJECT_VERSION = "1.0"