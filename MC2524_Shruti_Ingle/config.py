from dotenv import load_dotenv
import os

load_dotenv()

# Hugging Face API token

HF_API_TOKEN = os.getenv("HUGGINGFACEHUB_API_TOKEN")

# PDF text chunking

CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200

# Embedding model

EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

# Vector database storage path

VECTOR_DB_PATH = "vector_db"
