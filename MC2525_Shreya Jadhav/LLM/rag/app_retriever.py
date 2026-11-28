"""Current application retrieval, independent of the submitted Phase 2 indexes."""

from __future__ import annotations

import re
from functools import lru_cache

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from LLM.embeddings.build_phase2_knowledge_base import medical_documents
from LLM.rag.phase2_retriever import load_index, retrieve_documents


DATA_TERMS = re.compile(
    r"\b(?:api|census|cdc|data|dataset|fused|fusion|state|states|"
    r"record|records|population|income|median|prevalence|weather|"
    r"temperature|humidity|precipitation|wind|correlation|average|mean)\b",
    re.IGNORECASE,
)

EXPLICIT_DATA_TERMS = re.compile(
    r"\b(?:api|census|cdc|dataset|fused|fusion|records?|population|"
    r"income|prevalence|weather|temperature|humidity|precipitation|"
    r"wind|correlation|average|mean)\b",
    re.IGNORECASE,
)


@lru_cache(maxsize=1)
def _live_medical_index():
    documents = medical_documents()
    if not documents:
        return None
    vectorizer = TfidfVectorizer(
        lowercase=True,
        stop_words="english",
        ngram_range=(1, 2),
        sublinear_tf=True,
        norm="l2",
    )
    matrix = vectorizer.fit_transform(doc["text"] for doc in documents)
    return documents, vectorizer, matrix


@lru_cache(maxsize=1)
def _state_names():
    return tuple(
        document["record_key"].lower()
        for document in load_index()["documents"]
        if document.get("record_type") == "fused_state_summary"
    )


def _asks_about_state(question: str) -> bool:
    lower = question.lower()
    return any(
        re.search(rf"\b{re.escape(state)}\b", lower)
        for state in _state_names()
    )


def retrieve_app_documents(question: str, k: int = 5) -> list[dict]:
    """Use current medical pages for health questions and Phase 2 data for data queries."""

    compares_pcos_terms = (
        re.search(r"\bpcos\b", question, re.IGNORECASE)
        and re.search(r"\bpcod\b", question, re.IGNORECASE)
        and not EXPLICIT_DATA_TERMS.search(question)
    )
    if not compares_pcos_terms and (
        DATA_TERMS.search(question) or _asks_about_state(question)
    ):
        return retrieve_documents(question, k=k)

    return retrieve_medical_documents(question, k=k)


def retrieve_medical_documents(question: str, k: int = 5) -> list[dict]:
    """Search local medical text, including for personal symptom reports."""

    live = _live_medical_index()
    if live is None:
        return []
    documents, vectorizer, matrix = live
    query = vectorizer.transform([question])
    scores = cosine_similarity(query, matrix).ravel()
    positions = scores.argsort()[::-1][:k]
    results = []
    for position in positions:
        if scores[position] <= 0:
            continue
        document = dict(documents[int(position)])
        document["score"] = float(scores[position])
        results.append(document)
    return results


def format_app_context(documents: list[dict]) -> str:
    blocks = []
    for document in documents:
        label = f"Source: {document.get('source', 'unknown source')}"
        if document.get("record_key"):
            label += f" | Record: {document['record_key']}"
        blocks.append(f"{label}\n{document['text']}")
    return "\n\n".join(blocks)
