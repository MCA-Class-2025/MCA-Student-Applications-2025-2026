"""
embeddings.py
-------------
Phase 4 of the RAG pipeline: Embedding generation using the Cohere Embed API
(hosted, HTTPS-only). This avoids ALL local native-library dependencies
(no torch, no onnxruntime), which sidesteps DLL-loading issues that some
locked-down Windows machines (corporate antivirus/EDR) run into with any
package that ships compiled binaries.

Get a free Cohere trial key at: https://dashboard.cohere.com/api-keys
"""

from typing import List
import numpy as np
import requests

COHERE_EMBED_URL = "https://api.cohere.com/v1/embed"
DEFAULT_MODEL = "embed-english-v3.0"   # 1024-dim


def _call_cohere_embed(texts: List[str], api_key: str, input_type: str,
                        model: str = DEFAULT_MODEL) -> np.ndarray:
    """Calls the Cohere Embed API and returns a (n_texts, dim) float32 array."""
    if not api_key:
        raise ValueError("A Cohere API key is required for embeddings. Add it in the sidebar.")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "texts": texts,
        "model": model,
        "input_type": input_type,   # "search_document" for indexing, "search_query" for queries
        "embedding_types": ["float"],
    }

    resp = requests.post(COHERE_EMBED_URL, headers=headers, json=payload, timeout=60)
    if resp.status_code != 200:
        raise RuntimeError(f"Cohere Embed API error ({resp.status_code}): {resp.text[:300]}")

    data = resp.json()
    embeddings = data["embeddings"]["float"]
    arr = np.array(embeddings, dtype="float32")

    # Normalize so cosine similarity == dot product (matches FAISS IndexFlatIP)
    norms = np.linalg.norm(arr, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    arr = arr / norms

    return arr.astype("float32")


def embed_texts(texts: List[str], api_key: str, model: str = DEFAULT_MODEL,
                 batch_size: int = 96) -> np.ndarray:
    """
    Embeds a list of documents/chunks for indexing.
    Cohere allows up to 96 texts per request, so we batch automatically.
    """
    all_embeddings = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        all_embeddings.append(_call_cohere_embed(batch, api_key, input_type="search_document", model=model))
    return np.vstack(all_embeddings) if all_embeddings else np.zeros((0, 1024), dtype="float32")


def embed_query(query: str, api_key: str, model: str = DEFAULT_MODEL) -> np.ndarray:
    """Embeds a single search query. Uses input_type='search_query' for asymmetric retrieval quality."""
    return _call_cohere_embed([query], api_key, input_type="search_query", model=model)
