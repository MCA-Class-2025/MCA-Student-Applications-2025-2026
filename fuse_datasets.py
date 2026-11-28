
import os
import time
from pathlib import Path

import pandas as pd
import requests

from dotenv import load_dotenv
from groq import Groq
from mistralai import Mistral
from huggingface_hub import InferenceClient


# ==========================================================
# 1. PROJECT PATHS
# ==========================================================

BASE_DIR = Path(__file__).resolve().parent

load_dotenv(BASE_DIR / ".env", override=True)

INPUT_FILE = BASE_DIR / "dataset" / "interior_design_dataset.csv"

OUTPUT_DIR = BASE_DIR / "fused_dataset"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_FILE = OUTPUT_DIR / "final_api_fused.csv"
CHECKPOINT_FILE = OUTPUT_DIR / "final_api_fused_progress.csv"
TEMP_FILE = OUTPUT_DIR / "final_api_fused_progress.tmp"

# None = process all records
# Example: 10 = process only first 10 records
TEST_LIMIT = None

DELAY = 1


# ==========================================================
# 2. API KEYS
# ==========================================================

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
HF_TOKEN = os.getenv("HF_TOKEN")
UNSPLASH_ACCESS_KEY = os.getenv("UNSPLASH_ACCESS_KEY")
PIXABAY_API_KEY = os.getenv("PIXABAY_API_KEY")


# ==========================================================
# 3. INITIALIZE API CLIENTS
# ==========================================================

groq_client = None
mistral_client = None
hf_client = None

print("\nCHECKING API CONFIGURATION")
print("=" * 60)

if GROQ_API_KEY:
    try:
        groq_client = Groq(api_key=GROQ_API_KEY)
        print("Groq: Connected")
    except Exception as e:
        print(f"Groq initialization error: {e}")
else:
    print("Groq: API key missing")

if MISTRAL_API_KEY:
    try:
        mistral_client = Mistral(api_key=MISTRAL_API_KEY)
        print("Mistral: Connected")
    except Exception as e:
        print(f"Mistral initialization error: {e}")
else:
    print("Mistral: API key missing")

if HF_TOKEN:
    try:
        hf_client = InferenceClient(
            token=HF_TOKEN,
            provider="auto"
        )
        print("Hugging Face: Connected")
    except Exception as e:
        print(f"Hugging Face initialization error: {e}")
else:
    print("Hugging Face: API token missing")

print("Unsplash:", "Configured" if UNSPLASH_ACCESS_KEY else "API key missing")
print("Pixabay:", "Configured" if PIXABAY_API_KEY else "API key missing")


# ==========================================================
# 4. GROQ MODEL DETECTION
# ==========================================================

GROQ_MODEL = None

def initialize_groq():

    global GROQ_MODEL

    if groq_client is None:
        return

    preferred_models = [
        "openai/gpt-oss-120b",
        "openai/gpt-oss-20b"
    ]

    try:
        models = groq_client.models.list()

        available_models = [
            model.id for model in models.data
        ]

        for model in preferred_models:
            if model in available_models:
                GROQ_MODEL = model
                print(f"Selected Groq model: {GROQ_MODEL}")
                return

        print("No preferred Groq model found.")

    except Exception as e:
        print(f"Groq model detection failed: {e}")


initialize_groq()


# ==========================================================
# 5. HELPER FUNCTIONS
# ==========================================================

def get_value(row, columns):

    for column in columns:

        if column in row.index:

            value = row[column]

            if pd.notna(value):

                value = str(value).strip()

                if value:
                    return value

    return "Not specified"


def extract_content(response):

    try:
        return response.choices[0].message.content or ""
    except Exception:
        return str(response)


def api_error(name, message):

    print(f"    {name} error: {message}")

    return f"{name} error: {message}"


# ==========================================================
# 6. CREATE INTERIOR DESIGN PROMPT
# ==========================================================

def create_prompt(row):

    style = get_value(
        row,
        ["style_tags", "style", "Style"]
    )

    material = get_value(
        row,
        ["material_type", "material", "Material"]
    )

    color = get_value(
        row,
        ["color_palette", "color", "colour"]
    )

    description = get_value(
        row,
        ["design_description", "description"]
    )

    preference = get_value(
        row,
        ["user_preference", "preference"]
    )

    return f"""
You are an expert interior designer.

Interior style: {style}
Material: {material}
Colour palette: {color}
Description: {description}
User preference: {preference}

Provide practical interior design advice covering:

1. Room styling
2. Product placement
3. Colour coordination
4. Suitable furniture and decor
5. Final recommendation

Keep the response concise and useful.
"""


# ==========================================================
# 7. GROQ API
# ==========================================================

def call_groq(prompt):

    if groq_client is None:
        return "Groq API key missing or client unavailable"

    if not GROQ_MODEL:
        return "Groq unavailable: no supported model detected"

    try:

        response = groq_client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert interior designer."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            max_tokens=400
        )

        return extract_content(response)

    except Exception as e:
        return api_error("Groq", e)


# ==========================================================
# 8. MISTRAL API
# ==========================================================

def call_mistral(prompt):

    if mistral_client is None:
        return "Mistral API key missing or client unavailable"

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

        return extract_content(response)

    except Exception as e:
        return api_error("Mistral", e)


# ==========================================================
# 9. HUGGING FACE API
# ==========================================================

def call_huggingface(prompt):

    if hf_client is None:
        return "Hugging Face token missing or client unavailable"

    try:

        response = hf_client.chat.completions.create(
            model="meta-llama/Llama-3.1-8B-Instruct",
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert interior designer."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            max_tokens=400
        )

        return extract_content(response)

    except Exception as e:
        return api_error("Hugging Face", e)


# ==========================================================
# 10. UNSPLASH API
# ==========================================================

def call_unsplash(row):

    if not UNSPLASH_ACCESS_KEY:
        return "Unsplash API key missing"

    style = get_value(
        row,
        ["style_tags", "style", "Style"]
    )

    query = f"{style} interior design"

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

        results = response.json().get("results", [])

        urls = [
            photo["urls"]["regular"]
            for photo in results
            if photo.get("urls", {}).get("regular")
        ]

        return " | ".join(urls) if urls else "No Unsplash images found"

    except Exception as e:
        return api_error("Unsplash", e)


# ==========================================================
# 11. PIXABAY API
# ==========================================================

def call_pixabay(row):

    if not PIXABAY_API_KEY:
        return "Pixabay API key missing"

    style = get_value(
        row,
        ["style_tags", "style", "Style"]
    )

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

        results = response.json().get("hits", [])

        urls = [
            image["webformatURL"]
            for image in results
            if image.get("webformatURL")
        ]

        return " | ".join(urls) if urls else "No Pixabay images found"

    except Exception as e:
        return api_error("Pixabay", e)


# ==========================================================
# 12. API FUSION STATUS
# ==========================================================

API_COLUMNS = [
    "groq_design_advice",
    "mistral_design_advice",
    "huggingface_design_advice",
    "unsplash_image_url",
    "pixabay_image_urls"
]


def get_status(record):

    failed = []

    for column in API_COLUMNS:

        value = str(record.get(column, "")).lower()

        if any(word in value for word in [
            "error",
            "unavailable",
            "missing",
            "failed"
        ]):
            failed.append(column)

    if failed:
        return "partial: " + ", ".join(failed)

    return "complete"


# ==========================================================
# 13. LOAD ORIGINAL DATASET
# ==========================================================

print("\nLOADING DATASET")
print("=" * 60)

if not INPUT_FILE.exists():
    raise FileNotFoundError(
        f"Dataset not found: {INPUT_FILE}"
    )

df = pd.read_csv(INPUT_FILE)

print("Original records:", len(df))
print("Original columns:", len(df.columns))

if TEST_LIMIT is not None:
    df = df.head(TEST_LIMIT).copy()
    print("TEST MODE:", len(df), "records")
else:
    print("FULL MODE: Processing all records")


# ==========================================================
# 14. LOAD PREVIOUS CHECKPOINT
# ==========================================================

if CHECKPOINT_FILE.exists():

    progress_df = pd.read_csv(CHECKPOINT_FILE)

    if "source_row_id" not in progress_df.columns:
        raise ValueError(
            "Checkpoint file has no source_row_id column. "
            "Rename or remove the old progress file before restarting."
        )

    completed_ids = set(
        pd.to_numeric(
            progress_df["source_row_id"],
            errors="coerce"
        ).dropna().astype(int)
    )

    print("Previously completed records:", len(completed_ids))

else:

    progress_df = pd.DataFrame()
    completed_ids = set()


# ==========================================================
# 15. PROCESS AND FUSE DATA
# ==========================================================

print("\nSTARTING 5-API DATA FUSION")
print("=" * 60)

for index, row in df.iterrows():

    source_row_id = int(index)

    if source_row_id in completed_ids:
        print(f"Skipping completed record {source_row_id + 1}")
        continue

    print(
        f"\nProcessing {source_row_id + 1} / {len(df)}"
    )

    prompt = create_prompt(row)

    print("  -> Groq")
    groq_result = call_groq(prompt)

    print("  -> Mistral")
    mistral_result = call_mistral(prompt)

    print("  -> Hugging Face")
    huggingface_result = call_huggingface(prompt)

    print("  -> Unsplash")
    unsplash_result = call_unsplash(row)

    print("  -> Pixabay")
    pixabay_result = call_pixabay(row)

    record = row.to_dict()

    record.update({
        "source_row_id": source_row_id,
        "groq_design_advice": groq_result,
        "mistral_design_advice": mistral_result,
        "huggingface_design_advice": huggingface_result,
        "unsplash_image_url": unsplash_result,
        "pixabay_image_urls": pixabay_result
    })

    record["api_fusion_status"] = get_status(record)

    progress_df = pd.concat(
        [progress_df, pd.DataFrame([record])],
        ignore_index=True
    )

    # Save checkpoint after every record
    progress_df.to_csv(TEMP_FILE, index=False)
    TEMP_FILE.replace(CHECKPOINT_FILE)

    completed_ids.add(source_row_id)

    print("  Record saved successfully.")

    time.sleep(DELAY)


# ==========================================================
# 16. CREATE FINAL DATASET
# ==========================================================

if progress_df.empty:
    raise RuntimeError("No records were processed.")

progress_df = progress_df.sort_values(
    "source_row_id"
).reset_index(drop=True)

# Save to temporary file first, then replace final output
final_temp = OUTPUT_DIR / "final_api_fused.tmp"

progress_df.to_csv(final_temp, index=False)
final_temp.replace(OUTPUT_FILE)


# ==========================================================
# 17. SUCCESS SUMMARY
# ==========================================================

print("\nAPI RESULT SUMMARY")
print("=" * 60)

for column, name in [
    ("groq_design_advice", "Groq"),
    ("mistral_design_advice", "Mistral"),
    ("huggingface_design_advice", "Hugging Face"),
    ("unsplash_image_url", "Unsplash"),
    ("pixabay_image_urls", "Pixabay")
]:

    successful = 0

    for value in progress_df[column].fillna(""):

        value = str(value).lower()

        if not any(word in value for word in [
            "error",
            "unavailable",
            "missing",
            "failed"
        ]):
            successful += 1

    print(
        f"{name}: {successful}/{len(progress_df)} successful"
    )


# ==========================================================
# 18. FINAL SUMMARY
# ==========================================================

print("\nAPI DATA FUSION COMPLETED")
print("=" * 60)

print("Final records:", len(progress_df))
print("Final columns:", len(progress_df.columns))

print("\nSaved file:")
print(OUTPUT_FILE)

print("\nFusion status:")
print(progress_df["api_fusion_status"].value_counts())

# Remove checkpoint only after successful final save
if CHECKPOINT_FILE.exists():
    CHECKPOINT_FILE.unlink()

print("\nAll processing completed successfully.")
print("=" * 60)
