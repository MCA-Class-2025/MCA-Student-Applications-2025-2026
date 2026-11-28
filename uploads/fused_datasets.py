import os
import time
import requests
import pandas as pd

from dotenv import load_dotenv
from groq import Groq
from mistralai.client import Mistral
from huggingface_hub import InferenceClient


# ==========================================================
# CONFIGURATION
# ==========================================================

load_dotenv()

INPUT_FILE = "dataset/interior_design_dataset.csv"

OUTPUT_DIR = "fused_dataset"

OUTPUT_FILE = os.path.join(
    OUTPUT_DIR,
    "final_api_fused.csv"
)

# Change to None when you want all 1000 records
TEST_LIMIT = 10

os.makedirs(OUTPUT_DIR, exist_ok=True)


# ==========================================================
# API KEYS
# ==========================================================

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
HF_TOKEN = os.getenv("HF_TOKEN")
UNSPLASH_ACCESS_KEY = os.getenv("UNSPLASH_ACCESS_KEY")
PIXABAY_API_KEY = os.getenv("PIXABAY_API_KEY")


# ==========================================================
# CHECK API KEYS
# ==========================================================

print("=" * 70)
print("CHECKING API KEYS")
print("=" * 70)

keys = {
    "Groq": GROQ_API_KEY,
    "Mistral": MISTRAL_API_KEY,
    "Hugging Face": HF_TOKEN,
    "Unsplash": UNSPLASH_ACCESS_KEY,
    "Pixabay": PIXABAY_API_KEY
}

for name, key in keys.items():

    if key:
        print(f"✓ {name} API key found")
    else:
        print(f"✗ {name} API key missing")


# ==========================================================
# CLIENTS
# ==========================================================

print()
print("=" * 70)
print("INITIALIZING API CLIENTS")
print("=" * 70)


groq_client = None
mistral_client = None
hf_client = None


if GROQ_API_KEY:
    try:
        groq_client = Groq(
            api_key=GROQ_API_KEY
        )
        print("✓ Groq client initialized")
    except Exception as e:
        print(f"✗ Groq initialization failed: {e}")


if MISTRAL_API_KEY:
    try:
        mistral_client = Mistral(
            api_key=MISTRAL_API_KEY
        )
        print("✓ Mistral client initialized")
    except Exception as e:
        print(f"✗ Mistral initialization failed: {e}")


if HF_TOKEN:
    try:
        hf_client = InferenceClient(
            token=HF_TOKEN
        )
        print("✓ Hugging Face client initialized")
    except Exception as e:
        print(f"✗ Hugging Face initialization failed: {e}")


# ==========================================================
# GROQ MODEL
# ==========================================================

GROQ_MODEL = None


def initialize_groq():

    global GROQ_MODEL

    if not groq_client:
        return

    try:

        models = groq_client.models.list()

        available_models = [
            model.id
            for model in models.data
        ]

        preferred_models = [
            "openai/gpt-oss-120b",
            "openai/gpt-oss-20b",
            "llama-3.3-70b-versatile",
            "llama-3.1-8b-instant"
        ]

        for model in preferred_models:

            if model in available_models:

                GROQ_MODEL = model

                print(
                    f"✓ Groq model selected: {GROQ_MODEL}"
                )

                return

        print("✗ No supported Groq model found")

    except Exception as e:

        print(
            f"✗ Groq model detection failed: {e}"
        )


initialize_groq()


# ==========================================================
# HUGGING FACE MODEL
# ==========================================================

HF_MODEL = "HuggingFaceH4/zephyr-7b-beta"


# ==========================================================
# HELPER
# ==========================================================

def get_value(row, columns):

    for column in columns:

        if column in row.index:

            value = row[column]

            if pd.notna(value):

                text = str(value).strip()

                if text:
                    return text

    return "Not specified"


# ==========================================================
# CREATE PROMPT
# ==========================================================

def create_prompt(row):

    product = get_value(
        row,
        [
            "product_name",
            "Product Name",
            "product"
        ]
    )

    style = get_value(
        row,
        [
            "style_tags",
            "style",
            "Style"
        ]
    )

    material = get_value(
        row,
        [
            "material_type",
            "material",
            "Material"
        ]
    )

    color = get_value(
        row,
        [
            "color_palette",
            "color",
            "colour"
        ]
    )

    description = get_value(
        row,
        [
            "design_description",
            "description"
        ]
    )

    return f"""
You are an expert interior designer.

Product:
{product}

Style:
{style}

Material:
{material}

Colour palette:
{color}

Description:
{description}

Give practical interior design advice.

Include:

1. Room styling
2. Product placement
3. Colour coordination
4. Suitable furniture or decor
5. Short practical recommendation

Keep the answer concise and useful.
"""


# ==========================================================
# GROQ
# ==========================================================

def call_groq(prompt):

    if not groq_client:
        return "Groq unavailable"

    if not GROQ_MODEL:
        return "Groq model unavailable"

    try:

        response = groq_client.chat.completions.create(

            model=GROQ_MODEL,

            messages=[
                {
                    "role": "system",
                    "content":
                    "You are an expert interior designer."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],

            max_tokens=400,

            temperature=0.7
        )

        return response.choices[0].message.content

    except Exception as e:

        return f"Groq error: {str(e)}"


# ==========================================================
# MISTRAL
# ==========================================================

def call_mistral(prompt):

    if not mistral_client:

        return "Mistral unavailable"

    try:

        response = mistral_client.chat.complete(

            model="mistral-small-latest",

            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],

            max_tokens=400
        )

        return response.choices[0].message.content

    except Exception as e:

        return f"Mistral error: {str(e)}"


# ==========================================================
# HUGGING FACE
# ==========================================================

def call_huggingface(prompt):

    if not hf_client:

        return "Hugging Face unavailable"

    try:

        response = hf_client.text_generation(

            prompt,

            model=HF_MODEL,

            max_new_tokens=300,

            temperature=0.7
        )

        if response:

            return str(response)

        return "Hugging Face empty response"

    except Exception as e:

        return f"Hugging Face error: {str(e)}"


# ==========================================================
# UNSPLASH
# ==========================================================

def call_unsplash(row):

    if not UNSPLASH_ACCESS_KEY:

        return "Unsplash unavailable"

    product = get_value(
        row,
        [
            "product_name",
            "Product Name",
            "product"
        ]
    )

    style = get_value(
        row,
        [
            "style_tags",
            "style",
            "Style"
        ]
    )

    query = f"{style} interior design {product}"

    try:

        response = requests.get(

            "https://api.unsplash.com/search/photos",

            params={
                "query": query,
                "per_page": 3,
                "client_id": UNSPLASH_ACCESS_KEY
            },

            timeout=30
        )

        response.raise_for_status()

        data = response.json()

        results = data.get(
            "results",
            []
        )

        urls = []

        for photo in results:

            url = photo.get(
                "urls",
                {}
            ).get(
                "regular"
            )

            if url:
                urls.append(url)

        if not urls:

            return "No Unsplash images found"

        return " | ".join(urls)

    except Exception as e:

        return f"Unsplash error: {str(e)}"


# ==========================================================
# PIXABAY
# ==========================================================

def call_pixabay(row):

    if not PIXABAY_API_KEY:

        return "Pixabay unavailable"

    product = get_value(
        row,
        [
            "product_name",
            "Product Name",
            "product"
        ]
    )

    style = get_value(
        row,
        [
            "style_tags",
            "style",
            "Style"
        ]
    )

    # Keep Pixabay query short.
    # Long queries can cause 400 errors.

    query = f"{style} interior design"

    try:

        response = requests.get(

            "https://pixabay.com/api/",

            params={
                "key": PIXABAY_API_KEY,
                "q": query,
                "image_type": "photo",
                "orientation": "horizontal",
                "safesearch": "true",
                "per_page": 3
            },

            timeout=30
        )

        response.raise_for_status()

        data = response.json()

        results = data.get(
            "hits",
            []
        )

        urls = []

        for image in results:

            url = image.get(
                "webformatURL"
            )

            if url:
                urls.append(url)

        if not urls:

            return "No Pixabay images found"

        return " | ".join(urls)

    except Exception as e:

        return f"Pixabay error: {str(e)}"


# ==========================================================
# LOAD DATASET
# ==========================================================

print()
print("=" * 70)
print("LOADING DATASET")
print("=" * 70)

if not os.path.exists(INPUT_FILE):

    print(
        f"ERROR: Dataset not found:\n{INPUT_FILE}"
    )

    raise SystemExit


df = pd.read_csv(INPUT_FILE)

print(
    f"Original records: {len(df)}"
)

print(
    f"Original columns: {len(df.columns)}"
)


if TEST_LIMIT:

    df = df.head(TEST_LIMIT)

    print(
        f"TEST MODE: {len(df)} records"
    )


# ==========================================================
# DATA FUSION
# ==========================================================

print()
print("=" * 70)
print("STARTING 5-API DATA FUSION")
print("=" * 70)

results = []

total = len(df)


for position, (_, row) in enumerate(
    df.iterrows(),
    start=1
):

    print()
    print(
        f"Processing {position} / {total}"
    )

    prompt = create_prompt(row)


    # ------------------------------------------------------
    # GROQ
    # ------------------------------------------------------

    print("  → Groq")

    groq_result = call_groq(
        prompt
    )


    # ------------------------------------------------------
    # MISTRAL
    # ------------------------------------------------------

    print("  → Mistral")

    mistral_result = call_mistral(
        prompt
    )


    # ------------------------------------------------------
    # HUGGING FACE
    # ------------------------------------------------------

    print("  → Hugging Face")

    huggingface_result = call_huggingface(
        prompt
    )


    # ------------------------------------------------------
    # UNSPLASH
    # ------------------------------------------------------

    print("  → Unsplash")

    unsplash_result = call_unsplash(
        row
    )


    # ------------------------------------------------------
    # PIXABAY
    # ------------------------------------------------------

    print("  → Pixabay")

    pixabay_result = call_pixabay(
        row
    )


    results.append({

        "groq_design_advice":
            groq_result,

        "mistral_design_advice":
            mistral_result,

        "huggingface_design_advice":
            huggingface_result,

        "unsplash_image_url":
            unsplash_result,

        "pixabay_image_urls":
            pixabay_result

    })


    # Small delay to avoid hitting APIs too quickly

    time.sleep(1)


# ==========================================================
# CREATE API DATAFRAME
# ==========================================================

api_df = pd.DataFrame(
    results
)


# ==========================================================
# FUSE ORIGINAL + API DATA
# ==========================================================

fused_df = pd.concat(

    [
        df.reset_index(drop=True),
        api_df.reset_index(drop=True)
    ],

    axis=1
)


# ==========================================================
# STATUS
# ==========================================================

def get_status(row):

    failed = []

    checks = [

        (
            "groq_design_advice",
            "Groq"
        ),

        (
            "mistral_design_advice",
            "Mistral"
        ),

        (
            "huggingface_design_advice",
            "Hugging Face"
        ),

        (
            "unsplash_image_url",
            "Unsplash"
        ),

        (
            "pixabay_image_urls",
            "Pixabay"
        )

    ]

    for column, name in checks:

        value = str(
            row[column]
        ).lower()

        failure_words = [
            "error",
            "unavailable",
            "failed",
            "empty response",
            "not found"
        ]

        if any(
            word in value
            for word in failure_words
        ):

            failed.append(name)


    if failed:

        return (
            "partial: "
            + ", ".join(failed)
        )

    return "complete"


fused_df[
    "api_fusion_status"
] = fused_df.apply(
    get_status,
    axis=1
)


# ==========================================================
# SAVE
# ==========================================================

fused_df.to_csv(
    OUTPUT_FILE,
    index=False
)


# ==========================================================
# SUMMARY
# ==========================================================

print()
print("=" * 70)
print("API DATA FUSION COMPLETED")
print("=" * 70)

print(
    f"Final records: {len(fused_df)}"
)

print(
    f"Final columns: {len(fused_df.columns)}"
)

print()

print("Added API columns:")

print(
    "  - groq_design_advice"
)

print(
    "  - mistral_design_advice"
)

print(
    "  - huggingface_design_advice"
)

print(
    "  - unsplash_image_url"
)

print(
    "  - pixabay_image_urls"
)

print(
    "  - api_fusion_status"
)

print()

print(
    f"Saved file:\n{OUTPUT_FILE}"
)

print("=" * 70)


# ==========================================================
# API SUCCESS SUMMARY
# ==========================================================

print()
print("=" * 70)
print("API RESULT SUMMARY")
print("=" * 70)


api_columns = {

    "Groq":
        "groq_design_advice",

    "Mistral":
        "mistral_design_advice",

    "Hugging Face":
        "huggingface_design_advice",

    "Unsplash":
        "unsplash_image_url",

    "Pixabay":
        "pixabay_image_urls"

}


for name, column in api_columns.items():

    successful = 0

    for value in fused_df[column]:

        text = str(value).lower()

        if not any(
            word in text
            for word in [
                "error",
                "unavailable",
                "failed"
            ]
        ):

            successful += 1

    print(
        f"{name}: {successful}/{len(fused_df)} successful"
    )


print()
print("✓ ALL 5 API PROCESSING FINISHED")
print("=" * 70)