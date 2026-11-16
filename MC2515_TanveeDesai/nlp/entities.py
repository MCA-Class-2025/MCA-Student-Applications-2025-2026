"""
nlp/entities.py — Named entity extraction (lightweight, no spaCy model required).
Uses regex patterns to extract medical entities from drug text.
"""

import re
from typing import Dict, List


_DOSAGE_PATTERN = re.compile(
    r"\b\d+(?:\.\d+)?\s*(?:mg|mcg|g|ml|mL|IU|units?|tablet|capsule|patch)\b",
    re.IGNORECASE,
)

_FREQUENCY_PATTERN = re.compile(
    r"\b(?:once|twice|three times|four times|daily|weekly|monthly|"
    r"every \d+ hours?|bid|tid|qid|qd|prn)\b",
    re.IGNORECASE,
)

_ROUTE_PATTERN = re.compile(
    r"\b(?:oral(?:ly)?|intravenous(?:ly)?|intramuscular(?:ly)?|topical(?:ly)?|"
    r"subcutaneous(?:ly)?|sublingual(?:ly)?|inhaled?|inhalation|transdermal)\b",
    re.IGNORECASE,
)


def extract_dosages(text: str) -> List[str]:
    """Extract dosage mentions from text."""
    matches = _DOSAGE_PATTERN.findall(text)
    return list(set(m.strip() for m in matches))


def extract_frequencies(text: str) -> List[str]:
    """Extract frequency mentions from text."""
    matches = _FREQUENCY_PATTERN.findall(text)
    return list(set(m.strip() for m in matches))


def extract_routes(text: str) -> List[str]:
    """Extract route of administration mentions."""
    matches = _ROUTE_PATTERN.findall(text)
    return list(set(m.strip() for m in matches))


def extract_all_entities(text: str) -> Dict[str, List[str]]:
    """Extract all medical entities from a block of text."""
    return {
        "dosages": extract_dosages(text),
        "frequencies": extract_frequencies(text),
        "routes": extract_routes(text),
    }
