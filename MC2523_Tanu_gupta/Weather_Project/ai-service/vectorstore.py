import os
import pandas as pd

from langchain_core.documents import Document
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings


# ==========================================
# CONFIGURATION
# ==========================================

INPUT_FILE = "data/weather_cleaned.csv"
VECTORSTORE_PATH = "vectorstore"

BATCH_SIZE = 1000


# ==========================================
# LOAD DATASET
# ==========================================

print("Loading cleaned weather dataset...")

df = pd.read_csv(INPUT_FILE)

print("Records loaded:", len(df))


# ==========================================
# CREATE EMBEDDING MODEL
# ==========================================

print("\nLoading embedding model...")

embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)

print("Embedding model loaded.")


# ==========================================
# CREATE FAISS DATABASE BATCH BY BATCH
# ==========================================

vectorstore = None

total_records = len(df)


print("\nCreating FAISS vector database...")
print("Batch size:", BATCH_SIZE)
print()


for start in range(0, total_records, BATCH_SIZE):

    end = min(
        start + BATCH_SIZE,
        total_records
    )

    batch = df.iloc[start:end]

    documents = []


    # --------------------------------------
    # CREATE DOCUMENTS FOR CURRENT BATCH
    # --------------------------------------

    for _, row in batch.iterrows():

        content = f"""
Historical Weather Record

City: {row['city']}

Date: {row['date']}

Weather condition: {row['weather_description']}

Maximum temperature: {row['temperature_2m_max']} degrees Celsius.

Minimum temperature: {row['temperature_2m_min']} degrees Celsius.

Maximum apparent temperature: {row['apparent_temperature_max']} degrees Celsius.

Minimum apparent temperature: {row['apparent_temperature_min']} degrees Celsius.

Total precipitation: {row['precipitation_sum']} mm.

Total rainfall: {row['rain_sum']} mm.

Maximum wind speed: {row['wind_speed_10m_max']} km/h.

Maximum wind gust: {row['wind_gusts_10m_max']} km/h.

Dominant wind direction: {row['wind_direction_10m_dominant']} degrees.
""".strip()


        metadata = {

            "city": str(row["city"]),

            "date": str(row["date"]),

            "weather_code": int(
                row["weather_code"]
            ),

            "weather_condition":
                str(row["weather_description"])

        }


        documents.append(
            Document(
                page_content=content,
                metadata=metadata
            )
        )


    # --------------------------------------
    # CREATE / ADD TO FAISS
    # --------------------------------------

    if vectorstore is None:

        vectorstore = FAISS.from_documents(
            documents,
            embeddings
        )

    else:

        vectorstore.add_documents(
            documents
        )


    # --------------------------------------
    # PROGRESS
    # --------------------------------------

    percentage = (
        end / total_records
    ) * 100


    print(
        f"Processed: {end}/{total_records} "
        f"({percentage:.2f}%)"
    )


# ==========================================
# SAVE VECTORSTORE
# ==========================================

print("\nSaving FAISS vector database...")


os.makedirs(
    VECTORSTORE_PATH,
    exist_ok=True
)


vectorstore.save_local(
    VECTORSTORE_PATH
)


# ==========================================
# COMPLETED
# ==========================================

print("\n======================================")

print("FAISS VECTOR DATABASE CREATED")

print("======================================")

print(
    "Total documents:",
    total_records
)

print(
    "Vector store:",
    VECTORSTORE_PATH
)

print("======================================")