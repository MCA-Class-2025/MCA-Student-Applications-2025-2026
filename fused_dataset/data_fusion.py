import os
import time
import requests
import pandas as pd

from dotenv import load_dotenv


# ==========================================================
# 1. CONFIGURATION
# ==========================================================

load_dotenv()

INPUT_FILE = "fused_dataset/fused_interior_decor.csv"
OUTPUT_FILE = "fused_dataset/final_api_fused.csv"


# ==========================================================
# TEST MODE
# ==========================================================
#
# FIRST:
#     TEST_LIMIT = 10
#
# AFTER ALL 5 APIs SHOW WORKING:
#     TEST_LIMIT = None
#
# ==========================================================

TEST_LIMIT = 10


# ==========================================================
# 2. API MODELS
# ==========================================================

# Groq official production model
GROQ_MODEL = "openai/gpt-oss-20b"

# Gemini current stable model
GEMINI_MODEL = "gemini-3.6-flash"

# Mistral
MISTRAL_MODEL = "mistral-small-latest"


# ==========================================================
# 3. DELAYS
# ==========================================================

GROQ_DELAY = 0.5
GEMINI_DELAY = 2
MISTRAL_DELAY = 0.5
IMAGE_DELAY = 0.5


# ==========================================================
# 4. LOAD API KEYS
# ==========================================================

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
UNSPLASH_ACCESS_KEY = os.getenv("UNSPLASH_ACCESS_KEY")
PIXABAY_API_KEY = os.getenv("PIXABAY_API_KEY")


# ==========================================================
# 5. CHECK API KEYS
# ==========================================================

print("=" * 70)
print("CHECKING API KEYS")
print("=" * 70)

api_keys = {
    "Groq": GROQ_API_KEY,
    "Gemini": GEMINI_API_KEY,
    "Mistral": MISTRAL_API_KEY,
    "Unsplash": UNSPLASH_ACCESS_KEY,
    "Pixabay": PIXABAY_API_KEY
}

missing_keys = []

for name, key in api_keys.items():

    if key:
        print(f"✓ {name}: API key found")
    else:
        print(f"✗ {name}: API key missing")
        missing_keys.append(name)


if missing_keys:

    print()
    print("ERROR: Missing API keys:")
    print(", ".join(missing_keys))
    print()
    print("Check your .env file.")

    raise SystemExit


# ==========================================================
# 6. DATASET
# ==========================================================

print()
print("=" * 70)
print("LOADING DATASET")
print("=" * 70)


if not os.path.exists(INPUT_FILE):

    print()
    print("ERROR: Dataset not found:")
    print(INPUT_FILE)
    print()

    raise SystemExit


df = pd.read_csv(INPUT_FILE)

print(
    f"Original dataset records: {len(df)}"
)


# ==========================================================
# 7. TEST LIMIT
# ==========================================================

if TEST_LIMIT is not None:

    df = df.head(TEST_LIMIT).copy()

    print(
        f"TEST MODE: processing {len(df)} records"
    )

else:

    print(
        f"FULL MODE: processing {len(df)} records"
    )


# ==========================================================
# 8. OUTPUT COLUMNS
# ==========================================================

OUTPUT_COLUMNS = [

    "groq_design_advice",

    "gemini_design_advice",

    "mistral_design_advice",

    "unsplash_image_url",

    "pixabay_image_url",

    "api_fusion_status"
]


for column in OUTPUT_COLUMNS:

    if column not in df.columns:

        df[column] = ""


# ==========================================================
# 9. CLEAN FUNCTION
# ==========================================================

def clean(value):

    if value is None:
        return ""

    text = str(value).strip()

    if text.lower() in [
        "nan",
        "none",
        "null"
    ]:

        return ""

    return text


# ==========================================================
# 10. CREATE DESIGN QUERY
# ==========================================================

def create_design_query(row):

    style = clean(
        row.get("style_tags", "")
    )

    material = clean(
        row.get("material_type", "")
    )

    color = clean(
        row.get("color_palette", "")
    )

    category = clean(
        row.get("category", "")
    )

    product = clean(
        row.get("product_name", "")
    )

    description = clean(
        row.get("design_description", "")
    )

    query = f"""
You are an expert interior designer.

Style:
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

Give one short and practical interior design recommendation.

Focus on:
- placement
- styling
- colour coordination
- materials
- lighting
- decoration

Do not invent product names.
Do not invent prices.
Do not mention prices unless provided.

Keep the recommendation concise.
""".strip()

    return query


# ==========================================================
# 11. GROQ API
# ==========================================================

def call_groq(query):

    if not GROQ_API_KEY:

        return "Groq error: API key missing"


    url = (
        "https://api.groq.com/"
        "openai/v1/chat/completions"
    )


    headers = {

        "Authorization":
        f"Bearer {GROQ_API_KEY}",

        "Content-Type":
        "application/json"
    }


    payload = {

        "model":
        GROQ_MODEL,

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
        200
    }


    try:

        response = requests.post(

            url,

            headers=headers,

            json=payload,

            timeout=60
        )


        if response.status_code != 200:

            print()
            print("=" * 70)
            print("GROQ API ERROR")
            print("=" * 70)

            print(
                "Status:",
                response.status_code
            )

            print(
                "Response:",
                response.text[:1000]
            )

            print("=" * 70)

            return (
                f"Groq error: HTTP "
                f"{response.status_code}"
            )


        data = response.json()


        choices = data.get(
            "choices",
            []
        )


        if not choices:

            return (
                "Groq error: empty choices"
            )


        result = (
            choices[0]
            .get("message", {})
            .get("content", "")
        )


        if result:

            return result.strip()


        return (
            "Groq error: empty response"
        )


    except Exception as e:

        print()
        print("=" * 70)
        print("GROQ CONNECTION ERROR")
        print("=" * 70)

        print(
            type(e).__name__
        )

        print(
            str(e)
        )

        print("=" * 70)

        return (
            f"Groq error: "
            f"{type(e).__name__}: "
            f"{str(e)}"
        )


# ==========================================================
# 12. GEMINI API
# ==========================================================

def call_gemini(query):

    if not GEMINI_API_KEY:

        return "Gemini error: API key missing"


    # IMPORTANT:
    # This is a plain STRING.
    # No Gemini SDK is being used.
    # Therefore the tuple validation problem
    # cannot occur here.

    model_name = "gemini-3.6-flash"


    url = (
        "https://generativelanguage.googleapis.com/"
        "v1beta/models/"
        + model_name
        + ":generateContent"
    )


    headers = {

        "Content-Type":
        "application/json",

        "x-goog-api-key":
        GEMINI_API_KEY
    }


    payload = {

        "contents": [

            {

                "parts": [

                    {

                        "text":
                        "You are an expert interior designer.\n\n"
                        + query
                    }

                ]

            }

        ],

        "generationConfig": {

            "temperature":
            0.3,

            "maxOutputTokens":
            200
        }
    }


    try:

        response = requests.post(

            url,

            headers=headers,

            json=payload,

            timeout=60
        )


        # --------------------------------------------------
        # ERROR
        # --------------------------------------------------

        if response.status_code != 200:

            print()
            print("=" * 70)
            print("GEMINI API ERROR")
            print("=" * 70)

            print(
                "Model:",
                model_name
            )

            print(
                "Status:",
                response.status_code
            )

            print(
                "Response:",
                response.text[:1500]
            )

            print("=" * 70)

            return (
                f"Gemini error: HTTP "
                f"{response.status_code}"
            )


        # --------------------------------------------------
        # JSON
        # --------------------------------------------------

        data = response.json()


        candidates = data.get(
            "candidates",
            []
        )


        if not candidates:

            return (
                "Gemini error: "
                "no candidates"
            )


        content = candidates[0].get(
            "content",
            {}
        )


        parts = content.get(
            "parts",
            []
        )


        if not parts:

            return (
                "Gemini error: "
                "no response parts"
            )


        result_parts = []


        for part in parts:

            text = part.get(
                "text",
                ""
            )

            if text:

                result_parts.append(
                    text
                )


        result = "\n".join(
            result_parts
        ).strip()


        if result:

            return result


        return (
            "Gemini error: "
            "empty response"
        )


    except Exception as e:

        print()
        print("=" * 70)
        print("GEMINI CONNECTION ERROR")
        print("=" * 70)

        print(
            type(e).__name__
        )

        print(
            str(e)
        )

        print("=" * 70)

        return (
            f"Gemini error: "
            f"{type(e).__name__}: "
            f"{str(e)}"
        )


# ==========================================================
# 13. MISTRAL API
# ==========================================================

def call_mistral(query):

    if not MISTRAL_API_KEY:

        return (
            "Mistral error: API key missing"
        )


    url = (
        "https://api.mistral.ai/"
        "v1/chat/completions"
    )


    headers = {

        "Authorization":
        f"Bearer {MISTRAL_API_KEY}",

        "Content-Type":
        "application/json"
    }


    payload = {

        "model":
        MISTRAL_MODEL,

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
        200
    }


    try:

        response = requests.post(

            url,

            headers=headers,

            json=payload,

            timeout=60
        )


        if response.status_code != 200:

            print(
                "Mistral error:",
                response.text[:500]
            )

            return (
                f"Mistral error: HTTP "
                f"{response.status_code}"
            )


        data = response.json()


        choices = data.get(
            "choices",
            []
        )


        if not choices:

            return (
                "Mistral error: "
                "empty choices"
            )


        result = (
            choices[0]
            .get("message", {})
            .get("content", "")
        )


        if result:

            return result.strip()


        return (
            "Mistral error: "
            "empty response"
        )


    except Exception as e:

        return (
            f"Mistral error: "
            f"{type(e).__name__}: "
            f"{str(e)}"
        )


# ==========================================================
# 14. IMAGE SEARCH QUERIES
# ==========================================================

def get_image_queries(row):

    style = clean(
        row.get("style_tags", "")
    )

    category = clean(
        row.get("category", "")
    )

    material = clean(
        row.get("material_type", "")
    )

    product = clean(
        row.get("product_name", "")
    )

    color = clean(
        row.get("color_palette", "")
    )


    queries = []


    if style:

        queries.append(
            f"{style} interior design"
        )


    if category:

        queries.append(
            f"{category} interior"
        )


    if product:

        queries.append(
            f"{product} interior"
        )


    if material:

        queries.append(
            f"{material} interior design"
        )


    if color:

        queries.append(
            f"{color} interior design"
        )


    queries.append(
        "modern interior design"
    )


    final_queries = []


    for query in queries:

        query = clean(query)


        if (
            query
            and
            query not in final_queries
        ):

            final_queries.append(
                query
            )


    return final_queries


# ==========================================================
# 15. UNSPLASH API
# ==========================================================

def call_unsplash(row):

    if not UNSPLASH_ACCESS_KEY:

        return (
            "Unsplash error: API key missing"
        )


    url = (
        "https://api.unsplash.com/"
        "search/photos"
    )


    queries = get_image_queries(
        row
    )


    for query in queries:

        try:

            params = {

                "client_id":
                UNSPLASH_ACCESS_KEY,

                "query":
                query,

                "per_page":
                1
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


            if results:

                image_url = (
                    results[0]
                    .get("urls", {})
                    .get("regular", "")
                )


                if image_url:

                    return image_url


        except Exception:

            continue


    return (
        "Unsplash error: "
        "No image found"
    )


# ==========================================================
# 16. PIXABAY API
# ==========================================================

def call_pixabay(row):

    if not PIXABAY_API_KEY:

        return (
            "Pixabay error: API key missing"
        )


    url = (
        "https://pixabay.com/api/"
    )


    queries = get_image_queries(
        row
    )


    for query in queries:

        try:

            params = {

                "key":
                PIXABAY_API_KEY,

                "q":
                query,

                "image_type":
                "photo",

                "orientation":
                "horizontal",

                "safesearch":
                "true",

                "per_page":
                3
            }


            response = requests.get(

                url,

                params=params,

                timeout=30
            )


            response.raise_for_status()


            data = response.json()


            hits = data.get(
                "hits",
                []
            )


            if hits:

                image_url = (
                    hits[0]
                    .get(
                        "largeImageURL",
                        ""
                    )
                )


                if image_url:

                    return image_url


                image_url = (
                    hits[0]
                    .get(
                        "webformatURL",
                        ""
                    )
                )


                if image_url:

                    return image_url


        except Exception:

            continue


    return (
        "Pixabay error: "
        "No image found"
    )


# ==========================================================
# 17. TEXT API TEST
# ==========================================================

def text_api_working(result):

    text = clean(result)


    if not text:

        return False


    lower = text.lower()


    if lower.startswith(
        "groq error:"
    ):

        return False


    if lower.startswith(
        "gemini error:"
    ):

        return False


    if lower.startswith(
        "mistral error:"
    ):

        return False


    return True


# ==========================================================
# 18. IMAGE API TEST
# ==========================================================

def image_api_working(result):

    text = clean(result)


    return (
        text.startswith("http://")
        or
        text.startswith("https://")
    )


# ==========================================================
# 19. TEST ALL FIVE APIs
# ==========================================================

print()
print("=" * 70)
print("TESTING ALL 5 APIs")
print("=" * 70)


TEST_QUERY = """
Give one short practical interior design tip
for a modern minimalist living room.
"""


# ----------------------------------------------------------
# GROQ
# ----------------------------------------------------------

print()
print("→ Testing Groq")

groq_test = call_groq(
    TEST_QUERY
)

print(
    groq_test[:500]
)


# ----------------------------------------------------------
# GEMINI
# ----------------------------------------------------------

print()
print("→ Testing Gemini")

print(
    "Gemini model:",
    GEMINI_MODEL
)

gemini_test = call_gemini(
    TEST_QUERY
)

print(
    gemini_test[:500]
)


# ----------------------------------------------------------
# MISTRAL
# ----------------------------------------------------------

print()
print("→ Testing Mistral")

mistral_test = call_mistral(
    TEST_QUERY
)

print(
    mistral_test[:500]
)


# ----------------------------------------------------------
# UNSPLASH
# ----------------------------------------------------------

print()
print("→ Testing Unsplash")


if len(df) > 0:

    unsplash_test = call_unsplash(
        df.iloc[0]
    )

else:

    unsplash_test = (
        "Unsplash error: "
        "no dataset"
    )


print(
    unsplash_test[:500]
)


# ----------------------------------------------------------
# PIXABAY
# ----------------------------------------------------------

print()
print("→ Testing Pixabay")


if len(df) > 0:

    pixabay_test = call_pixabay(
        df.iloc[0]
    )

else:

    pixabay_test = (
        "Pixabay error: "
        "no dataset"
    )


print(
    pixabay_test[:500]
)


# ==========================================================
# 20. API TEST SUMMARY
# ==========================================================

print()
print("=" * 70)
print("API TEST SUMMARY")
print("=" * 70)


groq_ok = text_api_working(
    groq_test
)

gemini_ok = text_api_working(
    gemini_test
)

mistral_ok = text_api_working(
    mistral_test
)

unsplash_ok = image_api_working(
    unsplash_test
)

pixabay_ok = image_api_working(
    pixabay_test
)


print(
    "Groq:",
    "✓ WORKING"
    if groq_ok
    else "✗ FAILED"
)

print(
    "Gemini:",
    "✓ WORKING"
    if gemini_ok
    else "✗ FAILED"
)

print(
    "Mistral:",
    "✓ WORKING"
    if mistral_ok
    else "✗ FAILED"
)

print(
    "Unsplash:",
    "✓ WORKING"
    if unsplash_ok
    else "✗ FAILED"
)

print(
    "Pixabay:",
    "✓ WORKING"
    if pixabay_ok
    else "✗ FAILED"
)


# ==========================================================
# 21. STOP IF ANY API FAILS
# ==========================================================

failed_apis = []


if not groq_ok:

    failed_apis.append(
        "Groq"
    )


if not gemini_ok:

    failed_apis.append(
        "Gemini"
    )


if not mistral_ok:

    failed_apis.append(
        "Mistral"
    )


if not unsplash_ok:

    failed_apis.append(
        "Unsplash"
    )


if not pixabay_ok:

    failed_apis.append(
        "Pixabay"
    )


if failed_apis:

    print()
    print("=" * 70)
    print("DATA FUSION NOT STARTED")
    print("=" * 70)

    print()

    print(
        "These APIs failed:"
    )


    for api in failed_apis:

        print(
            f"✗ {api}"
        )


    print()

    print(
        "Fix the failed API first."
    )

    print(
        "No dataset records were processed."
    )

    raise SystemExit


# ==========================================================
# 22. ALL APIs WORKING
# ==========================================================

print()
print("=" * 70)
print("ALL 5 APIs WORKING")
print("=" * 70)

print()
print("=" * 70)
print("STARTING DATA FUSION")
print("=" * 70)


# ==========================================================
# 23. PROCESS RECORDS
# ==========================================================

total = len(df)


for i, (index, row) in enumerate(
    df.iterrows(),
    start=1
):

    print()
    print("=" * 60)

    print(
        f"Processing {i} / {total}"
    )

    print("=" * 60)


    # ------------------------------------------------------
    # QUERY
    # ------------------------------------------------------

    query = create_design_query(
        row
    )


    # ------------------------------------------------------
    # GROQ
    # ------------------------------------------------------

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


    time.sleep(
        GROQ_DELAY
    )


    # ------------------------------------------------------
    # GEMINI
    # ------------------------------------------------------

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


    time.sleep(
        GEMINI_DELAY
    )


    # ------------------------------------------------------
    # MISTRAL
    # ------------------------------------------------------

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


    time.sleep(
        MISTRAL_DELAY
    )


    # ------------------------------------------------------
    # UNSPLASH
    # ------------------------------------------------------

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


    time.sleep(
        IMAGE_DELAY
    )


    # ------------------------------------------------------
    # PIXABAY
    # ------------------------------------------------------

    print(
        "  → Pixabay"
    )

    pixabay_result = call_pixabay(
        row
    )


    df.at[
        index,
        "pixabay_image_url"
    ] = pixabay_result


    time.sleep(
        IMAGE_DELAY
    )


    # ======================================================
    # STATUS
    # ======================================================

    errors = []


    if not text_api_working(
        groq_result
    ):

        errors.append(
            "Groq"
        )


    if not text_api_working(
        gemini_result
    ):

        errors.append(
            "Gemini"
        )


    if not text_api_working(
        mistral_result
    ):

        errors.append(
            "Mistral"
        )


    if not image_api_working(
        unsplash_result
    ):

        errors.append(
            "Unsplash"
        )


    if not image_api_working(
        pixabay_result
    ):

        errors.append(
            "Pixabay"
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


    print()
    print(
        f"  Status: {status}"
    )


    # ======================================================
    # SAVE PROGRESS
    # ======================================================

    output_directory = os.path.dirname(
        OUTPUT_FILE
    )


    if output_directory:

        os.makedirs(
            output_directory,
            exist_ok=True
        )


    df.to_csv(
        OUTPUT_FILE,
        index=False
    )


    print(
        f"  ✓ Progress saved "
        f"({i}/{total})"
    )


# ==========================================================
# 24. FINAL SAVE
# ==========================================================

df.to_csv(
    OUTPUT_FILE,
    index=False
)


# ==========================================================
# 25. FINAL SUMMARY
# ==========================================================

print()
print("=" * 70)
print("API DATA FUSION COMPLETED")
print("=" * 70)

print(
    f"Records processed: {len(df)}"
)

print(
    f"Output file: {OUTPUT_FILE}"
)


# ==========================================================
# 26. STATUS SUMMARY
# ==========================================================

print()
print("=" * 70)
print("FUSION STATUS SUMMARY")
print("=" * 70)


print(
    df[
        "api_fusion_status"
    ]
    .value_counts()
    .to_string()
)


# ==========================================================
# 27. SUCCESS COUNTS
# ==========================================================

print()
print("=" * 70)
print("API SUCCESS COUNTS")
print("=" * 70)


def count_success(column):

    values = (
        df[column]
        .astype(str)
        .str.strip()
    )


    return (
        ~values
        .str.lower()
        .str.contains(
            r"error|missing|failed|quota|unavailable",
            regex=True,
            na=False
        )
    ).sum()


print(
    "Groq:",
    count_success(
        "groq_design_advice"
    ),
    "/",
    len(df)
)


print(
    "Gemini:",
    count_success(
        "gemini_design_advice"
    ),
    "/",
    len(df)
)


print(
    "Mistral:",
    count_success(
        "mistral_design_advice"
    ),
    "/",
    len(df)
)


unsplash_success = (
    df[
        "unsplash_image_url"
    ]
    .astype(str)
    .str.startswith(
        "http"
    )
    .sum()
)


pixabay_success = (
    df[
        "pixabay_image_url"
    ]
    .astype(str)
    .str.startswith(
        "http"
    )
    .sum()
)


print(
    "Unsplash:",
    unsplash_success,
    "/",
    len(df)
)


print(
    "Pixabay:",
    pixabay_success,
    "/",
    len(df)
)


# ==========================================================
# 28. FIRST 3 FUSED RECORDS
# ==========================================================

print()
print("=" * 70)
print("FIRST 3 FUSED RECORDS")
print("=" * 70)


display_columns = [

    "product_name",

    "style_tags",

    "groq_design_advice",

    "gemini_design_advice",

    "mistral_design_advice",

    "unsplash_image_url",

    "pixabay_image_url",

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
    .to_string(
        index=False
    )
)


# ==========================================================
# 29. COMPLETED
# ==========================================================

print()
print("=" * 70)
print("ALL 5 API DATA FUSION COMPLETED")
print("=" * 70)