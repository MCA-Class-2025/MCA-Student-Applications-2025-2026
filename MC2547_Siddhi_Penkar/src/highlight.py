"""
highlight.py
------------
Renders the original PDF page a retrieved chunk came from, with the
matching text highlighted - giving a visual "source page highlighting"
feature without needing any extra dependencies (uses PyMuPDF only).

Approach:
- The exact PDF file for a chunk's "source" is looked up in data/uploaded_pdfs
  (chunks store the sanitized filename that was used when saving).
- A short search snippet (first few words of the chunk) is located on the
  page via PyMuPDF's page.search_for(), which does exact substring matching.
- If found, a highlight annotation is added and the page is rendered to a
  PNG image. If the snippet can't be located (e.g. due to PDF text-extraction
  line-break quirks), the full page is still rendered so the user can see
  context, with a flag indicating the highlight wasn't precisely located.

IMPORTANT: This opens the saved PDF and modifies an IN-MEMORY copy only
(annotations are never written back with doc.save()), so the original
uploaded PDF file on disk is never altered.
"""

import os
from typing import Optional, Tuple

import fitz  # PyMuPDF

from src.utils import UPLOADED_PDFS_DIR, get_logger

logger = get_logger(__name__)


class HighlightError(Exception):
    """Raised when a source page cannot be located or rendered."""
    pass


def build_search_snippet(chunk_text: str, max_words: int = 8) -> str:
    """
    Builds a short snippet from the start of a chunk, used for locating the
    chunk's text on its source page. Short snippets are far more likely to
    be found via exact substring search than the full (long) chunk text,
    since PDF text extraction can introduce line-break/whitespace
    differences over longer spans.

    Args:
        chunk_text (str): Full chunk text.
        max_words (int): Number of leading words to use as the snippet.

    Returns:
        str: A short search snippet.
    """
    if not chunk_text:
        return ""
    words = chunk_text.strip().split()
    return " ".join(words[:max_words])


def resolve_pdf_path(source_filename: str) -> str:
    """
    Resolves a chunk's "source" field back to the saved PDF file on disk.

    Args:
        source_filename (str): Sanitized filename stored in chunk metadata.

    Returns:
        str: Full path to the PDF file.

    Raises:
        HighlightError: If the file cannot be found.
    """
    filepath = os.path.join(UPLOADED_PDFS_DIR, source_filename)
    if not os.path.exists(filepath):
        raise HighlightError(
            f"Original PDF '{source_filename}' was not found in "
            f"'{UPLOADED_PDFS_DIR}'. It may have been deleted since the "
            "knowledge base was built."
        )
    return filepath


def get_highlighted_page_image(source_filename: str, page_number: int,
                                chunk_text: str, zoom: float = 1.6
                                ) -> Tuple[bytes, bool]:
    """
    Renders a PDF page as a PNG image, highlighting the chunk's text if it
    can be located on that page.

    Args:
        source_filename (str): Sanitized source filename (chunk["source"]).
        page_number (int): 1-indexed page number (chunk["page"]).
        chunk_text (str): The chunk's text, used to build a search snippet.
        zoom (float): Rendering zoom factor (higher = sharper image).

    Returns:
        Tuple[bytes, bool]: (PNG image bytes, whether the highlight was
                              successfully located on the page).

    Raises:
        HighlightError: If the PDF or page cannot be opened/rendered.
    """
    if not page_number or page_number < 1:
        raise HighlightError("No valid page number available for this chunk.")

    filepath = resolve_pdf_path(source_filename)

    try:
        doc = fitz.open(filepath)
    except Exception as exc:
        raise HighlightError(f"Could not open PDF '{source_filename}': {exc}")

    try:
        if page_number > doc.page_count:
            raise HighlightError(
                f"Page {page_number} does not exist in '{source_filename}' "
                f"(document has {doc.page_count} page(s))."
            )

        page = doc[page_number - 1]

        found_rects = []
        snippet = build_search_snippet(chunk_text, max_words=8)
        if snippet:
            found_rects = page.search_for(snippet)

        # Retry with a shorter snippet if the longer one wasn't found
        if not found_rects:
            shorter_snippet = build_search_snippet(chunk_text, max_words=4)
            if shorter_snippet:
                found_rects = page.search_for(shorter_snippet)

        highlight_found = bool(found_rects)

        for rect in found_rects:
            annot = page.add_highlight_annot(rect)
            annot.set_colors(stroke=(1, 0.85, 0.2))  # soft amber highlight
            annot.update()

        matrix = fitz.Matrix(zoom, zoom)
        pixmap = page.get_pixmap(matrix=matrix)
        image_bytes = pixmap.tobytes("png")

        return image_bytes, highlight_found

    except HighlightError:
        raise
    except Exception as exc:
        logger.error(f"Failed to render highlighted page: {exc}")
        raise HighlightError(f"Failed to render page {page_number} of '{source_filename}': {exc}")
    finally:
        doc.close()