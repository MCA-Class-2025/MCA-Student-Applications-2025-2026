import pandas as pd
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

BASE = Path(__file__).resolve().parent
DATA_FILE = BASE / "final_api_enriched_interview_dataset.csv"

# Retrieval settings
TOP_K = 3
MIN_SIMILARITY = 0.30
ALLOWED_QUALITY = {"STRONG_MATCH", "REVIEW_MATCH"}

df = pd.read_csv(DATA_FILE)

# Normalize fields
text_cols = [
    "question", "category", "skill", "programming_language",
    "stackoverflow_title", "stackoverflow_tags", "stackoverflow_link",
    "match_quality"
]
for col in text_cols:
    if col in df.columns:
        df[col] = df[col].fillna("").astype(str)

# -----------------------------
# BEFORE API
# -----------------------------
before_df = df.copy()

# -----------------------------
# AFTER API
# Only validated MATCHED records.
# Remove duplicate question/API pairs.
# Remove weak matches and low-similarity results.
# -----------------------------
api_df = df[df["api_match_status"] == "MATCHED"].copy()

api_df["calculated_text_similarity"] = pd.to_numeric(
    api_df["calculated_text_similarity"], errors="coerce"
).fillna(0)

api_df = api_df[
    api_df["match_quality"].isin(ALLOWED_QUALITY)
    & (api_df["calculated_text_similarity"] >= MIN_SIMILARITY)
].copy()

# Remove repeated question + Stack Overflow title pairs.
api_df = api_df.drop_duplicates(
    subset=["question", "stackoverflow_title"],
    keep="first"
).reset_index(drop=True)

api_df["search_text"] = (
    api_df["question"] + " " +
    api_df["category"] + " " +
    api_df["skill"] + " " +
    api_df["stackoverflow_title"] + " " +
    api_df["stackoverflow_tags"]
)

if len(api_df) == 0:
    raise ValueError("No validated API records remain after filtering.")

vectorizer = TfidfVectorizer(
    stop_words="english",
    ngram_range=(1, 2)
)
matrix = vectorizer.fit_transform(api_df["search_text"])


def retrieve_enriched_context(user_question, top_k=TOP_K):
    """Retrieve unique, validated, relevant API context."""
    query_vector = vectorizer.transform([user_question])
    scores = cosine_similarity(query_vector, matrix)[0]

    ranked = scores.argsort()[::-1]

    results = []
    seen_keys = set()

    for idx in ranked:
        row = api_df.iloc[idx]
        similarity = float(scores[idx])

        if similarity < MIN_SIMILARITY:
            continue

        key = (
            str(row["question"]).strip().lower(),
            str(row["stackoverflow_title"]).strip().lower()
        )

        if key in seen_keys:
            continue

        seen_keys.add(key)

        results.append({
            "question": row["question"],
            "category": row["category"],
            "skill": row["skill"],
            "difficulty": row["difficulty"],
            "match_quality": row["match_quality"],
            "calculated_text_similarity": row["calculated_text_similarity"],
            "stackoverflow_title": row["stackoverflow_title"],
            "stackoverflow_tags": row["stackoverflow_tags"],
            "stackoverflow_score": row["stackoverflow_score"],
            "stackoverflow_answer_count": row["stackoverflow_answer_count"],
            "stackoverflow_is_answered": row["stackoverflow_is_answered"],
            "stackoverflow_view_count": row["stackoverflow_view_count"],
            "stackoverflow_accepted_answer": row["stackoverflow_accepted_answer"],
            "stackoverflow_link": row["stackoverflow_link"],
            "retrieval_similarity": round(similarity, 4)
        })

        if len(results) >= top_k:
            break

    return results


def build_before_context(user_question):
    """Original-dataset context before API enrichment."""
    matches = before_df[
        before_df["question"].str.lower().str.strip()
        == user_question.lower().strip()
    ]

    if matches.empty:
        return {
            "question": user_question,
            "category": "",
            "skill": "",
            "difficulty": "",
            "external_technical_context": "Not available"
        }

    row = matches.iloc[0]

    return {
        "question": row["question"],
        "category": row["category"],
        "skill": row["skill"],
        "difficulty": row["difficulty"],
        "external_technical_context": "Not available"
    }


def build_llm_prompt(user_question, results):
    context = "\n\n".join(
        f"""Interview question: {r['question']}
Category: {r['category']}
Skill: {r['skill']}
Difficulty: {r['difficulty']}
Match quality: {r['match_quality']}
Text similarity: {r['calculated_text_similarity']}
Stack Overflow title: {r['stackoverflow_title']}
Tags: {r['stackoverflow_tags']}
Score: {r['stackoverflow_score']}
Answers: {r['stackoverflow_answer_count']}
Answered: {r['stackoverflow_is_answered']}
Views: {r['stackoverflow_view_count']}
Accepted-answer available: {r['stackoverflow_accepted_answer']}
External source: {r['stackoverflow_link']}"""
        for r in results
    )

    return f"""You are an AI Interview Preparation Assistant.

Candidate question:
{user_question}

Use the original interview dataset together with the validated API-enriched
technical context below. The Stack Overflow information is supporting
context only; it is not the candidate's answer.

ENRICHED CONTEXT:
{context}

Generate an interview-ready response containing:
1. Simple definition
2. Key technical points
3. Short example
4. Interview tip
"""


def create_before_after_report(user_question, results):
    before = build_before_context(user_question)

    rows = [
        ["Interview question", before["question"], user_question],
        ["Category", before["category"], results[0]["category"] if results else "No API context"],
        ["Skill", before["skill"], results[0]["skill"] if results else "No API context"],
        ["Difficulty", before["difficulty"], results[0]["difficulty"] if results else "No API context"],
        ["External technical context", "Not available", "Available"],
        ["Stack Overflow title", "Not available", results[0]["stackoverflow_title"] if results else "Not available"],
        ["Technical tags", "Not available", results[0]["stackoverflow_tags"] if results else "Not available"],
        ["Community score", "Not available", results[0]["stackoverflow_score"] if results else "Not available"],
        ["Answer count", "Not available", results[0]["stackoverflow_answer_count"] if results else "Not available"],
        ["Answered status", "Not available", results[0]["stackoverflow_is_answered"] if results else "Not available"],
        ["View count", "Not available", results[0]["stackoverflow_view_count"] if results else "Not available"],
        ["Accepted answer", "Not available", results[0]["stackoverflow_accepted_answer"] if results else "Not available"],
        ["Text similarity", "Not available", results[0]["calculated_text_similarity"] if results else "Not available"],
        ["Match quality", "Not available", results[0]["match_quality"] if results else "Not available"],
        ["External reference", "Not available", results[0]["stackoverflow_link"] if results else "Not available"],
    ]

    report = pd.DataFrame(rows, columns=["Feature", "Before API", "After API"])
    report.to_csv(BASE / "before_after_api_enrichment.csv", index=False)

    summary = pd.DataFrame([{
        "total_dataset_records": len(df),
        "api_candidates": int(df["api_match_status"].notna().sum()),
        "validated_api_matches": int((df["api_match_status"] == "MATCHED").sum()),
        "usable_after_deduplication_and_filtering": len(api_df),
        "retrieved_context_records": len(results),
        "minimum_similarity_threshold": MIN_SIMILARITY,
        "weak_matches_excluded": "YES",
        "duplicate_question_api_pairs_removed": "YES"
    }])

    summary.to_csv(BASE / "llm_before_after_summary.csv", index=False)

    return report


if __name__ == "__main__":
    print("=" * 75)
    print("FINAL LLM ENRICHMENT DEMONSTRATION")
    print("=" * 75)
    print(f"Original dataset records: {len(df)}")
    print(f"API MATCHED records: {(df['api_match_status'] == 'MATCHED').sum()}")
    print(f"Usable API records after quality filter: {len(api_df)}")
    print(f"Minimum retrieval similarity: {MIN_SIMILARITY}")
    print("Weak matches excluded: YES")
    print("Duplicate question/API pairs removed: YES")
    print()

    user_question = input(
        "Enter an interview question (Enter = event delegation example): "
    ).strip()

    if not user_question:
        user_question = "Explain event delegation in JavaScript."

    results = retrieve_enriched_context(user_question)

    print("\n--- FINAL FILTERED RETRIEVED CONTEXT ---")

    if not results:
        print("No sufficiently relevant validated API context found.")
    else:
        for i, r in enumerate(results, 1):
            print(f"\n{i}. {r['question']}")
            print(f"   Category: {r['category']}")
            print(f"   Difficulty: {r['difficulty']}")
            print(f"   Match quality: {r['match_quality']}")
            print(f"   Similarity: {r['retrieval_similarity']}")
            print(f"   Stack Overflow: {r['stackoverflow_title']}")
            print(f"   Tags: {r['stackoverflow_tags']}")
            print(f"   Score: {r['stackoverflow_score']}")
            print(f"   Answers: {r['stackoverflow_answer_count']}")
            print(f"   Link: {r['stackoverflow_link']}")

    report = create_before_after_report(user_question, results)

    prompt = build_llm_prompt(user_question, results) if results else (
        f"Candidate question: {user_question}\n\n"
        "No sufficiently relevant validated API context was retrieved."
    )

    prompt_file = BASE / "llm_ready_enriched_prompt.txt"
    prompt_file.write_text(prompt, encoding="utf-8")

    print("\n--- BEFORE VS AFTER ---")
    print(report.to_string(index=False))

    print("\n--- FILES CREATED ---")
    print(BASE / "before_after_api_enrichment.csv")
    print(BASE / "llm_before_after_summary.csv")
    print(prompt_file)
    print("\nLLM enrichment demonstration completed.")
