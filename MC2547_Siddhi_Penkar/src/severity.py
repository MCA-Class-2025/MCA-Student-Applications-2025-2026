"""
severity.py
-----------
Lightweight, keyword-based severity classification for bug report chunks.

This is intentionally simple (no extra ML model / API calls) so it runs
instantly on every chunk during knowledge-base creation, and requires no
new dependencies. Each chunk is tagged with one of:

    Critical > High > Medium > Low

based on the presence of severity-indicating keywords/phrases. If multiple
severity levels' keywords appear in the same chunk, the highest one wins
(Critical takes priority over High, etc.) since it's better to flag a chunk
as more severe than to under-report risk.
"""

from typing import List, Dict

from src.utils import get_logger

logger = get_logger(__name__)

SEVERITY_LEVELS = ["Critical", "High", "Medium", "Low"]

# Ordered from most to least severe. Keywords are matched case-insensitively
# as substrings, so simple word forms cover most variants.
SEVERITY_KEYWORDS = {
    "Critical": [
        "crash", "crashes", "crashed", "critical", "fatal", "data loss",
        "security vulnerability", "exploit", "corruption", "corrupted",
        "system down", "outage", "deadlock", "segmentation fault", "segfault",
        "unrecoverable", "production down", "blocker",
    ],
    "High": [
        "exception", "error", "failure", "failed", "fails", "high priority",
        "major", "broken", "not working", "unresponsive", "timeout",
        "memory leak", "null pointer", "nullpointerexception", "stack trace",
        "regression",
    ],
    "Medium": [
        "warning", "unexpected behavior", "inconsistent", "incorrect result",
        "medium priority", "performance issue", "slow", "degraded",
        "intermittent", "edge case",
    ],
    "Low": [
        "cosmetic", "typo", "ui glitch", "minor", "low priority",
        "enhancement", "suggestion", "documentation", "trivial",
        "formatting",
    ],
}


def classify_severity(text: str) -> str:
    """
    Classifies a single chunk of text into a severity level based on
    keyword matches.

    Args:
        text (str): Chunk text to classify.

    Returns:
        str: One of "Critical", "High", "Medium", "Low". Defaults to "Low"
             if no keywords match (i.e. nothing indicates elevated severity).
    """
    if not text:
        return "Low"

    lowered = text.lower()

    for level in SEVERITY_LEVELS:  # already ordered Critical -> Low
        keywords = SEVERITY_KEYWORDS[level]
        if any(keyword in lowered for keyword in keywords):
            return level

    return "Low"


def tag_chunks_with_severity(chunks: List[Dict]) -> List[Dict]:
    """
    Adds a "severity" field to every chunk record in place (and returns it).

    Args:
        chunks (List[Dict]): Chunk records as produced by chunking.py.

    Returns:
        List[Dict]: The same chunks list, each record now containing "severity".
    """
    for chunk in chunks:
        chunk["severity"] = classify_severity(chunk.get("text", ""))

    logger.info(f"Tagged severity for {len(chunks)} chunks.")
    return chunks


def compute_severity_distribution(chunks: List[Dict]) -> Dict[str, int]:
    """
    Computes counts of chunks per severity level, useful for a distribution
    chart across the whole knowledge base.

    Args:
        chunks (List[Dict]): Chunk records, each expected to have "severity".

    Returns:
        Dict[str, int]: Mapping of severity level -> chunk count, in a fixed
                         Critical -> Low order for consistent chart display.
    """
    distribution = {level: 0 for level in SEVERITY_LEVELS}

    for chunk in chunks:
        level = chunk.get("severity", "Low")
        if level not in distribution:
            level = "Low"
        distribution[level] += 1

    return distribution