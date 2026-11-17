
import os
import time
import pandas as pd
import chromadb

from dotenv import load_dotenv
from google import genai
from google.genai import types

# --------------------------------------------------
# CONFIGURATION
# --------------------------------------------------

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    raise ValueError(
        "GEMINI_API_KEY not found. Check your .env file."
    )

DATASET_PATH = "data/fused_country_intelligence.csv"
CHROMA_PATH = "data/chroma_db"

COLLECTION_NAME = "country_intelligence"

EMBEDDING_MODEL = "gemini-embedding-001"
EMBEDDING_DIMENSIONS = 768

# Smaller batches reduce the number of tokens per request.
BATCH_SIZE = 5

# Wait between successful embedding requests.
WAIT_BETWEEN_BATCHES = 35

# Retry settings for quota errors.
MAX_RETRIES = 5

client = genai.Client(api_key=API_KEY)


# --------------------------------------------------
# CLEAN DATA VALUES
# --------------------------------------------------

def clean_value(value):

    if pd.isna(value):
        return None

    return str(value).strip()


# --------------------------------------------------
# CONVERT COUNTRY ROW INTO DOCUMENT
# --------------------------------------------------

def create_country_document(row):

    country_name = clean_value(row.get("Country Name"))

    lines = [
        f"Country: {country_name or 'Unknown'}"
    ]

    for column in row.index:

        value = clean_value(row[column])

        if value is not None and value != "":
            lines.append(f"{column}: {value}")

    return "\n".join(lines)


# --------------------------------------------------
# GENERATE EMBEDDINGS WITH AUTOMATIC RETRIES
# --------------------------------------------------

def generate_embeddings(documents):

    for attempt in range(1, MAX_RETRIES + 1):

        try:

            response = client.models.embed_content(
                model=EMBEDDING_MODEL,
                contents=documents,
                config=types.EmbedContentConfig(
                    task_type="RETRIEVAL_DOCUMENT",
                    output_dimensionality=EMBEDDING_DIMENSIONS
                )
            )

            return [
                embedding.values
                for embedding in response.embeddings
            ]

        except Exception as error:

            error_message = str(error)

            is_quota_error = (
                "429" in error_message
                or "RESOURCE_EXHAUSTED" in error_message
                or "quota" in error_message.lower()
            )

            if not is_quota_error:
                raise

            if attempt == MAX_RETRIES:
                raise

            wait_time = 65 * attempt

            print(
                f"\nGemini quota limit reached."
                f"\nRetry {attempt}/{MAX_RETRIES}."
                f"\nWaiting {wait_time} seconds...\n"
            )

            time.sleep(wait_time)

    raise RuntimeError("Embedding generation failed.")


# --------------------------------------------------
# BUILD OR RESUME KNOWLEDGE BASE
# --------------------------------------------------

def build_knowledge_base():

    print("Loading fused country dataset...")

    if not os.path.exists(DATASET_PATH):
        raise FileNotFoundError(
            f"Dataset not found: {DATASET_PATH}"
        )

    df = pd.read_csv(DATASET_PATH)

    if "Country Name" not in df.columns:
        raise ValueError(
            "Country Name column not found in dataset."
        )

    print("Dataset records:", len(df))
    print("Dataset columns:", len(df.columns))

    # Connect to existing ChromaDB database.
    chroma_client = chromadb.PersistentClient(
        path=CHROMA_PATH
    )

    # Get existing collection or create it.
    collection = chroma_client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={
            "description": "Fused country intelligence dataset"
        }
    )

    print(
        "Existing knowledge base records:",
        collection.count()
    )

    # Find IDs already stored so we do not process them again.
    existing_records = collection.get()

    existing_ids = set(existing_records["ids"])

    documents = []
    ids = []
    metadatas = []

    # Prepare only records that are not already stored.
    for index, row in df.iterrows():

        country_name = clean_value(
            row.get("Country Name")
        )

        country_code = clean_value(
            row.get("Country Code")
        )

        if not country_name:
            country_name = f"Unknown Country {index}"

        if not country_code:
            country_code = "Unknown"

        record_id = f"{country_code}_{index}"

        # Skip records already present in ChromaDB.
        if record_id in existing_ids:
            continue

        document = create_country_document(row)

        documents.append(document)
        ids.append(record_id)

        metadatas.append({
            "country_name": country_name,
            "country_code": country_code,
            "record_index": int(index)
        })

    total_pending = len(documents)

    print("\nRecords still to process:", total_pending)

    if total_pending == 0:

        print("All dataset records are already in the knowledge base.")
        print("Final knowledge base count:", collection.count())
        return

    # Process remaining records in small batches.
    for start in range(0, total_pending, BATCH_SIZE):

        end = min(start + BATCH_SIZE, total_pending)

        batch_documents = documents[start:end]
        batch_ids = ids[start:end]
        batch_metadatas = metadatas[start:end]

        print(
            f"\nProcessing pending records "
            f"{start + 1} to {end} of {total_pending}..."
        )

        # Generate embeddings.
        embeddings = generate_embeddings(
            batch_documents
        )

        # Save records immediately after successful embedding.
        collection.add(
            ids=batch_ids,
            documents=batch_documents,
            embeddings=embeddings,
            metadatas=batch_metadatas
        )

        print(
            "Successfully saved records:",
            collection.count()
        )

        # Wait before the next embedding request.
        if end < total_pending:

            print(
                f"Waiting {WAIT_BETWEEN_BATCHES} seconds "
                "to avoid Gemini quota limits..."
            )

            time.sleep(WAIT_BETWEEN_BATCHES)

    print("\n--------------------------------")
    print("KNOWLEDGE BASE BUILD COMPLETED")
    print("--------------------------------")

    print("CSV records:", len(df))
    print("Knowledge base records:", collection.count())


# --------------------------------------------------
# RUN SCRIPT
# --------------------------------------------------

if __name__ == "__main__":

    try:
        build_knowledge_base()

    except Exception as error:

        print("\nKnowledge base build stopped.")
        print("Error:", error)
        print(
            "Your successfully saved records have been retained. "
            "Run this script again to resume."
        )
