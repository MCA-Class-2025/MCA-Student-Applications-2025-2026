"""
embedding.py
------------
Generates semantic embeddings for document chunks and user queries using
SentenceTransformer ("all-MiniLM-L6-v2").

The model is loaded once and cached (via a module-level singleton) so that
repeated calls do not reload the model from disk/hub each time.
"""

from typing import List
import numpy as np

from sentence_transformers import SentenceTransformer

from src.utils import MODELS_DIR, get_logger

logger = get_logger(__name__)

EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"

_model_instance = None


def load_embedding_model() -> SentenceTransformer:
    """
    Loads (or returns a cached instance of) the SentenceTransformer embedding model.

    Returns:
        SentenceTransformer: The loaded embedding model.
    """
    global _model_instance

    if _model_instance is not None:
        return _model_instance

    try:
        logger.info(f"Loading embedding model '{EMBEDDING_MODEL_NAME}'...")
        _model_instance = SentenceTransformer(
            EMBEDDING_MODEL_NAME,
            cache_folder=MODELS_DIR,
        )
        logger.info("Embedding model loaded successfully.")
    except Exception as exc:
        logger.error(f"Failed to load embedding model: {exc}")
        raise RuntimeError(
            f"Could not load embedding model '{EMBEDDING_MODEL_NAME}'. "
            f"Check your internet connection or local model cache. Details: {exc}"
        )

    return _model_instance


def encode_documents(texts: List[str]) -> np.ndarray:
    """
    Encodes a list of document chunk texts into embeddings.

    Args:
        texts (List[str]): List of text chunks.

    Returns:
        np.ndarray: 2D array of shape (num_texts, embedding_dim), dtype float32.
    """
    if not texts:
        raise ValueError("No texts provided for embedding.")

    model = load_embedding_model()
    embeddings = model.encode(
        texts,
        batch_size=32,
        show_progress_bar=False,
        convert_to_numpy=True,
        normalize_embeddings=True,
    )
    return np.asarray(embeddings, dtype="float32")


def encode_query(query: str) -> np.ndarray:
    """
    Encodes a single user query string into an embedding vector.

    Args:
        query (str): The user's natural language query.

    Returns:
        np.ndarray: 1D array of shape (embedding_dim,), dtype float32.
    """
    if not query or not query.strip():
        raise ValueError("Query text is empty.")

    model = load_embedding_model()
    embedding = model.encode(
        [query.strip()],
        show_progress_bar=False,
        convert_to_numpy=True,
        normalize_embeddings=True,
    )
    return np.asarray(embedding, dtype="float32")[0]


def get_embedding_dimension() -> int:
    """Returns the dimensionality of the embedding model's output vectors."""
    model = load_embedding_model()
    return model.get_sentence_embedding_dimension()
