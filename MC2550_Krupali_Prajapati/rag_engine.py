
import os
import re
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

CHROMA_PATH = "data/chroma_db"

COLLECTION_NAME = "country_intelligence"

EMBEDDING_MODEL = "gemini-embedding-001"
GENERATION_MODEL = "gemini-3.1-flash-lite"

EMBEDDING_DIMENSIONS = 768

client = genai.Client(api_key=API_KEY)

chroma_client = chromadb.PersistentClient(
    path=CHROMA_PATH
)


# --------------------------------------------------
# GET KNOWLEDGE BASE COLLECTION
# --------------------------------------------------

def get_collection():

    try:
        return chroma_client.get_collection(
            name=COLLECTION_NAME
        )

    except Exception as error:
        raise RuntimeError(
            "Knowledge base not found. "
            "Run: python build_knowledge_base.py"
        ) from error


# --------------------------------------------------
# KNOWLEDGE BASE RECORD COUNT
# --------------------------------------------------

def knowledge_base_count():

    collection = get_collection()

    return collection.count()


# --------------------------------------------------
# GENERATE QUESTION EMBEDDING
# --------------------------------------------------

def generate_question_embedding(question):

    response = client.models.embed_content(
        model=EMBEDDING_MODEL,
        contents=question,
        config=types.EmbedContentConfig(
            task_type="RETRIEVAL_QUERY",
            output_dimensionality=EMBEDDING_DIMENSIONS
        )
    )

    return response.embeddings[0].values


# --------------------------------------------------
# RETRIEVE RELEVANT COUNTRY RECORDS
# --------------------------------------------------

def retrieve_documents(question, top_k=5):

    collection = get_collection()

    # Read the available country records and their metadata.
    all_records = collection.get(
        include=["documents", "metadatas"]
    )

    all_documents = all_records.get("documents") or []
    all_metadatas = all_records.get("metadatas") or []

    # Find country names explicitly mentioned in the question.
    mentioned_countries = []

    for metadata in all_metadatas:

        country_name = metadata.get("country_name", "")

        if not country_name:
            continue

        pattern = (
            r"(?<!\w)"
            + re.escape(country_name)
            + r"(?!\w)"
        )

        if re.search(pattern, question, re.IGNORECASE):
            if country_name not in mentioned_countries:
                mentioned_countries.append(country_name)

    documents = []
    metadatas = []

    # Exact country matching takes priority.
    if mentioned_countries:

        for document, metadata in zip(
            all_documents,
            all_metadatas
        ):

            if metadata.get("country_name") in mentioned_countries:
                documents.append(document)
                metadatas.append(metadata)

    # If no country is explicitly named, use semantic search.
    else:

        question_embedding = generate_question_embedding(
            question
        )

        results = collection.query(
            query_embeddings=[question_embedding],
            n_results=min(top_k, collection.count()),
            include=["documents", "metadatas", "distances"]
        )

        documents = results["documents"][0]
        metadatas = results["metadatas"][0]

    if not documents:
        return "", []

    # Create context for Gemini.
    context_parts = []

    for document in documents:
        context_parts.append(document)

    context = "\n\n--------------------\n\n".join(
        context_parts
    )

    # Prepare source names for the application.
    sources = []

    for metadata in metadatas:

        country_name = metadata.get(
            "country_name",
            "Unknown country"
        )

        country_code = metadata.get(
            "country_code",
            "Unknown"
        )

        sources.append(
            f"{country_name} ({country_code})"
        )

    return context, sources


# --------------------------------------------------
# GENERATE ANSWER USING GEMINI
# --------------------------------------------------

def answer_question(question):

    if not question or not question.strip():
        return (
            "Please enter a question.",
            []
        )

    context, sources = retrieve_documents(
        question,
        top_k=5
    )

    if not context:
        return (
            "I could not find relevant information in the "
            "country intelligence knowledge base.",
            []
        )

    prompt = f"""
You are an AI Country Intelligence Assistant.

Answer the user's question using ONLY the country
intelligence records provided below.

IMPORTANT RULES:

1. Use the retrieved records as your source of information.
2. Do not invent statistics, values, dates or facts.
3. If a requested field is missing or unavailable,
   clearly state that it is not available in the dataset.
4. If the user asks to compare countries, compare the
   corresponding values from each country's record.
5. Mention the country names in your answer.
6. Explain the answer in clear and simple language.
7. Do not claim that a value is missing if it is present
   in the supplied records.
8. Do not use outside knowledge to fill missing dataset values.

RETRIEVED COUNTRY INTELLIGENCE RECORDS:

{context}

USER QUESTION:

{question}

ANSWER:
"""

    try:

        response = client.models.generate_content(
            model=GENERATION_MODEL,
            contents=prompt
        )

        answer = response.text

        if not answer:
            answer = "Gemini did not return a response."

        return answer, sources

    except Exception as error:

        return (
            f"Unable to generate an answer: {str(error)}",
            sources
        )
