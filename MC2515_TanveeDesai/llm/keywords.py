"""
nlp/keywords.py — Keyword extraction from drug text.
"""

from typing import List, Tuple

from analysis.clustering import extract_keywords_tfidf
from nlp.preprocessing import preprocess_text
from utils.logging import logger


def extract_keywords_from_warnings(warnings_text: str, top_n: int = 15) -> List[Tuple[str, float]]:
    """Extract keywords from a warnings/label text block."""
    if not warnings_text:
        return []
    processed = preprocess_text(warnings_text)
    return extract_keywords_tfidf([processed], top_n=top_n)


def extract_keywords_from_abstracts(abstracts: List[str], top_n: int = 20) -> List[Tuple[str, float]]:
    """Extract common research keywords from PubMed abstracts."""
    if not abstracts:
        return []
    processed = [preprocess_text(a) for a in abstracts if a]
    if not processed:
        return []
    return extract_keywords_tfidf(processed, top_n=top_n)


def extract_research_topics(articles: List[dict], top_n: int = 20) -> List[Tuple[str, float]]:
    """Extract topics from article titles and abstracts."""
    texts = []
    for art in articles:
        title = art.get("title", "")
        abstract = art.get("abstract", "")
        combined = f"{title} {abstract}"
        if combined.strip():
            texts.append(preprocess_text(combined))
    return extract_keywords_tfidf(texts, top_n=top_n) if texts else []
