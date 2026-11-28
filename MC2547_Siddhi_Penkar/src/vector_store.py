"""
vector_store.py
----------------
Manages the FAISS vector database for BugAssist AI.

Responsibilities:
- Build a new FAISS index from document chunk embeddings.
- Save the index and associated chunk metadata to disk.
- Load an existing index and metadata from disk.
- Provide raw similarity search against the index.
"""

import os
import pickle
from typing import List, Dict, Tuple

import numpy as np
import faiss

from src.utils import FAISS_INDEX_PATH, FAISS_METADATA_PATH, FAISS_INDEX_DIR, get_logger

logger = get_logger(__name__)


class VectorStoreError(Exception):
    """Raised for FAISS index build/load/search failures."""
    pass


def build_faiss_index(embeddings: np.ndarray) -> faiss.Index:
    """
    Builds a new FAISS index (flat, inner-product on normalized vectors
    == cosine similarity) from the given embeddings.

    Args:
        embeddings (np.ndarray): Array of shape (n_chunks, embedding_dim).

    Returns:
        faiss.Index: The constructed FAISS index.
    """
    if embeddings is None or len(embeddings) == 0:
        raise VectorStoreError("Cannot build FAISS index: embeddings array is empty.")

    dimension = embeddings.shape[1]
    index = faiss.IndexFlatIP(dimension)  # cosine similarity via normalized vectors
    index.add(embeddings)
    logger.info(f"Built FAISS index with {index.ntotal} vectors (dim={dimension}).")
    return index


def save_faiss_index(index: faiss.Index, chunk_metadata: List[Dict]) -> None:
    """
    Persists the FAISS index and chunk metadata to disk.

    Args:
        index (faiss.Index): The FAISS index to save.
        chunk_metadata (List[Dict]): List of chunk records (text, source, chunk_id)
            in the same order they were added to the index.
    """
    os.makedirs(FAISS_INDEX_DIR, exist_ok=True)

    try:
        faiss.write_index(index, FAISS_INDEX_PATH)
        with open(FAISS_METADATA_PATH, "wb") as f:
            pickle.dump(chunk_metadata, f)
        logger.info(
            f"Saved FAISS index to '{FAISS_INDEX_PATH}' "
            f"and metadata to '{FAISS_METADATA_PATH}'."
        )
    except Exception as exc:
        logger.error(f"Failed to save FAISS index/metadata: {exc}")
        raise VectorStoreError(f"Failed to save FAISS index: {exc}")


def load_faiss_index() -> Tuple[faiss.Index, List[Dict]]:
    """
    Loads an existing FAISS index and its chunk metadata from disk.

    Returns:
        Tuple[faiss.Index, List[Dict]]: The loaded index and chunk metadata.

    Raises:
        VectorStoreError: If the index or metadata files do not exist or fail to load.
    """
    if not os.path.exists(FAISS_INDEX_PATH) or not os.path.exists(FAISS_METADATA_PATH):
        raise VectorStoreError(
            "No knowledge base found. Please upload PDFs and click "
            "'Create Knowledge Base' before searching."
        )

    try:
        index = faiss.read_index(FAISS_INDEX_PATH)
        with open(FAISS_METADATA_PATH, "rb") as f:
            chunk_metadata = pickle.load(f)
        logger.info(f"Loaded FAISS index with {index.ntotal} vectors.")
        return index, chunk_metadata
    except Exception as exc:
        logger.error(f"Failed to load FAISS index/metadata: {exc}")
        raise VectorStoreError(f"Failed to load existing knowledge base: {exc}")


def index_exists() -> bool:
    """Checks whether a saved FAISS index and metadata file exist on disk."""
    return os.path.exists(FAISS_INDEX_PATH) and os.path.exists(FAISS_METADATA_PATH)


def search_index(index: faiss.Index, query_embedding: np.ndarray,
                  top_k: int = 3) -> Tuple[np.ndarray, np.ndarray]:
    """
    Performs a similarity search against the FAISS index.

    Args:
        index (faiss.Index): The FAISS index to search.
        query_embedding (np.ndarray): 1D query embedding vector.
        top_k (int): Number of top results to retrieve.

    Returns:
        Tuple[np.ndarray, np.ndarray]: (scores, indices) arrays of shape (top_k,).
    """
    if index.ntotal == 0:
        raise VectorStoreError("The FAISS index is empty. Build the knowledge base first.")

    query_vector = np.asarray([query_embedding], dtype="float32")
    top_k = min(top_k, index.ntotal)

    scores, indices = index.search(query_vector, top_k)
    return scores[0], indices[0]
