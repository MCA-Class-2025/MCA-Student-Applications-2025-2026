import os

from langchain_community.document_loaders import (
    PyPDFLoader,
    TextLoader
)
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma


# ============================================================
# CONFIGURATION
# ============================================================

PDF_FOLDER = "data/pdfs"
TXT_FOLDER = "data/Text"
CHROMA_DB = "chroma_db"

EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"


# ============================================================
# LOAD DOCUMENTS
# ============================================================

def load_documents():

    documents = []

    # --------------------------------------------------------
    # PDF FILES
    # --------------------------------------------------------

    if os.path.exists(PDF_FOLDER):

        for file in os.listdir(PDF_FOLDER):

            if file.lower().endswith(".pdf"):

                pdf_path = os.path.join(
                    PDF_FOLDER,
                    file
                )

                try:

                    loader = PyPDFLoader(pdf_path)

                    docs = loader.load()

                    documents.extend(docs)

                    print(f"Loaded PDF: {file}")

                except Exception as e:

                    print(
                        f"Error loading {file}: {e}"
                    )

    # --------------------------------------------------------
    # TEXT FILES
    # --------------------------------------------------------

    if os.path.exists(TXT_FOLDER):

        for file in os.listdir(TXT_FOLDER):

            if file.lower().endswith(".txt"):

                txt_path = os.path.join(
                    TXT_FOLDER,
                    file
                )

                try:

                    loader = TextLoader(
                        txt_path,
                        encoding="utf-8"
                    )

                    docs = loader.load()

                    documents.extend(docs)

                    print(f"Loaded TXT: {file}")

                except Exception as e:

                    print(
                        f"Error loading {file}: {e}"
                    )

    return documents


# ============================================================
# CREATE CHUNKS
# ============================================================

def create_chunks(documents):

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=100
    )

    chunks = splitter.split_documents(
        documents
    )

    return chunks


# ============================================================
# CREATE / UPDATE CHROMA DATABASE
# ============================================================

def create_vector_database():

    print("Loading documents...")

    documents = load_documents()

    if not documents:

        print("No documents found.")

        return False

    print(
        f"Loaded {len(documents)} documents"
    )

    # Create chunks

    chunks = create_chunks(
        documents
    )

    print(
        f"Total chunks: {len(chunks)}"
    )

    # Embeddings

    embedding = HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL
    )

    # Create Chroma database

    print(
        "Creating / updating ChromaDB..."
    )

    Chroma.from_documents(
        documents=chunks,
        embedding=embedding,
        persist_directory=CHROMA_DB
    )

    print(
        "ChromaDB updated successfully!"
    )

    return True


# ============================================================
# RUN DIRECTLY
# ============================================================

if __name__ == "__main__":

    create_vector_database()