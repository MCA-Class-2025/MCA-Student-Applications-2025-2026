"""
vector_store.py
----------------
Phase 5 of the RAG pipeline: Vector database operations using FAISS.
FAISS is chosen because it is local, free, fast, and requires no external
service/API key -- ideal for a Streamlit Community Cloud deployment.
"""

import os
import json
import pickle
from typing import List, Dict, Tuple

import numpy as np
import faiss


class PolicyVectorStore:
    """A thin wrapper around a FAISS IndexFlatIP index plus a metadata store."""

    def __init__(self, embedding_dim: int = 384):
        self.embedding_dim = embedding_dim
        self.index = faiss.IndexFlatIP(embedding_dim)   # inner product == cosine on normalized vecs
        self.chunk_metadata: List[Dict] = []             # parallel array: index i -> metadata for vector i

    def add(self, embeddings: np.ndarray, chunks: List) -> None:
        """Adds embeddings and their corresponding Chunk objects to the store."""
        assert embeddings.shape[0] == len(chunks), "Embeddings and chunks length mismatch"
        self.index.add(embeddings)
        for chunk in chunks:
            self.chunk_metadata.append({
                "chunk_id": chunk.chunk_id,
                "text": chunk.text,
                "source_file": chunk.source_file,
                "doc_title": chunk.doc_title,
                "chunk_index": chunk.chunk_index,
                "metadata": chunk.metadata,
            })

    def search(self, query_embedding: np.ndarray, top_k: int = 4) -> List[Dict]:
        """Returns the top_k most similar chunks with similarity scores."""
        if self.index.ntotal == 0:
            return []
        top_k = min(top_k, self.index.ntotal)
        scores, indices = self.index.search(query_embedding, top_k)
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx == -1:
                continue
            entry = dict(self.chunk_metadata[idx])
            entry["score"] = float(score)
            results.append(entry)
        return results

    def save(self, directory: str) -> None:
        """Persists the FAISS index and metadata to disk."""
        os.makedirs(directory, exist_ok=True)
        faiss.write_index(self.index, os.path.join(directory, "index.faiss"))
        with open(os.path.join(directory, "metadata.pkl"), "wb") as f:
            pickle.dump(self.chunk_metadata, f)
        with open(os.path.join(directory, "config.json"), "w") as f:
            json.dump({"embedding_dim": self.embedding_dim, "total_vectors": self.index.ntotal}, f)

    @classmethod
    def load(cls, directory: str) -> "PolicyVectorStore":
        """Loads a previously saved FAISS index and metadata from disk."""
        with open(os.path.join(directory, "config.json"), "r") as f:
            config = json.load(f)
        store = cls(embedding_dim=config["embedding_dim"])
        store.index = faiss.read_index(os.path.join(directory, "index.faiss"))
        with open(os.path.join(directory, "metadata.pkl"), "rb") as f:
            store.chunk_metadata = pickle.load(f)
        return store

    @staticmethod
    def exists(directory: str) -> bool:
        return os.path.exists(os.path.join(directory, "index.faiss")) and \
               os.path.exists(os.path.join(directory, "metadata.pkl"))
