
import os
import pickle
import faiss
import numpy as np

from rag.document_loader import load_food_documents
from rag.embeddings import create_embeddings
from config import BASE_DIR

INDEX_DIR = os.path.join(BASE_DIR, "data", "rag_index")

INDEX_FILE = os.path.join(
    INDEX_DIR, "food_index.faiss"
)

METADATA_FILE = os.path.join(
    INDEX_DIR, "food_metadata.pkl"
)


def build_vector_store():
    os.makedirs(INDEX_DIR, exist_ok=True)

    print("Loading PDF and Excel documents...")
    documents = load_food_documents()

    if not documents:
        raise ValueError("Knowledge base is empty.")

    print("\nCreating embeddings...")
    embeddings = create_embeddings(documents)

    embeddings = np.asarray(
        embeddings, dtype=np.float32
    )

    dimension = embeddings.shape[1]

    print("\nBuilding FAISS index...")

    index = faiss.IndexFlatIP(dimension)
    index.add(embeddings)

    faiss.write_index(index, INDEX_FILE)

    with open(METADATA_FILE, "wb") as file:
        pickle.dump(documents, file)

    print("\n========== VECTOR STORE ==========")
    print(f"Total indexed documents: {index.ntotal}")
    print(f"Embedding dimensions: {dimension}")
    print(f"Index saved: {INDEX_FILE}")
    print("FAISS knowledge base created successfully.")


if __name__ == "__main__":
    build_vector_store()
