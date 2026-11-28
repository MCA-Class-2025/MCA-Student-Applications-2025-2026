"""
chunking.py
-----------
Splits cleaned, per-page documents into overlapping chunks suitable for
embedding and semantic retrieval.

Design:
- Word-based sliding window chunking, applied PER PAGE (not across the
  whole document) so that every chunk can be traced back to an exact
  page number - required for source-page highlighting.
- Configurable chunk size and overlap.
- Preserves source filename + page number as metadata for each chunk.
"""

from typing import List, Dict

from src.utils import get_logger

logger = get_logger(__name__)

DEFAULT_CHUNK_SIZE = 250   # words per chunk
DEFAULT_CHUNK_OVERLAP = 50  # overlapping words between consecutive chunks


def chunk_text(text: str, chunk_size: int = DEFAULT_CHUNK_SIZE,
                overlap: int = DEFAULT_CHUNK_OVERLAP) -> List[str]:
    """
    Splits a single block of text into overlapping chunks based on word count.

    Args:
        text (str): Input text to split.
        chunk_size (int): Number of words per chunk.
        overlap (int): Number of overlapping words between consecutive chunks.

    Returns:
        List[str]: List of text chunks.
    """
    if not text or not text.strip():
        return []

    if overlap >= chunk_size:
        logger.warning(
            f"Overlap ({overlap}) >= chunk_size ({chunk_size}); "
            "reducing overlap to chunk_size // 4 to avoid infinite loop."
        )
        overlap = chunk_size // 4

    words = text.split()
    if not words:
        return []

    chunks = []
    step = chunk_size - overlap
    start = 0

    while start < len(words):
        end = start + chunk_size
        chunk_words = words[start:end]
        chunk = " ".join(chunk_words).strip()
        if chunk:
            chunks.append(chunk)
        if end >= len(words):
            break
        start += step

    return chunks


def chunk_document_pages(pages_by_file: Dict[str, List[Dict]],
                          chunk_size: int = DEFAULT_CHUNK_SIZE,
                          overlap: int = DEFAULT_CHUNK_OVERLAP) -> List[Dict]:
    """
    Chunks multiple documents (already split into cleaned pages) and attaches
    full metadata (source filename, page number, chunk id) to each chunk.

    Args:
        pages_by_file (Dict[str, List[Dict]]): Mapping of
            filename -> [{"page": int, "text": cleaned_text}, ...]
        chunk_size (int): Words per chunk.
        overlap (int): Overlapping words between chunks.

    Returns:
        List[Dict]: List of chunk records, each with:
            {
                "text": str,
                "source": str,       # source filename (sanitized, on disk)
                "page": int,         # 1-indexed page number within the source
                "chunk_id": int      # index of chunk within the source document
            }
    """
    all_chunks = []

    for filename, pages in pages_by_file.items():
        doc_chunk_counter = 0
        for page_record in pages:
            page_num = page_record["page"]
            page_text = page_record["text"]
            page_chunks = chunk_text(page_text, chunk_size=chunk_size, overlap=overlap)

            for chunk in page_chunks:
                all_chunks.append({
                    "text": chunk,
                    "source": filename,
                    "page": page_num,
                    "chunk_id": doc_chunk_counter,
                })
                doc_chunk_counter += 1

        logger.info(f"Created {doc_chunk_counter} chunks from '{filename}' "
                    f"across {len(pages)} page(s)")

    if not all_chunks:
        logger.warning("No chunks were generated from the provided documents.")

    return all_chunks


# ---------------------------------------------------------------------------
# Legacy helper (flat filename -> text, no page tracking). Kept for
# backward-compatibility with any external callers; the default app.py
# pipeline now uses chunk_document_pages() instead.
# ---------------------------------------------------------------------------

def chunk_documents(documents: Dict[str, str], chunk_size: int = DEFAULT_CHUNK_SIZE,
                     overlap: int = DEFAULT_CHUNK_OVERLAP) -> List[Dict]:
    """Legacy: chunks a flat {filename: text} mapping with no page metadata."""
    all_chunks = []
    for filename, text in documents.items():
        chunks = chunk_text(text, chunk_size=chunk_size, overlap=overlap)
        for idx, chunk in enumerate(chunks):
            all_chunks.append({
                "text": chunk,
                "source": filename,
                "page": None,
                "chunk_id": idx,
            })
    return all_chunks