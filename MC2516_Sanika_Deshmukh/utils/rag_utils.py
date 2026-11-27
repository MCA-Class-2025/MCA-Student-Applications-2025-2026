"""
rag_utils.py — Lightweight RAG (Retrieval-Augmented Generation) for PlatePal
------------------------------------------------------------------------------
How it works:
1. Every time a food is analyzed, the result is embedded using Gemini's
   free text-embedding model and stored in a local JSON vector store.
2. When the user asks a question, their query is also embedded.
3. The most similar past analyses are retrieved (cosine similarity).
4. These are injected into the Gemini chat prompt as extra context,
   making answers smarter and personalized to the user's food history.

Vector store: plain JSON file (no heavy dependencies like FAISS or Chroma)
Embedding model: Gemini text-embedding-004 (free, via REST API)
Similarity: cosine similarity with numpy
"""

import json
import os
from datetime import datetime

import numpy as np
import requests

VECTOR_STORE_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "rag_vector_store.json"
)

EMBED_URL = "https://generativelanguage.googleapis.com/v1beta/models/text-embedding-004:embedContent"
TIMEOUT   = 30


def get_embedding(text: str, api_key: str):
    """Get a 768-dim embedding from Gemini text-embedding-004. Returns None on failure."""
    try:
        resp = requests.post(
            EMBED_URL,
            params={"key": api_key},
            json={
                "model": "models/text-embedding-004",
                "content": {"parts": [{"text": text[:8000]}]},
                "taskType": "RETRIEVAL_DOCUMENT",
            },
            timeout=TIMEOUT,
        )
        if resp.status_code == 200:
            return resp.json()["embedding"]["values"]
        return None
    except Exception:
        return None


def cosine_similarity(a, b) -> float:
    va = np.array(a, dtype=np.float32)
    vb = np.array(b, dtype=np.float32)
    dot  = float(np.dot(va, vb))
    norm = float(np.linalg.norm(va) * np.linalg.norm(vb))
    return dot / norm if norm > 0 else 0.0


def _load_store() -> list:
    if not os.path.exists(VECTOR_STORE_FILE):
        return []
    try:
        with open(VECTOR_STORE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def _save_store(store: list) -> None:
    with open(VECTOR_STORE_FILE, "w", encoding="utf-8") as f:
        json.dump(store, f, ensure_ascii=False, indent=2)


def add_to_vector_store(dish_name: str, analysis_text: str, api_key: str, extra_metadata: dict = None) -> bool:
    """
    Embed and store a food analysis.
    If embedding fails (rate limit / API error), stores without embedding
    so the counter always increments and text search still works.
    Returns True always (stored either with or without embedding).
    """
    text_to_embed = f"Dish: {dish_name}\n\n{analysis_text}"
    embedding = get_embedding(text_to_embed, api_key)  # None if fails — that's OK

    store = _load_store()

    # Avoid exact duplicate entries for the same dish in the same minute
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    for existing in store:
        if existing.get("dish_name") == dish_name and existing.get("timestamp") == now_str:
            return True  # already stored this minute

    store.append({
        "id":        len(store),
        "timestamp": now_str,
        "dish_name": dish_name,
        "text":      analysis_text[:1500],
        "embedding": embedding,   # may be None — handled gracefully in retrieve_similar
        "metadata":  extra_metadata or {},
    })
    _save_store(store)
    return True


def retrieve_similar(query: str, api_key: str, top_k: int = 3, min_score: float = 0.45) -> list:
    """Embed query and return top_k most similar past analyses."""
    store = _load_store()
    if not store:
        return []
    query_emb = get_embedding(query, api_key)
    if query_emb is None:
        return []
    scored = sorted(
        [(cosine_similarity(query_emb, e["embedding"]), e)
         for e in store if e.get("embedding")],
        key=lambda x: x[0], reverse=True
    )
    return [{"score": round(s, 3), **e} for s, e in scored[:top_k] if s >= min_score]


def build_rag_context(similar_entries: list) -> str:
    """Format retrieved entries as context string for Gemini prompt."""
    if not similar_entries:
        return ""
    lines = ["[RAG Context — Similar dishes from your history:]"]
    for i, e in enumerate(similar_entries, 1):
        lines.append(f"\n{i}. {e['dish_name']} ({e['timestamp']}, similarity {e['score']}):\n{e['text'][:400]}")
    return "\n".join(lines)


def get_store_stats() -> dict:
    store = _load_store()
    if not store:
        return {"count": 0, "dishes": [], "latest": None}
    return {
        "count":  len(store),
        "dishes": list(dict.fromkeys(e["dish_name"] for e in store))[:10],
        "latest": store[-1]["timestamp"],
    }


def clear_vector_store() -> None:
    if os.path.exists(VECTOR_STORE_FILE):
        os.remove(VECTOR_STORE_FILE)
