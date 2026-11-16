"""
rag/chunking.py — Text chunking for RAG pipeline.
"""

from typing import Any, Dict, List

from config.settings import CHUNK_SIZE, CHUNK_OVERLAP
from utils.logging import logger


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> List[str]:
    """
    Split text into overlapping chunks by character count.
    Tries to split on sentence/paragraph boundaries.
    """
    if not text or len(text) <= chunk_size:
        return [text] if text else []

    chunks = []
    start = 0
    text_len = len(text)

    while start < text_len:
        end = min(start + chunk_size, text_len)

        if end < text_len:
            # Try to find a sentence boundary
            for sep in ["\n\n", ". ", "\n", " "]:
                boundary = text.rfind(sep, start + chunk_size // 2, end)
                if boundary > start:
                    end = boundary + len(sep)
                    break

        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)

        # Final chunk reached — stop. Otherwise start would loop forever
        # (start = end - overlap stays < text_len when end == text_len).
        if end >= text_len:
            break

        start = end - overlap
        if start >= text_len:
            break

    return chunks


def chunk_document(doc: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Chunk a single document dict into multiple chunk dicts.
    Each chunk inherits the parent document's metadata.
    """
    content = doc.get("content", "")
    metadata = doc.get("metadata", {})
    doc_id = doc.get("doc_id", "")
    title = doc.get("title", "")

    chunks_text = chunk_text(content)
    if not chunks_text:
        return []

    chunks = []
    for i, chunk_text_item in enumerate(chunks_text):
        chunks.append({
            "chunk_id": f"{doc_id}_chunk_{i}",
            "doc_id": doc_id,
            "title": title,
            "content": chunk_text_item,
            "chunk_index": i,
            "total_chunks": len(chunks_text),
            "metadata": {
                **metadata,
                "chunk_index": i,
                "total_chunks": len(chunks_text),
            },
        })

    return chunks


def chunk_all_documents(documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Chunk all documents in the RAG corpus.
    Returns flat list of all chunks.
    """
    all_chunks = []
    for doc in documents:
        chunks = chunk_document(doc)
        all_chunks.extend(chunks)

    logger.info(f"Chunked {len(documents)} documents into {len(all_chunks)} chunks")
    return all_chunks
