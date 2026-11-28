"""
nlp/preprocessing.py — NLP text preprocessing pipeline.
"""

import re
import string
from typing import List

from utils.logging import logger

# Lazy NLTK imports (only download once)
_nltk_ready = False

def _ensure_nltk():
    global _nltk_ready
    if _nltk_ready:
        return
    try:
        import nltk
        for resource in ["punkt", "stopwords", "punkt_tab"]:
            try:
                nltk.download(resource, quiet=True)
            except Exception:
                pass
        _nltk_ready = True
    except Exception as e:
        logger.warning(f"NLTK setup issue: {e}")


def preprocess_text(text: str, remove_stopwords: bool = True) -> str:
    """
    Basic NLP preprocessing:
    - Lowercase
    - Remove punctuation
    - Remove stopwords (optional)
    - Remove numbers
    """
    _ensure_nltk()

    if not text:
        return ""

    text = text.lower()
    text = re.sub(r"\d+", "", text)
    text = text.translate(str.maketrans("", "", string.punctuation))
    text = re.sub(r"\s+", " ", text).strip()

    if remove_stopwords:
        try:
            from nltk.corpus import stopwords
            stop_words = set(stopwords.words("english"))
            tokens = text.split()
            tokens = [t for t in tokens if t not in stop_words and len(t) > 2]
            text = " ".join(tokens)
        except Exception:
            pass

    return text


def tokenize(text: str) -> List[str]:
    """Simple whitespace tokenization after preprocessing."""
    processed = preprocess_text(text)
    return [t for t in processed.split() if t]
