"""
ArtSense AI - Hybrid Fast Search + Gemini RAG Pipeline
Simple filter searches use pandas directly; detailed questions use FAISS + Gemini.
"""

import os
import time
import hashlib
from pathlib import Path

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_google_genai import ChatGoogleGenerativeAI


# -------------------- CONFIGURATION --------------------

BASE_DIR = Path(__file__).resolve().parent
DATA_PATH = BASE_DIR / "fused_data" / "final_fused_dataset.csv"
VECTOR_DB_PATH = BASE_DIR / "vector_db"
SIGNATURE_FILE = VECTOR_DB_PATH / "dataset_signature.txt"

# Change this version if create_artwork_text() changes.
DOCUMENT_VERSION = "artsense-hybrid-v1"
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

# Retain the model name used in your current project.
# If Google reports it is unavailable, choose a model enabled for your API key.
GEMINI_MODEL = "gemini-3.6-flash"

REQUIRED_COLUMNS = [
    "title", "artist", "date", "medium", "department",
    "classification", "culture", "description", "image_url",
    "object_id", "source", "record_source", "price",
    "signed", "condition", "period", "movement"
]

SOURCE_ALIASES = {
    "Met Museum": ["met museum", "metropolitan museum", "the met"],
    "Smithsonian": ["smithsonian museum", "smithsonian"],
    "Art Institute of Chicago": ["art institute of chicago", "chicago museum"],
    "Cleveland Museum": ["cleveland museum of art", "cleveland museum"],
    "Victoria and Albert Museum": [
        "victoria and albert museum", "victoria and albert",
        "v&a", "v & a", "v and a"
    ],
}

MOVEMENTS = sorted([
    "Baroque", "Abstract", "Realism", "Expressionism", "Pop Art",
    "Conceptual", "Surrealism", "Impressionism",
    "Geometric Abstraction", "Minimalism", "Abstract Expressionism",
    "Feminist Art", "Traditional", "Post-Minimalism"
], key=len, reverse=True)

PERIODS = sorted(
    ["Contemporary", "Post-War", "Modern", "19th Century"],
    key=len,
    reverse=True
)


# -------------------- DATASET HELPERS --------------------

def clean_value(value):
    if pd.isna(value):
        return "Unknown"
    value = str(value).strip()
    if not value or value.lower() in {"nan", "none", "null"}:
        return "Unknown"
    return value


def create_artwork_text(row):
    description = str(row["description"])[:300]
    return (
        f"Artwork Title: {row['title']}\n"
        f"Artist: {row['artist']}\n"
        f"Date: {row['date']}\n"
        f"Medium: {row['medium']}\n"
        f"Department: {row['department']}\n"
        f"Classification: {row['classification']}\n"
        f"Culture: {row['culture']}\n"
        f"Movement: {row['movement']}\n"
        f"Period: {row['period']}\n"
        f"Price: {row['price']}\n"
        f"Condition: {row['condition']}\n"
        f"Signed: {row['signed']}\n"
        f"Source: {row['source']}\n"
        f"Description: {description}"
    )


def load_dataset():
    if not DATA_PATH.exists():
        raise FileNotFoundError(
            f"Dataset not found: {DATA_PATH}\n"
            "Check fused_data/final_fused_dataset.csv."
        )

    data = pd.read_csv(DATA_PATH)

    if "Unnamed: 0" in data.columns:
        data = data.drop(columns=["Unnamed: 0"])

    for column in REQUIRED_COLUMNS:
        if column not in data.columns:
            data[column] = "Unknown"

    for column in REQUIRED_COLUMNS:
        data[column] = data[column].apply(clean_value)

    data["artwork_text"] = data.apply(create_artwork_text, axis=1)
    return data


def make_documents(data):
    documents = []
    for index, row in data.iterrows():
        documents.append(
            Document(
                page_content=row["artwork_text"],
                metadata={
                    "id": int(index),
                    "title": row["title"],
                    "artist": row["artist"],
                    "source": row["source"],
                    "record_source": row["record_source"],
                    "movement": row["movement"],
                    "period": row["period"],
                    "medium": row["medium"],
                    "date": row["date"],
                    "price": row["price"],
                },
            )
        )
    return documents


def get_dataset_signature():
    digest = hashlib.sha256()
    digest.update(DATA_PATH.read_bytes())
    digest.update(DOCUMENT_VERSION.encode("utf-8"))
    return digest.hexdigest()


# -------------------- CACHED INITIALIZATION --------------------

@st.cache_resource(show_spinner="Loading ArtSense AI models and artwork database...")
def get_resources():
    """Initialize models and database once; reuse them on Streamlit reruns."""
    print("\nInitializing ArtSense AI...")
    load_dotenv(BASE_DIR / ".env")

    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError(
            "GOOGLE_API_KEY not found. Add it to the .env file "
            "inside your ArtSense-AI folder."
        )

    init_start = time.perf_counter()

    start = time.perf_counter()
    data = load_dataset()
    documents = make_documents(data)
    print(f"Dataset preparation: {time.perf_counter() - start:.2f}s")
    print(f"Dataset shape: {data.shape}")

    start = time.perf_counter()
    embeddings = HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL,
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )
    print(f"Embedding model initialization: {time.perf_counter() - start:.2f}s")

    index_file = VECTOR_DB_PATH / "index.faiss"
    pickle_file = VECTOR_DB_PATH / "index.pkl"
    signature = get_dataset_signature()

    saved_signature = (
        SIGNATURE_FILE.read_text(encoding="utf-8").strip()
        if SIGNATURE_FILE.exists()
        else None
    )

    index_is_current = (
        index_file.exists()
        and pickle_file.exists()
        and saved_signature == signature
    )

    start = time.perf_counter()
    if index_is_current:
        vector_db = FAISS.load_local(
            str(VECTOR_DB_PATH),
            embeddings,
            allow_dangerous_deserialization=True,
        )
        print("Existing FAISS database loaded.")
    else:
        print("Building FAISS database. First startup may take a while...")
        VECTOR_DB_PATH.mkdir(parents=True, exist_ok=True)
        vector_db = FAISS.from_documents(documents, embeddings)
        vector_db.save_local(str(VECTOR_DB_PATH))
        SIGNATURE_FILE.write_text(signature, encoding="utf-8")
        print(f"Created FAISS database with {len(documents)} records.")

    print(f"FAISS load/build time: {time.perf_counter() - start:.2f}s")

    llm = ChatGoogleGenerativeAI(
        model=GEMINI_MODEL,
        google_api_key=api_key,
        temperature=0.2,
        max_output_tokens=350,
        max_retries=1,
        timeout=60,
    )

    print(f"Total initialization: {time.perf_counter() - init_start:.2f}s")
    print("ArtSense AI is ready.")
    return data, vector_db, llm


# -------------------- FILTER DETECTION --------------------

def detect_filter(query):
    query_lower = query.lower()

    for source, aliases in SOURCE_ALIASES.items():
        if any(alias in query_lower for alias in aliases):
            return "source", source

    for movement in MOVEMENTS:
        if movement.lower() in query_lower:
            return "movement", movement

    for period in PERIODS:
        if period.lower() in query_lower:
            return "period", period

    return None, None


def is_simple_search(query):
    """
    Direct CSV answers for basic filter/list requests.
    Explanations, comparisons and recommendations use Gemini.
    """
    q = query.lower().strip()

    detailed_words = [
        "recommend", "recommendation", "why", "explain",
        "compare", "comparison", "analyze", "analysis",
        "difference", "describe", "suggest"
    ]
    if any(word in q for word in detailed_words):
        return False

    simple_starts = (
        "find ", "show ", "list ", "display ",
        "search ", "get ", "which artworks"
    )
    return detect_filter(q)[0] is not None and q.startswith(simple_starts)


# -------------------- FAST DIRECT DATASET SEARCH --------------------

def format_artworks(data, limit=8):
    if data.empty:
        return "I could not find matching artworks in the dataset."

    output = [f"Found {len(data)} matching artwork(s)."]
    for number, (_, row) in enumerate(data.head(limit).iterrows(), start=1):
        output.append(
            f"\n{number}. **{row['title']}**\n"
            f"   Artist: {row['artist']}\n"
            f"   Movement: {row['movement']}\n"
            f"   Period: {row['period']}\n"
            f"   Medium: {row['medium']}\n"
            f"   Price: {row['price']}\n"
            f"   Source: {row['source']}"
        )

    if len(data) > limit:
        output.append(f"\nShowing first {limit} of {len(data)} results.")
    return "\n".join(output)


def direct_dataset_search(query):
    data, _, _ = get_resources()
    field, value = detect_filter(query)
    if not field:
        return None

    matches = data[
        data[field].str.casefold() == value.casefold()
    ].copy()

    return format_artworks(matches)


# -------------------- FAISS SEMANTIC SEARCH --------------------

def search_artworks(query, k=3):
    _, vector_db, _ = get_resources()
    field, value = detect_filter(query)

    if field:
        results = vector_db.similarity_search(
            query, k=k, filter={field: value}
        )
        if results:
            return results

    return vector_db.similarity_search(query, k=k)


# -------------------- GEMINI RAG FOR DETAILED QUESTIONS --------------------

def ask_with_gemini(question, k=3):
    _, _, llm = get_resources()

    retrieval_start = time.perf_counter()
    results = search_artworks(question, k=k)
    retrieval_time = time.perf_counter() - retrieval_start
    print(f"FAISS retrieval time: {retrieval_time:.2f}s")

    if not results:
        return "I could not find enough information in the artwork dataset."

    context = "\n\n".join(
        f"ARTWORK {i + 1}\n{doc.page_content}"
        for i, doc in enumerate(results)
    )

    prompt = f"""
You are ArtSense AI, an assistant for artwork discovery,
recommendation and analysis.

Use ONLY the artwork records in the supplied database context.
Do not invent information or use outside knowledge.
If the answer is not supported by the context, say:
"I could not find enough information in the artwork dataset."

Mention artwork titles and artists when relevant.
For recommendations, briefly explain why each artwork matches.
Use bullet points for multiple artworks.
Treat Unknown as missing information.
Keep the response concise and useful.

ARTWORK DATABASE CONTEXT:
{context}

USER QUESTION:
{question}

ARTSENSE AI ANSWER:
"""

    gemini_start = time.perf_counter()
    response = llm.invoke(prompt)
    gemini_time = time.perf_counter() - gemini_start
    print(f"Gemini response time: {gemini_time:.2f}s")
    print(f"Retrieval + Gemini time: {retrieval_time + gemini_time:.2f}s")

    answer = getattr(response, "text", None)
    if not answer:
        answer = str(response.content)
    return answer


# -------------------- FUNCTION USED BY app.py --------------------

def ask_artsense(question, k=3):
    """
    Hybrid mode:
      - Basic museum/movement/period searches: direct CSV response.
      - Detailed questions and recommendations: FAISS + Gemini.
    """
    if not question or not str(question).strip():
        return "Please enter a question about artworks."

    question = str(question).strip()
    total_start = time.perf_counter()

    try:
        if is_simple_search(question):
            print("\nResponse mode: FAST DIRECT DATASET SEARCH")
            answer = direct_dataset_search(question)
            print(
                f"Direct search total time: "
                f"{time.perf_counter() - total_start:.2f}s"
            )
            return answer

        print("\nResponse mode: FAISS + GEMINI RAG")
        answer = ask_with_gemini(question, k=k)
        print(
            f"Total ArtSense AI time: "
            f"{time.perf_counter() - total_start:.2f}s"
        )
        return answer

    except Exception as error:
        print(f"ArtSense AI error: {error}")
        return (
            "Sorry, ArtSense AI could not process your question.\n\n"
            f"Error: {error}"
        )


if __name__ == "__main__":
    for test_question in [
        "Show Abstract artworks",
        "Recommend interesting artworks",
    ]:
        print("\n" + "=" * 60)
        print("QUESTION:", test_question)
        print("=" * 60)
        print(ask_artsense(test_question))
