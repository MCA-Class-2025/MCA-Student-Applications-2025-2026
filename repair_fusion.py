import os
import time
import requests
import pandas as pd

from dotenv import load_dotenv
from groq import Groq
from google import genai
from huggingface_hub import InferenceClient


# ==========================================================
# CONFIGURATION
# ==========================================================

load_dotenv()

INPUT_FILE = "fused_dataset/final_api_fused.csv"
OUTPUT_FILE = "fused_dataset/final_api_fused.csv"

# ----------------------------------------------------------
# REPAIR MODE
# ----------------------------------------------------------
# None = repair ALL failed records
# 10 = repair only first 10 failed records for testing
# ----------------------------------------------------------

REPAIR_LIMIT = 10

SAVE_EVERY = 10


# ==========================================================
# API KEYS
# ==========================================================

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
HF_TOKEN = os.getenv("HF_TOKEN")
UNSPLASH_ACCESS_KEY = os.getenv("UNSPLASH_ACCESS_KEY")
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")


# ==========================================================
# LOAD DATASET
# ==========================================================

print("=" * 70)
print("LOADING EXISTING FUSED DATASET")
print("=" * 70)

if not os.path.exists(INPUT_FILE):
    print("ERROR: Final fused dataset not found:")
    print(INPUT_FILE)
    raise SystemExit

df = pd.read_csv(INPUT_FILE)

print(f"Records loaded: {len(df)}")


# ==========================================================
# CLIENTS
# ==========================================================

groq_client = None
gemini_client = None
hf_client = None


if GROQ_API_KEY:
    groq_client = Groq(
        api_key=GROQ_API_KEY
    )


if GEMINI_API_KEY:
    gemini_client = genai.Client(
        api_key=GEMINI_API_KEY
    )


if HF_TOKEN:
    hf_client = InferenceClient(
        token=HF_TOKEN
    )


# ==========================================================
# CREATE DESIGN QUERY
# ==========================================================

def create_design_query(row):

    style = str(
        row.get("style_tags", "")
    )

    material = str(
        row.get("material_type", "")
    )

    color = str(
        row.get("color_palette", "")
    )

    category = str(
        row.get("category", "")
    )

    product = str(
        row.get("product_name", "")
    )

    description = str(
        row.get("design_description", "")
    )

    return f"""
You are an expert interior designer.

Interior design style:
{style}

Material:
{material}

Colour palette:
{color}

Category:
{category}

Product:
{product}

Design description:
{description}

Give one short, practical interior design recommendation
for this product and design style.

Focus on:
- placement
- colour coordination
- materials
- lighting
- decoration

Do not invent product names.
Do not mention prices.
""".strip()


# ==========================================================
# ERROR DETECTION
# ==========================================================

def is_failed(value):

    if pd.isna(value):
        return True

    value = str(value).strip()

    if not value:
        return True

    error_words = [
        "error",
        "missing",
        "failed",
        "quota",
        "unsupported",
        "bad request",
        "not found",
        "429",
        "404",
        "406",
        "provider"
    ]

    return any(
        word in value.lower()
        for word in error_words
    )


# ==========================================================
# GROQ
# ==========================================================

def call_groq(query):

    if not groq_client:
        return "Groq API key missing"

    try:

        response = groq_client.chat.completions.create(

            model="llama-3.3-70b-versatile",

            messages=[
                {
                    "role": "system",
                    "content":
                    "You are an expert interior designer."
                },
                {
                    "role": "user",
                    "content": query
                }
            ],

            temperature=0.3,
            max_tokens=250
        )

        return (
            response.choices[0]
            .message.content
            .strip()
        )

    except Exception as e:

        return f"Groq error: {e}"


# ==========================================================
# GEMINI
# ==========================================================

def call_gemini(query):

    if not gemini_client:
        return "Gemini API key missing"

    try:

        response = gemini_client.models.generate_content(

            model="gemini-3.6-flash",

            contents=(
                "You are an expert interior designer.\n\n"
                + query
            )
        )

        if response.text:
            return response.text.strip()

        return "Gemini empty response"

    except Exception as e:

        return f"Gemini error: {e}"


# ==========================================================
# HUGGING FACE
# ==========================================================

def call_huggingface(query):

    if not hf_client:
        return "Hugging Face API key missing"

    try:

        # Use a text-generation model that can be
        # accessed through the inference client.
        model = "Qwen/Qwen2.5-1.5B-Instruct"

        result = hf_client.text_generation(

            prompt=query,

            model=model,

            max_new_tokens=150,

            temperature=0.3
        )

        return str(result).strip()

    except Exception as e:

        return f"Hugging Face error: {e}"


# ==========================================================
# UNSPLASH
# ==========================================================

def call_unsplash(row):

    if not UNSPLASH_ACCESS_KEY:
        return "Unsplash API key missing"

    try:

        style = str(
            row.get("style_tags", "")
        )

        category = str(
            row.get("category", "")
        )

        product = str(
            row.get("product_name", "")
        )

        search_query = (
            f"{style} {category} "
            f"interior design {product}"
        ).strip()

        url = "https://api.unsplash.com/search/photos"

        params = {
            "query": search_query,
            "per_page": 1,
            "client_id": UNSPLASH_ACCESS_KEY
        }

        response = requests.get(
            url,
            params=params,
            timeout=30
        )

        response.raise_for_status()

        data = response.json()

        results = data.get(
            "results",
            []
        )

        if not results:
            return ""

        return (
            results[0]
            .get("urls", {})
            .get("regular", "")
        )

    except Exception as e:

        return f"Unsplash error: {e}"


# ==========================================================
# MISTRAL
# ==========================================================

def call_mistral(query):

    if not MISTRAL_API_KEY:
        return "Mistral API key missing"

    try:

        url = (
            "https://api.mistral.ai/v1/chat/completions"
        )

        headers = {
            "Authorization":
            f"Bearer {MISTRAL_API_KEY}",

            "Content-Type":
            "application/json"
        }

        payload = {

            "model":
            "mistral-small-latest",

            "messages": [

                {
                    "role":
                    "system",

                    "content":
                    "You are an expert interior designer."
                },

                {
                    "role":
                    "user",

                    "content":
                    query
                }
            ],

            "temperature":
            0.3,

            "max_tokens":
            250
        }

        response = requests.post(

            url,

            headers=headers,

            json=payload,

            timeout=60
        )

        response.raise_for_status()

        data = response.json()

        return (
            data["choices"][0]
            ["message"]
            ["content"]
            .strip()
        )

    except Exception as e:

        return f"Mistral error: {e}"


# ==========================================================
# FIND FAILED RECORDS
# ==========================================================

api_columns = {

    "gemini_design_advice": "Gemini",

    "huggingface_design_advice": "Hugging Face",

    "unsplash_image_url": "Unsplash",

    "mistral_design_advice": "Mistral"
}


print("\n" + "=" * 70)
print("CHECKING FAILED API RESULTS")
print("=" * 70)


for column, name in api_columns.items():

    failed_count = df[column].apply(
        is_failed
    ).sum()

    print(
        f"{name}: {failed_count} failed"
    )


# ==========================================================
# BUILD REPAIR LIST
# ==========================================================

failed_indices = set()

for column in api_columns:

    failed_rows = df[
        df[column].apply(is_failed)
    ].index

    failed_indices.update(
        failed_rows.tolist()
    )


failed_indices = sorted(
    failed_indices
)


print(
    f"\nTotal records requiring repair: "
    f"{len(failed_indices)}"
)


# ==========================================================
# APPLY REPAIR LIMIT
# ==========================================================

if REPAIR_LIMIT is not None:

    failed_indices = failed_indices[
        :REPAIR_LIMIT
    ]

    print(
        f"TEST REPAIR MODE: "
        f"{len(failed_indices)} records"
    )

else:

    print(
        "FULL REPAIR MODE"
    )


# ==========================================================
# REPAIR
# ==========================================================

print("\n" + "=" * 70)
print("STARTING API REPAIR")
print("=" * 70)


for count, index in enumerate(
    failed_indices,
    start=1
):

    row = df.loc[index]

    print(
        f"\nRepairing "
        f"{count} / {len(failed_indices)}"
    )

    query = create_design_query(
        row
    )


    # ------------------------------------------------------
    # GEMINI
    # ------------------------------------------------------

    if is_failed(
        df.at[
            index,
            "gemini_design_advice"
        ]
    ):

        print("  → Gemini")

        result = call_gemini(
            query
        )

        df.at[
            index,
            "gemini_design_advice"
        ] = result

        time.sleep(2)


    # ------------------------------------------------------
    # HUGGING FACE
    # ------------------------------------------------------

    if is_failed(
        df.at[
            index,
            "huggingface_design_advice"
        ]
    ):

        print("  → Hugging Face")

        result = call_huggingface(
            query
        )

        df.at[
            index,
            "huggingface_design_advice"
        ] = result

        time.sleep(1)


    # ------------------------------------------------------
    # UNSPLASH
    # ------------------------------------------------------

    if is_failed(
        df.at[
            index,
            "unsplash_image_url"
        ]
    ):

        print("  → Unsplash")

        result = call_unsplash(
            row
        )

        df.at[
            index,
            "unsplash_image_url"
        ] = result

        time.sleep(1)


    # ------------------------------------------------------
    # MISTRAL
    # ------------------------------------------------------

    if is_failed(
        df.at[
            index,
            "mistral_design_advice"
        ]
    ):

        print("  → Mistral")

        result = call_mistral(
            query
        )

        df.at[
            index,
            "mistral_design_advice"
        ] = result

        time.sleep(1)


    # ------------------------------------------------------
    # UPDATE STATUS
    # ------------------------------------------------------

    errors = []

    checks = {

        "Gemini":
        df.at[
            index,
            "gemini_design_advice"
        ],

        "HuggingFace":
        df.at[
            index,
            "huggingface_design_advice"
        ],

        "Unsplash":
        df.at[
            index,
            "unsplash_image_url"
        ],

        "Mistral":
        df.at[
            index,
            "mistral_design_advice"
        ]
    }


    for name, value in checks.items():

        if is_failed(value):

            errors.append(
                name
            )


    if errors:

        df.at[
            index,
            "api_fusion_status"
        ] = (
            "partial: "
            +
            ", ".join(errors)
        )

    else:

        df.at[
            index,
            "api_fusion_status"
        ] = "completed"


    # ------------------------------------------------------
    # SAVE PROGRESS
    # ------------------------------------------------------

    if count % SAVE_EVERY == 0:

        df.to_csv(
            OUTPUT_FILE,
            index=False
        )

        print(
            f"  ✓ Progress saved "
            f"({count}/{len(failed_indices)})"
        )


# ==========================================================
# FINAL SAVE
# ==========================================================

df.to_csv(
    OUTPUT_FILE,
    index=False
)


# ==========================================================
# FINAL REPORT
# ==========================================================

print("\n" + "=" * 70)
print("REPAIR COMPLETED")
print("=" * 70)

print(
    f"Total dataset records: {len(df)}"
)

print("\nFinal status:")

print(
    df[
        "api_fusion_status"
    ].value_counts()
)


print("\nAPI error counts:")

for column, name in api_columns.items():

    failed_count = df[column].apply(
        is_failed
    ).sum()

    print(
        f"{name}: {failed_count}"
    )


print("\nSaved:")

print(
    OUTPUT_FILE
)

print("\n" + "=" * 70)
print("DONE")
print("=" * 70)