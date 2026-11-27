
import fitz
import os
import re

from config import BASE_DIR

PDF_PATH = os.path.join(
    BASE_DIR, "data", "recipes", "Indian_dishes.pdf"
)

CHUNK_SIZE = 1000
CHUNK_OVERLAP = 150


def clean_text(text):
    text = text.replace("\x00", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def split_text(text):
    chunks = []
    start = 0

    while start < len(text):
        end = start + CHUNK_SIZE
        chunk = text[start:end].strip()

        if len(chunk) > 80:
            chunks.append(chunk)

        start = end - CHUNK_OVERLAP

    return chunks


def load_pdf_documents():
    if not os.path.exists(PDF_PATH):
        raise FileNotFoundError(
            f"Recipe PDF not found: {PDF_PATH}"
        )

    documents = []

    pdf = fitz.open(PDF_PATH)

    for page_number, page in enumerate(pdf, start=1):
        text = clean_text(page.get_text("text"))

        if not text:
            continue

        for chunk_number, chunk in enumerate(
            split_text(text), start=1
        ):
            documents.append({
                "text": chunk,
                "source_type": "PDF",
                "source_file": "Indian_dishes.pdf",
                "page": page_number,
                "chunk": chunk_number,
                "food_id": "",
                "food_name": ""
            })

    pdf.close()

    print(f"PDF pages processed: {page_number}")
    print(f"PDF text chunks created: {len(documents)}")

    if not documents:
        print(
            "WARNING: No selectable text was extracted. "
            "Some PDF pages may require OCR."
        )

    return documents


if __name__ == "__main__":
    docs = load_pdf_documents()

    if docs:
        print("\nSample extracted text:")
        print(docs[0]["text"][:500])
