import os
from dotenv import load_dotenv

load_dotenv()

# =========================================================
# API KEY CONFIGURATION
# Insert your API keys in .env for each feature below.
# If a feature-specific key is empty, OPENAI_API_KEY is used.
# =========================================================

API_KEYS = {
    # API 1 - Personalized study plan (already integrated)
    "study_plan": os.getenv("OPENAI_API_KEY", ""),

    # API 2 - AI interview question generation
    "question_generation": os.getenv("OPENAI_QUESTIONS_API_KEY", ""),

    # API 3 - AI answer evaluation
    "answer_evaluation": os.getenv("OPENAI_ANSWER_EVAL_API_KEY", ""),

    # API 4 - Post-interview AI feedback summary
    "interview_feedback": os.getenv("OPENAI_FEEDBACK_API_KEY", ""),

    # API 5 - Pre-interview skill gap analysis
    "skill_analysis": os.getenv("OPENAI_SKILL_ANALYSIS_API_KEY", ""),
}


def get_api_key(feature: str) -> str:
    """Return the API key for a feature, falling back to OPENAI_API_KEY."""

    key = API_KEYS.get(feature, "").strip()
    if key:
        return key
    return API_KEYS.get("study_plan", "").strip()


def get_openai_client(feature: str):
    """Create an OpenAI client for the given feature if a key is available."""

    api_key = get_api_key(feature)
    if not api_key:
        return None

    try:
        from openai import OpenAI
        return OpenAI(api_key=api_key)
    except Exception as exc:
        print(f"Notice: Could not initialize OpenAI client for {feature}:", exc)
        return None
