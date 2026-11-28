"""
rag/vector_store.py — FAISS vector store for RAG retrieval.

Supports:
- Indexing chunks
- Similarity search
- Metadata storage
- Index persistence
- Index rebuilding
"""

import json
import pickle
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from config.settings import PROCESSED_DIR
from utils.logging import logger

# Lazy FAISS import
_faiss = None


def _get_faiss():
    global _faiss
    if _faiss is None:
        import faiss
        _faiss = faiss
    return _faiss


_INDEX_PATH = PROCESSED_DIR / "faiss_index"
_METADATA_PATH = PROCESSED_DIR / "faiss_metadata.pkl"


class FAISSVectorStore:
    """
    Lightweight FAISS-based vector store with metadata support.
    """

    def __init__(self):
        self.index = None
        self.metadata: List[Dict[str, Any]] = []
        self.texts: List[str] = []
        self.dimension: int = 384  # all-MiniLM-L6-v2 output dim

    def build_index(self, chunks: List[Dict[str, Any]]) -> None:
        """
        Build FAISS index from embedded chunks.
        Chunks must have 'embedding', 'content', and 'metadata' fields.
        """
        faiss = _get_faiss()

        embeddings = []
        texts = []
        metadata = []

        for chunk in chunks:
            emb = chunk.get("embedding")
            if emb is None:
                continue
            emb_arr = np.array(emb, dtype=np.float32)
            embeddings.append(emb_arr)
            texts.append(chunk.get("content", ""))
            metadata.append({
                "chunk_id": chunk.get("chunk_id", ""),
                "doc_id": chunk.get("doc_id", ""),
                "title": chunk.get("title", ""),
                "metadata": chunk.get("metadata", {}),
            })

        if not embeddings:
            logger.warning("No embeddings to index")
            return

        matrix = np.stack(embeddings, axis=0)
        self.dimension = matrix.shape[1]

        # Inner product index (works with normalized embeddings for cosine similarity)
        self.index = faiss.IndexFlatIP(self.dimension)
        self.index.add(matrix)
        self.texts = texts
        self.metadata = metadata

        logger.info(f"FAISS index built: {self.index.ntotal} vectors, dim={self.dimension}")

    def search(
        self,
        query_embedding: np.ndarray,
        top_k: int = 6,
    ) -> List[Dict[str, Any]]:
        """
        Search for top_k most similar chunks.
        Returns list of result dicts with score, text, and metadata.
        """
        if self.index is None or self.index.ntotal == 0:
            return []

        q = np.array(query_embedding, dtype=np.float32).reshape(1, -1)
        scores, indices = self.index.search(q, min(top_k, self.index.ntotal))

        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < 0 or idx >= len(self.texts):
                continue
            results.append({
                "score": float(score),
                "text": self.texts[idx],
                "metadata": self.metadata[idx],
            })

        return results

    def save(self, prefix: str = "drug") -> None:
        """Save FAISS index and metadata to disk."""
        faiss = _get_faiss()
        try:
            index_path = _INDEX_PATH.parent / f"faiss_{prefix}.index"
            meta_path = _METADATA_PATH.parent / f"faiss_{prefix}_meta.pkl"

            if self.index is not None:
                faiss.write_index(self.index, str(index_path))

            with open(meta_path, "wb") as f:
                pickle.dump(
                    {"metadata": self.metadata, "texts": self.texts, "dimension": self.dimension},
                    f,
                )
            logger.info(f"FAISS index saved to {index_path}")
        except Exception as e:
            logger.warning(f"Could not save FAISS index: {e}")

    def load(self, prefix: str = "drug") -> bool:
        """Load FAISS index from disk. Returns True if successful."""
        faiss = _get_faiss()
        try:
            index_path = _INDEX_PATH.parent / f"faiss_{prefix}.index"
            meta_path = _METADATA_PATH.parent / f"faiss_{prefix}_meta.pkl"

            if not index_path.exists() or not meta_path.exists():
                return False

            self.index = faiss.read_index(str(index_path))
            with open(meta_path, "rb") as f:
                saved = pickle.load(f)

            self.metadata = saved["metadata"]
            self.texts = saved["texts"]
            self.dimension = saved.get("dimension", 384)
            logger.info(f"FAISS index loaded: {self.index.ntotal} vectors")
            return True
        except Exception as e:
            logger.warning(f"Could not load FAISS index: {e}")
            return False

    @property
    def is_ready(self) -> bool:
        return self.index is not None and self.index.ntotal > 0

    @property
    def total_vectors(self) -> int:
        return self.index.ntotal if self.index else 0
