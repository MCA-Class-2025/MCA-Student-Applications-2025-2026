"""
rag/embeddings.py — Embedding generation using sentence-transformers.

Model: sentence-transformers/all-MiniLM-L6-v2 (lightweight, ~80MB)
"""

from typing import Any, Dict, List, Optional

import numpy as np

from config.settings import EMBEDDING_MODEL
from utils.logging import logger

# Lazy load the model to avoid slow startup
_model = None


def _get_model():
    global _model
    if _model is None:
        try:
            from sentence_transformers import SentenceTransformer
            logger.info(f"Loading embedding model: {EMBEDDING_MODEL}")
            _model = SentenceTransformer(EMBEDDING_MODEL)
            logger.info("Embedding model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            raise
    return _model


def embed_texts(texts: List[str], batch_size: int = 32) -> np.ndarray:
    """
    Generate embeddings for a list of texts.
    Returns numpy array of shape (n_texts, embedding_dim).
    """
    if not texts:
        return np.array([])

    model = _get_model()
    try:
        embeddings = model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=len(texts) > 50,
            normalize_embeddings=True,  # For cosine similarity
        )
        logger.info(f"Generated {len(embeddings)} embeddings, dim={embeddings.shape[1]}")
        return embeddings
    except Exception as e:
        logger.error(f"Embedding generation failed: {e}")
        raise


def embed_query(query: str) -> np.ndarray:
    """Generate embedding for a single query string."""
    return embed_texts([query])[0]


def embed_chunks(chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Add embeddings to a list of chunk dicts.
    Returns chunks with 'embedding' field added.
    """
    texts = [c.get("content", "") for c in chunks]
    embeddings = embed_texts(texts)

    for chunk, emb in zip(chunks, embeddings):
        chunk["embedding"] = emb.tolist()

    return chunks
