"""
pdf_loader.py
-------------
Handles PDF ingestion for BugAssist AI.

Responsibilities:
- Accept multiple uploaded PDF files (from Streamlit's file_uploader).
- Save uploaded files locally to data/uploaded_pdfs.
- Extract text from each PDF **per page** using PyMuPDF (fitz), so that
  page numbers can be carried through chunking -> retrieval -> UI, and
  used later for source-page highlighting.
- Handle corrupt / invalid / empty PDFs gracefully.
"""

import os
from typing import List, Dict

import fitz  # PyMuPDF

from src.utils import UPLOADED_PDFS_DIR, EXTRACTED_TEXT_DIR, get_logger, safe_filename

logger = get_logger(__name__)


class PDFLoadError(Exception):
    """Raised when a PDF cannot be read or processed."""
    pass


def save_uploaded_pdf(uploaded_file) -> str:
    """
    Saves a Streamlit UploadedFile object to disk using a sanitized filename.

    IMPORTANT: The sanitized filename (via safe_filename) is used consistently
    as the "source" identifier throughout the pipeline (chunks, metadata,
    highlighting) so that a chunk's source can always be mapped back to the
    exact PDF file saved on disk.

    Args:
        uploaded_file: Streamlit UploadedFile instance.

    Returns:
        str: Full path to the saved PDF file.
    """
    os.makedirs(UPLOADED_PDFS_DIR, exist_ok=True)
    filename = safe_filename(uploaded_file.name)
    filepath = os.path.join(UPLOADED_PDFS_DIR, filename)

    try:
        with open(filepath, "wb") as f:
            f.write(uploaded_file.getbuffer())
        logger.info(f"Saved uploaded PDF: {filepath}")
    except Exception as exc:
        logger.error(f"Failed to save uploaded file {filename}: {exc}")
        raise PDFLoadError(f"Could not save uploaded file '{filename}': {exc}")

    return filepath


def extract_pages_from_pdf(filepath: str) -> List[Dict]:
    """
    Extracts text from a PDF file, one record per page, using PyMuPDF.

    Args:
        filepath (str): Path to the PDF file.

    Returns:
        List[Dict]: List of {"page": int (1-indexed), "text": str} records
                     for every page that contains extractable text.

    Raises:
        PDFLoadError: If the PDF is invalid, corrupt, or has no extractable text.
    """
    if not os.path.exists(filepath):
        raise PDFLoadError(f"File not found: {filepath}")

    try:
        doc = fitz.open(filepath)
    except Exception as exc:
        logger.error(f"Invalid or corrupt PDF '{filepath}': {exc}")
        raise PDFLoadError(f"Invalid or corrupt PDF file: {os.path.basename(filepath)}")

    if doc.page_count == 0:
        doc.close()
        raise PDFLoadError(f"PDF has no pages: {os.path.basename(filepath)}")

    pages = []
    try:
        for page_index, page in enumerate(doc):
            page_text = page.get_text("text")
            if page_text and page_text.strip():
                pages.append({"page": page_index + 1, "text": page_text})
    except Exception as exc:
        logger.error(f"Error extracting text from '{filepath}': {exc}")
        raise PDFLoadError(f"Error extracting text from PDF: {os.path.basename(filepath)}")
    finally:
        doc.close()

    if not pages:
        raise PDFLoadError(
            f"No extractable text found in '{os.path.basename(filepath)}'. "
            "It may be a scanned/image-only PDF."
        )

    return pages


def process_uploaded_pdfs(uploaded_files: List) -> Dict[str, List[Dict]]:
    """
    Processes multiple uploaded PDF files: saves each, extracts per-page text,
    and persists a plain-text copy to disk for reference/debugging.

    Args:
        uploaded_files (List): List of Streamlit UploadedFile objects.

    Returns:
        Dict[str, List[Dict]]: Mapping of {sanitized_filename: [ {"page", "text"}, ... ]}
                                for successful files. Files that fail are skipped and logged.
    """
    os.makedirs(EXTRACTED_TEXT_DIR, exist_ok=True)
    results: Dict[str, List[Dict]] = {}
    errors: Dict[str, str] = {}

    if not uploaded_files:
        raise PDFLoadError("No files were uploaded. Please upload at least one PDF.")

    for uploaded_file in uploaded_files:
        try:
            filepath = save_uploaded_pdf(uploaded_file)
            source_name = os.path.basename(filepath)  # sanitized filename, used as source id
            pages = extract_pages_from_pdf(filepath)

            # Persist extracted text (concatenated) for reference/debugging
            base_name = os.path.splitext(source_name)[0]
            text_out_path = os.path.join(EXTRACTED_TEXT_DIR, f"{base_name}.txt")
            with open(text_out_path, "w", encoding="utf-8") as f:
                f.write("\n\n".join(p["text"] for p in pages))

            results[source_name] = pages
            logger.info(
                f"Successfully extracted {len(pages)} page(s) of text from '{source_name}'"
            )

        except PDFLoadError as exc:
            logger.warning(f"Skipping '{uploaded_file.name}': {exc}")
            errors[uploaded_file.name] = str(exc)
        except Exception as exc:
            logger.error(f"Unexpected error processing '{uploaded_file.name}': {exc}")
            errors[uploaded_file.name] = f"Unexpected error: {exc}"

    if not results:
        raise PDFLoadError(
            "None of the uploaded PDFs could be processed. Errors: " + str(errors)
        )

    if errors:
        logger.warning(f"Some PDFs failed to process: {errors}")

    return results