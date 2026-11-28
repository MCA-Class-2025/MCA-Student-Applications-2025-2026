"""
preprocessing.py
-----------------
Text cleaning and normalization utilities used before chunking and embedding.

Two cleaning modes are provided:

1. light_clean_text() / clean_document_pages()
   - Whitespace + control-character normalization ONLY.
   - Preserves original case and punctuation.
   - Used as the DEFAULT pipeline going into chunking, because:
       a) Sentence-Transformer embeddings work better on natural text
          (stack traces like "NullPointerException" or "->" carry meaning).
       b) Preserving original text allows exact-match search on the source
          PDF page for the "source page highlighting" feature.

2. clean_text() (legacy / optional)
   - Full aggressive clean: lowercase + symbol stripping.
   - Still available for callers that want heavily normalized text
     (e.g. simple keyword search), but is NOT used by the default RAG
     pipeline anymore.
"""

import re
from typing import List, Dict

from src.utils import get_logger

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Light cleaning (default pipeline) - preserves case & punctuation
# ---------------------------------------------------------------------------

def remove_control_characters(text: str) -> str:
    """Removes non-printable / control characters that sometimes leak from PDFs."""
    return re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)


def remove_extra_whitespace(text: str) -> str:
    """Collapses multiple spaces, tabs, and newlines into single spaces/newlines."""
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n\s*\n+", "\n\n", text)
    text = re.sub(r" +\n", "\n", text)
    return text.strip()


def light_clean_text(text: str) -> str:
    """
    Minimal cleaning: strips control characters and normalizes whitespace only.
    Original case and punctuation/symbols are preserved.

    Args:
        text (str): Raw text extracted from a PDF page.

    Returns:
        str: Lightly cleaned text.
    """
    if not text or not text.strip():
        return ""
    text = remove_control_characters(text)
    text = remove_extra_whitespace(text)
    return text


def clean_document_pages(pages_by_file: Dict[str, List[Dict]]) -> Dict[str, List[Dict]]:
    """
    Applies light_clean_text() to every page of every document.

    Args:
        pages_by_file (Dict[str, List[Dict]]): Mapping of
            filename -> [{"page": int, "text": raw_text}, ...]

    Returns:
        Dict[str, List[Dict]]: Same structure, with cleaned page text.
                                Empty pages after cleaning are dropped.
    """
    cleaned: Dict[str, List[Dict]] = {}

    for filename, pages in pages_by_file.items():
        cleaned_pages = []
        for page_record in pages:
            cleaned_text = light_clean_text(page_record.get("text", ""))
            if cleaned_text:
                cleaned_pages.append({"page": page_record["page"], "text": cleaned_text})
        if cleaned_pages:
            cleaned[filename] = cleaned_pages
        else:
            logger.warning(f"All pages for '{filename}' were empty after cleaning; skipping.")

    return cleaned


# ---------------------------------------------------------------------------
# Legacy aggressive cleaning (kept for optional/backward-compat use)
# ---------------------------------------------------------------------------

def to_lowercase(text: str) -> str:
    """Converts text to lowercase."""
    return text.lower()


def remove_special_characters(text: str) -> str:
    """Removes unnecessary symbols while preserving common code/log punctuation."""
    pattern = r"[^a-zA-Z0-9\s\.\,\:\;\_\-\/\\\(\)\[\]\{\}\'\"\=\+\#\@\%]"
    return re.sub(pattern, " ", text)


def clean_text(text: str, lowercase: bool = True) -> str:
    """
    Full (aggressive) preprocessing pipeline: control-char removal, symbol
    stripping, whitespace normalization, and optional lowercasing.

    NOTE: Not used by the default RAG pipeline (see module docstring) -
    kept available for callers that explicitly want heavily normalized text.
    """
    if not text or not text.strip():
        logger.warning("clean_text received empty input.")
        return ""

    text = remove_control_characters(text)
    text = remove_special_characters(text)
    text = remove_extra_whitespace(text)

    if lowercase:
        text = to_lowercase(text)

    return text


def clean_documents(documents: dict) -> dict:
    """Applies clean_text() to a dictionary of {filename: raw_text}. (Legacy helper.)"""
    cleaned = {}
    for filename, text in documents.items():
        cleaned_text = clean_text(text)
        if cleaned_text:
            cleaned[filename] = cleaned_text
        else:
            logger.warning(f"Cleaned text for '{filename}' is empty; skipping.")
    return cleaned