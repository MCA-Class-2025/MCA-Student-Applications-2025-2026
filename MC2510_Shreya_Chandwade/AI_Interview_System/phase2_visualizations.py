import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

BASE = Path(__file__).resolve().parent
DATA = BASE / "final_api_enriched_interview_dataset.csv"
OUT = BASE / "phase2_visualizations"

OUT.mkdir(exist_ok=True)

df = pd.read_csv(DATA)

# ============================================================
# 1. DISTRIBUTION — Difficulty
# ============================================================

difficulty = df["difficulty"].dropna().value_counts()

plt.figure(figsize=(8, 5))
difficulty.plot(kind="bar")
plt.title("Distribution of Interview Question Difficulty")
plt.xlabel("Difficulty")
plt.ylabel("Number of Questions")
plt.xticks(rotation=0)
plt.tight_layout()
plt.savefig(OUT / "01_difficulty_distribution.png", dpi=300)
plt.close()


# ============================================================
# 2. BOXPLOT — Stack Overflow Score
# ============================================================

api = df[df["api_match_status"] == "MATCHED"].copy()

plt.figure(figsize=(8, 5))
plt.boxplot(api["stackoverflow_score"].dropna())
plt.title("Distribution of Stack Overflow Scores")
plt.ylabel("Stack Overflow Score")
plt.tight_layout()
plt.savefig(OUT / "02_stackoverflow_score_boxplot.png", dpi=300)
plt.close()


# ============================================================
# 3. RELATIONSHIP — Score vs Answer Count
# ============================================================

relationship = api[
    ["stackoverflow_score", "stackoverflow_answer_count"]
].dropna()

plt.figure(figsize=(8, 5))
plt.scatter(
    relationship["stackoverflow_score"],
    relationship["stackoverflow_answer_count"],
    alpha=0.6
)
plt.title("Stack Overflow Score vs Answer Count")
plt.xlabel("Stack Overflow Score")
plt.ylabel("Answer Count")
plt.tight_layout()
plt.savefig(OUT / "03_score_vs_answers.png", dpi=300)
plt.close()


# ============================================================
# 4. RELATIONSHIP — Score vs View Count
# ============================================================

relationship = api[
    ["stackoverflow_score", "stackoverflow_view_count"]
].dropna()

plt.figure(figsize=(8, 5))
plt.scatter(
    relationship["stackoverflow_score"],
    relationship["stackoverflow_view_count"],
    alpha=0.6
)
plt.title("Stack Overflow Score vs View Count")
plt.xlabel("Stack Overflow Score")
plt.ylabel("View Count")
plt.tight_layout()
plt.savefig(OUT / "04_score_vs_views.png", dpi=300)
plt.close()


# ============================================================
# 5. CORRELATION HEATMAP
# ============================================================

numeric_cols = [
    "stackoverflow_score",
    "stackoverflow_answer_count",
    "stackoverflow_view_count",
    "calculated_text_similarity"
]

corr = api[numeric_cols].corr()

plt.figure(figsize=(8, 6))
plt.imshow(corr, interpolation="nearest")
plt.colorbar()

plt.xticks(
    range(len(corr.columns)),
    corr.columns,
    rotation=45,
    ha="right"
)

plt.yticks(
    range(len(corr.columns)),
    corr.columns
)

plt.title("Correlation Heatmap of API-Enriched Variables")

# Add correlation values
for i in range(len(corr.columns)):
    for j in range(len(corr.columns)):
        plt.text(
            j,
            i,
            f"{corr.iloc[i, j]:.2f}",
            ha="center",
            va="center"
        )

plt.tight_layout()
plt.savefig(OUT / "05_api_correlation_heatmap.png", dpi=300)
plt.close()


# ============================================================
# 6. API-FUSION INSIGHT VISUALIZATION
# ============================================================

quality = (
    df[df["match_quality"].notna()]
    ["match_quality"]
    .value_counts()
)

plt.figure(figsize=(9, 5))
quality.plot(kind="bar")
plt.title("API Match Quality After Dataset Fusion")
plt.xlabel("Match Quality")
plt.ylabel("Number of Records")
plt.xticks(rotation=0)
plt.tight_layout()
plt.savefig(OUT / "06_api_fusion_match_quality.png", dpi=300)
plt.close()


# ============================================================
# SUMMARY
# ============================================================

print("=" * 65)
print("PHASE II — MANDATORY VISUALIZATIONS COMPLETED")
print("=" * 65)

for file in sorted(OUT.glob("*.png")):
    print(file)

print("\nTotal visualizations:", len(list(OUT.glob("*.png"))))