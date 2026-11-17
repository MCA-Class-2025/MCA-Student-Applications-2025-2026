"""
MovieMind AI
Improved FAISS Vector Store
Uses Cosine Similarity
"""

from pathlib import Path

import faiss
import numpy as np

# --------------------------------------------------
# Paths
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent

MODEL_DIR = BASE_DIR / "models"
FAISS_DIR = BASE_DIR / "faiss_db"

EMBEDDING_FILE = MODEL_DIR / "movie_embeddings.npy"
INDEX_FILE = FAISS_DIR / "movie.index"

# --------------------------------------------------
# Load Embeddings
# --------------------------------------------------

print("=" * 60)
print("Loading Movie Embeddings...")
print("=" * 60)

embeddings = np.load(EMBEDDING_FILE).astype("float32")

print("Embedding Shape :", embeddings.shape)

# --------------------------------------------------
# Normalize Embeddings
# --------------------------------------------------

print("\nNormalizing Embeddings...")

faiss.normalize_L2(embeddings)

# --------------------------------------------------
# Create Cosine Similarity Index
# --------------------------------------------------

dimension = embeddings.shape[1]

print("Creating FAISS Cosine Similarity Index...")

index = faiss.IndexFlatIP(dimension)

index.add(embeddings)

print("Total Movies Indexed :", index.ntotal)

# --------------------------------------------------
# Save Index
# --------------------------------------------------

FAISS_DIR.mkdir(exist_ok=True)

faiss.write_index(index, str(INDEX_FILE))

print("\nFAISS Index Saved Successfully!")

print("Location :", INDEX_FILE)

print("\nDone!")