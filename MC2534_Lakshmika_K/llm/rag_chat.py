import os
import json
import faiss
import numpy as np

from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
from google import genai


# ==================================================
# 1. LOAD API KEY
# ==================================================

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("GEMINI_API_KEY not found in .env file")

client = genai.Client(api_key=api_key)


# ==================================================
# 2. LOAD RAG KNOWLEDGE BASE
# ==================================================

RAG_PATH = "data/rag"

index = faiss.read_index(
    f"{RAG_PATH}/waste_knowledge.index"
)

with open(
    f"{RAG_PATH}/documents.json",
    "r",
    encoding="utf-8"
) as file:
    documents = json.load(file)


# ==================================================
# 3. LOAD EMBEDDING MODEL
# ==================================================

embedding_model = SentenceTransformer(
    "all-MiniLM-L6-v2"
)


# ==================================================
# 4. RETRIEVAL FUNCTION
# ==================================================

def retrieve_documents(question, top_k=5):

    question_embedding = embedding_model.encode(
        [question],
        normalize_embeddings=True
    )

    question_embedding = np.asarray(
        question_embedding,
        dtype="float32"
    )

    scores, indices = index.search(
        question_embedding,
        top_k
    )

    results = []

    for score, idx in zip(scores[0], indices[0]):

        if idx < len(documents):

            results.append({
                "score": float(score),
                "document": documents[idx]
            })

    return results


# ==================================================
# 5. GENERATE LLM RESPONSE
# ==================================================

def generate_answer(question):

    retrieved = retrieve_documents(
        question,
        top_k=5
    )

    # Prepare retrieved context
    context_parts = []

    for i, item in enumerate(retrieved, start=1):

        context_parts.append(
            f"""
--- Retrieved Document {i} ---
Similarity Score: {item['score']:.4f}

{item['document']}
"""
        )

    context = "\n".join(context_parts)

    prompt = f"""
You are a Smart Waste Segregation and Collection Assistant.

You must answer the user's question using the
retrieved waste-management information provided below.

Do not invent statistics or facts that are not
supported by the retrieved information.

If the retrieved information is insufficient,
say that clearly.

RETRIEVED KNOWLEDGE:
====================
{context}
====================

USER QUESTION:
{question}

Give a clear and practical answer.
"""

    response = client.models.generate_content(
       model="gemini-3.6-flash",
        contents=prompt
    )

    return retrieved, response.text


# ==================================================
# 6. CHAT INTERFACE
# ==================================================

if __name__ == "__main__":

    print("\n======================================")
    print("♻️ SMART WASTE RAG ASSISTANT")
    print("======================================")
    print("Ask a question about waste management.")
    print("Type 'exit' to stop.\n")

    while True:

        question = input("You: ")

        if question.lower() == "exit":
            print("Goodbye!")
            break

        try:

            retrieved, answer = generate_answer(question)

            print("\n🔎 RETRIEVED DATA FROM KAGGLE:")
            print("--------------------------------------")

            for i, item in enumerate(
                retrieved,
                start=1
            ):

                print(
                    f"\nDocument {i} "
                    f"(Similarity: {item['score']:.4f})"
                )

                print(
                    item["document"][:500]
                )

            print("\n🤖 LLM ANSWER:")
            print("--------------------------------------")
            print(answer)
            print()

        except Exception as e:

            print("\n❌ Error:")
            print(e)