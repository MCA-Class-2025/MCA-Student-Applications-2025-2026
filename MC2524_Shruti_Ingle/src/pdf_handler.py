import os
from config import CHUNK_OVERLAP, CHUNK_SIZE
from langchain_core.documents import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader

def load_pdfs(file_paths):
    documents = []
    for path in file_paths:
        ext = os.path.splitext(path)[1].lower()

        # PDF
        if ext == ".pdf":
            loader = PyPDFLoader(path)
            docs = loader.load()
            for d in docs:
                d.metadata["source_file"] = os.path.basename(path)
            documents.extend(docs)

        # TXT
        elif ext == ".txt":
            with open(path, "r", encoding="utf-8") as f:
                text = f.read()
            documents.append(
                Document(
                    page_content=text,
                    metadata={
                        "source_file": os.path.basename(path),
                        "page": 0,
                    },
                )
            )

        # DOCX
        elif ext == ".docx":
            try:
                from docx import Document as DocxDocument

                doc = DocxDocument(path)
                text = "\n".join(p.text for p in doc.paragraphs)
                documents.append(
                    Document(
                        page_content=text,
                        metadata={
                            "source_file": os.path.basename(path),
                            "page": 0,
                        },
                    )
                )
            except Exception:
                pass

        # Images (OCR)
        elif ext in [".png", ".jpg", ".jpeg"]:
            try:
                import pytesseract
                from PIL import Image

                text = pytesseract.image_to_string(Image.open(path))
                documents.append(
                    Document(
                        page_content=text,
                        metadata={
                            "source_file": os.path.basename(path),
                            "page": 0,
                        },
                    )
                )
            except Exception:
                pass

    return documents


def split_documents(documents):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
    )
    return splitter.split_documents(documents)