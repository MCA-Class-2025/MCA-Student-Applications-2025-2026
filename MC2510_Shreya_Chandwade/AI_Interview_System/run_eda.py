import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

INPUT = Path("final_api_enriched_interview_dataset.csv")
OUT = Path("eda_results")
OUT.mkdir(exist_ok=True)

df = pd.read_csv(INPUT)

print("=" * 60)
print("STAGE 5 — EXPLORATORY DATA ANALYSIS")
print("=" * 60)

# ---------------------------------------------------------
# 1. BASIC DATASET INFORMATION
# ---------------------------------------------------------

basic = pd.DataFrame({
    "Metric": [
        "Total Records",
        "Total Columns",
        "API Candidate Records",
        "API Matched Records",
        "API No-Match Records",
        "Strong Matches",
        "Review Matches",
        "Weak Matches"
    ],
    "Value": [
        len(df),
        len(df.columns),
        df["api_match_status"].notna().sum(),
        df["api_match_status"].isin(["MATCHED"]).sum(),
        df["api_match_status"].isin(
            ["NO_MATCH", "RETRY_NO_MATCH"]
        ).sum(),
        (df["match_quality"] == "STRONG_MATCH").sum(),
        (df["match_quality"] == "REVIEW_MATCH").sum(),
        (df["match_quality"] == "WEAK_MATCH").sum()
    ]
})

basic.to_csv(OUT / "01_basic_dataset_summary.csv", index=False)

print("\nBASIC INFORMATION")
print(basic.to_string(index=False))


# ---------------------------------------------------------
# 2. SOURCE DISTRIBUTION
# ---------------------------------------------------------

source = df["source_dataset"].value_counts()

source.to_csv(OUT / "02_source_distribution.csv")

plt.figure(figsize=(10, 6))
source.plot(kind="bar")
plt.title("Interview Dataset Source Distribution")
plt.xlabel("Source Dataset")
plt.ylabel("Number of Records")
plt.xticks(rotation=45, ha="right")
plt.tight_layout()
plt.savefig(OUT / "02_source_distribution.png", dpi=300)
plt.close()

print("\nSOURCE DISTRIBUTION")
print(source)


# ---------------------------------------------------------
# 3. CATEGORY DISTRIBUTION
# ---------------------------------------------------------

category = df["category"].value_counts()

category.to_csv(OUT / "03_category_distribution.csv")

plt.figure(figsize=(12, 8))
category.sort_values().plot(kind="barh")
plt.title("Interview Question Category Distribution")
plt.xlabel("Number of Questions")
plt.ylabel("Category")
plt.tight_layout()
plt.savefig(OUT / "03_category_distribution.png", dpi=300)
plt.close()

print("\nCATEGORY DISTRIBUTION")
print(category)


# ---------------------------------------------------------
# 4. DIFFICULTY DISTRIBUTION
# ---------------------------------------------------------

difficulty = df["difficulty"].value_counts(dropna=False)

difficulty.to_csv(OUT / "04_difficulty_distribution.csv")

plt.figure(figsize=(8, 5))
difficulty.drop(labels=[float("nan")], errors="ignore").plot(
    kind="bar"
)
plt.title("Interview Question Difficulty Distribution")
plt.xlabel("Difficulty")
plt.ylabel("Number of Questions")
plt.tight_layout()
plt.savefig(OUT / "04_difficulty_distribution.png", dpi=300)
plt.close()

print("\nDIFFICULTY DISTRIBUTION")
print(difficulty)


# ---------------------------------------------------------
# 5. API MATCH STATUS
# ---------------------------------------------------------

api_status = df["api_match_status"].value_counts(dropna=False)

api_status.to_csv(OUT / "05_api_match_status.csv")

plt.figure(figsize=(8, 5))
api_status[api_status.index.notna()].plot(kind="bar")
plt.title("Stack Overflow API Match Status")
plt.xlabel("API Match Status")
plt.ylabel("Number of Records")
plt.tight_layout()
plt.savefig(OUT / "05_api_match_status.png", dpi=300)
plt.close()

print("\nAPI MATCH STATUS")
print(api_status)


# ---------------------------------------------------------
# 6. MATCH QUALITY
# ---------------------------------------------------------

quality = df["match_quality"].value_counts(dropna=False)

quality.to_csv(OUT / "06_match_quality.csv")

quality_plot = quality[quality.index.notna()]

plt.figure(figsize=(8, 5))
quality_plot.plot(kind="bar")
plt.title("Stack Overflow Match Quality")
plt.xlabel("Match Quality")
plt.ylabel("Number of Records")
plt.tight_layout()
plt.savefig(OUT / "06_match_quality.png", dpi=300)
plt.close()

print("\nMATCH QUALITY")
print(quality)


# ---------------------------------------------------------
# 7. ANSWERED VS UNANSWERED
# ---------------------------------------------------------

api_df = df[df["api_match_status"].isin(
    ["MATCHED"]
)].copy()

answered = api_df[
    "stackoverflow_is_answered"
].value_counts(dropna=False)

answered.to_csv(OUT / "07_answered_vs_unanswered.csv")

plt.figure(figsize=(8, 5))
answered.plot(kind="bar")
plt.title("Stack Overflow Matched Questions: Answered vs Unanswered")
plt.xlabel("Answered")
plt.ylabel("Number of Questions")
plt.tight_layout()
plt.savefig(OUT / "07_answered_vs_unanswered.png", dpi=300)
plt.close()

print("\nANSWERED VS UNANSWERED")
print(answered)


# ---------------------------------------------------------
# 8. STACK OVERFLOW SCORE DISTRIBUTION
# ---------------------------------------------------------

score = pd.to_numeric(
    api_df["stackoverflow_score"],
    errors="coerce"
).dropna()

print("\nSTACK OVERFLOW SCORE")
print(score.describe())

score.describe().to_csv(
    OUT / "08_score_statistics.csv"
)

plt.figure(figsize=(9, 5))
plt.hist(score, bins=20)
plt.title("Stack Overflow Score Distribution")
plt.xlabel("Stack Overflow Score")
plt.ylabel("Number of Questions")
plt.tight_layout()
plt.savefig(OUT / "08_score_distribution.png", dpi=300)
plt.close()


# ---------------------------------------------------------
# 9. ANSWER COUNT DISTRIBUTION
# ---------------------------------------------------------

answers = pd.to_numeric(
    api_df["stackoverflow_answer_count"],
    errors="coerce"
).dropna()

print("\nANSWER COUNT")
print(answers.describe())

answers.describe().to_csv(
    OUT / "09_answer_count_statistics.csv"
)

plt.figure(figsize=(9, 5))
plt.hist(answers, bins=20)
plt.title("Stack Overflow Answer Count Distribution")
plt.xlabel("Number of Answers")
plt.ylabel("Number of Questions")
plt.tight_layout()
plt.savefig(OUT / "09_answer_count_distribution.png", dpi=300)
plt.close()


# ---------------------------------------------------------
# 10. VIEW COUNT DISTRIBUTION
# ---------------------------------------------------------

views = pd.to_numeric(
    api_df["stackoverflow_view_count"],
    errors="coerce"
).dropna()

print("\nVIEW COUNT")
print(views.describe())

views.describe().to_csv(
    OUT / "10_view_count_statistics.csv"
)

plt.figure(figsize=(9, 5))
plt.hist(views, bins=20)
plt.title("Stack Overflow View Count Distribution")
plt.xlabel("View Count")
plt.ylabel("Number of Questions")
plt.tight_layout()
plt.savefig(OUT / "10_view_count_distribution.png", dpi=300)
plt.close()


# ---------------------------------------------------------
# 11. API MATCH SCORE
# ---------------------------------------------------------

match_score = pd.to_numeric(
    api_df["api_match_score"],
    errors="coerce"
).dropna()

print("\nAPI MATCH SCORE")
print(match_score.describe())

match_score.describe().to_csv(
    OUT / "11_api_match_score_statistics.csv"
)

plt.figure(figsize=(9, 5))
plt.hist(match_score, bins=20)
plt.title("API Match Score Distribution")
plt.xlabel("API Match Score")
plt.ylabel("Number of Records")
plt.tight_layout()
plt.savefig(OUT / "11_api_match_score_distribution.png", dpi=300)
plt.close()


# ---------------------------------------------------------
# 12. TEXT SIMILARITY
# ---------------------------------------------------------

similarity = pd.to_numeric(
    api_df["calculated_text_similarity"],
    errors="coerce"
).dropna()

print("\nTEXT SIMILARITY")
print(similarity.describe())

similarity.describe().to_csv(
    OUT / "12_text_similarity_statistics.csv"
)

plt.figure(figsize=(9, 5))
plt.hist(similarity, bins=20)
plt.title("Question–Stack Overflow Text Similarity")
plt.xlabel("Similarity Score")
plt.ylabel("Number of Records")
plt.tight_layout()
plt.savefig(OUT / "12_text_similarity_distribution.png", dpi=300)
plt.close()


# ---------------------------------------------------------
# 13. MISSING VALUE ANALYSIS
# ---------------------------------------------------------

missing = pd.DataFrame({
    "Column": df.columns,
    "Missing_Count": df.isna().sum(),
    "Missing_Percentage": (
        df.isna().sum() / len(df) * 100
    ).round(2)
})

missing = missing.sort_values(
    "Missing_Percentage",
    ascending=False
)

missing.to_csv(
    OUT / "13_missing_value_analysis.csv",
    index=False
)

print("\nTOP MISSING-VALUE COLUMNS")
print(missing.head(15).to_string(index=False))


# ---------------------------------------------------------
# 14. API FIELD COMPLETENESS
# ---------------------------------------------------------

api_columns = [
    "stackoverflow_question_id",
    "stackoverflow_title",
    "stackoverflow_tags",
    "stackoverflow_score",
    "stackoverflow_answer_count",
    "stackoverflow_is_answered",
    "stackoverflow_view_count",
    "stackoverflow_accepted_answer",
    "stackoverflow_link",
    "api_match_status",
    "api_match_score",
    "api_retrieved_date"
]

api_quality = pd.DataFrame({
    "API_Field": api_columns,
    "Filled_Count": [
        df[c].notna().sum()
        for c in api_columns
    ],
    "Missing_Count": [
        df[c].isna().sum()
        for c in api_columns
    ]
})

api_quality.to_csv(
    OUT / "14_api_field_completeness.csv",
    index=False
)

print("\nAPI FIELD COMPLETENESS")
print(api_quality.to_string(index=False))


# ---------------------------------------------------------
# 15. TOP STACK OVERFLOW TAGS
# ---------------------------------------------------------

tags = []

for value in api_df["stackoverflow_tags"].dropna():
    value = str(value)

    # Handle common formats
    value = value.replace("<", "").replace(">", ",")

    for tag in value.split(","):
        tag = tag.strip()

        if tag:
            tags.append(tag)

top_tags = pd.Series(tags).value_counts().head(20)

top_tags.to_csv(
    OUT / "15_top_stackoverflow_tags.csv"
)

plt.figure(figsize=(10, 7))
top_tags.sort_values().plot(kind="barh")
plt.title("Top Stack Overflow Technical Tags")
plt.xlabel("Frequency")
plt.ylabel("Tag")
plt.tight_layout()
plt.savefig(
    OUT / "15_top_stackoverflow_tags.png",
    dpi=300
)
plt.close()

print("\nTOP STACK OVERFLOW TAGS")
print(top_tags)


# ---------------------------------------------------------
# 16. CATEGORY VS API MATCH
# ---------------------------------------------------------

category_api = pd.crosstab(
    df["category"],
    df["api_match_status"]
)

category_api.to_csv(
    OUT / "16_category_vs_api_match.csv"
)

print("\nCATEGORY VS API MATCH")
print(category_api)


# ---------------------------------------------------------
# 17. DIFFICULTY VS MATCH QUALITY
# ---------------------------------------------------------

difficulty_quality = pd.crosstab(
    df["difficulty"],
    df["match_quality"]
)

difficulty_quality.to_csv(
    OUT / "17_difficulty_vs_match_quality.csv"
)

print("\nDIFFICULTY VS MATCH QUALITY")
print(difficulty_quality)


# ---------------------------------------------------------
# 18. FINAL EDA SUMMARY
# ---------------------------------------------------------

matched = (df["api_match_status"] == "MATCHED").sum()
candidates = df["api_match_status"].notna().sum()

summary = pd.DataFrame({
    "Metric": [
        "Total dataset records",
        "Total dataset columns",
        "API candidates",
        "API matched",
        "API no-match/retry-no-match",
        "API match rate",
        "Strong matches",
        "Review matches",
        "Weak matches",
        "Records without API enrichment"
    ],
    "Value": [
        len(df),
        len(df.columns),
        candidates,
        matched,
        df["api_match_status"].isin(
            ["NO_MATCH", "RETRY_NO_MATCH"]
        ).sum(),
        round(matched / candidates * 100, 2)
        if candidates else 0,
        (df["match_quality"] == "STRONG_MATCH").sum(),
        (df["match_quality"] == "REVIEW_MATCH").sum(),
        (df["match_quality"] == "WEAK_MATCH").sum(),
        df["api_match_status"].isna().sum()
    ]
})

summary.to_csv(
    OUT / "FINAL_EDA_SUMMARY.csv",
    index=False
)

print("\n" + "=" * 60)
print("EDA COMPLETED")
print("=" * 60)
print(summary.to_string(index=False))
print("\nAll results saved inside:")
print(OUT.resolve())