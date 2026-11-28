import faiss
import pickle
from sentence_transformers import SentenceTransformer


# ==========================================================
# LOAD MODEL
# ==========================================================

print("Loading embedding model...")

model = SentenceTransformer(
    "sentence-transformers/all-MiniLM-L6-v2"
)


# ==========================================================
# LOAD INTERIOR VECTOR DATABASE
# ==========================================================

interior_index = faiss.read_index(
    "vector_db/interior.index"
)

with open(
    "vector_db/interior_documents.pkl",
    "rb"
) as f:
    interior_documents = pickle.load(f)


# ==========================================================
# LOAD DECOR VECTOR DATABASE
# ==========================================================

decor_index = faiss.read_index(
    "vector_db/decor.index"
)

with open(
    "vector_db/decor_documents.pkl",
    "rb"
) as f:
    decor_documents = pickle.load(f)


# ==========================================================
# USER QUERY
# ==========================================================

query = input(
    "\nEnter your interior design requirement: "
)


# ==========================================================
# CREATE QUERY EMBEDDING
# ==========================================================

query_embedding = model.encode(
    [query],
    convert_to_numpy=True
).astype("float32")


# ==========================================================
# SEARCH INTERIOR DATASET
# ==========================================================

k = 5

distances, indices = interior_index.search(
    query_embedding,
    k
)


print("\n======================================")
print("INTERIOR DESIGN RESULTS")
print("======================================")


for i, index in enumerate(indices[0]):

    print(f"\n--- Result {i + 1} ---")

    print(
        interior_documents[index]
    )

    print(
        "Distance:",
        distances[0][i]
    )


# ==========================================================
# SEARCH DECOR DATASET
# ==========================================================

decor_k = 5

decor_distances, decor_indices = decor_index.search(
    query_embedding,
    decor_k
)


print("\n======================================")
print("FURNITURE / DECOR RESULTS")
print("======================================")


for i, index in enumerate(decor_indices[0]):

    print(f"\n--- Result {i + 1} ---")

    print(
        decor_documents[index]
    )

    print(
        "Distance:",
        decor_distances[0][i]
    )


print("\n======================================")
print("RAG RETRIEVAL TEST COMPLETED")
print("======================================")