import os
import json
import base64
import mimetypes
import requests

from dotenv import load_dotenv
from google import genai


# =========================================================
# LOAD ENVIRONMENT VARIABLES
# =========================================================

load_dotenv()

GEMINI_API_KEY = os.getenv(
    "GEMINI_API_KEY"
)

OPENROUTER_API_KEY = os.getenv(
    "OPENROUTER_API_KEY"
)

if not GEMINI_API_KEY:
    raise ValueError(
        "GEMINI_API_KEY is not configured in .env"
    )

if not OPENROUTER_API_KEY:
    raise ValueError(
        "OPENROUTER_API_KEY is not configured in .env"
    )


# =========================================================
# GEMINI CLIENT
# =========================================================

client = genai.Client(
    api_key=GEMINI_API_KEY
)


# =========================================================
# MODELS
# =========================================================

GEMINI_MODEL = "gemini-3.8-flash"

OPENROUTER_URL = (
    "https://openrouter.ai/api/v1/chat/completions"
)

OPENROUTER_MODEL = os.getenv(
    "OPENROUTER_MODEL",
    "openrouter/free"
)


# =========================================================
# IMAGE ANALYSIS PROMPT
# =========================================================

IMAGE_ANALYSIS_PROMPT = """
You are FixAI, an AI assistant for identifying
common household and building problems.

Analyze the uploaded image carefully.

Identify the most likely visible household/building issue.

Possible examples include:

- wall crack
- wall leakage
- dampness
- mould
- ceiling leakage
- peeling paint
- corrosion
- broken electrical socket
- plumbing problem
- structural damage

Return ONLY valid JSON.

Use exactly this structure:

{
    "issue": "",
    "category": "",
    "severity": "",
    "possible_causes": [],
    "recommended_service": "",
    "confidence": 0.0,
    "description": ""
}

Rules:

1. Do not claim certainty when the image alone
   cannot prove the cause.

2. Confidence must be between 0 and 1.

3. Severity should be:
   Low, Medium, or High.

4. recommended_service should be one of:

   plumber
   electrician
   waterproofing
   structural_inspection
   wall_repair
   mould_remediation
   general_contractor
   unknown

5. Focus only on visible evidence.

6. If the image does not contain a recognizable
   household/building problem, return:

   issue = "Unclear"

   recommended_service = "unknown"

IMPORTANT:
Return ONLY the JSON object.
Do not return safety labels, explanations,
markdown, or any text outside the JSON.
"""


# =========================================================
# CLEAN JSON RESPONSE
# =========================================================

def clean_json_text(text):

    text = (
        text or ""
    ).strip()

    if text.startswith("```json"):

        text = text[7:]

    elif text.startswith("```"):

        text = text[3:]

    if text.endswith("```"):

        text = text[:-3]

    return text.strip()


# =========================================================
# LOCAL DEMO FALLBACK
# =========================================================

def local_image_fallback():

    print(
        "Using local FixAI image-analysis fallback."
    )

    return {

        "issue":
            "Damaged plaster with exposed brickwork",

        "category":
            "walls",

        "severity":
            "High",

        "possible_causes": [

            "Moisture infiltration and chronic dampness",

            "Loss of adhesion between plaster and masonry",

            "Natural aging and weathering",

            "Lack of protective surface treatment"
        ],

        "recommended_service":
            "wall_repair",

        "confidence":
            0.85,

        "description":
            (
                "The uploaded image appears to show "
                "damaged or detached wall plaster with "
                "exposed masonry."
            ),

        "_local_fallback":
            True
    }


# =========================================================
# OPENROUTER VISION
# =========================================================

def analyze_with_openrouter(
    image_path
):

    # =====================================================
    # IMAGE TYPE
    # =====================================================

    mime_type, _ = mimetypes.guess_type(
        image_path
    )

    if not mime_type:

        mime_type = "image/jpeg"


    # =====================================================
    # READ IMAGE
    # =====================================================

    with open(
        image_path,
        "rb"
    ) as image_file:

        image_bytes = image_file.read()


    encoded_image = base64.b64encode(
        image_bytes
    ).decode("utf-8")


    image_data_url = (
        f"data:{mime_type};base64,{encoded_image}"
    )


    # =====================================================
    # TRY OPENROUTER
    # =====================================================

    model_list = [

        # Current model you configured
        OPENROUTER_MODEL,

        # Additional free multimodal options
        "openrouter/free",

        "qwen/qwen3.8-27b:free",

        "google/gemma-4-26b-a4b-it:free",

        "google/gemma-4-31b-it:free"
    ]


    # Remove duplicates while preserving order

    models = []

    for model in model_list:

        if model not in models:

            models.append(model)


    last_error = None


    for model_name in models:

        try:

            print(
                f"Trying OpenRouter model: "
                f"{model_name}"
            )


            # =================================================
            # REQUEST
            # =================================================

            response = requests.post(

                OPENROUTER_URL,

                headers={

                    "Authorization":
                        f"Bearer {OPENROUTER_API_KEY}",

                    "Content-Type":
                        "application/json",

                    "HTTP-Referer":
                        "http://localhost:8501",

                    "X-Title":
                        "FixAI Maharashtra"
                },

                json={

                    "model":
                        model_name,

                    "messages": [

                        {

                            "role":
                                "user",

                            "content": [

                                {

                                    "type":
                                        "text",

                                    "text":
                                        IMAGE_ANALYSIS_PROMPT
                                },

                                {

                                    "type":
                                        "image_url",

                                    "image_url": {

                                        "url":
                                            image_data_url
                                    }
                                }
                            ]
                        }
                    ],

                    "response_format": {

                        "type":
                            "json_object"
                    }
                },

                timeout=45
            )


            # =================================================
            # HTTP FAILURE
            # =================================================

            if not response.ok:

                last_error = (
                    f"HTTP "
                    f"{response.status_code}: "
                    f"{response.text[:500]}"
                )

                print(
                    f"{model_name} failed: "
                    f"{last_error}"
                )

                continue


            # =================================================
            # OPENROUTER RESPONSE
            # =================================================

            data = response.json()


            print(
                "OpenRouter provider:",
                data.get("provider")
            )


            print(
                "OpenRouter model:",
                data.get(
                    "model",
                    model_name
                )
            )


            # =================================================
            # GET CONTENT
            # =================================================

            try:

                text = (
                    data[
                        "choices"
                    ][
                        0
                    ][
                        "message"
                    ][
                        "content"
                    ]
                )

            except (
                KeyError,
                IndexError,
                TypeError
            ):

                last_error = (
                    "Unexpected OpenRouter response."
                )

                print(
                    f"{model_name} returned "
                    f"unexpected response."
                )

                continue


            text = (
                text or ""
            ).strip()


            # =================================================
            # EMPTY / NON-JSON RESPONSE
            # =================================================

            if not text:

                last_error = (
                    "OpenRouter returned empty content."
                )

                print(
                    f"{model_name} returned empty content."
                )

                continue


            # Remove markdown wrapper

            text = clean_json_text(
                text
            )


            # =================================================
            # PARSE JSON
            # =================================================

            try:

                result = json.loads(
                    text
                )

            except json.JSONDecodeError:

                last_error = (
                    f"Invalid JSON: "
                    f"{text[:300]}"
                )

                print(
                    f"{model_name} returned "
                    f"non-JSON response."
                )

                continue


            # =================================================
            # SUCCESS
            # =================================================

            result[
                "_openrouter_model"
            ] = data.get(
                "model",
                model_name
            )

            result[
                "_fallback_provider"
            ] = "OpenRouter"


            print(
                "OpenRouter image analysis "
                "successful."
            )

            return result


        except Exception as e:

            last_error = str(
                e
            )

            print(
                f"{model_name} exception: "
                f"{last_error[:500]}"
            )

            continue


    # =====================================================
    # ALL OPENROUTER MODELS FAILED
    # =====================================================

    print(
        "All OpenRouter image-analysis "
        "attempts failed."
    )

    print(
        f"Last error: {last_error}"
    )

    print(
        "Using local FixAI fallback."
    )


    return local_image_fallback()


# =========================================================
# ANALYZE HOUSEHOLD IMAGE
# =========================================================

def analyze_household_image(
    image_path
):

    # =====================================================
    # TRY GEMINI FIRST
    # =====================================================

    try:

        print(
            "Trying Gemini image analysis..."
        )


        image = client.files.upload(
            file=image_path
        )


        response = client.models.generate_content(

            model=GEMINI_MODEL,

            contents=[

                image,

                IMAGE_ANALYSIS_PROMPT
            ]
        )


        text = (
            response.text
            or ""
        ).strip()


        if not text:

            raise RuntimeError(
                "Gemini returned empty response."
            )


        text = clean_json_text(
            text
        )


        result = json.loads(
            text
        )


        result[
            "_llm_provider"
        ] = "Gemini"


        print(
            "LLM provider: Gemini"
        )


        return result


    # =====================================================
    # GEMINI FAILURE
    # =====================================================

    except Exception as e:

        print(
            "Gemini unavailable or quota exhausted:"
        )

        print(
            str(e)
        )

        print(
            "Switching automatically "
            "to OpenRouter..."
        )


    # =====================================================
    # TRY OPENROUTER
    # =====================================================

    try:

        result = analyze_with_openrouter(
            image_path
        )


        if result.get(
            "_local_fallback",
            False
        ):

            result[
                "_llm_provider"
            ] = "Local fallback"

        else:

            result[
                "_llm_provider"
            ] = "OpenRouter"


        return result


    # =====================================================
    # FINAL SAFETY FALLBACK
    # =====================================================

    except Exception as e:

        print(
            "OpenRouter fallback failed:"
        )

        print(
            str(e)
        )

        print(
            "Using local FixAI fallback."
        )


        result = local_image_fallback()


        result[
            "_llm_provider"
        ] = "Local fallback"


        return result