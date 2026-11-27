import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

BASE = Path("C:/AI_Interview_System")
INPUT = BASE / "final_api_enriched_interview_dataset.csv"
OUT = BASE / "stage7_results"

OUT.mkdir(exist_ok=True)

df = pd.read_csv(INPUT)

print("=" * 65)
print("STAGE 7 — BEFORE VS AFTER API ENRICHMENT")
print("=" * 65)

# ---------------------------------------------------------
# BEFORE ENRICHMENT
# Original dataset information
# ---------------------------------------------------------

before = {
    "Total Records": len(df),
    "Total Columns": 17,
    "Question Information": "Question, category, skill, difficulty",
    "External Technical Information": "Not available",
    "Community Validation": "Not available",
    "Technical Tags": "Not available",
    "Answer Availability": "Not available",
    "Popularity Information": "Not available",
    "Similarity Score": "Not available"
}

# ---------------------------------------------------------
# AFTER ENRICHMENT
# ---------------------------------------------------------

api_candidates = df[df["api_match_status"].notna()].copy()
matched = df[df["api_match_status"] == "MATCHED"].copy()

after = {
    "Total Records": len(df),
    "Total Columns": len(df.columns),
    "API Candidate Records": len(api_candidates),
    "API Matched Records": len(matched),
    "API Match Rate (%)": round(
        len(matched) / len(api_candidates) * 100, 2
    ),
    "Answered Stack Overflow Questions": int(
        matched["stackoverflow_is_answered"].sum()
    ),
    "Strong Matches": int(
        (df["match_quality"] == "STRONG_MATCH").sum()
    ),
    "Review Matches": int(
        (df["match_quality"] == "REVIEW_MATCH").sum()
    ),
    "Weak Matches": int(
        (df["match_quality"] == "WEAK_MATCH").sum()
    ),
    "Technical Tags Available": int(
        matched["stackoverflow_tags"].notna().sum()
    ),
    "Popularity/View Information": int(
        matched["stackoverflow_view_count"].notna().sum()
    )
}

# ---------------------------------------------------------
# SAVE BEFORE / AFTER TABLE
# ---------------------------------------------------------

comparison = pd.DataFrame([
    {
        "Feature": "Dataset Records",
        "Before API": len(df),
        "After API": len(df),
        "Change": "Same records; enrichment added"
    },
    {
        "Feature": "Dataset Columns",
        "Before API": 17,
        "After API": len(df.columns),
        "Change": f"+{len(df.columns)-17} enrichment/validation fields"
    },
    {
        "Feature": "External Technical Information",
        "Before API": "No",
        "After API": "Yes",
        "Change": "Added"
    },
    {
        "Feature": "Stack Overflow Technical Tags",
        "Before API": "No",
        "After API": "Yes",
        "Change": "Added"
    },
    {
        "Feature": "Community Answers",
        "Before API": "No",
        "After API": "Yes",
        "Change": "Added for matched questions"
    },
    {
        "Feature": "Question Popularity",
        "Before API": "No",
        "After API": "Yes",
        "Change": "View counts added"
    },
    {
        "Feature": "Community Score",
        "Before API": "No",
        "After API": "Yes",
        "Change": "Score added"
    },
    {
        "Feature": "Text Similarity",
        "Before API": "No",
        "After API": "Yes",
        "Change": "Similarity calculated"
    },
    {
        "Feature": "Match Quality",
        "Before API": "No",
        "After API": "Yes",
        "Change": "Strong/Review/Weak classification"
    }
])

comparison.to_csv(
    OUT / "01_before_vs_after.csv",
    index=False
)

print("\nBEFORE VS AFTER")
print(comparison.to_string(index=False))


# ---------------------------------------------------------
# API ENRICHMENT STATISTICS
# ---------------------------------------------------------

stats = pd.DataFrame({
    "Metric": [
        "Total Dataset Records",
        "API Candidates",
        "Matched",
        "No Match",
        "Match Rate (%)",
        "Strong Match",
        "Review Match",
        "Weak Match",
        "Answered Matches",
        "Unanswered Matches"
    ],
    "Value": [
        len(df),
        len(api_candidates),
        len(matched),
        len(api_candidates) - len(matched),
        round(len(matched) / len(api_candidates) * 100, 2),
        (df["match_quality"] == "STRONG_MATCH").sum(),
        (df["match_quality"] == "REVIEW_MATCH").sum(),
        (df["match_quality"] == "WEAK_MATCH").sum(),
        matched["stackoverflow_is_answered"].sum(),
        (~matched["stackoverflow_is_answered"]).sum()
    ]
})

stats.to_csv(
    OUT / "02_api_enrichment_statistics.csv",
    index=False
)

print("\nAPI ENRICHMENT STATISTICS")
print(stats.to_string(index=False))


# ---------------------------------------------------------
# MATCH QUALITY CHART
# ---------------------------------------------------------

quality = df["match_quality"].dropna().value_counts()

plt.figure(figsize=(9, 6))
quality.plot(kind="bar")
plt.title("API Match Quality After Enrichment")
plt.xlabel("Match Quality")
plt.ylabel("Number of Records")
plt.tight_layout()
plt.savefig(
    OUT / "03_match_quality.png",
    dpi=300
)
plt.close()


# ---------------------------------------------------------
# BEFORE VS AFTER CAPABILITY CHART
# ---------------------------------------------------------

features = [
    "Original\nQuestion Data",
    "External\nInformation",
    "Technical\nTags",
    "Community\nAnswers",
    "Popularity\nData",
    "Similarity\nScore",
    "Match\nQuality"
]

before_values = [1, 0, 0, 0, 0, 0, 0]
after_values = [1, 1, 1, 1, 1, 1, 1]

x = range(len(features))

plt.figure(figsize=(12, 6))

plt.plot(
    x,
    before_values,
    marker="o",
    label="Before API"
)

plt.plot(
    x,
    after_values,
    marker="o",
    label="After API"
)

plt.xticks(x, features)
plt.yticks([0, 1], ["Not Available", "Available"])
plt.title("Capabilities Before and After API Enrichment")
plt.legend()
plt.tight_layout()

plt.savefig(
    OUT / "04_before_after_capabilities.png",
    dpi=300
)

plt.close()


# ---------------------------------------------------------
# CATEGORY + API MATCH
# ---------------------------------------------------------

category_match = pd.crosstab(
    df["category"],
    df["api_match_status"]
)

category_match.to_csv(
    OUT / "05_category_api_relationship.csv"
)


# ---------------------------------------------------------
# DIFFICULTY + MATCH QUALITY
# ---------------------------------------------------------

difficulty_match = pd.crosstab(
    df["difficulty"],
    df["match_quality"]
)

difficulty_match.to_csv(
    OUT / "06_difficulty_match_relationship.csv"
)


# ---------------------------------------------------------
# NEW RELATIONSHIPS
# ---------------------------------------------------------

relationships = pd.DataFrame({
    "New Relationship": [
        "Interview Question → Stack Overflow Question",
        "Interview Question → Stack Overflow Tags",
        "Interview Question → Community Score",
        "Interview Question → Answer Count",
        "Interview Question → View Count",
        "Interview Question → Answered Status",
        "Interview Question → Text Similarity",
        "Interview Question → Match Quality",
        "Difficulty → API Match Quality",
        "Category → API Match Status"
    ],
    "Purpose": [
        "Find related external technical content",
        "Identify related technologies and concepts",
        "Measure community approval/popularity",
        "Measure availability of alternative solutions",
        "Measure popularity of technical content",
        "Identify whether a community answer exists",
        "Measure relevance between questions",
        "Filter reliable API matches",
        "Study matching behavior by difficulty",
        "Study API coverage across categories"
    ]
})

relationships.to_csv(
    OUT / "07_new_relationships.csv",
    index=False
)


print("\n" + "=" * 65)
print("STAGE 7 COMPLETED")
print("=" * 65)
print("Output folder:")
print(OUT.resolve())
print("\nFiles created:")
for file in sorted(OUT.iterdir()):
    print(" -", file.name)