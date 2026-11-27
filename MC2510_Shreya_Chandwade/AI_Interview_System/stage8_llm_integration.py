import pandas as pd
from pathlib import Path

BASE = Path("C:/AI_Interview_System")

INPUT = BASE / "final_api_enriched_interview_dataset.csv"
OUT = BASE / "stage8_llm_results"

OUT.mkdir(exist_ok=True)

df = pd.read_csv(INPUT)

print("=" * 70)
print("STAGE 8 — LLM INTEGRATION ANALYSIS")
print("=" * 70)

# ---------------------------------------------------------
# 1. SELECT HIGH-QUALITY API ENRICHED QUESTIONS
# ---------------------------------------------------------

enriched = df[
    df["match_quality"].isin(
        ["STRONG_MATCH", "REVIEW_MATCH"]
    )
].copy()

print("\nHigh-quality enriched records:", len(enriched))

# ---------------------------------------------------------
# 2. LLM-READY DATASET
# ---------------------------------------------------------

llm_columns = [
    "master_row_id",
    "job_role",
    "category",
    "skill",
    "programming_language",
    "difficulty",
    "question",
    "answer",
    "expected_topics",
    "stackoverflow_title",
    "stackoverflow_tags",
    "stackoverflow_score",
    "stackoverflow_answer_count",
    "stackoverflow_is_answered",
    "stackoverflow_view_count",
    "stackoverflow_link",
    "calculated_text_similarity",
    "match_quality"
]

llm_columns = [
    c for c in llm_columns
    if c in enriched.columns
]

llm_ready = enriched[llm_columns].copy()

llm_ready.to_csv(
    OUT / "llm_ready_enriched_questions.csv",
    index=False
)

print("LLM-ready records:", len(llm_ready))


# ---------------------------------------------------------
# 3. QUESTION GENERATION INFORMATION
# ---------------------------------------------------------

question_generation = enriched.groupby(
    ["job_role", "difficulty"]
).size().reset_index(
    name="available_questions"
)

question_generation.to_csv(
    OUT / "01_question_generation_resources.csv",
    index=False
)

print("\nQuestion generation resources:")
print(question_generation.head(20).to_string(index=False))


# ---------------------------------------------------------
# 4. SKILL/TOPIC ENRICHMENT
# ---------------------------------------------------------

skill_enrichment = enriched[
    [
        "category",
        "skill",
        "stackoverflow_tags"
    ]
].dropna(
    subset=["stackoverflow_tags"]
)

skill_enrichment.to_csv(
    OUT / "02_skill_topic_enrichment.csv",
    index=False
)


# ---------------------------------------------------------
# 5. QUALITY FILTER FOR LLM
# ---------------------------------------------------------

# Recommended records for reliable retrieval
recommended = enriched[
    enriched["match_quality"] == "STRONG_MATCH"
].copy()

recommended.to_csv(
    OUT / "03_high_confidence_llm_knowledge.csv",
    index=False
)

print("\nHigh-confidence records:", len(recommended))


# ---------------------------------------------------------
# 6. CREATE LLM CONTEXT
# ---------------------------------------------------------

def create_context(row):

    context = f"""
Interview Question:
{row.get('question', '')}

Category:
{row.get('category', '')}

Skill:
{row.get('skill', '')}

Difficulty:
{row.get('difficulty', '')}

Related Stack Overflow Question:
{row.get('stackoverflow_title', '')}

Stack Overflow Tags:
{row.get('stackoverflow_tags', '')}

Community Score:
{row.get('stackoverflow_score', '')}

Answer Count:
{row.get('stackoverflow_answer_count', '')}

Answered:
{row.get('stackoverflow_is_answered', '')}

Popularity/View Count:
{row.get('stackoverflow_view_count', '')}

Text Similarity:
{row.get('calculated_text_similarity', '')}

Match Quality:
{row.get('match_quality', '')}
"""

    return context.strip()


recommended["llm_context"] = recommended.apply(
    create_context,
    axis=1
)

recommended[
    [
        "master_row_id",
        "question",
        "llm_context"
    ]
].to_csv(
    OUT / "04_llm_context_data.csv",
    index=False
)


# ---------------------------------------------------------
# 7. LLM USE CASES
# ---------------------------------------------------------

use_cases = pd.DataFrame({
    "LLM_Function": [
        "Question Generation",
        "Question Retrieval",
        "Answer Evaluation",
        "Feedback Generation",
        "Skill Gap Analysis",
        "Personalized Study Plan",
        "Difficulty-Based Interview",
        "Topic-Based Interview"
    ],

    "Before_API": [
        "Generate questions from original dataset",
        "Retrieve using original question/category information",
        "Evaluate candidate answer",
        "Generate feedback from candidate answer",
        "Identify gaps from candidate performance",
        "Create study plan from performance",
        "Use Easy/Medium/Hard labels",
        "Use existing category/skill"
    ],

    "After_API": [
        "Generate questions with additional technical context",
        "Retrieve related community-validated technical content",
        "Use related technical context during evaluation",
        "Provide richer technical feedback",
        "Connect weak skills with related technical topics",
        "Recommend related topics and resources",
        "Combine difficulty with API relevance",
        "Use Stack Overflow technical tags"
    ]
})

use_cases.to_csv(
    OUT / "05_llm_before_after_use_cases.csv",
    index=False
)


# ---------------------------------------------------------
# 8. EXAMPLE LLM PROMPT
# ---------------------------------------------------------

if len(recommended) > 0:

    row = recommended.iloc[0]

    prompt = f"""
You are an AI technical interviewer.

Use the following validated interview knowledge:

Question:
{row['question']}

Category:
{row['category']}

Skill:
{row['skill']}

Difficulty:
{row['difficulty']}

Related technical topic:
{row['stackoverflow_title']}

Stack Overflow tags:
{row['stackoverflow_tags']}

Community score:
{row['stackoverflow_score']}

Answer count:
{row['stackoverflow_answer_count']}

Text similarity:
{row['calculated_text_similarity']}

Match quality:
{row['match_quality']}

Task:
1. Ask the candidate this interview question.
2. Evaluate the candidate's answer.
3. Check technical correctness.
4. Identify missing concepts.
5. Give improvement suggestions.
6. Recommend related topics for revision.

Do not treat Stack Overflow metadata as the candidate's answer.
Use it only as supporting technical context.
"""

    with open(
        OUT / "06_example_llm_prompt.txt",
        "w",
        encoding="utf-8"
    ) as f:
        f.write(prompt)

    print("\nExample LLM prompt created.")


# ---------------------------------------------------------
# 9. FINAL INTEGRATION SUMMARY
# ---------------------------------------------------------

summary = pd.DataFrame({
    "Metric": [
        "Total Dataset Records",
        "Total Dataset Columns",
        "API-Enriched Records",
        "Strong Matches",
        "Review Matches",
        "LLM Recommended Records",
        "LLM Context Fields Added"
    ],

    "Value": [
        len(df),
        len(df.columns),
        df["api_match_status"].notna().sum(),
        (df["match_quality"] == "STRONG_MATCH").sum(),
        (df["match_quality"] == "REVIEW_MATCH").sum(),
        len(recommended),
        8
    ]
})

summary.to_csv(
    OUT / "07_llm_integration_summary.csv",
    index=False
)

print("\n" + "=" * 70)
print("LLM INTEGRATION COMPLETED")
print("=" * 70)

print(summary.to_string(index=False))

print("\nOutput folder:")
print(OUT.resolve())

print("\nFiles created:")

for file in sorted(OUT.iterdir()):
    print(" -", file.name)