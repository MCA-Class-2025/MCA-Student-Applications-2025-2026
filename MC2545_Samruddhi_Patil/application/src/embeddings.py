"""
MovieMind AI
Embedding Generation Module
"""

import pickle
from pathlib import Path

import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer

# ---------------------------------------------------
# Project Paths
# ---------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent

DATA_DIR = BASE_DIR / "data"
MODEL_DIR = BASE_DIR / "models"

INPUT_FILE = DATA_DIR / "processed_movies.csv"

EMBEDDING_FILE = MODEL_DIR / "movie_embeddings.npy"
METADATA_FILE = MODEL_DIR / "movie_metadata.pkl"

# ---------------------------------------------------
# Load Dataset
# ---------------------------------------------------

print("=" * 60)
print("Loading Processed Dataset...")
print("=" * 60)

df = pd.read_csv(INPUT_FILE)

print(f"Movies Loaded : {len(df)}")

# ---------------------------------------------------
# Load Embedding Model
# ---------------------------------------------------

print("\nLoading Sentence Transformer Model...")

model = SentenceTransformer("all-MiniLM-L6-v2")

print("Model Loaded Successfully!")

# ---------------------------------------------------
# Generate Embeddings
# ---------------------------------------------------

print("\nGenerating Movie Embeddings...")

embeddings = model.encode(
    df["search_text"].tolist(),
    batch_size=32,
    show_progress_bar=True,
    convert_to_numpy=True
)

# ---------------------------------------------------
# Save Embeddings
# ---------------------------------------------------

np.save(EMBEDDING_FILE, embeddings)

print("\nEmbeddings Saved!")

# ---------------------------------------------------
# Save Metadata
# ---------------------------------------------------

metadata = df.to_dict("records")

with open(METADATA_FILE, "wb") as file:
    pickle.dump(metadata, file)

print("Metadata Saved!")

print("\nEmbedding Shape :", embeddings.shape)

print("\nFiles Created:")
print(EMBEDDING_FILE)

print(METADATA_FILE)

print("\nDone!")