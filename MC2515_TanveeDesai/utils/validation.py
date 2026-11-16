"""
utils/validation.py — Input validation helpers.
"""

import re
from typing import Optional


def sanitize_drug_name(name: str) -> str:
    """
    Sanitize a raw user-entered medicine name.

    Rules:
    - Strip leading/trailing whitespace
    - Collapse internal whitespace
    - Remove unsafe characters (keep alphanumeric, hyphens, spaces, parentheses)
    - Title-case for consistency
    """
    name = name.strip()
    name = re.sub(r"\s+", " ", name)
    name = re.sub(r"[^a-zA-Z0-9\s\-\(\)]", "", name)
    return name.strip()


def is_valid_drug_name(name: str) -> bool:
    """Return True if name is non-empty and plausible."""
    cleaned = sanitize_drug_name(name)
    return bool(cleaned) and len(cleaned) >= 2


def truncate_text(text: str, max_chars: int = 500) -> str:
    """Truncate text to max_chars, appending '...' if truncated."""
    if len(text) <= max_chars:
        return text
    return text[:max_chars].rsplit(" ", 1)[0] + "..."


def safe_str(value, default: str = "") -> str:
    """Convert value to string, returning default if None/empty."""
    if value is None:
        return default
    s = str(value).strip()
    return s if s else default


def safe_int(value, default: int = 0) -> int:
    """Safely convert value to int."""
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def safe_float(value, default: float = 0.0) -> float:
    """Safely convert value to float."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return default
