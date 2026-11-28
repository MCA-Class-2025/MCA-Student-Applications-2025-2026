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
# IMPORTANT
# ----------------------------------------------------------
# Start with 10.
#
# After testing successfully:
#
# REPAIR_LIMIT = None
#
# will process all remaining failed records.
# ----------------------------------------------------------

REPAIR_LIMIT = 10

SAVE_EVERY = 5

# Number of retries for network APIs
MAX_RETRIES = 3


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

    print("\nERROR:")
    print("Final fused dataset not found:")
    print(INPUT_FILE)

    raise SystemExit


df = pd.read_csv(INPUT_FILE)

print(
    f"Records loaded: {len(df)}"
)


# ==========================================================
# CHECK REQUIRED COLUMNS
# ==========================================================

required_columns = [

    "groq_design_advice",
    "gemini_design_advice",
    "huggingface_design_advice",
    "unsplash_image_url",
    "mistral_design_advice",
    "api_fusion_status"
]


for column in required_columns:

    if column not in df.columns:

        df[column] = ""


# ==========================================================
# INITIALIZE CLIENTS
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

Give one short, practical interior design recommendation.

Focus on:
- placement
- colour coordination
- materials
- lighting
- decoration

Do not invent product names.
Do not mention prices.
Keep the answer concise.
"""

    return query.strip()


# ==========================================================
# ERROR DETECTION
# ==========================================================

def is_failed(value):

    if pd.isna(value):

        return True

    value = str(value).strip()

    if value == "":

        return True

    error_words = [

        "error",

        "missing",

        "failed",

        "quota",

        "unsupported",

        "bad request",

        "not found",

        "resource_exhausted",

        "429",

        "404",

        "406",

        "connection aborted",

        "connectionpool",

        "provider"
    ]

    value_lower = value.lower()

    return any(
        word in value_lower
        for word in error_words
    )


# ==========================================================
# GEMINI QUOTA DETECTION
# ==========================================================

def is_gemini_quota_error(value):

    if pd.isna(value):

        return False

    text = str(value).lower()

    return (
        "429" in text
        or
        "resource_exhausted" in text
        or
        "quota" in text
    )


# ==========================================================
# GROQ
# ==========================================================

def call_groq(query):

    if not groq_client:

        return "Groq API key missing"

    for attempt in range(
        1,
        MAX_RETRIES + 1
    ):

        try:

            response = groq_client.chat.completions.create(

                model="llama-3.3-70b-versatile",

                messages=[

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

            error_text = str(e)

            print(
                f"    Groq attempt "
                f"{attempt}/{MAX_RETRIES} failed"
            )

            if "429" in error_text:

                wait_time = 10 * attempt

            else:

                wait_time = 3 * attempt

            if attempt < MAX_RETRIES:

                time.sleep(
                    wait_time
                )

            else:

                return (
                    f"Groq error: "
                    f"{error_text}"
                )


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
                +
                query
            )
        )

        if response.text:

            return response.text.strip()

        return "Gemini empty response"

    except Exception as e:

        error_text = str(e)

        # --------------------------------------------------
        # IMPORTANT:
        # Do NOT repeatedly retry Gemini quota errors.
        # --------------------------------------------------

        if (
            "429" in error_text
            or
            "RESOURCE_EXHAUSTED"
            in error_text
            or
            "quota"
            in error_text.lower()
        ):

            print(
                "    Gemini quota exhausted."
            )

            print(
                "    Gemini will be skipped."
            )

            return (
                "Gemini quota exhausted"
            )

        return (
            f"Gemini error: "
            f"{error_text}"
        )


# ==========================================================
# HUGGING FACE
# ==========================================================

def call_huggingface(query):

    if not hf_client:

        return "Hugging Face API key missing"

    try:

        # --------------------------------------------------
        # Use a model currently recommended by the
        # Hugging Face Inference Providers documentation.
        # --------------------------------------------------

        model = "google/gemma-2-2b-it"

        result = hf_client.text_generation(

            prompt=query,

            model=model,

            max_new_tokens=150,

            temperature=0.3
        )

        if result:

            return str(
                result
            ).strip()

        return (
            "Hugging Face empty response"
        )

    except Exception as e:

        return (
            f"Hugging Face error: "
            f"{str(e)}"
        )


# ==========================================================
# UNSPLASH
# ==========================================================

def call_unsplash(row):

    if not UNSPLASH_ACCESS_KEY:

        return (
            "Unsplash API key missing"
        )

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

    product = str(
        row.get(
            "product_name",
            ""
        )
    )

    search_query = (
        f"{style} "
        f"{category} "
        f"interior design "
        f"{product}"
    ).strip()

    url = (
        "https://api.unsplash.com/search/photos"
    )

    params = {

        "query":
        search_query,

        "per_page":
        1,

        "client_id":
        UNSPLASH_ACCESS_KEY
    }


    for attempt in range(
        1,
        MAX_RETRIES + 1
    ):

        try:

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

            print(
                f"    Unsplash attempt "
                f"{attempt}/{MAX_RETRIES} failed"
            )

            if attempt < MAX_RETRIES:

                time.sleep(
                    3 * attempt
                )

            else:

                return (
                    f"Unsplash error: "
                    f"{str(e)}"
                )


# ==========================================================
# MISTRAL
# ==========================================================

def call_mistral(query):

    if not MISTRAL_API_KEY:

        return (
            "Mistral API key missing"
        )

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


    for attempt in range(
        1,
        MAX_RETRIES + 1
    ):

        try:

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

            print(
                f"    Mistral attempt "
                f"{attempt}/{MAX_RETRIES} failed"
            )

            if attempt < MAX_RETRIES:

                time.sleep(
                    5 * attempt
                )

            else:

                return (
                    f"Mistral error: "
                    f"{str(e)}"
                )


# ==========================================================
# CHECK CURRENT API STATUS
# ==========================================================

print("\n" + "=" * 70)
print("CURRENT API STATUS")
print("=" * 70)


api_columns = {

    "groq_design_advice":
    "Groq",

    "gemini_design_advice":
    "Gemini",

    "huggingface_design_advice":
    "Hugging Face",

    "unsplash_image_url":
    "Unsplash",

    "mistral_design_advice":
    "Mistral"
}


for column, name in api_columns.items():

    failed_count = df[
        column
    ].apply(
        is_failed
    ).sum()

    success_count = (
        len(df)
        -
        failed_count
    )

    print(
        f"{name}: "
        f"{success_count} successful | "
        f"{failed_count} failed"
    )


# ==========================================================
# FIND RECORDS THAT NEED REPAIR
# ==========================================================

failed_indices = set()


for column in api_columns:

    failed_rows = df[
        df[column].apply(
            is_failed
        )
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
# LIMIT FOR TESTING
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
# REPAIR LOOP
# ==========================================================

print("\n" + "=" * 70)
print("STARTING API REPAIR")
print("=" * 70)


for count, index in enumerate(
    failed_indices,
    start=1
):

    print(
        f"\nRepairing "
        f"{count} / "
        f"{len(failed_indices)}"
    )


    row = df.loc[index]

    query = create_design_query(
        row
    )


    # ======================================================
    # GROQ
    # ======================================================

    if is_failed(
        df.at[
            index,
            "groq_design_advice"
        ]
    ):

        print(
            "  → Groq"
        )

        result = call_groq(
            query
        )

        # Only replace the failed value.
        df.at[
            index,
            "groq_design_advice"
        ] = result

        time.sleep(1)


    # ======================================================
    # GEMINI
    # ======================================================

    if is_failed(
        df.at[
            index,
            "gemini_design_advice"
        ]
    ):

        old_value = df.at[
            index,
            "gemini_design_advice"
        ]

        # --------------------------------------------------
        # If the existing error is already quota-related,
        # don't waste another Gemini request.
        # --------------------------------------------------

        if is_gemini_quota_error(
            old_value
        ):

            print(
                "  → Gemini SKIPPED "
                "(quota exhausted)"
            )

        else:

            print(
                "  → Gemini"
            )

            result = call_gemini(
                query
            )

            df.at[
                index,
                "gemini_design_advice"
            ] = result

            time.sleep(2)


    # ======================================================
    # HUGGING FACE
    # ======================================================

    if is_failed(
        df.at[
            index,
            "huggingface_design_advice"
        ]
    ):

        print(
            "  → Hugging Face"
        )

        result = call_huggingface(
            query
        )

        df.at[
            index,
            "huggingface_design_advice"
        ] = result

        time.sleep(2)


    # ======================================================
    # UNSPLASH
    # ======================================================

    if is_failed(
        df.at[
            index,
            "unsplash_image_url"
        ]
    ):

        print(
            "  → Unsplash"
        )

        result = call_unsplash(
            row
        )

        df.at[
            index,
            "unsplash_image_url"
        ] = result

        time.sleep(1)


    # ======================================================
    # MISTRAL
    # ======================================================

    if is_failed(
        df.at[
            index,
            "mistral_design_advice"
        ]
    ):

        print(
            "  → Mistral"
        )

        result = call_mistral(
            query
        )

        df.at[
            index,
            "mistral_design_advice"
        ] = result

        time.sleep(2)


    # ======================================================
    # UPDATE STATUS
    # ======================================================

    errors = []


    for column, name in api_columns.items():

        value = df.at[
            index,
            column
        ]

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


    print(
        "  Status: "
        +
        df.at[
            index,
            "api_fusion_status"
        ]
    )


    # ======================================================
    # SAVE PROGRESS
    # ======================================================

    if count % SAVE_EVERY == 0:

        df.to_csv(
            OUTPUT_FILE,
            index=False
        )

        print(
            f"  ✓ Progress saved "
            f"({count}/"
            f"{len(failed_indices)})"
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
    f"Total dataset records: "
    f"{len(df)}"
)


print("\nFINAL STATUS:")

print(
    df[
        "api_fusion_status"
    ].value_counts()
)


print("\nFINAL API ERROR COUNTS:")


for column, name in api_columns.items():

    failed_count = df[
        column
    ].apply(
        is_failed
    ).sum()

    print(
        f"{name}: "
        f"{failed_count} failed"
    )


print("\nSaved file:")

print(
    OUTPUT_FILE
)


print("\n" + "=" * 70)
print("DONE")
print("=" * 70)