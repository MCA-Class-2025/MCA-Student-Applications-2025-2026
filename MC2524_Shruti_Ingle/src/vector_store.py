import os
from config import EMBEDDING_MODEL, VECTOR_DB_PATH
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings


def create_vector_store(documents):
    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
    db = FAISS.from_documents(documents, embeddings)

    os.makedirs(VECTOR_DB_PATH, exist_ok=True)
    db.save_local(VECTOR_DB_PATH)

    return db


def load_vector_store():
    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
    return FAISS.load_local(
        VECTOR_DB_PATH,
        embeddings,
        allow_dangerous_deserialization=True,
    )