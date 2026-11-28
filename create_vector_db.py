import os
import pickle
import pandas as pd
import faiss
from sentence_transformers import SentenceTransformer

# ==========================================================
# PATHS
# ==========================================================

INTERIOR_FILE = "processed_dataset/interior_rag_documents.csv"
DECOR_FILE = "processed_dataset/decor_rag_documents.csv"

VECTOR_DIR = "vector_db"

os.makedirs(VECTOR_DIR, exist_ok=True)


# ==========================================================
# LOAD EMBEDDING MODEL
# ==========================================================

print("Loading embedding model...")

model = SentenceTransformer(
    "sentence-transformers/all-MiniLM-L6-v2"
)

print("Embedding model loaded.")


# ==========================================================
# FUNCTION TO CREATE FAISS DATABASE
# ==========================================================

def create_vector_database(csv_file, index_file, documents_file):

    print("\nLoading:", csv_file)

    df = pd.read_csv(csv_file)

    documents = df["text"].fillna("").astype(str).tolist()

    print("Documents:", len(documents))

    print("Creating embeddings...")

    embeddings = model.encode(
        documents,
        show_progress_bar=True,
        convert_to_numpy=True
    )

    # Make sure FAISS uses float32
    embeddings = embeddings.astype("float32")

    print("Embedding shape:", embeddings.shape)

    # ------------------------------------------------------
    # Create FAISS index
    # ------------------------------------------------------

    dimension = embeddings.shape[1]

    index = faiss.IndexFlatL2(dimension)

    index.add(embeddings)

    print("FAISS vectors:", index.ntotal)

    # ------------------------------------------------------
    # Save FAISS index
    # ------------------------------------------------------

    faiss.write_index(
        index,
        index_file
    )

    # ------------------------------------------------------
    # Save original documents
    # ------------------------------------------------------

    with open(documents_file, "wb") as f:
        pickle.dump(documents, f)

    print("Saved:")
    print(index_file)
    print(documents_file)


# ==========================================================
# INTERIOR DESIGN VECTOR DATABASE
# ==========================================================

create_vector_database(
    INTERIOR_FILE,
    f"{VECTOR_DIR}/interior.index",
    f"{VECTOR_DIR}/interior_documents.pkl"
)


# ==========================================================
# DECOR VECTOR DATABASE
# ==========================================================

create_vector_database(
    DECOR_FILE,
    f"{VECTOR_DIR}/decor.index",
    f"{VECTOR_DIR}/decor_documents.pkl"
)


# ==========================================================
# COMPLETE
# ==========================================================

print("\n==========================================")
print("VECTOR DATABASE CREATION COMPLETED")
print("==========================================")