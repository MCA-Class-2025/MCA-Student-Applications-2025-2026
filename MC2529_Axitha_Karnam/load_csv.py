import os

from langchain_community.document_loaders import CSVLoader
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma


CSV_FILE = "merged_finance_data.csv"
CHROMA_DB = "chroma_db"

EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

BATCH_SIZE = 200


print("====================================")
print("Loading CSV...")
print("File:", CSV_FILE)
print("====================================")


# ------------------------------------------------------------
# LOAD CSV
# ------------------------------------------------------------

loader = CSVLoader(
    file_path=CSV_FILE
)

documents = loader.load()

print("CSV rows loaded:", len(documents))


# ------------------------------------------------------------
# EMBEDDING MODEL
# ------------------------------------------------------------

print("\nLoading embedding model...")

embedding = HuggingFaceEmbeddings(
    model_name=EMBEDDING_MODEL
)

print("Embedding model loaded successfully.")


# ------------------------------------------------------------
# CREATE CHROMA
# ------------------------------------------------------------

print("\nCreating Chroma database...")

db = Chroma(
    persist_directory=CHROMA_DB,
    embedding_function=embedding
)

print("Chroma database ready.")


# ------------------------------------------------------------
# ADD DOCUMENTS IN BATCHES
# ------------------------------------------------------------

total_documents = len(documents)

print("\nStarting embedding process...")
print("Total documents:", total_documents)
print("Batch size:", BATCH_SIZE)


for start in range(0, total_documents, BATCH_SIZE):

    end = min(
        start + BATCH_SIZE,
        total_documents
    )

    batch = documents[start:end]

    print(
        f"\nProcessing documents "
        f"{start + 1} - {end} "
        f"of {total_documents}..."
    )

    db.add_documents(batch)

    print(
        f"Completed: {end}/{total_documents}"
    )


print("\n====================================")
print("CSV RAG LOADING COMPLETE")
print("====================================")
print("Total documents:", total_documents)
print("Chroma database:", CHROMA_DB)