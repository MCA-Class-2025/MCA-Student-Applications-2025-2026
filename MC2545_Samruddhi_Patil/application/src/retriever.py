"""
MovieMind AI
Semantic Retriever
"""

import pickle
from pathlib import Path

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

# ---------------------------------------------------
# Paths
# ---------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent

MODEL_DIR = BASE_DIR / "models"
FAISS_DIR = BASE_DIR / "faiss_db"

INDEX_FILE = FAISS_DIR / "movie.index"
METADATA_FILE = MODEL_DIR / "movie_metadata.pkl"

# ---------------------------------------------------
# Load Model
# ---------------------------------------------------

print("=" * 60)
print("Loading Model...")
print("=" * 60)

model = SentenceTransformer("all-MiniLM-L6-v2")

print("Model Loaded!")

# ---------------------------------------------------
# Load FAISS
# ---------------------------------------------------

index = faiss.read_index(str(INDEX_FILE))

print("FAISS Loaded!")

# ---------------------------------------------------
# Load Metadata
# ---------------------------------------------------

with open(METADATA_FILE, "rb") as file:
    metadata = pickle.load(file)

print("Metadata Loaded!")

print("\nReady!")

# ---------------------------------------------------
# Search Loop
# ---------------------------------------------------

while True:

    query = input("\nAsk about movies (type 'exit' to quit): ")

    if query.lower() == "exit":
        break

    query_embedding = model.encode([query])

    distances, indices = index.search(
        np.array(query_embedding).astype("float32"),
        5
    )

    print("\n" + "=" * 70)
    print("Top Movie Recommendations")
    print("=" * 70)

    for rank, idx in enumerate(indices[0], start=1):

        movie = metadata[idx]

        print(f"\n🎬 {rank}. {movie['title']}")
        print(f"⭐ Rating : {movie['vote_average']}")
        print(f"🎭 Genres : {movie['genres_clean']}")
        print(f"🎥 Director : {movie['director']}")
        print(f"📅 Release : {movie['release_date']}")

        print("\nOverview:")
        print(movie["overview"][:300] + "...")

        print("-" * 70)