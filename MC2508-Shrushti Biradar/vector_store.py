
"""
vector_store.py

Creates a FAISS vector store from PDF text chunks
using Hugging Face sentence embeddings.
"""

from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings


def create_vector_store(chunks):
    """Convert document chunks into vectors and store them in FAISS."""

    if not chunks:
        raise ValueError("No PDF text chunks were provided.")

    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )

    vector_store = FAISS.from_documents(
        documents=chunks,
        embedding=embeddings,
    )

    return vector_store
