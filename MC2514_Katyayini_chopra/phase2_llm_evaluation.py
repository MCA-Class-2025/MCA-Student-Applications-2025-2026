import os
import json
import time
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from google import genai

from services.fused_rag_service import retrieve_fused_records


# =========================================================
# PATHS
# =========================================================

PROJECT_ROOT = Path(__file__).resolve().parent
ORIGINAL_CSV = PROJECT_ROOT / "data" / "building_defect_knowledge.csv"
FUSED_CSV = PROJECT_ROOT / "data" / "fixai_fused_dataset.csv"
OUTPUT_CSV = PROJECT_ROOT / "output" / "phase2_llm_test_results.csv"

# Use the same model that is already working in your project.
MODEL_NAME = "gemini-3.8-flash"
MAX_RETRIES = 6
RETRY_BASE_SECONDS = 3
BETWEEN_REQUEST_SECONDS = 2


# =========================================================
# GEMINI CLIENT
# =========================================================

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY is not set in .env")

client = genai.Client(api_key=GEMINI_API_KEY)


# =========================================================
# GEMINI TEXT REQUEST WITH 503 RETRY
# =========================================================

def ask_gemini(prompt: str) -> str:
    response = None

    for attempt in range(MAX_RETRIES):
        try:
            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=prompt
            )
            break

        except Exception as e:
            error_text = str(e)

            is_503 = (
                "503" in error_text
                or "UNAVAILABLE" in error_text
            )

            if not is_503:
                raise

            if attempt == MAX_RETRIES - 1:
                raise

            wait_time = RETRY_BASE_SECONDS * (2 ** attempt)
            print(
                f"Gemini temporarily unavailable (503). "
                f"Retrying in {wait_time} seconds..."
            )
            time.sleep(wait_time)

    if response is None:
        raise RuntimeError("Gemini did not return a response.")

    return (response.text or "").strip()


# =========================================================
# CONTEXT FORMATTERS
# =========================================================

def original_context(df: pd.DataFrame) -> str:
    # Only original 5 attributes are exposed to the BEFORE system.
    cols = [
        "work_type",
        "location",
        "element",
        "defect",
        "example_description",
    ]
    return df[cols].to_json(
        orient="records",
        indent=2,
        force_ascii=False
    )


def build_after_context(question: str) -> str:
    records = retrieve_fused_records(question, top_k=5)
    return json.dumps(
        records,
        indent=2,
        default=str,
        ensure_ascii=False
    )


# =========================================================
# BEFORE / AFTER PROMPTS
# =========================================================

def before_prompt(question: str, df: pd.DataFrame) -> str:
    return f"""
You are the BEFORE version of FixAI.

You can use ONLY the original building-defect dataset below.
It contains the original five attributes:
work_type, location, element, defect, example_description.

Do NOT use external knowledge.
Do NOT infer API-derived professional, weather, air-quality,
latitude/longitude, rating, experience, price or service-type
values if they are not explicitly present in the original data.

If the question cannot be answered from the original dataset,
clearly say that the information is not available in the
original dataset.

Question:
{question}

ORIGINAL DATASET:
{original_context(df)}

Answer in 1-3 concise sentences.
"""


def after_prompt(question: str, retrieved_context: str) -> str:
    return f"""
You are the AFTER version of FixAI.

Answer the user's question using the semantically retrieved
records from the Phase-1 fused dataset below.

These records contain the original defect information plus
API-derived geographic, weather, air-quality and professional
attributes.

Use only information supported by the retrieved records.
Do not invent values.

Question:
{question}

RETRIEVED FUSED RECORDS:
{retrieved_context}

Answer in 1-3 concise sentences.
"""


# =========================================================
# TEST QUESTION BUILDER
# =========================================================

def build_tests(fused_df: pd.DataFrame):
    # -----------------------------------------------------
    # SET 1: Answerable from original dataset
    # -----------------------------------------------------
    set1 = [
        {
            "set": "Set 1",
            "type": "Original dataset",
            "question": "How many Water leak records are present in the original dataset?",
            "expected": "6",
            "source": "Original defect dataset: defect = Water leak"
        },
        {
            "set": "Set 1",
            "type": "Original dataset",
            "question": "Which building element appears most frequently in the original dataset?",
            "expected": "Wall (13 records)",
            "source": "Original defect dataset: element distribution"
        },
        {
            "set": "Set 1",
            "type": "Original dataset",
            "question": "How many records have work_type = RC?",
            "expected": "6",
            "source": "Original defect dataset: work_type distribution"
        },
        {
            "set": "Set 1",
            "type": "Original dataset",
            "question": "Which location category occurs most frequently in the original dataset?",
            "expected": "Exterior (10 records)",
            "source": "Original defect dataset: location distribution"
        },
        {
            "set": "Set 1",
            "type": "Original dataset",
            "question": "How many Broken defect records are present in the original dataset?",
            "expected": "1",
            "source": "Original defect dataset: defect = Broken"
        },
    ]

    # -----------------------------------------------------
    # SET 2: Require fused/API-enriched information
    # Build questions from real fused rows so that the
    # expected answers are generated directly from the CSV.
    # -----------------------------------------------------
    chosen = (
        fused_df
        .drop_duplicates(subset=["api_context_city"])
        .head(5)
        .copy()
    )

    set2 = []

    for _, row in chosen.iterrows():
        city = str(row["api_context_city"])
        defect = str(row["defect"])
        element = str(row["element"])

        professional_name = str(row["professional_name"])
        professional_area = str(row["professional_area"])
        professional_phone = str(row["professional_phone"])
        professional_rating = str(row["professional_rating"])
        professional_experience = str(row["professional_experience"])
        professional_price = str(row["professional_price_range"])

        temperature = str(row["weather_temperature"])
        humidity = str(row["weather_humidity"])
        aqi = str(row["air_us_aqi"])
        pm25 = str(row["air_pm2_5"])
        service_type = str(row["service_type"])

        question_type = len(set2)

        if question_type == 0:
            question = (
                f"For the {city} record involving a {defect.lower()} "
                f"on a {element.lower()}, which professional is listed "
                f"and what is the listed price range?"
            )
            expected = (
                f"{professional_name}; price range {professional_price}"
            )
            source = (
                "Fused CSV professional fields for "
                f"api_context_city={city}"
            )

        elif question_type == 1:
            question = (
                f"For the {city} fused record involving a {defect.lower()}, "
                f"what temperature and humidity values were recorded?"
            )
            expected = (
                f"Temperature {temperature}; humidity {humidity}"
            )
            source = (
                "Fused CSV weather fields for "
                f"api_context_city={city}"
            )

        elif question_type == 2:
            question = (
                f"For the {city} fused record involving a {defect.lower()}, "
                f"what US AQI and PM2.5 values were recorded?"
            )
            expected = (
                f"US AQI {aqi}; PM2.5 {pm25}"
            )
            source = (
                "Fused CSV air-quality fields for "
                f"api_context_city={city}"
            )

        elif question_type == 3:
            question = (
                f"For the {city} record involving a {defect.lower()} "
                f"on a {element.lower()}, what service_type is recorded "
                f"in the enriched dataset?"
            )
            expected = service_type
            source = (
                "Fused CSV derived field service_type for "
                f"api_context_city={city}"
            )

        else:
            question = (
                f"For the {city} record involving a {defect.lower()}, "
                f"what rating and experience are listed for the matched professional?"
            )
            expected = (
                f"Rating {professional_rating}; "
                f"experience {professional_experience} years"
            )
            source = (
                "Fused CSV professional fields for "
                f"api_context_city={city}"
            )

        set2.append({
            "set": "Set 2",
            "type": "Fused/API-enriched",
            "question": question,
            "expected": expected,
            "source": source
        })

        if len(set2) == 5:
            break

    # Exactly 5 enriched questions, using five different study cities.
    return set1, set2


# =========================================================
# MAIN EVALUATION
# =========================================================

def main():
    if not ORIGINAL_CSV.exists():
        raise FileNotFoundError(
            f"Original dataset not found: {ORIGINAL_CSV}"
        )

    if not FUSED_CSV.exists():
        raise FileNotFoundError(
            f"Fused dataset not found: {FUSED_CSV}"
        )

    original_df = pd.read_csv(ORIGINAL_CSV)
    fused_df = pd.read_csv(FUSED_CSV)

    set1, set2 = build_tests(fused_df)
    tests = set1 + set2

    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)

    # Resume from an existing partial result file.
    results = []

    if OUTPUT_CSV.exists():
        try:
            existing_df = pd.read_csv(OUTPUT_CSV)
            if "test_no" in existing_df.columns:
                results = existing_df.to_dict("records")
                completed_tests = {
                    int(x)
                    for x in existing_df["test_no"].dropna().tolist()
                }
            else:
                completed_tests = set()
        except Exception:
            completed_tests = set()
    else:
        completed_tests = set()

    print("=" * 70)
    print("FIXAI PHASE 2 - BEFORE / AFTER LLM EVALUATION")
    print("=" * 70)

    if completed_tests:
        print(
            f"Resuming: {len(completed_tests)} test(s) already saved."
        )

    for i, test in enumerate(tests, start=1):

        if i in completed_tests:
            print()
            print(f"[{i}/10] Already completed - skipping.")
            continue

        question = test["question"]

        print()
        print(f"[{i}/10] {test['set']}")
        print(f"QUESTION: {question}")

        # -------------------------------------------------
        # BEFORE
        # -------------------------------------------------
        before = ask_gemini(
            before_prompt(
                question,
                original_df
            )
        )

        print(f"BEFORE: {before}")

        time.sleep(BETWEEN_REQUEST_SECONDS)

        # -------------------------------------------------
        # AFTER
        # -------------------------------------------------
        retrieved = build_after_context(question)

        after = ask_gemini(
            after_prompt(
                question,
                retrieved
            )
        )

        print(f"AFTER:  {after}")

        # -------------------------------------------------
        # SAVE IMMEDIATELY
        # -------------------------------------------------
        results.append({
            "test_no": i,
            "set": test["set"],
            "type": test["type"],
            "question": question,
            "before_response": before,
            "after_response": after,
            "expected_answer": test["expected"],
            "source_record": test["source"],
            "correct_before": "MANUAL_REVIEW",
            "correct_after": "MANUAL_REVIEW",
            "complete_before": "MANUAL_REVIEW",
            "complete_after": "MANUAL_REVIEW",
            "hallucination_before": "MANUAL_REVIEW",
            "hallucination_after": "MANUAL_REVIEW",
        })

        pd.DataFrame(results).sort_values("test_no").to_csv(
            OUTPUT_CSV,
            index=False,
            encoding="utf-8-sig"
        )

    print()
    print("=" * 70)
    print("EVALUATION COMPLETE")
    print("=" * 70)
    print(f"Saved results to: {OUTPUT_CSV}")
    print()
    print(
        "Important: correctness/completeness/hallucination columns "
        "are intentionally left for manual review."
    )


if __name__ == "__main__":
    main()
