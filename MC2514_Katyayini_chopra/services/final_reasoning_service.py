import os
import json
import requests

from dotenv import load_dotenv
from google import genai

from services.fused_rag_service import (
    retrieve_fused_records
)


# =========================================================
# ENVIRONMENT
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
        "GEMINI_API_KEY is not set in .env"
    )

if not OPENROUTER_API_KEY:
    raise ValueError(
        "OPENROUTER_API_KEY is not set in .env"
    )


# =========================================================
# CLIENT
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
# JSON CLEANER
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
# OPENROUTER TEXT REQUEST
# =========================================================

def ask_openrouter(prompt):

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
                OPENROUTER_MODEL,

            "messages": [

                {
                    "role":
                        "user",

                    "content":
                        prompt
                }
            ]
        },

        timeout=45
    )


    if not response.ok:

        raise RuntimeError(

            f"OpenRouter error "
            f"{response.status_code}: "
            f"{response.text[:800]}"
        )


    data = response.json()


    try:

        return (
            data[
                "choices"
            ][
                0
            ][
                "message"
            ][
                "content"
            ]
            or ""
        )

    except (
        KeyError,
        IndexError,
        TypeError
    ) as e:

        raise RuntimeError(
            f"Invalid OpenRouter response: {data}"
        ) from e


# =========================================================
# LOCAL RAG FALLBACK
# =========================================================

def build_local_fallback(
    fused_data,
    fused_knowledge
):

    image_analysis = fused_data.get(
        "image_analysis",
        {}
    )


    issue = image_analysis.get(
        "issue",
        "Unclear"
    )


    category = image_analysis.get(
        "category",
        "Unknown"
    )


    severity = image_analysis.get(
        "severity",
        "Medium"
    )


    confidence = image_analysis.get(
        "confidence",
        0.0
    )


    possible_causes = image_analysis.get(
        "possible_causes",
        []
    )


    recommended_service = image_analysis.get(
        "recommended_service",
        "unknown"
    )


    # -----------------------------------------------------
    # RAG EVIDENCE
    # -----------------------------------------------------

    rag_evidence = []

    rag_services = []

    rag_defects = []

    rag_descriptions = []


    for record in fused_knowledge:

        clean_record = {

            "defect":
                record.get("defect"),

            "service_type":
                record.get("service_type"),

            "location":
                record.get(
                    "api_context_city"
                ),

            "professional":
                record.get(
                    "professional_name"
                ),

            "description":
                record.get(
                    "example_description"
                )
        }


        # Remove empty values

        clean_record = {

            k: v

            for k, v in clean_record.items()

            if v not in (
                None,
                "",
                "nan"
            )
        }


        if clean_record:

            rag_evidence.append(
                clean_record
            )


        if record.get(
            "service_type"
        ):

            rag_services.append(
                record.get(
                    "service_type"
                )
            )


        if record.get(
            "defect"
        ):

            rag_defects.append(
                record.get(
                    "defect"
                )
            )


        if record.get(
            "example_description"
        ):

            rag_descriptions.append(
                record.get(
                    "example_description"
                )
            )


    # -----------------------------------------------------
    # SERVICE
    # -----------------------------------------------------

    if (
        not recommended_service
        or recommended_service == "unknown"
    ):

        if rag_services:

            recommended_service = (
                rag_services[0]
            )


    # -----------------------------------------------------
    # CAUSES
    # -----------------------------------------------------

    likely_causes = []


    for cause in possible_causes:

        if cause:

            likely_causes.append(
                cause
            )


    # Add relevant retrieved defect information

    for defect in rag_defects:

        if defect not in likely_causes:

            likely_causes.append(
                defect
            )


    if not likely_causes:

        likely_causes.append(
            "Cause cannot be confirmed from "
            "the available information alone."
        )


    # -----------------------------------------------------
    # PROFESSIONAL
    # -----------------------------------------------------

    local_services = fused_data.get(
        "local_services",
        []
    )


    professional = None


    if local_services:

        professional = (
            local_services[0]
        )


    # -----------------------------------------------------
    # WEATHER / AIR
    # -----------------------------------------------------

    weather = fused_data.get(
        "weather",
        {}
    )


    air_quality = fused_data.get(
        "air_quality",
        {}
    )


    # -----------------------------------------------------
    # EXPLANATION
    # -----------------------------------------------------

    explanation = (

        f"The uploaded image indicates "
        f"{issue}. "

        f"FixAI retrieved "
        f"{len(fused_knowledge)} relevant "
        f"records from its enriched "
        f"knowledge base. "

    )


    if rag_descriptions:

        explanation += (

            "Related knowledge includes: "
            f"{rag_descriptions[0]}. "
        )


    explanation += (

        "This information is used as "
        "supporting context. The exact "
        "underlying cause may require "
        "an on-site inspection."
    )


    # -----------------------------------------------------
    # ACTION
    # -----------------------------------------------------

    recommended_action = (

        f"Consider contacting a "
        f"{recommended_service} professional "
        "for inspection and repair."
    )


    # -----------------------------------------------------
    # RETURN LOCAL RESULT
    # -----------------------------------------------------

    return {

        "issue":
            issue,

        "category":
            category,

        "severity":
            severity,

        "confidence":
            confidence,

        "likely_causes":
            likely_causes[:5],

        "environmental_factors": {

            "weather":
                weather,

            "air_quality":
                air_quality
        },

        "recommended_action":
            recommended_action,

        "recommended_service":
            recommended_service,

        "professional":
            professional,

        "explanation":
            explanation,

        "warning":
            (
                "External LLM reasoning was "
                "temporarily unavailable. "
                "This fallback result uses "
                "the available image analysis, "
                "retrieved knowledge and live data."
            ),

        "_fused_knowledge_records":
            len(fused_knowledge),

        "_rag_evidence":
            rag_evidence,

        "_fallback_mode":
            True
    }


# =========================================================
# FINAL DIAGNOSIS
# =========================================================

def generate_final_diagnosis(
    fused_data
):

    # =====================================================
    # IMAGE ANALYSIS
    # =====================================================

    image_analysis = fused_data.get(
        "image_analysis",
        {}
    )


    issue = image_analysis.get(
        "issue",
        ""
    )


    category = image_analysis.get(
        "category",
        ""
    )


    element = image_analysis.get(
        "element",
        ""
    )


    recommended_service = image_analysis.get(
        "recommended_service",
        ""
    )


    # =====================================================
    # LOCATION
    # =====================================================

    location_data = fused_data.get(
        "location",
        {}
    )


    location = location_data.get(
        "address",
        ""
    )


    # =====================================================
    # RAG QUERY
    # =====================================================

    rag_query = (

        f"Defect issue: {issue}. "

        f"Category: {category}. "

        f"Element: {element}. "

        f"Recommended service: "
        f"{recommended_service}. "

        f"Location: {location}."
    )


    # =====================================================
    # RETRIEVE RAG RECORDS
    # =====================================================

    try:

        fused_knowledge = (
            retrieve_fused_records(
                rag_query,
                top_k=5
            )
        )

    except Exception as e:

        print(
            f"RAG retrieval failed: {e}"
        )

        fused_knowledge = []


    print(
        f"RAG retrieved "
        f"{len(fused_knowledge)} records."
    )


    # =====================================================
    # PROMPT
    # =====================================================

    prompt = f"""
You are FixAI, an AI household problem
diagnosis assistant for Maharashtra.

Use image analysis, retrieved knowledge
and current live information to produce
a practical diagnosis.

IMAGE ANALYSIS:
{json.dumps(
    image_analysis,
    indent=2,
    default=str
)}

RETRIEVED FUSED KNOWLEDGE:
{json.dumps(
    fused_knowledge,
    indent=2,
    default=str
)}

CURRENT LIVE DATA:
{json.dumps(
    fused_data,
    indent=2,
    default=str
)}

Return ONLY valid JSON with:

{{
    "issue": "",
    "category": "",
    "severity": "",
    "confidence": 0.0,
    "likely_causes": [],
    "environmental_factors": "",
    "recommended_action": "",
    "recommended_service": "",
    "professional": null,
    "explanation": "",
    "warning": ""
}}

Rules:

1. Use image analysis as primary evidence.

2. Use retrieved fused records as supporting
   knowledge.

3. Do not invent information.

4. Do not claim environmental information
   proves causation.

5. Preserve exact professional information
   supplied by local_services.

6. Return valid JSON only.
"""


    # =====================================================
    # TRY GEMINI
    # =====================================================

    try:

        response = client.models.generate_content(

            model=GEMINI_MODEL,

            contents=prompt
        )


        text = clean_json_text(
            response.text
        )


        result = json.loads(
            text
        )


        print(
            "Final reasoning provider: Gemini"
        )


    # =====================================================
    # GEMINI FAILED
    # =====================================================

    except Exception as gemini_error:

        print(
            "Gemini final reasoning unavailable:"
        )

        print(
            str(gemini_error)
        )


        # =================================================
        # TRY OPENROUTER
        # =================================================

        try:

            print(
                "Trying OpenRouter..."
            )


            text = ask_openrouter(
                prompt
            )


            text = clean_json_text(
                text
            )


            result = json.loads(
                text
            )


            print(
                "Final reasoning provider: "
                "OpenRouter"
            )


        # =================================================
        # BOTH FAILED
        # =================================================

        except Exception as openrouter_error:

            print(
                "OpenRouter final reasoning unavailable:"
            )

            print(
                str(openrouter_error)
            )


            print(
                "Using LOCAL RAG fallback."
            )


            # IMPORTANT:
            # fused_data is passed directly here.
            result = build_local_fallback(
                fused_data,
                fused_knowledge
            )


    # =====================================================
    # PROFESSIONAL PRESERVATION
    # =====================================================

    local_services = fused_data.get(
        "local_services",
        []
    )


    if local_services:

        result["professional"] = (
            local_services[0]
        )

    else:

        result["professional"] = None


    # =====================================================
    # TRACEABILITY
    # =====================================================

    result[
        "_fused_knowledge_records"
    ] = len(
        fused_knowledge
    )


    if "_rag_evidence" not in result:

        result[
            "_rag_evidence"
        ] = fused_knowledge


    return result
