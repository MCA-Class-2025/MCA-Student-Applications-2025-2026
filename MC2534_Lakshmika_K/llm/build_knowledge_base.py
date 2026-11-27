import os
import json
import pandas as pd
import numpy as np
import faiss

from sentence_transformers import SentenceTransformer


# ==========================================
# PATHS
# ==========================================

DATASET_PATH = "dataset"
RAG_PATH = "data/rag"

os.makedirs(RAG_PATH, exist_ok=True)


# ==========================================
# KAGGLE DATASETS
# ==========================================

FILES = [
    "cities_master.csv",
    "Waste_Management_and_Recycling_India.csv",
    "Waste_Management_India_20K.csv"
]


# ==========================================
# LOAD AND CONVERT DATA INTO DOCUMENTS
# ==========================================

documents = []
metadata = []

print("\nLoading Kaggle datasets...\n")

for filename in FILES:

    path = os.path.join(DATASET_PATH, filename)

    df = pd.read_csv(path)

    df.columns = df.columns.str.strip()

    print(f"{filename} -> {df.shape[0]} rows, {df.shape[1]} columns")

    for index, row in df.iterrows():

        information = []

        for column in df.columns:

            value = row[column]

            if pd.notna(value):

                information.append(
                    f"{column}: {value}"
                )

        document = (
            f"Source Dataset: {filename}\n"
            + "\n".join(information)
        )

        documents.append(document)

        metadata.append({
            "source": filename,
            "row": int(index)
        })


print("\nTotal documents created:", len(documents))


# ==========================================
# CREATE EMBEDDINGS
# ==========================================

print("\nLoading embedding model...")

embedding_model = SentenceTransformer(
    "all-MiniLM-L6-v2"
)

print("Creating embeddings...")
print("This may take some time because the dataset is large.\n")

embeddings = embedding_model.encode(
    documents,
    batch_size=32,
    show_progress_bar=True,
    normalize_embeddings=True
)

embeddings = np.asarray(
    embeddings,
    dtype="float32"
)


# ==========================================
# CREATE FAISS VECTOR DATABASE
# ==========================================

print("\nCreating FAISS vector database...")

dimension = embeddings.shape[1]

index = faiss.IndexFlatIP(dimension)

index.add(embeddings)


# ==========================================
# SAVE FAISS INDEX
# ==========================================

index_path = os.path.join(
    RAG_PATH,
    "waste_knowledge.index"
)

faiss.write_index(
    index,
    index_path
)


# ==========================================
# SAVE DOCUMENTS
# ==========================================

documents_path = os.path.join(
    RAG_PATH,
    "documents.json"
)

with open(
    documents_path,
    "w",
    encoding="utf-8"
) as file:

    json.dump(
        documents,
        file,
        ensure_ascii=False
    )


# ==========================================
# SAVE METADATA
# ==========================================

metadata_path = os.path.join(
    RAG_PATH,
    "metadata.json"
)

with open(
    metadata_path,
    "w",
    encoding="utf-8"
) as file:

    json.dump(
        metadata,
        file,
        ensure_ascii=False
    )


# ==========================================
# FINAL RESULT
# ==========================================

print("\n")
print("=" * 60)
print("       RAG KNOWLEDGE BASE CREATED")
print("=" * 60)

print("\nTotal documents:", len(documents))

print("Embedding dimension:", dimension)

print("\nCreated files:")

print("1. data/rag/waste_knowledge.index")
print("2. data/rag/documents.json")
print("3. data/rag/metadata.json")

print("\nRAG knowledge base is ready!")