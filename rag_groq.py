
import os
import re
import math
import base64
import pickle
import requests

from pathlib import Path
from collections import Counter
from dotenv import load_dotenv

# ==========================================================
# 1. PATHS AND API CONFIGURATION
# ==========================================================

BASE_DIR = Path(__file__).resolve().parent
VECTOR_DIR = BASE_DIR / "vector_db"

load_dotenv(BASE_DIR / ".env", override=True)

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "").strip()
CLOUDFLARE_ACCOUNT_ID = os.getenv("CLOUDFLARE_ACCOUNT_ID", "").strip()
CLOUDFLARE_API_TOKEN = os.getenv("CLOUDFLARE_API_TOKEN", "").strip()

GROQ_MODEL = "openai/gpt-oss-120b"
CLOUDFLARE_MODEL = "@cf/black-forest-labs/flux-1-schnell"

INTERIOR_DOCS_PATH = VECTOR_DIR / "interior_documents.pkl"
DECOR_DOCS_PATH = VECTOR_DIR / "decor_documents.pkl"

# Keep the FLUX prompt below its 2,048-character limit.
CLOUDFLARE_PROMPT_LIMIT = 1800

# ==========================================================
# 2. GROQ CLIENT
# ==========================================================

groq_client = None

if GROQ_API_KEY:
    try:
        from groq import Groq
        groq_client = Groq(api_key=GROQ_API_KEY)
        print("Groq connected successfully.")
    except Exception as exc:
        print("Groq initialization error:", exc)


# ==========================================================
# 3. LOAD RAG DOCUMENTS
# ==========================================================

def load_documents(file_path):
    if not file_path.exists():
        print("Document file not found:", file_path)
        return []

    try:
        with open(file_path, "rb") as file:
            documents = pickle.load(file)

        if isinstance(documents, list):
            print(f"Loaded {len(documents)} documents from {file_path.name}")
            return documents

        print("Unexpected document format:", file_path.name)
        return []

    except Exception as exc:
        print(f"Could not load {file_path.name}:", exc)
        return []


interior_documents = load_documents(INTERIOR_DOCS_PATH)
decor_documents = load_documents(DECOR_DOCS_PATH)


def get_api_configuration():
    return {
        "Groq": bool(groq_client),
        "Cloudflare": bool(
            CLOUDFLARE_ACCOUNT_ID and CLOUDFLARE_API_TOKEN
        ),
        "Interior RAG documents": len(interior_documents),
        "Decor RAG documents": len(decor_documents),
    }


# ==========================================================
# 4. DOCUMENT TEXT CONVERSION
# ==========================================================

def document_to_text(document):
    if isinstance(document, str):
        return document

    if isinstance(document, dict):
        return " | ".join(
            f"{key}: {value}"
            for key, value in document.items()
            if value is not None
        )

    if hasattr(document, "page_content"):
        return str(document.page_content)

    return str(document)


def tokenize(text):
    return re.findall(r"[a-zA-Z0-9]+", str(text).lower())


# ==========================================================
# 5. KEYWORD-BASED DATASET RETRIEVAL
# ==========================================================

def search_faiss(query, index=None, documents=None, top_k=5):
    """
    Compatibility function retaining the old search_faiss name.
    This implementation uses BM25-style keyword retrieval,
    not a real FAISS vector index.
    """

    if documents is None:
        documents = interior_documents

    if not documents or top_k <= 0:
        return []

    query_words = tokenize(query)
    if not query_words:
        return []

    tokenized_docs = [
        tokenize(document_to_text(doc))
        for doc in documents
    ]

    total_docs = len(tokenized_docs)
    if total_docs == 0:
        return []

    doc_frequency = Counter()
    for tokens in tokenized_docs:
        doc_frequency.update(set(tokens))

    average_length = (
        sum(len(tokens) for tokens in tokenized_docs) / total_docs
    ) or 1

    scored = []

    for position, tokens in enumerate(tokenized_docs):
        if not tokens:
            continue

        frequencies = Counter(tokens)
        score = 0.0
        document_length = len(tokens)

        for word in query_words:
            frequency = frequencies.get(word, 0)
            if frequency == 0:
                continue

            df = doc_frequency.get(word, 0)

            idf = math.log(
                1 + (total_docs - df + 0.5) / (df + 0.5)
            )

            denominator = frequency + 1.2 * (
                0.25 + 0.75 * document_length / average_length
            )

            score += idf * (frequency * 2.2) / denominator

        if score > 0:
            scored.append((score, position))

    scored.sort(key=lambda item: item[0], reverse=True)

    return [
        documents[position]
        for _, position in scored[:top_k]
    ]


def retrieve_context(query, top_k=5, max_chars=6500):
    interior_results = search_faiss(
        query,
        documents=interior_documents,
        top_k=top_k,
    )

    decor_results = search_faiss(
        query,
        documents=decor_documents,
        top_k=top_k,
    )

    context_parts = []

    for doc in interior_results:
        context_parts.append(
            "INTERIOR DATA:\n" + document_to_text(doc)
        )

    for doc in decor_results:
        context_parts.append(
            "DECOR DATA:\n" + document_to_text(doc)
        )

    if not context_parts:
        return "No relevant information was found in the loaded datasets."

    return "\n\n".join(context_parts)[:max_chars]


# ==========================================================
# 6. GROQ CHAT HELPER
# ==========================================================

def groq_chat(prompt, system_message=None, max_tokens=1400, temperature=0.4):
    if groq_client is None:
        return (
            "Groq API is not configured. "
            "Please check GROQ_API_KEY in your .env file."
        )

    try:
        response = groq_client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": system_message or (
                        "You are a professional interior design assistant. "
                        "Give practical, clear and realistic recommendations."
                    ),
                },
                {"role": "user", "content": str(prompt)},
            ],
            max_completion_tokens=max_tokens,
            temperature=temperature,
        )

        answer = response.choices[0].message.content
        return answer.strip() if answer else "The AI returned an empty response."

    except Exception as exc:
        return f"Groq API error: {exc}"


# ==========================================================
# 7. GENERATE INTERIOR DESIGN USING GROQ + RAG
# ==========================================================

def generate_design(query, selected_products=None):
    context = retrieve_context(query, top_k=5)

    product_context = ""
    if selected_products:
        product_context = (
            "\nSELECTED PRODUCTS:\n"
            + str(selected_products)[:2000]
        )

    prompt = f"""
Create a practical and attractive interior design recommendation.

USER REQUIREMENTS:
{str(query)[:5000]}

RELEVANT RETRIEVED DATASET RECORDS:
{context}

{product_context}

Include these sections:
1. Design Concept
2. Space Planning and Furniture Placement
3. Recommended Furniture and Decor
4. Colour and Material Palette
5. Lighting Plan
6. Storage and Space-Saving Ideas
7. Budget Guidance
8. Why This Design Fits the Room

Use retrieved dataset information when relevant.
Do not invent exact product prices.
Respect the user's dimensions, style and budget.
If the dataset has no relevant information, say so clearly.
"""

    return groq_chat(
        prompt,
        system_message=(
            "You are an experienced interior designer. "
            "Your recommendations must be realistic, useful and budget-aware."
        ),
        max_tokens=1800,
        temperature=0.5,
    )


# ==========================================================
# 8. GROQ DESIGN REVIEW
# ==========================================================

def review_design(prompt):
    """
    Uses Groq for design review instead of relying on Mistral billing.
    """

    return groq_chat(
        prompt,
        system_message=(
            "You are a professional interior design reviewer. "
            "Check furniture scale, circulation, room dimensions, "
            "colour coordination, functionality and budget suitability. "
            "Give concise, practical improvements."
        ),
        max_tokens=900,
        temperature=0.3,
    )


# ==========================================================
# 9. CLOUDFLARE FLUX IMAGE GENERATION
# ==========================================================

def generate_interior_image(
    room,
    style,
    room_size,
    lighting,
    description,
    budget="Not specified",
    design_answer="",
    color_palette="Not specified",
    furniture_preference="Not specified",
):
    if not CLOUDFLARE_ACCOUNT_ID or not CLOUDFLARE_API_TOKEN:
        return None, (
            "Cloudflare credentials are missing. Check "
            "CLOUDFLARE_ACCOUNT_ID and CLOUDFLARE_API_TOKEN "
            "in your .env file."
        )

    # Keep the design summary short so the final prompt stays within
    # Cloudflare FLUX's 2,048-character prompt limit.
    short_design = re.sub(
        r"\s+", " ", str(design_answer or "")
    ).strip()[:350]

    short_description = re.sub(
        r"\s+", " ", str(description or "")
    ).strip()[:250]

    prompt = (
        "Photorealistic professional interior architecture photograph. "
        f"Room: {room}. "
        f"Interior style: {style}. "
        f"Room dimensions: {room_size}. "
        f"Colour palette: {color_palette}. "
        f"Lighting: {lighting}. "
        f"Furniture: {furniture_preference}. "
        f"Budget level: {budget}. "
        f"User requirements: {short_description}. "
        f"Design concept: {short_design}. "
        "Show a complete, realistic room with correctly scaled furniture, "
        "practical layout, clear walking space, coordinated materials, "
        "natural shadows and balanced lighting. "
        "Wide-angle interior photography, eye-level camera, high detail. "
        "No people, no text, no labels, no watermark, no logo, no collage."
    )

    # Final safety limit. Do not send a prompt over the API limit.
    prompt = prompt[:CLOUDFLARE_PROMPT_LIMIT]

    url = (
        "https://api.cloudflare.com/client/v4/accounts/"
        f"{CLOUDFLARE_ACCOUNT_ID}/ai/run/{CLOUDFLARE_MODEL}"
    )

    headers = {
        "Authorization": f"Bearer {CLOUDFLARE_API_TOKEN}",
        "Content-Type": "application/json",
    }

    try:
        response = requests.post(
            url,
            headers=headers,
            json={"prompt": prompt},
            timeout=180,
        )

        if response.status_code != 200:
            try:
                error_data = response.json()
                error_message = error_data.get("errors", error_data)
            except Exception:
                error_message = response.text[:500]

            return None, (
                f"Cloudflare image generation failed "
                f"({response.status_code}): {error_message}"
            )

        content_type = response.headers.get(
            "content-type", ""
        ).lower()

        # Direct image response.
        if content_type.startswith("image/"):
            image_bytes = response.content
            if image_bytes:
                return image_bytes, None
            return None, "Cloudflare returned an empty image."

        # JSON response containing a base64 image.
        data = response.json()

        if data.get("success") is False:
            return None, (
                "Cloudflare returned an error: "
                + str(data.get("errors", data))
            )

        result = data.get("result") or {}
        image_data = result.get("image")

        if not image_data:
            return None, (
                "Cloudflare responded, but the response did not "
                "contain image data."
            )

        # Some APIs return a data URI; remove its prefix if present.
        if isinstance(image_data, str) and image_data.startswith("data:"):
            image_data = image_data.split(",", 1)[-1]

        image_bytes = base64.b64decode(image_data)

        if not image_bytes:
            return None, "The generated image was empty."

        return image_bytes, None

    except requests.exceptions.Timeout:
        return None, (
            "Cloudflare image generation timed out. "
            "Please try again."
        )

    except requests.exceptions.RequestException as exc:
        return None, f"Cloudflare connection error: {exc}"

    except Exception as exc:
        return None, f"Image generation error: {exc}"


# ==========================================================
# 10. MAIN DESIGN FUNCTION - BACKWARD COMPATIBLE
# ==========================================================

def design_answer(
    room,
    style,
    budget,
    room_size,
    lighting,
    description,
    selected_products=None,
    color_palette="Not specified",
    furniture_preference="Not specified",
):
    query = f"""
Room: {room}
Interior style: {style}
Budget: {budget}
Room size: {room_size}
Lighting: {lighting}
Colour palette: {color_palette}
Furniture preference: {furniture_preference}
Requirements: {description}
"""

    answer = generate_design(
        query,
        selected_products=selected_products,
    )

    image = None
    image_error = None

    if (
        not str(answer).startswith("Groq API is not configured")
        and not str(answer).startswith("Groq API error:")
    ):
        image, image_error = generate_interior_image(
            room=room,
            style=style,
            room_size=room_size,
            lighting=lighting,
            description=description,
            budget=budget,
            design_answer=answer,
            color_palette=color_palette,
            furniture_preference=furniture_preference,
        )

    return {
        "answer": answer,
        "image": image,
        "image_error": image_error,
        "query": query,
    }
