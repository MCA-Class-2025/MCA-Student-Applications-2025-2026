
import os
import pickle
from functools import lru_cache

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

from rag.vector_store import INDEX_FILE, METADATA_FILE
from rag.embeddings import MODEL_NAME


os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

_model = None
_index = None
_documents = None


def load_retriever():
    """Load embedding model and FAISS index once."""

    global _model, _index, _documents

    if _model is not None and _index is not None:
        return True

    if not os.path.exists(INDEX_FILE):
        raise FileNotFoundError(
            "FAISS index not found. Run python -m rag.vector_store"
        )

    if not os.path.exists(METADATA_FILE):
        raise FileNotFoundError(
            "FAISS metadata not found. Rebuild the index."
        )

    print("Loading food retrieval system...")

    _model = SentenceTransformer(MODEL_NAME)

    _index = faiss.read_index(INDEX_FILE)

    with open(METADATA_FILE, "rb") as file:
        _documents = pickle.load(file)

    if _index.ntotal != len(_documents):
        raise ValueError(
            "FAISS index and metadata do not match. "
            "Run python -m rag.vector_store"
        )

    print("Food retrieval system ready.")

    return True


@lru_cache(maxsize=128)
def _retrieve_cached(query, top_k):
    """Cache embeddings search results for repeated questions."""

    load_retriever()

    embedding = _model.encode(
        [query],
        convert_to_numpy=True,
        normalize_embeddings=True,
        show_progress_bar=False
    )

    embedding = np.asarray(embedding, dtype="float32")

    count = min(top_k, _index.ntotal)

    if count == 0:
        return tuple()

    scores, indices = _index.search(embedding, count)

    results = []

    for score, position in zip(scores[0], indices[0]):
        if position < 0:
            continue

        document = dict(_documents[position])
        document["similarity_score"] = float(score)

        results.append(document)

    return tuple(results)


def retrieve_food(query, top_k=6):
    """Retrieve relevant PDF and Excel documents."""

    if not query or not query.strip():
        return []

    normalized_query = " ".join(query.lower().split())

    results = _retrieve_cached(normalized_query, top_k)

    return [dict(document) for document in results]


if __name__ == "__main__":
    results = retrieve_food(
        "How is Rajma Masala prepared?"
    )

    print("Retrieved documents:", len(results))

    for document in results:
        print(
            document.get("source_type"),
            document.get("food_name"),
            document.get("page")
        )
