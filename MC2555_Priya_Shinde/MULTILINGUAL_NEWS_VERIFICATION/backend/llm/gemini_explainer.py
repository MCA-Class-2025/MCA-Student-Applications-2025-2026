from pathlib import Path
import os

from dotenv import load_dotenv
from google import genai


# ============================================================
# PROJECT PATH
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

ENV_FILE = PROJECT_ROOT / ".env"

load_dotenv(ENV_FILE)


# ============================================================
# GEMINI CONFIGURATION
# ============================================================

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise RuntimeError(
        "GEMINI_API_KEY was not found in the project .env file."
    )


MODEL_NAME = "gemini-3.7-flash"


# ============================================================
# GEMINI CLIENT
# ============================================================

client = genai.Client(
    api_key=GEMINI_API_KEY
)


# ============================================================
# TEST / EXPLANATION FUNCTION
# ============================================================

def generate_explanation(claim, verdict, ml_prediction,
                         ml_confidence, evidence_score,
                         evidence_status):

    prompt = f"""
You are an AI explanation assistant for a multilingual
news verification system.

Your job is to explain the verification result clearly.

IMPORTANT RULES:

1. Do NOT invent facts.
2. Do NOT add evidence that was not provided.
3. Do NOT perform a new web search.
4. Use ONLY the information provided below.
5. Do NOT change the system verdict.
6. Explain the result in simple professional language.

CLAIM:
{claim}

SYSTEM VERDICT:
{verdict}

ML PREDICTION:
{ml_prediction}

ML CONFIDENCE:
{ml_confidence}%

EVIDENCE SCORE:
{evidence_score}%

EVIDENCE STATUS:
{evidence_status}

Write a concise explanation containing:

- What the system concluded.
- Why the system reached that conclusion.
- Whether the available evidence is strong, weak, or inconclusive.

Do not use headings.
Keep the explanation between 2 and 4 sentences.
"""

    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=prompt
    )

    return response.text.strip()


# ============================================================
# DIRECT TEST
# ============================================================

if __name__ == "__main__":

    print("\n========================================")
    print(" GEMINI NEWS VERIFICATION TEST")
    print("========================================")

    test_claim = (
        "India beat Sri Lanka by 165 runs "
        "in the first Test in Galle."
    )

    explanation = generate_explanation(
        claim=test_claim,
        verdict="Likely Real",
        ml_prediction="Real",
        ml_confidence=55.28,
        evidence_score=99.73,
        evidence_status="Strongly Supporting"
    )

    print("\nGemini Explanation:")
    print("----------------------------------------")
    print(explanation)
    print("----------------------------------------")