"""
data_processing.py
-------------------
Phase 3 of the RAG pipeline: Document loading, cleaning, chunking, and
metadata generation for the Company Policy Chatbot.

Supports: .md, .txt, .csv, .pdf, .docx
"""

import os
import re
import csv
import uuid
from dataclasses import dataclass, field
from typing import List, Dict, Optional


@dataclass
class Chunk:
    """A single chunk of text ready for embedding, with traceable metadata."""
    chunk_id: str
    text: str
    source_file: str
    doc_title: str
    chunk_index: int
    metadata: Dict = field(default_factory=dict)


# --------------------------------------------------------------------------- #
# Document Loaders
# --------------------------------------------------------------------------- #

def load_markdown_or_text(filepath: str) -> str:
    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()


def load_csv_as_documents(filepath: str) -> List[Dict]:
    """
    Loads a CSV (e.g. FAQs) and turns each row into a small pseudo-document.
    Expects a 'question'/'answer' style CSV but degrades gracefully for any CSV.
    """
    docs = []
    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            if "question" in row and "answer" in row:
                text = f"Q: {row['question'].strip()}\nA: {row['answer'].strip()}"
                extra = {"category": row.get("category", "General"), "row": i}
            else:
                text = " | ".join(f"{k}: {v}" for k, v in row.items())
                extra = {"row": i}
            docs.append({"text": text, "metadata": extra})
    return docs


def load_pdf(filepath: str) -> str:
    """Extracts text from a PDF using pypdf. Falls back gracefully if unavailable."""
    try:
        from pypdf import PdfReader
    except ImportError:
        raise ImportError("pypdf is required to load PDF files. Run: pip install pypdf")

    reader = PdfReader(filepath)
    pages_text = []
    for page in reader.pages:
        pages_text.append(page.extract_text() or "")
    return "\n\n".join(pages_text)


def load_docx(filepath: str) -> str:
    """Extracts text from a .docx file using python-docx."""
    try:
        import docx
    except ImportError:
        raise ImportError("python-docx is required to load DOCX files. Run: pip install python-docx")

    d = docx.Document(filepath)
    parts = [p.text for p in d.paragraphs if p.text.strip()]
    for table in d.tables:
        for row in table.rows:
            parts.append(" | ".join(cell.text for cell in row.cells))
    return "\n".join(parts)


# --------------------------------------------------------------------------- #
# Cleaning
# --------------------------------------------------------------------------- #

def clean_text(text: str) -> str:
    """Basic text cleaning: normalize whitespace, strip markdown noise for embedding quality."""
    text = re.sub(r"\r\n", "\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = text.strip()
    return text


def strip_markdown_light(text: str) -> str:
    """Removes heavy markdown symbols while preserving readable structure for embeddings."""
    text = re.sub(r"^#{1,6}\s*", "", text, flags=re.MULTILINE)   # headings
    text = re.sub(r"\*\*(.*?)\*\*", r"\1", text)                  # bold
    text = re.sub(r"\|", " ", text)                               # table pipes
    text = re.sub(r"^-{2,}$", "", text, flags=re.MULTILINE)
    return text


# --------------------------------------------------------------------------- #
# Chunking
# --------------------------------------------------------------------------- #

def chunk_text(
    text: str,
    chunk_size: int = 800,
    chunk_overlap: int = 150,
) -> List[str]:
    """
    Splits text into overlapping chunks by character count, but tries to break
    on paragraph/sentence boundaries for cleaner retrieval units.
    """
    if len(text) <= chunk_size:
        return [text] if text.strip() else []

    # First split into paragraphs to respect natural boundaries
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]

    chunks = []
    current = ""

    for para in paragraphs:
        if len(current) + len(para) + 2 <= chunk_size:
            current = f"{current}\n\n{para}" if current else para
        else:
            if current:
                chunks.append(current.strip())
            # If a single paragraph is itself too long, hard-split it
            if len(para) > chunk_size:
                for i in range(0, len(para), chunk_size - chunk_overlap):
                    chunks.append(para[i:i + chunk_size].strip())
                current = ""
            else:
                current = para

    if current:
        chunks.append(current.strip())

    # Apply overlap between consecutive chunks for better context continuity
    overlapped = []
    for i, c in enumerate(chunks):
        if i == 0:
            overlapped.append(c)
        else:
            tail = chunks[i - 1][-chunk_overlap:] if len(chunks[i - 1]) > chunk_overlap else chunks[i - 1]
            overlapped.append(f"{tail}\n{c}")

    return overlapped


# --------------------------------------------------------------------------- #
# Main ingestion pipeline
# --------------------------------------------------------------------------- #

SUPPORTED_EXTENSIONS = {".md", ".txt", ".csv", ".pdf", ".docx"}


def process_file(filepath: str, chunk_size: int = 800, chunk_overlap: int = 150) -> List[Chunk]:
    """
    Loads a single file, cleans it, chunks it, and returns a list of Chunk objects
    with metadata (source file, title, chunk index) for citation/traceability.
    """
    filename = os.path.basename(filepath)
    ext = os.path.splitext(filename)[1].lower()
    title = os.path.splitext(filename)[0].replace("_", " ").title()

    chunks: List[Chunk] = []

    if ext == ".csv":
        docs = load_csv_as_documents(filepath)
        for i, d in enumerate(docs):
            chunks.append(Chunk(
                chunk_id=str(uuid.uuid4()),
                text=clean_text(d["text"]),
                source_file=filename,
                doc_title=title,
                chunk_index=i,
                metadata={**d["metadata"], "file_type": "csv"},
            ))
        return chunks

    if ext in (".md", ".txt"):
        raw = load_markdown_or_text(filepath)
    elif ext == ".pdf":
        raw = load_pdf(filepath)
    elif ext == ".docx":
        raw = load_docx(filepath)
    else:
        raise ValueError(f"Unsupported file type: {ext}. Supported: {SUPPORTED_EXTENSIONS}")

    cleaned = clean_text(raw)
    readable = strip_markdown_light(cleaned)
    text_chunks = chunk_text(readable, chunk_size=chunk_size, chunk_overlap=chunk_overlap)

    for i, chunk in enumerate(text_chunks):
        if not chunk.strip():
            continue
        chunks.append(Chunk(
            chunk_id=str(uuid.uuid4()),
            text=chunk,
            source_file=filename,
            doc_title=title,
            chunk_index=i,
            metadata={"file_type": ext.replace(".", "")},
        ))

    return chunks


def process_directory(directory: str, chunk_size: int = 800, chunk_overlap: int = 150) -> List[Chunk]:
    """Processes every supported file in a directory into a flat list of Chunks."""
    all_chunks: List[Chunk] = []
    for filename in sorted(os.listdir(directory)):
        ext = os.path.splitext(filename)[1].lower()
        if ext not in SUPPORTED_EXTENSIONS:
            continue
        filepath = os.path.join(directory, filename)
        try:
            file_chunks = process_file(filepath, chunk_size, chunk_overlap)
            all_chunks.extend(file_chunks)
            print(f"  [OK] {filename}: {len(file_chunks)} chunks")
        except Exception as e:
            print(f"  [SKIP] {filename}: {e}")
    return all_chunks


def validate_chunks(chunks: List[Chunk]) -> Dict:
    """Phase 3 - Data validation: sanity checks on the processed chunks."""
    report = {
        "total_chunks": len(chunks),
        "empty_chunks": sum(1 for c in chunks if not c.text.strip()),
        "avg_chunk_length": round(sum(len(c.text) for c in chunks) / max(len(chunks), 1), 1),
        "sources": sorted(set(c.source_file for c in chunks)),
        "num_sources": len(set(c.source_file for c in chunks)),
    }
    return report
