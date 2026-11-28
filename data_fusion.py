import os
import time
import requests
import pandas as pd

from dotenv import load_dotenv
from groq import Groq
from google import genai


# ==========================================================
# 1. CONFIGURATION
# ==========================================================

load_dotenv()

INPUT_FILE = "fused_dataset/fused_interior_decor.csv"
OUTPUT_FILE = "fused_dataset/final_api_fused.csv"

# ----------------------------------------------------------
# TEST MODE
# ----------------------------------------------------------
# FIRST RUN:
TEST_LIMIT = 10

# AFTER 10 RECORD TEST WORKS:
# TEST_LIMIT = None
# ----------------------------------------------------------

TEST_LIMIT = 10

# ----------------------------------------------------------
# API MODELS
# ----------------------------------------------------------

GROQ_MODEL = "llama-3.1-8b-instant"

# Stable Gemini model
GEMINI_MODEL = "gemini-3.7-flash",

MISTRAL_MODEL = "mistral-small-latest"

# ----------------------------------------------------------
# DELAYS
# ----------------------------------------------------------

API_DELAY = 1
GEMINI_DELAY = 3

# ----------------------------------------------------------
# RETRY SETTINGS
# ----------------------------------------------------------

MAX_RETRIES = 2
REQUEST_TIMEOUT = 45

# ----------------------------------------------------------
# RESUME
# ----------------------------------------------------------

RESUME_EXISTING_OUTPUT = True

# ----------------------------------------------------------
# Gemini quota flag
# ----------------------------------------------------------

GEMINI_QUOTA_EXHAUSTED = False


# ==========================================================
# 2. LOAD ENVIRONMENT
# ==========================================================

load_dotenv()


# ==========================================================
# 3. API KEYS
# ==========================================================

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
UNSPLASH_ACCESS_KEY = os.getenv("UNSPLASH_ACCESS_KEY")
PIXABAY_API_KEY = os.getenv("PIXABAY_API_KEY")


# ==========================================================
# 4. CHECK API KEYS
# ==========================================================

print("=" * 70)
print("CHECKING FIVE API KEYS")
print("=" * 70)

api_keys = {
    "Groq": GROQ_API_KEY,
    "Gemini": GEMINI_API_KEY,
    "Mistral": MISTRAL_API_KEY,
    "Unsplash": UNSPLASH_ACCESS_KEY,
    "Pixabay": PIXABAY_API_KEY,
}

missing_keys = []

for name, key in api_keys.items():

    if key:
        print(f"✓ {name}: API key found")
    else:
        print(f"✗ {name}: API key MISSING")
        missing_keys.append(name)


if missing_keys:

    print("\nERROR: Missing API keys:")
    print(", ".join(missing_keys))

    print("\nCheck your .env file.")

    raise SystemExit


# ==========================================================
# 5. INITIALIZE CLIENTS
# ==========================================================

print("\n" + "=" * 70)
print("INITIALIZING API CLIENTS")
print("=" * 70)


groq_client = None
gemini_client = None


# ----------------------------------------------------------
# GROQ
# ----------------------------------------------------------

try:

    groq_client = Groq(
        api_key=GROQ_API_KEY
    )

    print("✓ Groq client initialized")

except Exception as e:

    print(f"✗ Groq initialization failed: {e}")


# ----------------------------------------------------------
# GEMINI
# ----------------------------------------------------------

try:

    gemini_client = genai.Client(
        api_key=GEMINI_API_KEY
    )

    print("✓ Gemini client initialized")

except Exception as e:

    print(f"✗ Gemini initialization failed: {e}")


# ==========================================================
# 6. LOAD DATASET
# ==========================================================

print("\n" + "=" * 70)
print("LOADING DATASET")
print("=" * 70)


if not os.path.exists(INPUT_FILE):

    print(
        f"\nERROR: Input file not found:\n"
        f"{INPUT_FILE}"
    )

    print(
        "\nRun this command from:"
    )

    print(
        r"C:\Users\subbu\OneDrive\Desktop\chatbot"
    )

    raise SystemExit


original_df = pd.read_csv(
    INPUT_FILE
)

print(
    f"Original dataset records: "
    f"{len(original_df)}"
)


# ==========================================================
# 7. RESUME EXISTING OUTPUT
# ==========================================================

if (
    RESUME_EXISTING_OUTPUT
    and
    os.path.exists(OUTPUT_FILE)
):

    try:

        existing_df = pd.read_csv(
            OUTPUT_FILE
        )

        if len(existing_df) == len(original_df):

            print(
                "\nExisting output found."
            )

            print(
                "Using existing output for resume."
            )

            df = existing_df.copy()

        else:

            print(
                "\nExisting output size does not "
                "match input."
            )

            print(
                "Starting from input dataset."
            )

            df = original_df.copy()

    except Exception as e:

        print(
            f"\nCould not load existing output: {e}"
        )

        df = original_df.copy()

else:

    df = original_df.copy()


# ==========================================================
# 8. CREATE OUTPUT COLUMNS
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
# 9. APPLY TEST LIMIT
# ==========================================================

if TEST_LIMIT is not None:

    work_df = df.head(
        TEST_LIMIT
    ).copy()

    print(
        f"\nTEST MODE: "
        f"{len(work_df)} records"
    )

else:

    work_df = df.copy()

    print(
        f"\nFULL MODE: "
        f"{len(work_df)} records"
    )


# ==========================================================
# 10. HELPER
# ==========================================================

def clean(value):

    if value is None:

        return ""

    value = str(value).strip()

    if value.lower() in [
        "nan",
        "none",
        "null"
    ]:

        return ""

    return value


# ==========================================================
# 11. CREATE DESIGN QUERY
# ==========================================================

def create_design_query(row):

    style = clean(
        row.get(
            "style_tags",
            ""
        )
    )

    material = clean(
        row.get(
            "material_type",
            ""
        )
    )

    colour = clean(
        row.get(
            "color_palette",
            ""
        )
    )

    category = clean(
        row.get(
            "category",
            ""
        )
    )

    product = clean(
        row.get(
            "product_name",
            ""
        )
    )

    description = clean(
        row.get(
            "design_description",
            ""
        )
    )

    return f"""
You are an expert interior designer.

Style:
{style}

Material:
{material}

Colour palette:
{colour}

Category:
{category}

Product:
{product}

Description:
{description}

Give ONE short practical interior design recommendation.

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

Keep the answer concise.
""".strip()


# ==========================================================
# 12. GROQ
# ==========================================================

def call_groq(query):

    if not groq_client:

        return "Groq error: client unavailable"

    for attempt in range(
        MAX_RETRIES + 1
    ):

        try:

            response = (
                groq_client
                .chat
                .completions
                .create(

                    model=GROQ_MODEL,

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

                    max_tokens=180
                )
            )

            result = (
                response
                .choices[0]
                .message
                .content
            )

            if result:

                return result.strip()

            return (
                "Groq error: empty response"
            )

        except Exception as e:

            error = str(e)

            if attempt < MAX_RETRIES:

                if (
                    "429" in error
                    or
                    "rate" in error.lower()
                ):

                    time.sleep(
                        5 * (attempt + 1)
                    )

                    continue

            return (
                f"Groq error: {error}"
            )

    return "Groq error: failed"


# ==========================================================
# 13. GEMINI
# ==========================================================

def call_gemini(query):

    global GEMINI_QUOTA_EXHAUSTED

    # ----------------------------------------------
    # Stop repeated quota calls
    # ----------------------------------------------

    if GEMINI_QUOTA_EXHAUSTED:

        return (
            "Gemini skipped: quota exhausted"
        )

    if not gemini_client:

        return (
            "Gemini error: client unavailable"
        )

    for attempt in range(
        MAX_RETRIES + 1
    ):

        try:

            response = (
                gemini_client
                .models
                .generate_content(

                    model=GEMINI_MODEL,

                    contents=(
                        "You are an expert interior designer.\n\n"
                        + query
                    )
                )
            )

            result = getattr(
                response,
                "text",
                None
            )

            if result:

                return result.strip()

            return (
                "Gemini error: empty response"
            )

        except Exception as e:

            error = str(e)

            # --------------------------------------
            # QUOTA
            # --------------------------------------

            if (
                "429" in error
                or
                "quota" in error.lower()
                or
                "resource_exhausted" in error.lower()
            ):

                GEMINI_QUOTA_EXHAUSTED = True

                print(
                    "\n⚠ Gemini quota exhausted."
                )

                print(
                    "⚠ Gemini will be skipped "
                    "for remaining records."
                )

                return (
                    "Gemini skipped: quota exhausted"
                )

            # --------------------------------------
            # RETRY TEMPORARY ERROR
            # --------------------------------------

            if attempt < MAX_RETRIES:

                time.sleep(
                    3 * (attempt + 1)
                )

                continue

            return (
                f"Gemini error: {error}"
            )

    return "Gemini error: failed"


# ==========================================================
# 14. MISTRAL
# ==========================================================

def call_mistral(query):

    if not MISTRAL_API_KEY:

        return (
            "Mistral error: API key missing"
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
        180
    }

    for attempt in range(
        MAX_RETRIES + 1
    ):

        try:

            response = requests.post(

                url,

                headers=headers,

                json=payload,

                timeout=REQUEST_TIMEOUT
            )

            response.raise_for_status()

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

            if isinstance(
                result,
                list
            ):

                text_parts = []

                for item in result:

                    if isinstance(
                        item,
                        dict
                    ):

                        text = item.get(
                            "text",
                            ""
                        )

                        if text:

                            text_parts.append(
                                text
                            )

                result = " ".join(
                    text_parts
                )

            if result:

                return str(
                    result
                ).strip()

            return (
                "Mistral error: "
                "empty response"
            )

        except Exception as e:

            if attempt < MAX_RETRIES:

                time.sleep(
                    3 * (attempt + 1)
                )

                continue

            return (
                f"Mistral error: {e}"
            )

    return "Mistral error: failed"


# ==========================================================
# 15. IMAGE SEARCH QUERY
# ==========================================================

def get_image_query(row):

    style = clean(
        row.get(
            "style_tags",
            ""
        )
    )

    category = clean(
        row.get(
            "category",
            ""
        )
    )

    material = clean(
        row.get(
            "material_type",
            ""
        )
    )

    product = clean(
        row.get(
            "product_name",
            ""
        )
    )

    parts = []

    if style:

        parts.append(style)

    if category:

        parts.append(category)

    if material:

        parts.append(material)

    if product:

        parts.append(product)

    parts.append(
        "interior design"
    )

    query = " ".join(parts)

    # Keep image search query short
    return query[:100]


# ==========================================================
# 16. UNSPLASH
# ==========================================================

def call_unsplash(row):

    if not UNSPLASH_ACCESS_KEY:

        return (
            "Unsplash error: API key missing"
        )

    query = get_image_query(
        row
    )

    url = (
        "https://api.unsplash.com/search/photos"
    )

    params = {

        "client_id":
        UNSPLASH_ACCESS_KEY,

        "query":
        query,

        "per_page":
        1,

        "orientation":
        "landscape"
    }

    for attempt in range(
        MAX_RETRIES + 1
    ):

        try:

            response = requests.get(

                url,

                params=params,

                timeout=REQUEST_TIMEOUT
            )

            # Rate limit
            if response.status_code == 429:

                if attempt < MAX_RETRIES:

                    time.sleep(
                        10 * (attempt + 1)
                    )

                    continue

                return (
                    "Unsplash error: "
                    "rate limit exceeded"
                )

            response.raise_for_status()

            data = response.json()

            results = data.get(
                "results",
                []
            )

            if results:

                urls = (
                    results[0]
                    .get(
                        "urls",
                        {}
                    )
                )

                image_url = (
                    urls.get(
                        "regular",
                        ""
                    )
                )

                if image_url:

                    return image_url

            return (
                "Unsplash error: "
                "No image found"
            )

        except Exception as e:

            if attempt < MAX_RETRIES:

                time.sleep(
                    3 * (attempt + 1)
                )

                continue

            return (
                f"Unsplash error: {e}"
            )

    return (
        "Unsplash error: failed"
    )


# ==========================================================
# 17. PIXABAY
# ==========================================================

def call_pixabay(row):

    if not PIXABAY_API_KEY:

        return (
            "Pixabay error: API key missing"
        )

    query = get_image_query(
        row
    )

    url = (
        "https://pixabay.com/api/"
    )

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

    for attempt in range(
        MAX_RETRIES + 1
    ):

        try:

            response = requests.get(

                url,

                params=params,

                timeout=REQUEST_TIMEOUT
            )

            if response.status_code == 429:

                if attempt < MAX_RETRIES:

                    time.sleep(
                        10 * (attempt + 1)
                    )

                    continue

                return (
                    "Pixabay error: "
                    "rate limit exceeded"
                )

            response.raise_for_status()

            data = response.json()

            hits = data.get(
                "hits",
                []
            )

            if hits:

                # Prefer large image
                image_url = (
                    hits[0]
                    .get(
                        "largeImageURL",
                        ""
                    )
                )

                if image_url:

                    return image_url

                # Fallback
                image_url = (
                    hits[0]
                    .get(
                        "webformatURL",
                        ""
                    )
                )

                if image_url:

                    return image_url

            return (
                "Pixabay error: "
                "No image found"
            )

        except Exception as e:

            if attempt < MAX_RETRIES:

                time.sleep(
                    3 * (attempt + 1)
                )

                continue

            return (
                f"Pixabay error: {e}"
            )

    return (
        "Pixabay error: failed"
    )


# ==========================================================
# 18. SUCCESS CHECKS
# ==========================================================

def text_success(result):

    text = clean(
        result
    ).lower()

    if not text:

        return False

    failure_words = [

        " api key missing",

        " error:",

        " skipped:",

        " returned empty",

        "client unavailable"
    ]

    for word in failure_words:

        if word in text:

            return False

    return True


def image_success(result):

    text = clean(
        result
    ).lower()

    return (
        text.startswith("http://")
        or
        text.startswith("https://")
    )


# ==========================================================
# 19. TEST ALL FIVE APIs
# ==========================================================

print("\n" + "=" * 70)
print("TESTING ALL FIVE APIs")
print("=" * 70)


TEST_QUERY = """
Give one short practical interior design tip
for a modern minimalist living room.
"""


# ----------------------------------------------------------
# GROQ TEST
# ----------------------------------------------------------

print("\n→ Testing Groq")

groq_test = call_groq(
    TEST_QUERY
)

print(
    groq_test[:200]
)


# ----------------------------------------------------------
# GEMINI TEST
# ----------------------------------------------------------

print("\n→ Testing Gemini")

gemini_test = call_gemini(
    TEST_QUERY
)

print(
    gemini_test[:200]
)


# ----------------------------------------------------------
# MISTRAL TEST
# ----------------------------------------------------------

print("\n→ Testing Mistral")

mistral_test = call_mistral(
    TEST_QUERY
)

print(
    mistral_test[:200]
)


# ----------------------------------------------------------
# UNSPLASH TEST
# ----------------------------------------------------------

print("\n→ Testing Unsplash")

if len(work_df) > 0:

    unsplash_test = call_unsplash(
        work_df.iloc[0]
    )

else:

    unsplash_test = (
        "Unsplash error: "
        "no dataset record"
    )

print(
    unsplash_test[:200]
)


# ----------------------------------------------------------
# PIXABAY TEST
# ----------------------------------------------------------

print("\n→ Testing Pixabay")

if len(work_df) > 0:

    pixabay_test = call_pixabay(
        work_df.iloc[0]
    )

else:

    pixabay_test = (
        "Pixabay error: "
        "no dataset record"
    )

print(
    pixabay_test[:200]
)


# ==========================================================
# 20. TEST SUMMARY
# ==========================================================

print("\n" + "=" * 70)
print("API TEST SUMMARY")
print("=" * 70)


test_results = {

    "Groq":
    text_success(
        groq_test
    ),

    "Gemini":
    text_success(
        gemini_test
    ),

    "Mistral":
    text_success(
        mistral_test
    ),

    "Unsplash":
    image_success(
        unsplash_test
    ),

    "Pixabay":
    image_success(
        pixabay_test
    )
}


for name, success in test_results.items():

    print(
        f"{name}: "
        f"{'✓ WORKING' if success else '✗ FAILED'}"
    )


# ==========================================================
# 21. DO NOT START 1000 RECORDS IF AN API IS BROKEN
# ==========================================================

failed_apis = [

    name

    for name, success
    in test_results.items()

    if not success
]


if failed_apis:

    print("\n" + "=" * 70)
    print("DATA FUSION NOT STARTED")
    print("=" * 70)

    print(
        "\nThese APIs failed the connection test:"
    )

    for name in failed_apis:

        print(
            f"✗ {name}"
        )

    print(
        "\nFix the failed API first."
    )

    print(
        "This prevents wasting API requests "
        "on 1,000 records."
    )

    raise SystemExit


print("\n✓ ALL FIVE APIs PASSED THE TEST")


# ==========================================================
# 22. START DATA FUSION
# ==========================================================

print("\n" + "=" * 70)
print("STARTING FIVE API DATA FUSION")
print("=" * 70)


total = len(
    work_df
)


for i, (index, row) in enumerate(

    work_df.iterrows(),

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

    time.sleep(
        API_DELAY
    )


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

    if not GEMINI_QUOTA_EXHAUSTED:

        time.sleep(
            GEMINI_DELAY
        )


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

    time.sleep(
        API_DELAY
    )


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

    time.sleep(
        API_DELAY
    )


    # ======================================================
    # PIXABAY
    # ======================================================

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
        API_DELAY
    )


    # ======================================================
    # STATUS
    # ======================================================

    errors = []


    # ------------------------------------------------------
    # GROQ STATUS
    # ------------------------------------------------------

    if not text_success(
        groq_result
    ):

        errors.append(
            "Groq"
        )


    # ------------------------------------------------------
    # GEMINI STATUS
    # ------------------------------------------------------

    if not text_success(
        gemini_result
    ):

        errors.append(
            "Gemini"
        )


    # ------------------------------------------------------
    # MISTRAL STATUS
    # ------------------------------------------------------

    if not text_success(
        mistral_result
    ):

        errors.append(
            "Mistral"
        )


    # ------------------------------------------------------
    # UNSPLASH STATUS
    # ------------------------------------------------------

    if not image_success(
        unsplash_result
    ):

        errors.append(
            "Unsplash"
        )


    # ------------------------------------------------------
    # PIXABAY STATUS
    # ------------------------------------------------------

    if not image_success(
        pixabay_result
    ):

        errors.append(
            "Pixabay"
        )


    # ------------------------------------------------------
    # FINAL STATUS
    # ------------------------------------------------------

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


    print(
        f"  Status: {status}"
    )


    # ======================================================
    # SAVE PROGRESS
    # ======================================================

    df.to_csv(

        OUTPUT_FILE,

        index=False
    )

    print(
        f"  ✓ Progress saved "
        f"({i}/{total})"
    )


# ==========================================================
# 23. FINAL SAVE
# ==========================================================

df.to_csv(

    OUTPUT_FILE,

    index=False
)


# ==========================================================
# 24. FINAL SUMMARY
# ==========================================================

print("\n" + "=" * 70)
print("FIVE API DATA FUSION COMPLETED")
print("=" * 70)

print(
    f"Records in original dataset: "
    f"{len(original_df)}"
)

print(
    f"Records processed this run: "
    f"{len(work_df)}"
)

print(
    f"Output file: "
    f"{OUTPUT_FILE}"
)


# ==========================================================
# 25. STATUS SUMMARY
# ==========================================================

print("\n" + "=" * 70)
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
# 26. API RESULT CHECK
# ==========================================================

print("\n" + "=" * 70)
print("API RESULT COUNTS")
print("=" * 70)


for column in [

    "groq_design_advice",

    "gemini_design_advice",

    "mistral_design_advice",

    "unsplash_image_url",

    "pixabay_image_url"

]:

    if column in df.columns:

        series = (
            df[column]
            .fillna("")
            .astype(str)
        )

        empty_count = (
            series
            .str.strip()
            .eq("")
            .sum()
        )

        print(
            f"{column}: "
            f"{len(df) - empty_count} non-empty / "
            f"{len(df)} total"
        )


# ==========================================================
# 27. FIRST THREE RECORDS
# ==========================================================

print("\n" + "=" * 70)
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


print("\n" + "=" * 70)
print("ALL FIVE API DATA FUSION COMPLETED")
print("=" * 70)