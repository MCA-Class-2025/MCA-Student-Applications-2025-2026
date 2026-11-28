import os
import time
import requests
import pandas as pd

from dotenv import load_dotenv
from groq import Groq
from google import genai
from huggingface_hub import InferenceClient
from mistralai.client import Mistral


# ==========================================================
# CONFIGURATION
# ==========================================================

load_dotenv()

INPUT_FILE = "fused_dataset/fused_interior_decor.csv"
OUTPUT_FILE = "fused_dataset/final_api_fused.csv"

# ==========================================================
# TEST MODE
# ==========================================================
# First test with 10 records.
#
# After ALL APIs work:
# TEST_LIMIT = None
# ==========================================================

TEST_LIMIT = 10


# ==========================================================
# API KEYS
# ==========================================================

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
HF_TOKEN = os.getenv("HF_TOKEN")
UNSPLASH_ACCESS_KEY = os.getenv("UNSPLASH_ACCESS_KEY")
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")


# ==========================================================
# CHECK API KEYS
# ==========================================================

print("=" * 70)
print("CHECKING API KEYS")
print("=" * 70)

keys = {
    "Groq": GROQ_API_KEY,
    "Gemini": GEMINI_API_KEY,
    "Hugging Face": HF_TOKEN,
    "Unsplash": UNSPLASH_ACCESS_KEY,
    "Mistral": MISTRAL_API_KEY
}

for name, key in keys.items():

    if key:
        print(f"✓ {name} API key found")
    else:
        print(f"✗ {name} API key NOT found")


# ==========================================================
# INITIALIZE CLIENTS
# ==========================================================

groq_client = None
gemini_client = None
hf_client = None
mistral_client = None


# ==========================================================
# GROQ CLIENT
# ==========================================================

if GROQ_API_KEY:

    groq_client = Groq(
        api_key=GROQ_API_KEY
    )


# ==========================================================
# GEMINI CLIENT
# ==========================================================

if GEMINI_API_KEY:

    gemini_client = genai.Client(
        api_key=GEMINI_API_KEY
    )


# ==========================================================
# HUGGING FACE CLIENT
# ==========================================================

if HF_TOKEN:

    hf_client = InferenceClient(
        token=HF_TOKEN
    )


# ==========================================================
# MISTRAL CLIENT
# ==========================================================

if MISTRAL_API_KEY:

    mistral_client = Mistral(
        api_key=MISTRAL_API_KEY
    )


# ==========================================================
# LOAD DATASET
# ==========================================================

print("\n" + "=" * 70)
print("LOADING EXISTING FUSED DATASET")
print("=" * 70)

try:

    df = pd.read_csv(
        INPUT_FILE
    )

except FileNotFoundError:

    print("\nERROR: Dataset not found.")
    print(
        f"Expected file: {INPUT_FILE}"
    )

    print("\nRun this from:")
    print(
        r"C:\Users\subbu\OneDrive\Desktop\chatbot"
    )

    raise SystemExit


print(
    f"Loaded records: {len(df)}"
)


# ==========================================================
# TEST LIMIT
# ==========================================================

if TEST_LIMIT is not None:

    df = df.head(
        TEST_LIMIT
    ).copy()

    print(
        f"TEST MODE: processing {len(df)} records"
    )

else:

    print(
        f"FULL MODE: processing {len(df)} records"
    )


# ==========================================================
# CREATE API COLUMNS
# ==========================================================

new_columns = [

    "groq_design_advice",

    "gemini_design_advice",

    "huggingface_design_advice",

    "unsplash_image_url",

    "mistral_design_advice",

    "api_fusion_status"
]


for column in new_columns:

    if column not in df.columns:

        df[column] = ""


# ==========================================================
# CREATE DESIGN QUERY
# ==========================================================

def create_design_query(row):

    style = str(
        row.get(
            "style_tags",
            ""
        )
    )

    material = str(
        row.get(
            "material_type",
            ""
        )
    )

    color = str(
        row.get(
            "color_palette",
            ""
        )
    )

    category = str(
        row.get(
            "category",
            ""
        )
    )

    product = str(
        row.get(
            "product_name",
            ""
        )
    )

    description = str(
        row.get(
            "design_description",
            ""
        )
    )

    query = f"""
You are an expert AI interior designer.

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

Give a short, practical interior design recommendation
for this product and design style.

Do not invent product names.
Do not mention prices unless they are provided.

Focus on:
- room styling
- product placement
- colour coordination
- materials
- lighting
- decoration

Keep the answer concise.
"""

    return query.strip()


# ==========================================================
# API 1 — GROQ
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
            response
            .choices[0]
            .message
            .content
            .strip()
        )

    except Exception as e:

        return (
            f"Groq error: {str(e)}"
        )


# ==========================================================
# API 2 — GEMINI
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

        return (
            "Gemini returned an empty response"
        )

    except Exception as e:

        return (
            f"Gemini error: {str(e)}"
        )


# ==========================================================
# API 3 — HUGGING FACE
# ==========================================================

def call_huggingface(query):

    if not hf_client:

        return "Hugging Face API key missing"

    try:

        result = hf_client.text_generation(

            prompt=query,

            model="google/flan-t5-base",

            max_new_tokens=150,

            temperature=0.3
        )

        return str(
            result
        ).strip()

    except Exception as e:

        print(
            "HUGGING FACE ERROR:"
        )

        print(
            repr(e)
        )

        return (
            f"Hugging Face error: {str(e)}"
        )


# ==========================================================
# API 4 — UNSPLASH
# ==========================================================

def call_unsplash(row):

    if not UNSPLASH_ACCESS_KEY:

        return "Unsplash API key missing"

    try:

        style = str(
            row.get(
                "style_tags",
                ""
            )
        )

        category = str(
            row.get(
                "category",
                ""
            )
        )

        color = str(
            row.get(
                "color_palette",
                ""
            )
        )

        search_query = (
            f"{style} {category} "
            f"interior {color}"
        ).strip()

        url = (
            "https://api.unsplash.com/search/photos"
        )

        params = {

            "query": search_query,

            "per_page": 1,

            "client_id":
            UNSPLASH_ACCESS_KEY
        }

        response = requests.get(

            url,

            params=params,

            timeout=20
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

        return (
            f"Unsplash error: {str(e)}"
        )


# ==========================================================
# API 5 — MISTRAL
# ==========================================================

def call_mistral(query):

    if not mistral_client:

        return "Mistral API key missing"

    try:

        response = mistral_client.chat.complete(

            model="mistral-large-latest",

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
            response
            .choices[0]
            .message
            .content
            .strip()
        )

    except Exception as e:

        return (
            f"Mistral error: {str(e)}"
        )


# ==========================================================
# TEST ALL APIs
# ==========================================================

print("\n" + "=" * 70)
print("TESTING APIs")
print("=" * 70)


test_query = """
Create a short recommendation for a modern minimalist
living room using neutral colours, comfortable furniture,
good lighting and decorative wall items.
"""


# ==========================================================
# GROQ TEST
# ==========================================================

print("\nTesting Groq...")

groq_test = call_groq(
    test_query
)

print(
    "Groq:",
    groq_test[:200]
)


# ==========================================================
# GEMINI TEST
# ==========================================================

print("\nTesting Gemini...")

gemini_test = call_gemini(
    test_query
)

print(
    "Gemini:",
    gemini_test[:200]
)


# ==========================================================
# HUGGING FACE TEST
# ==========================================================

print("\nTesting Hugging Face...")

hf_test = call_huggingface(
    test_query
)

print(
    "Hugging Face:",
    hf_test[:200]
)


# ==========================================================
# UNSPLASH TEST
# ==========================================================

print("\nTesting Unsplash...")

if len(df) > 0:

    unsplash_test = call_unsplash(
        df.iloc[0]
    )

else:

    unsplash_test = (
        "No dataset record available"
    )

print(
    "Unsplash:",
    unsplash_test[:200]
)


# ==========================================================
# MISTRAL TEST
# ==========================================================

print("\nTesting Mistral...")

mistral_test = call_mistral(
    test_query
)

print(
    "Mistral:",
    mistral_test[:200]
)


# ==========================================================
# API TEST SUMMARY
# ==========================================================

print("\n" + "=" * 70)
print("API TEST SUMMARY")
print("=" * 70)

test_results = {

    "Groq":
        groq_test,

    "Gemini":
        gemini_test,

    "Hugging Face":
        hf_test,

    "Unsplash":
        unsplash_test,

    "Mistral":
        mistral_test
}


for name, result in test_results.items():

    result_lower = str(
        result
    ).lower()

    if (
        "error" in result_lower
        or
        "missing" in result_lower
    ):

        print(
            f"✗ {name}: FAILED"
        )

    else:

        print(
            f"✓ {name}: OK"
        )


# ==========================================================
# START DATA FUSION
# ==========================================================

print("\n" + "=" * 70)
print("STARTING API DATA FUSION")
print("=" * 70)


total = len(df)


for i, (index, row) in enumerate(

    df.iterrows(),

    start=1

):

    print(
        f"\nProcessing {i} / {total}"
    )


    # ======================================================
    # CREATE QUERY
    # ======================================================

    query = create_design_query(
        row
    )


    # ======================================================
    # GROQ
    # ======================================================

    print(
        "  → Groq"
    )

    groq_result = call_groq(
        query
    )

    df.at[
        index,
        "groq_design_advice"
    ] = groq_result

    time.sleep(0.5)


    # ======================================================
    # GEMINI
    # ======================================================

    print(
        "  → Gemini"
    )

    gemini_result = call_gemini(
        query
    )

    df.at[
        index,
        "gemini_design_advice"
    ] = gemini_result

    time.sleep(0.5)


    # ======================================================
    # HUGGING FACE
    # ======================================================

    print(
        "  → Hugging Face"
    )

    hf_result = call_huggingface(
        query
    )

    df.at[
        index,
        "huggingface_design_advice"
    ] = hf_result

    time.sleep(0.5)


    # ======================================================
    # UNSPLASH
    # ======================================================

    print(
        "  → Unsplash"
    )

    unsplash_result = call_unsplash(
        row
    )

    df.at[
        index,
        "unsplash_image_url"
    ] = unsplash_result


    # ======================================================
    # MISTRAL
    # ======================================================

    print(
        "  → Mistral"
    )

    mistral_result = call_mistral(
        query
    )

    df.at[
        index,
        "mistral_design_advice"
    ] = mistral_result

    time.sleep(0.5)


    # ======================================================
    # STATUS
    # ======================================================

    errors = []


    if (
        "error" in
        groq_result.lower()
        or
        "missing" in
        groq_result.lower()
    ):

        errors.append(
            "Groq"
        )


    if (
        "error" in
        gemini_result.lower()
        or
        "missing" in
        gemini_result.lower()
    ):

        errors.append(
            "Gemini"
        )


    if (
        "error" in
        hf_result.lower()
        or
        "missing" in
        hf_result.lower()
    ):

        errors.append(
            "HuggingFace"
        )


    if (
        "error" in
        unsplash_result.lower()
        or
        "missing" in
        unsplash_result.lower()
    ):

        errors.append(
            "Unsplash"
        )


    if (
        "error" in
        mistral_result.lower()
        or
        "missing" in
        mistral_result.lower()
    ):

        errors.append(
            "Mistral"
        )


    if errors:

        status = (
            "partial: "
            +
            ", ".join(errors)
        )

    else:

        status = "completed"


    df.at[
        index,
        "api_fusion_status"
    ] = status


    # ======================================================
    # SAVE PROGRESS
    # ======================================================

    if i % 5 == 0:

        df.to_csv(

            OUTPUT_FILE,

            index=False
        )

        print(
            f"  ✓ Progress saved "
            f"({i}/{total})"
        )


# ==========================================================
# FINAL SAVE
# ==========================================================

df.to_csv(

    OUTPUT_FILE,

    index=False
)


# ==========================================================
# SUMMARY
# ==========================================================

print("\n")

print(
    "=" * 70
)

print(
    "API DATA FUSION COMPLETED"
)

print(
    "=" * 70
)

print(
    f"Final records: {len(df)}"
)

print(
    f"Final columns: {len(df.columns)}"
)


print("\nAdded API columns:")

for column in new_columns:

    print(
        f"- {column}"
    )


print("\nSaved file:")

print(
    OUTPUT_FILE
)


# ==========================================================
# SHOW FIRST 3 RECORDS
# ==========================================================

print("\n")

print(
    "=" * 70
)

print(
    "FIRST 3 FUSED RECORDS"
)

print(
    "=" * 70
)


display_columns = [

    "product_name",

    "style_tags",

    "groq_design_advice",

    "gemini_design_advice",

    "huggingface_design_advice",

    "unsplash_image_url",

    "mistral_design_advice",

    "api_fusion_status"
]


available_columns = [

    column

    for column in display_columns

    if column in df.columns

]


print(

    df[
        available_columns
    ]
    .head(3)
    .to_string()

)


print("\n")

print(
    "=" * 70
)

print(
    "ALL API FUSION COMPLETED"
)

print(
    "=" * 70
)