"""
Phase 2: semantic retrieval.

Chunks the document, embeds chunks with sentence-transformers, and
indexes them with FAISS for nearest-neighbour (cosine, via inner product
on normalized vectors) search. Kept separate from Phase 1's text_utils.py
so the app still runs without these (heavier) dependencies installed.
"""

import numpy as np
import streamlit as st

import faiss
from sentence_transformers import SentenceTransformer

CHUNK_SIZE_WORDS = 220
CHUNK_OVERLAP_WORDS = 40
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"  # small, fast, well-suited to a laptop demo


@st.cache_resource(show_spinner=False)
def load_embedding_model():
    """Cached across reruns/sessions so the model is only downloaded/loaded once."""
    return SentenceTransformer(EMBEDDING_MODEL_NAME)


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE_WORDS, overlap: int = CHUNK_OVERLAP_WORDS) -> list:
    """Word-based sliding-window chunking. Simple and dependency-free;
    swap for a token-aware splitter (e.g. from langchain) if needed later."""
    words = text.split()
    if not words:
        return []
    chunks = []
    start = 0
    step = max(chunk_size - overlap, 1)
    while start < len(words):
        chunk_words = words[start : start + chunk_size]
        chunk = " ".join(chunk_words).strip()
        if chunk:
            chunks.append(chunk)
        start += step
    return chunks


class DocumentIndex:
    """A FAISS index over one document's chunks, plus the chunks themselves
    so we can return the original text on retrieval. Optionally carries
    parallel metadata (e.g. {"id": ..., "name": ...}) per chunk, so
    retrieved context can be labeled for the LLM and cited to the user."""

    def __init__(self, chunks: list, metadata: list | None = None):
        self.chunks = chunks
        self.metadata = metadata or [{} for _ in chunks]
        model = load_embedding_model()
        embeddings = model.encode(
            chunks, normalize_embeddings=True, show_progress_bar=False
        )
        embeddings = np.asarray(embeddings, dtype="float32")
        self.dim = embeddings.shape[1]
        # Inner product on normalized vectors == cosine similarity
        self.index = faiss.IndexFlatIP(self.dim)
        self.index.add(embeddings)

    def search(self, query: str, k: int = 4) -> list:
        model = load_embedding_model()
        q_emb = model.encode([query], normalize_embeddings=True)
        q_emb = np.asarray(q_emb, dtype="float32")
        scores, idxs = self.index.search(q_emb, k)
        results = []
        for score, idx in zip(scores[0], idxs[0]):
            if idx == -1:
                continue
            results.append({"text": self.chunks[idx], "score": float(score), **self.metadata[idx]})
        return results


def build_index(full_text: str) -> DocumentIndex:
    chunks = chunk_text(full_text)
    return DocumentIndex(chunks)


def build_index_from_texts(texts: list, metadata: list | None = None) -> DocumentIndex:
    """Build an index directly from a list of pre-formed text chunks
    (e.g. one per structured dataset record), skipping the word-based
    chunker used for raw PDF text. `metadata`, if given, must be the
    same length as `texts` (before filtering blanks) and is carried
    alongside each chunk for citation."""
    if metadata is None:
        clean = [t.strip() for t in texts if t and t.strip()]
        return DocumentIndex(clean)

    clean_texts, clean_meta = [], []
    for t, m in zip(texts, metadata):
        if t and t.strip():
            clean_texts.append(t.strip())
            clean_meta.append(m)
    return DocumentIndex(clean_texts, clean_meta)
