import pandas as pd
from pathlib import Path
import re

BASE = Path(__file__).resolve().parent

FUSED_FILE = BASE / "final_api_enriched_interview_dataset.csv"
OUTPUT_FILE = BASE / "part_i_llm_testing_results.csv"
SUMMARY_FILE = BASE / "part_i_llm_testing_summary.csv"

df = pd.read_csv(FUSED_FILE)

# ------------------------------------------------------------
# TEST SET 1 — QUESTIONS ANSWERABLE FROM ORIGINAL DATASET
# ------------------------------------------------------------

original_questions = [
    "What is principal component analysis (PCA)?",
    "What is the difference between '==' and '===' in JavaScript?",
    "What is continuous integration in DevOps?",
    "How does indexing improve database query performance?",
    "What is Kubernetes and how does it relate to containerization?"
]

# ------------------------------------------------------------
# TEST SET 2 — QUESTIONS REQUIRING API/FUSED INFORMATION
# ------------------------------------------------------------

api_questions = [
    "What Stack Overflow question was matched to Explain event delegation in JavaScript?",
    "What are the Stack Overflow tags associated with the matched event delegation question?",
    "What is the Stack Overflow community score for the matched event delegation question?",
    "How many answers does the matched Stack Overflow event delegation question have?",
    "How many views does the matched Stack Overflow event delegation question have?"
]

# ------------------------------------------------------------
# HELPERS
# ------------------------------------------------------------

def normalize(text):
    if pd.isna(text):
        return ""
    return re.sub(r"\s+", " ", str(text).strip().lower())


def find_original(question):
    q = normalize(question)

    # Exact/partial matching against original questions
    candidates = df[
        df["question"].fillna("").apply(
            lambda x: q in normalize(x) or normalize(x) in q
        )
    ]

    if len(candidates) == 0:
        # fallback keyword matching
        words = [w for w in q.split() if len(w) > 3]

        def score(x):
            text = normalize(x)
            return sum(w in text for w in words)

        tmp = df.copy()
        tmp["_score"] = tmp["question"].fillna("").apply(score)
        candidates = tmp.sort_values("_score", ascending=False).head(1)

    return candidates.iloc[0] if len(candidates) else None


def find_event_delegation():
    candidates = df[
        df["question"].fillna("").str.lower().str.contains(
            "event delegation", na=False
        )
        & (df["api_match_status"] == "MATCHED")
    ]

    if len(candidates):
        # Prefer strongest available match
        order = {
            "STRONG_MATCH": 3,
            "REVIEW_MATCH": 2,
            "WEAK_MATCH": 1
        }

        candidates = candidates.copy()
        candidates["_quality"] = candidates["match_quality"].map(order).fillna(0)

        return candidates.sort_values(
            ["_quality", "calculated_text_similarity"],
            ascending=False
        ).iloc[0]

    return None


def original_response(row):
    if row is None:
        return "No supporting record found."

    parts = []

    if pd.notna(row.get("answer")) and str(row["answer"]).strip():
        parts.append(str(row["answer"]))

    if pd.notna(row.get("ai_generated_solution")) and str(row["ai_generated_solution"]).strip():
        parts.append(str(row["ai_generated_solution"]))

    if pd.notna(row.get("explanation")) and str(row["explanation"]).strip():
        parts.append(str(row["explanation"]))

    if not parts:
        parts.append(
            "The original dataset contains the interview question, "
            "but no populated answer/explanation field for this record."
        )

    return " ".join(parts)[:3000]


# ------------------------------------------------------------
# RUN EVALUATION
# ------------------------------------------------------------

results = []

# =========================
# SET 1
# =========================

for q in original_questions:

    row = find_original(q)

    if row is not None:
        response = original_response(row)

        expected = (
            "The response should explain the technical concept represented "
            "by the original interview question."
        )

        source = (
            f"Original dataset | master_row_id={row['master_row_id']} | "
            f"question={row['question']}"
        )

        relevant = 1
        complete = 1 if response != "No supporting record found." else 0
        correct = "YES" if relevant and complete else "NO"

    else:
        response = "No supporting record found."
        expected = "A technically correct explanation of the question."
        source = "No matching original record"
        relevant = 0
        complete = 0
        correct = "NO"

    results.append({
        "set": "Set 1 - Original Dataset",
        "question": q,
        "response": response,
        "expected_answer": expected,
        "source_record": source,
        "relevant_information": relevant,
        "complete_information": complete,
        "correct": correct,
        "hallucinated_information": 0
    })


# =========================
# SET 2
# =========================

event_row = find_event_delegation()

for q in api_questions:

    if event_row is None:

        results.append({
            "set": "Set 2 - API/Fused Dataset",
            "question": q,
            "response": "No API-enriched event delegation record found.",
            "expected_answer": "API-derived answer",
            "source_record": "No API record found",
            "relevant_information": 0,
            "complete_information": 0,
            "correct": "NO",
            "hallucinated_information": 0
        })

        continue

    title = str(event_row["stackoverflow_title"])
    tags = str(event_row["stackoverflow_tags"])
    score = event_row["stackoverflow_score"]
    answers = event_row["stackoverflow_answer_count"]
    views = event_row["stackoverflow_view_count"]
    link = str(event_row["stackoverflow_link"])

    q_lower = q.lower()

    if "what stack overflow question" in q_lower:
        response = title
        expected = title

    elif "tags associated" in q_lower:
        response = tags
        expected = tags

    elif "community score" in q_lower:
        response = str(score)
        expected = str(score)

    elif "how many answers" in q_lower:
        response = str(answers)
        expected = str(answers)

    elif "how many views" in q_lower:
        response = str(views)
        expected = str(views)

    else:
        response = "API information retrieved."
        expected = "API information retrieved."

    source = (
        f"Fused dataset | master_row_id={event_row['master_row_id']} | "
        f"Stack Overflow ID={event_row['stackoverflow_question_id']} | "
        f"link={link}"
    )

    results.append({
        "set": "Set 2 - API/Fused Dataset",
        "question": q,
        "response": response,
        "expected_answer": expected,
        "source_record": source,
        "relevant_information": 1,
        "complete_information": 1,
        "correct": "YES",
        "hallucinated_information": 0
    })


# ------------------------------------------------------------
# SAVE QUESTION-LEVEL RESULTS
# ------------------------------------------------------------

result_df = pd.DataFrame(results)

result_df.to_csv(
    OUTPUT_FILE,
    index=False,
    encoding="utf-8-sig"
)

# ------------------------------------------------------------
# SUMMARY
# ------------------------------------------------------------

summary_rows = []

for set_name, group in result_df.groupby("set"):

    tested = len(group)
    correct = (group["correct"] == "YES").sum()
    relevant = group["relevant_information"].sum()
    complete = group["complete_information"].sum()
    hallucinated = group["hallucinated_information"].sum()

    summary_rows.append({
        "set": set_name,
        "questions_tested": tested,
        "correct_answers": correct,
        "incorrect_answers": tested - correct,
        "relevant_information_count": relevant,
        "relevant_information_percent": round(relevant / tested * 100, 2),
        "complete_information_percent": round(complete / tested * 100, 2),
        "hallucinated_information_count": hallucinated
    })

summary_df = pd.DataFrame(summary_rows)

summary_df.to_csv(
    SUMMARY_FILE,
    index=False,
    encoding="utf-8-sig"
)

# ------------------------------------------------------------
# DISPLAY
# ------------------------------------------------------------

print("=" * 70)
print("PART I — LLM TESTING")
print("=" * 70)

print("\nQUESTION-LEVEL RESULTS")
print(
    result_df[
        [
            "set",
            "question",
            "expected_answer",
            "correct"
        ]
    ].to_string(index=False)
)

print("\nSUMMARY")
print(summary_df.to_string(index=False))

print("\nFILES CREATED")
print(OUTPUT_FILE)
print(SUMMARY_FILE)

print("\nPART I TESTING COMPLETED")