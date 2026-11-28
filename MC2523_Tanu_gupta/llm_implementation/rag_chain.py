import os
from pathlib import Path

from dotenv import load_dotenv
from google import genai

from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings


# =====================================================
# CONFIGURATION
# =====================================================

VECTORSTORE_PATH = Path(__file__).resolve().parent / "vectorstore"

EMBEDDING_MODEL = (
    "sentence-transformers/all-MiniLM-L6-v2"
)

GEMINI_MODEL = "gemini-3.6-flash"


# =====================================================
# LOAD ENVIRONMENT VARIABLES
# =====================================================

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:

    raise ValueError(
        "GEMINI_API_KEY not found in .env file"
    )


# =====================================================
# CREATE GEMINI CLIENT
# =====================================================

print("Connecting to Gemini...")

client = genai.Client(
    api_key=api_key
)

print("Gemini connected successfully.")


# =====================================================
# LOAD EMBEDDING MODEL
# =====================================================

print("\nLoading embedding model...")

embeddings = HuggingFaceEmbeddings(
    model_name=EMBEDDING_MODEL
)

print("Embedding model loaded.")


# =====================================================
# LOAD FAISS VECTORSTORE
# =====================================================

print("\nLoading FAISS vector database...")

vectorstore = FAISS.load_local(
    VECTORSTORE_PATH,
    embeddings,
    allow_dangerous_deserialization=True
)

print("FAISS loaded successfully.")


# =====================================================
# CREATE RETRIEVER
# =====================================================

retriever = vectorstore.as_retriever(
    search_kwargs={
        "k": 5
    }
)


# =====================================================
# RAG FUNCTION
# =====================================================

def ask_weather_question(question):

    # ---------------------------------------------
    # STEP 1: RETRIEVE RELEVANT DOCUMENTS
    # ---------------------------------------------

    documents = retriever.invoke(
        question
    )


    # ---------------------------------------------
    # STEP 2: CREATE CONTEXT
    # ---------------------------------------------

    context_parts = []

    for document in documents:

        context_parts.append(
            document.page_content
        )

    context = "\n\n".join(
        context_parts
    )


    # ---------------------------------------------
    # STEP 3: CREATE PROMPT
    # ---------------------------------------------

    prompt = f"""
You are an AI Weather Assistant.

Your job is to answer questions about
historical weather data.

IMPORTANT RULES:

1. Use ONLY the weather information provided
   in the context below.

2. Do NOT invent weather information.

3. If the answer is not available in the
   context, clearly say that the information
   is not available in the historical dataset.

4. Give a clear and concise answer.

5. Mention the city and date when they are
   available.

6. Use Celsius for temperature.

7. Use mm for rainfall and precipitation.

8. Use km/h for wind speed.


================ WEATHER CONTEXT ================

{context}


================ USER QUESTION ================

{question}


================ ANSWER ================
"""


    # ---------------------------------------------
    # STEP 4: SEND TO GEMINI
    # ---------------------------------------------

    response = client.models.generate_content(

        model=GEMINI_MODEL,

        contents=prompt

    )


    # ---------------------------------------------
    # STEP 5: RETURN ANSWER
    # ---------------------------------------------

    return response.text, documents


# =====================================================
# TEST CHAT
# =====================================================

print("\n==========================================")

print("AI WEATHER RAG SYSTEM")

print("==========================================")

print("Type 'exit' to stop.")


while True:

    question = input(
        "\nAsk your weather question: "
    )


    if question.lower() == "exit":

        print(
            "\nExiting AI Weather Assistant..."
        )

        break


    if not question.strip():

        print(
            "Please enter a question."
        )

        continue


    try:

        answer, documents = (
            ask_weather_question(
                question
            )
        )


        print("\n==========================================")

        print("AI ANSWER")

        print("==========================================")

        print(answer)


        print("\n==========================================")

        print("RETRIEVED RECORDS")

        print("==========================================")


        for i, document in enumerate(
            documents,
            start=1
        ):

            print(
                f"\nResult {i}:"
            )

            print(
                document.metadata
            )


    except Exception as e:

        print(
            "\nError while processing question:"
        )

        print(e)