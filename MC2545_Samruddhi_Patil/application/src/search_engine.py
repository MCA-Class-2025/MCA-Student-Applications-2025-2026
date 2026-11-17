"""
MovieMind AI
Improved Search Engine
"""

import pickle
from pathlib import Path

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

# --------------------------------------------------
# Paths
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent

MODEL_DIR = BASE_DIR / "models"
FAISS_DIR = BASE_DIR / "faiss_db"

# --------------------------------------------------
# Load Model
# --------------------------------------------------

print("Loading Sentence Transformer...")

model = SentenceTransformer("all-MiniLM-L6-v2")

print("Loading FAISS Index...")

index = faiss.read_index(str(FAISS_DIR / "movie.index"))

print("Loading Movie Metadata...")

with open(MODEL_DIR / "movie_metadata.pkl", "rb") as f:
    metadata = pickle.load(f)

print(f"Movies Loaded : {len(metadata)}")


# --------------------------------------------------
# Search Function
# --------------------------------------------------

def search_movies(query, top_k=5):

    query_lower = query.lower()

    # Encode query
    query_embedding = model.encode(
        [query],
        normalize_embeddings=True
    )

    # Search more results first
    distances, indices = index.search(
        np.array(query_embedding).astype("float32"),
        20
    )

    ranked_movies = []

    for score, idx in zip(distances[0], indices[0]):

        movie = metadata[idx]

        bonus = 0

        # Pull fields once and guard against NaN / missing values.
        # Some rows in the dataset have missing director/genres/title
        # values, which pandas represents as NaN (a float, not a
        # string) — calling .lower() on those crashes the search.
        title = movie.get("title")
        director = movie.get("director")
        genres = movie.get("genres_clean")

        # ----------------------------
        # Title Boost
        # ----------------------------

        if isinstance(title, str) and query_lower in title.lower():
            bonus += 0.50

        # ----------------------------
        # Director Boost
        # ----------------------------

        if isinstance(director, str) and director.lower() in query_lower:
            bonus += 0.40

        # ----------------------------
        # Genre Boost
        # ----------------------------

        if isinstance(genres, str):

            genres_lower = genres.lower()

            for word in query_lower.split():

                if word in genres_lower:
                    bonus += 0.15

        # ----------------------------
        # Final Score
        # ----------------------------

        final_score = float(score) + bonus

        ranked_movies.append((final_score, movie))

    # Sort by highest score
    ranked_movies.sort(
        key=lambda x: x[0],
        reverse=True
    )

    # Remove duplicates
    results = []

    seen_titles = set()

    for _, movie in ranked_movies:

        title = movie.get("title")

        if title and title not in seen_titles:

            results.append(movie)

            seen_titles.add(title)

        if len(results) == top_k:
            break

    return results