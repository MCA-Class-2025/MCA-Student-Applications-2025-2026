"""
utils.py
--------
Shared utility functions used across the BugAssist AI project:
- Path management
- Logging helpers
- File I/O helpers
- Timestamp helpers
"""

import os
import sys
import logging
from datetime import datetime

# ---------------------------------------------------------------------------
# Base project paths
# ---------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DATA_DIR = os.path.join(BASE_DIR, "data")
UPLOADED_PDFS_DIR = os.path.join(DATA_DIR, "uploaded_pdfs")
EXTRACTED_TEXT_DIR = os.path.join(DATA_DIR, "extracted_text")
FAISS_INDEX_DIR = os.path.join(DATA_DIR, "faiss_index")
MODELS_DIR = os.path.join(BASE_DIR, "models")
REPORTS_DIR = os.path.join(BASE_DIR, "reports")

FAISS_INDEX_PATH = os.path.join(FAISS_INDEX_DIR, "bugassist.index")
FAISS_METADATA_PATH = os.path.join(FAISS_INDEX_DIR, "bugassist_metadata.pkl")


def ensure_directories():
    """Create all required project directories if they do not already exist."""
    for directory in [
        UPLOADED_PDFS_DIR,
        EXTRACTED_TEXT_DIR,
        FAISS_INDEX_DIR,
        MODELS_DIR,
        REPORTS_DIR,
    ]:
        os.makedirs(directory, exist_ok=True)


def get_logger(name: str) -> logging.Logger:
    """
    Returns a configured logger instance.

    Args:
        name (str): Name of the logger, typically __name__ of calling module.

    Returns:
        logging.Logger: Configured logger.
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger


def timestamp() -> str:
    """Returns a filesystem-safe current timestamp string."""
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def save_text_file(content: str, filepath: str) -> None:
    """Saves text content to a file, creating parent directories if needed."""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)


def read_text_file(filepath: str) -> str:
    """Reads and returns text content from a file."""
    with open(filepath, "r", encoding="utf-8") as f:
        return f.read()


def safe_filename(filename: str) -> str:
    """Sanitizes a filename by removing unsafe characters."""
    keep_chars = (" ", ".", "_", "-")
    return "".join(c for c in filename if c.isalnum() or c in keep_chars).strip()


def save_report(query: str, response: str, retrieved_chunks=None, fmt: str = "txt") -> str:
    """
    Saves a generated bug-analysis answer (query + response + sources) to the
    reports/ directory as a timestamped TXT file.

    Args:
        query (str): The original user question.
        response (str): The generated LLM response.
        retrieved_chunks (list, optional): Source chunks used for the response.
        fmt (str): Output format, currently supports 'txt'.

    Returns:
        str: Path to the saved report file.
    """
    os.makedirs(REPORTS_DIR, exist_ok=True)
    ts = timestamp()
    filename = f"bug_report_{ts}.txt"
    filepath = os.path.join(REPORTS_DIR, filename)

    lines = [
        "=" * 70,
        "BugAssist AI - Generated Bug Analysis Report",
        f"Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "=" * 70,
        "",
        "USER QUESTION:",
        query.strip(),
        "",
        "-" * 70,
        "AI RESPONSE:",
        "-" * 70,
        response.strip(),
        "",
    ]

    if retrieved_chunks:
        lines.append("-" * 70)
        lines.append("RETRIEVED SOURCE CHUNKS:")
        lines.append("-" * 70)
        for i, chunk in enumerate(retrieved_chunks, start=1):
            lines.append(
                f"\n[{i}] Source: {chunk.get('source', 'unknown')} "
                f"| page: {chunk.get('page', 'unknown')} "
                f"| chunk #{chunk.get('chunk_id', '?')} "
                f"| severity: {chunk.get('severity', 'unknown')} "
                f"| score: {chunk.get('score', 0):.3f}"
            )
            lines.append(chunk.get("text", ""))

    with open(filepath, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    return filepath