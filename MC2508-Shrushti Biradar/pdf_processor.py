
"""
pdf_processor.py

Loads text from uploaded PDF files and splits it into
smaller chunks for semantic search.
"""

from io import BytesIO

from pypdf import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document


def process_pdfs(uploaded_files):
    """Extract and split text from multiple uploaded PDFs."""

    documents = []

    for uploaded_file in uploaded_files:
        pdf_bytes = BytesIO(uploaded_file.getvalue())
        reader = PdfReader(pdf_bytes)

        for page_number, page in enumerate(reader.pages, start=1):
            text = page.extract_text() or ""

            if text.strip():
                documents.append(
                    Document(
                        page_content=text,
                        metadata={
                            "source": uploaded_file.name,
                            "page": page_number,
                        },
                    )
                )

    if not documents:
        raise ValueError(
            "No readable text found. Check whether the PDFs contain selectable text."
        )

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=150,
    )

    chunks = splitter.split_documents(documents)

    return chunks
