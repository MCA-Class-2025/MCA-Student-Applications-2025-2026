"""
dataset_index.py
----------------
Build and load a FAISS index for the fused bug dataset.
"""

import os
import pickle
import pandas as pd
import numpy as np
import faiss

from src.embedding import encode_documents
from src.utils import FAISS_INDEX_DIR, get_logger

logger = get_logger(__name__)

DATASET_INDEX_PATH = os.path.join(FAISS_INDEX_DIR, "dataset.index")
DATASET_METADATA_PATH = os.path.join(FAISS_INDEX_DIR, "dataset_metadata.pkl")


def build_dataset_index(df: pd.DataFrame):
    """
    Build a FAISS index from the fused dataset.
    We embed the concatenation of title, description, and root cause analysis.
    Metadata stores the full row for retrieval.
    """
    if df is None or df.empty:
        logger.error("Cannot build dataset index: DataFrame is empty.")
        return None, None

    # Combine text fields for embedding
    texts = df.apply(
    lambda row: f"{row['title']} {row.get('description', '')} {row.get('root_cause', '')} {row.get('gemini_root_cause_analysis', '')}",
    axis=1
).tolist()

    try:
        embeddings = encode_documents(texts)
    except Exception as e:
        logger.error(f"Failed to encode dataset texts: {e}")
        return None, None

    dimension = embeddings.shape[1]
    index = faiss.IndexFlatIP(dimension)  # cosine similarity via normalized vectors
    index.add(embeddings)

    # Metadata: store the whole row as dict
    metadata = df.to_dict('records')

    # Save to disk
    os.makedirs(FAISS_INDEX_DIR, exist_ok=True)
    faiss.write_index(index, DATASET_INDEX_PATH)
    with open(DATASET_METADATA_PATH, 'wb') as f:
        pickle.dump(metadata, f)

    logger.info(f"Built dataset index with {len(df)} bugs. Saved to {DATASET_INDEX_PATH}")
    return index, metadata


def load_dataset_index():
    """Load the dataset index and metadata from disk."""
    if not os.path.exists(DATASET_INDEX_PATH) or not os.path.exists(DATASET_METADATA_PATH):
        return None, None
    index = faiss.read_index(DATASET_INDEX_PATH)
    with open(DATASET_METADATA_PATH, 'rb') as f:
        metadata = pickle.load(f)
    return index, metadata


def dataset_index_exists():
    """Check if dataset index files exist."""
    return os.path.exists(DATASET_INDEX_PATH) and os.path.exists(DATASET_METADATA_PATH)