import os
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


# =========================================================
# GEMINI
# =========================================================

if GEMINI_API_KEY:

    client = genai.Client(
        api_key=GEMINI_API_KEY
    )

else:

    client = None


GEMINI_MODEL = "gemini-3.8-flash"


# =========================================================
# OPENROUTER
# =========================================================

OPENROUTER_URL = (
    "https://openrouter.ai/api/v1/chat/completions"
)

OPENROUTER_MODEL = os.getenv(
    "OPENROUTER_MODEL",
    "openrouter/free"
)


# =========================================================
# OPENROUTER REQUEST
# =========================================================

def ask_openrouter(
    prompt
):

    if not OPENROUTER_API_KEY:

        raise RuntimeError(
            "OPENROUTER_API_KEY is not configured."
        )


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

        timeout=30
    )


    if not response.ok:

        raise RuntimeError(
            f"OpenRouter {response.status_code}: "
            f"{response.text[:500]}"
        )


    data = response.json()


    try:

        content = (
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
    ) as exc:

        raise RuntimeError(
            "OpenRouter returned no usable answer."
        ) from exc


    if not content:

        raise RuntimeError(
            "OpenRouter returned empty content."
        )


    return content


# =========================================================
# LOCAL CHAT FALLBACK
# =========================================================

def local_chat_response(
    question,
    fused_data,
    final_result,
    fused_records
):

    q = (
        question
        or ""
    ).lower().strip()


    # =====================================================
    # BASIC DATA
    # =====================================================

    issue = final_result.get(
        "issue",
        fused_data.get(
            "image_analysis",
            {}
        ).get(
            "issue",
            "the reported problem"
        )
    )


    severity = final_result.get(
        "severity",
        "Unknown"
    )


    service = final_result.get(
        "recommended_service",
        "unknown"
    )


    causes = final_result.get(
        "likely_causes",
        []
    )


    action = final_result.get(
        "recommended_action",
        ""
    )


    professional = final_result.get(
        "professional"
    )


    weather = fused_data.get(
        "weather",
        {}
    )


    air_quality = fused_data.get(
        "air_quality",
        {}
    )


    location = fused_data.get(
        "location",
        {}
    )


    # =====================================================
    # PROFESSIONAL QUESTIONS
    # =====================================================

    if any(
        word in q
        for word in [
            "professional",
            "plumber",
            "repairer",
            "who should",
            "contact"
        ]
    ):

        if professional:

            return (
                f"FixAI recommends "
                f"{professional.get('name', 'the listed professional')} "
                f"in {professional.get('area', '')}, "
                f"{professional.get('city', '')}. "
                f"They are listed for "
                f"{professional.get('service_type', service)}, "
                f"with a rating of "
                f"{professional.get('rating', 'N/A')} "
                f"and {professional.get('experience', 'N/A')} years "
                f"of experience. "
                f"The listed price range is "
                f"₹{professional.get('price_range', 'N/A')}."
            )

        return (
            "No suitable local professional was found "
            "in the available data."
        )


    # =====================================================
    # COST QUESTIONS
    # =====================================================

    if any(
        word in q
        for word in [
            "cost",
            "price",
            "expensive",
            "how much",
            "budget"
        ]
    ):

        if professional:

            return (
                f"The available professional listing shows "
                f"a price range of "
                f"₹{professional.get('price_range', 'N/A')}. "
                f"Actual cost can vary depending on the extent "
                f"of damage and the site inspection."
            )

        return (
            "A reliable repair cost is not available "
            "from the current information."
        )


    # =====================================================
    # WEATHER / RAIN QUESTIONS
    # =====================================================

    if any(
        word in q
        for word in [
            "rain",
            "rainfall",
            "humidity",
            "weather",
            "moisture"
        ]
    ):

        temperature = weather.get(
            "temperature",
            "N/A"
        )

        humidity = weather.get(
            "humidity",
            "N/A"
        )

        rainfall = weather.get(
            "precipitation",
            weather.get(
                "rainfall",
                "N/A"
            )
        )


        return (
            f"For the selected location, the available "
            f"weather data shows approximately "
            f"{temperature}°C temperature and "
            f"{humidity}% humidity, with precipitation "
            f"around {rainfall}. "
            f"These conditions may be relevant to moisture-related "
            f"problems, but they do not by themselves prove the cause."
        )


    # =====================================================
    # AIR QUALITY QUESTIONS
    # =====================================================

    if any(
        word in q
        for word in [
            "air quality",
            "aqi",
            "pm2.5",
            "pollution"
        ]
    ):

        if air_quality.get(
            "status"
        ) == "temporarily_unavailable":

            return (
                "Current air-quality data is temporarily "
                "unavailable. The other available FixAI "
                "information can still be used."
            )


        return (
            f"The available air-quality information for the "
            f"selected location includes US AQI "
            f"{air_quality.get('us_aqi', 'N/A')} "
            f"and PM2.5 "
            f"{air_quality.get('pm2_5', 'N/A')}. "
            f"These values provide environmental context but "
            f"do not prove the cause of the building defect."
        )


    # =====================================================
    # SAFETY QUESTIONS
    # =====================================================

    if any(
        word in q
        for word in [
            "dangerous",
            "danger",
            "safe",
            "unsafe",
            "serious"
        ]
    ):

        return (
            f"FixAI has classified the visible issue as "
            f"{severity}. "
            f"An image alone cannot confirm structural safety. "
            f"Because the issue is {issue}, an on-site inspection "
            f"is appropriate when there is significant damage, "
            f"active leakage, falling material or rapid worsening."
        )


    # =====================================================
    # DIY QUESTIONS
    # =====================================================

    if any(
        word in q
        for word in [
            "myself",
            "diy",
            "fix it",
            "repair it myself",
            "temporary"
        ]
    ):

        return (
            f"FixAI recommends: {action} "
            f"For a temporary measure, avoid disturbing loose "
            f"material and address any visible source of water "
            f"only when it can be done safely. "
            f"A professional inspection is recommended for "
            f"the underlying problem."
        )


    # =====================================================
    # CAUSE QUESTIONS
    # =====================================================

    if any(
        word in q
        for word in [
            "cause",
            "why",
            "causing",
            "happen"
        ]
    ):

        if causes:

            return (
                f"The main possible causes identified by FixAI "
                f"include: {', '.join(str(c) for c in causes[:4])}. "
                f"These are possible explanations rather than "
                f"confirmed causes from the image alone."
            )

        return (
            "The exact cause cannot be confirmed from the "
            "available information alone."
        )


    # =====================================================
    # RAG / ADDITIONAL INFORMATION QUESTIONS
    # =====================================================

    if any(
        word in q
        for word in [
            "additional information",
            "beyond the image",
            "consider",
            "retrieved",
            "knowledge",
            "data"
        ]
    ):

        return (
            f"Beyond the visible image, FixAI considered "
            f"the selected location, environmental conditions, "
            f"building-defect knowledge, local professional "
            f"information and {len(fused_records)} relevant "
            f"retrieved knowledge records."
        )


    # =====================================================
    # WHY SERVICE
    # =====================================================

    if any(
        word in q
        for word in [
            "recommend",
            "recommended service",
            "wall repair",
            "repair type"
        ]
    ):

        return (
            f"FixAI recommends {service} based on the visible "
            f"issue and the supporting defect knowledge. "
            f"The recommended action is: {action}"
        )


    # =====================================================
    # LOCATION
    # =====================================================

    if any(
        word in q
        for word in [
            "location",
            "where"
        ]
    ):

        return (
            f"The selected location is "
            f"{location.get('address', 'the selected area')}. "
            f"This location is used to obtain environmental "
            f"conditions and nearby professional information."
        )


    # =====================================================
    # GENERAL RESPONSE
    # =====================================================

    return (
        f"FixAI identified the visible issue as "
        f"{issue} with {severity} severity. "
        f"The recommended service is {service}. "
        f"{action} "
        f"I also used {len(fused_records)} relevant "
        f"knowledge records as supporting context. "
        f"For a precise assessment of the underlying cause, "
        f"an on-site inspection may be required."
    )


# =========================================================
# ASK FIXAI
# =========================================================

def ask_fixai(
    question,
    fused_data,
    final_result,
    chat_history=None
):

    if chat_history is None:

        chat_history = []


    # =====================================================
    # CURRENT DIAGNOSIS
    # =====================================================

    image_analysis = fused_data.get(
        "image_analysis",
        {}
    )


    issue = image_analysis.get(
        "issue",
        final_result.get(
            "issue",
            ""
        )
    )


    category = image_analysis.get(
        "category",
        final_result.get(
            "category",
            ""
        )
    )


    service_type = image_analysis.get(
        "recommended_service",
        final_result.get(
            "recommended_service",
            ""
        )
    )


    element = image_analysis.get(
        "element",
        ""
    )


    # =====================================================
    # RAG
    # =====================================================

    rag_query = (

        f"User question: {question}. "

        f"Current issue: {issue}. "

        f"Category: {category}. "

        f"Element: {element}. "

        f"Recommended service: "
        f"{service_type}."
    )


    try:

        fused_records = retrieve_fused_records(

            rag_query,

            top_k=5
        )

    except Exception as e:

        print(
            f"RAG retrieval failed: {e}"
        )

        fused_records = []


    print(
        f"Chat RAG retrieved "
        f"{len(fused_records)} records."
    )


    # =====================================================
    # CHAT HISTORY
    # =====================================================

    previous_messages = ""

    for message in chat_history[-6:]:

        previous_messages += (
            f"{message.get('role', '')}: "
            f"{message.get('content', '')}\n"
        )


    # =====================================================
    # PROMPT
    # =====================================================

    prompt = f"""
You are FixAI, a household problem assistant
for Maharashtra, India.

Answer the user's question using the current diagnosis,
retrieved knowledge and live data supplied below.

Do not invent information.

CURRENT DIAGNOSIS:
{final_result}

CURRENT LIVE DATA:
{fused_data}

RETRIEVED KNOWLEDGE:
{fused_records}

PREVIOUS CHAT:
{previous_messages}

USER QUESTION:
{question}

Rules:

- Answer directly and naturally.
- Use retrieved knowledge when relevant.
- Use professional details only from supplied data.
- Never invent phone numbers, ratings, prices or experience.
- Weather and air quality are supporting context, not proof of causation.
- Do not claim structural safety from an image alone.
- If information is insufficient, say so.
"""


    # =====================================================
    # TRY GEMINI
    # =====================================================

    if client is not None:

        try:

            response = client.models.generate_content(

                model=GEMINI_MODEL,

                contents=prompt
            )


            answer = (
                response.text
                or ""
            ).strip()


            if answer:

                print(
                    "Chat provider: Gemini"
                )

                return answer


        except Exception as e:

            print(
                f"Gemini chat unavailable: {e}"
            )


    # =====================================================
    # TRY OPENROUTER
    # =====================================================

    try:

        answer = ask_openrouter(
            prompt
        )


        print(
            "Chat provider: OpenRouter"
        )


        return answer


    except Exception as e:

        print(
            f"OpenRouter chat unavailable: {e}"
        )


    # =====================================================
    # LOCAL FALLBACK
    # =====================================================

    print(
        "Chat provider: Local FixAI fallback"
    )


    return local_chat_response(

        question=question,

        fused_data=fused_data,

        final_result=final_result,

        fused_records=fused_records
    )
