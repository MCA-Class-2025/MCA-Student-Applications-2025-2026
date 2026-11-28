import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

# ============================================================
# PHASE 1 - PART E
# EXPLORATORY DATA ANALYSIS OF FUSED DATASET
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[2]

INPUT_FILE = BASE_DIR / "data" / "processed" / "fused_dataset.csv"
OUTPUT_DIR = BASE_DIR / "data" / "processed" / "eda_part_e"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

print("=" * 90)
print("PHASE 1 - PART E : EDA OF FUSED DATASET")
print("=" * 90)

print("\nProject root:")
print(BASE_DIR)

print("\nFused dataset:")
print(INPUT_FILE)

# ============================================================
# LOAD DATA
# ============================================================

print("\n" + "=" * 90)
print("LOADING FUSED DATASET")
print("=" * 90)

if not INPUT_FILE.exists():
    raise FileNotFoundError(
        f"Fused dataset not found:\n{INPUT_FILE}"
    )

df = pd.read_csv(INPUT_FILE, low_memory=False)

print("Dataset loaded successfully.")
print("Rows       :", len(df))
print("Columns    :", len(df.columns))

# ============================================================
# PREPARE NUMERICAL VARIABLES
# ============================================================

df["title_length"] = (
    df["title"]
    .fillna("")
    .astype(str)
    .str.len()
)

df["text_length"] = (
    df["text"]
    .fillna("")
    .astype(str)
    .str.len()
)

df["description_length"] = (
    df["description"]
    .fillna("")
    .astype(str)
    .str.len()
)

# Convert dates
df["published_datetime"] = pd.to_datetime(
    df["published"],
    errors="coerce",
    utc=True
)

df["date_datetime"] = pd.to_datetime(
    df["date"],
    errors="coerce",
    utc=True
)

df["published_year"] = df["published_datetime"].dt.year

# ============================================================
# BASIC INFORMATION
# ============================================================

print("\n" + "=" * 90)
print("1. BASIC INFORMATION")
print("=" * 90)

print("Total records :", len(df))
print("Total attributes :", len(df.columns))

print("\nRecord type distribution:")
print(df["record_type"].value_counts())

# Save basic information
basic_info = pd.DataFrame({
    "metric": [
        "Total records",
        "Total attributes",
        "Original records",
        "API-only records"
    ],
    "value": [
        len(df),
        len(df.columns),
        (df["record_type"] == "ORIGINAL").sum(),
        (df["record_type"] == "API_ONLY").sum()
    ]
})

basic_info.to_csv(
    OUTPUT_DIR / "01_basic_information.csv",
    index=False
)

# ============================================================
# 2. API SOURCE ANALYSIS
# ============================================================

print("\n" + "=" * 90)
print("2. API SOURCE ANALYSIS")
print("=" * 90)

api_df = df[df["record_type"] == "API_ONLY"].copy()

api_distribution = (
    api_df["api"]
    .value_counts()
    .reset_index()
)

api_distribution.columns = ["api", "article_count"]

print(api_distribution)

api_distribution.to_csv(
    OUTPUT_DIR / "02_api_source_distribution.csv",
    index=False
)

plt.figure(figsize=(10, 6))

plt.bar(
    api_distribution["api"],
    api_distribution["article_count"]
)

plt.title("API Source Distribution")
plt.xlabel("API Source")
plt.ylabel("Number of Articles")
plt.xticks(rotation=30, ha="right")
plt.tight_layout()

plt.savefig(
    OUTPUT_DIR / "01_api_source_distribution.png",
    dpi=200
)

plt.close()

# ============================================================
# 3. SEARCH QUERY ANALYSIS
# ============================================================

print("\n" + "=" * 90)
print("3. SEARCH QUERY ANALYSIS")
print("=" * 90)

query_distribution = (
    api_df["query"]
    .value_counts()
    .reset_index()
)

query_distribution.columns = ["query", "article_count"]

print(query_distribution)

query_distribution.to_csv(
    OUTPUT_DIR / "03_query_distribution.csv",
    index=False
)

plt.figure(figsize=(12, 6))

plt.bar(
    query_distribution["query"],
    query_distribution["article_count"]
)

plt.title("API Search Query Distribution")
plt.xlabel("Search Query")
plt.ylabel("Number of Articles")
plt.xticks(rotation=25, ha="right")

plt.tight_layout()

plt.savefig(
    OUTPUT_DIR / "02_query_distribution.png",
    dpi=200
)

plt.close()

# ============================================================
# 4. NEWS SOURCE ANALYSIS
# ============================================================

print("\n" + "=" * 90)
print("4. NEWS SOURCE ANALYSIS")
print("=" * 90)

source_distribution = (
    api_df["api_source"]
    .value_counts()
    .head(20)
    .reset_index()
)

source_distribution.columns = [
    "news_source",
    "article_count"
]

print(source_distribution)

source_distribution.to_csv(
    OUTPUT_DIR / "04_top_news_sources.csv",
    index=False
)

plt.figure(figsize=(12, 7))

plt.barh(
    source_distribution["news_source"],
    source_distribution["article_count"]
)

plt.title("Top News Sources in API Dataset")
plt.xlabel("Number of Articles")
plt.ylabel("News Source")

plt.gca().invert_yaxis()

plt.tight_layout()

plt.savefig(
    OUTPUT_DIR / "03_top_news_sources.png",
    dpi=200
)

plt.close()

# ============================================================
# 5. TITLE LENGTH ANALYSIS
# ============================================================

print("\n" + "=" * 90)
print("5. TITLE LENGTH ANALYSIS")
print("=" * 90)

title_stats = api_df["title_length"].describe()

print(title_stats)

title_stats.to_csv(
    OUTPUT_DIR / "05_title_length_statistics.csv"
)

plt.figure(figsize=(10, 6))

plt.hist(
    api_df["title_length"],
    bins=20
)

plt.title("Distribution of API Article Title Length")
plt.xlabel("Title Length (characters)")
plt.ylabel("Number of Articles")

plt.tight_layout()

plt.savefig(
    OUTPUT_DIR / "04_title_length_distribution.png",
    dpi=200
)

plt.close()

# ============================================================
# 6. DESCRIPTION LENGTH ANALYSIS
# ============================================================

print("\n" + "=" * 90)
print("6. DESCRIPTION LENGTH ANALYSIS")
print("=" * 90)

description_stats = api_df["description_length"].describe()

print(description_stats)

description_stats.to_csv(
    OUTPUT_DIR / "06_description_length_statistics.csv"
)

plt.figure(figsize=(10, 6))

plt.hist(
    api_df["description_length"],
    bins=20
)

plt.title("Distribution of API Article Description Length")
plt.xlabel("Description Length (characters)")
plt.ylabel("Number of Articles")

plt.tight_layout()

plt.savefig(
    OUTPUT_DIR / "05_description_length_distribution.png",
    dpi=200
)

plt.close()

# ============================================================
# 7. TITLE VS DESCRIPTION LENGTH
# BIVARIATE ANALYSIS
# ============================================================

print("\n" + "=" * 90)
print("7. TITLE LENGTH VS DESCRIPTION LENGTH")
print("=" * 90)

correlation = api_df[
    ["title_length", "description_length"]
].corr()

print(correlation)

correlation.to_csv(
    OUTPUT_DIR / "07_title_description_correlation.csv"
)

plt.figure(figsize=(9, 6))

plt.scatter(
    api_df["title_length"],
    api_df["description_length"],
    alpha=0.7
)

plt.title("Title Length vs Description Length")
plt.xlabel("Title Length")
plt.ylabel("Description Length")

plt.tight_layout()

plt.savefig(
    OUTPUT_DIR / "06_title_vs_description.png",
    dpi=200
)

plt.close()

# ============================================================
# 8. API SOURCE VS DESCRIPTION LENGTH
# BIVARIATE ANALYSIS
# ============================================================

print("\n" + "=" * 90)
print("8. API SOURCE VS AVERAGE DESCRIPTION LENGTH")
print("=" * 90)

source_description = (
    api_df
    .groupby("api")["description_length"]
    .mean()
    .sort_values(ascending=False)
)

print(source_description)

source_description.to_csv(
    OUTPUT_DIR / "08_api_vs_description_length.csv"
)

plt.figure(figsize=(10, 6))

plt.bar(
    source_description.index,
    source_description.values
)

plt.title("Average Description Length by API Source")
plt.xlabel("API Source")
plt.ylabel("Average Description Length")

plt.xticks(rotation=30, ha="right")

plt.tight_layout()

plt.savefig(
    OUTPUT_DIR / "07_api_vs_description_length.png",
    dpi=200
)

plt.close()

# ============================================================
# 9. QUERY VS API SOURCE
# MULTIVARIATE / GROUP-WISE ANALYSIS
# ============================================================

print("\n" + "=" * 90)
print("9. SEARCH QUERY VS API SOURCE")
print("=" * 90)

query_api = pd.crosstab(
    api_df["query"],
    api_df["api"]
)

print(query_api)

query_api.to_csv(
    OUTPUT_DIR / "09_query_vs_api_source.csv"
)

plt.figure(figsize=(12, 7))

query_api.plot(
    kind="bar",
    figsize=(12, 7)
)

plt.title("Search Query vs API Source")
plt.xlabel("Search Query")
plt.ylabel("Number of Articles")
plt.xticks(rotation=25, ha="right")

plt.tight_layout()

plt.savefig(
    OUTPUT_DIR / "08_query_vs_api_source.png",
    dpi=200
)

plt.close()

# ============================================================
# 10. API SOURCE VS TITLE LENGTH
# ============================================================

print("\n" + "=" * 90)
print("10. API SOURCE VS TITLE LENGTH")
print("=" * 90)

source_title = (
    api_df
    .groupby("api")["title_length"]
    .mean()
    .sort_values(ascending=False)
)

print(source_title)

source_title.to_csv(
    OUTPUT_DIR / "10_api_vs_title_length.csv"
)

plt.figure(figsize=(10, 6))

plt.bar(
    source_title.index,
    source_title.values
)

plt.title("Average Title Length by API Source")
plt.xlabel("API Source")
plt.ylabel("Average Title Length")

plt.xticks(rotation=30, ha="right")

plt.tight_layout()

plt.savefig(
    OUTPUT_DIR / "09_api_vs_title_length.png",
    dpi=200
)

plt.close()

# ============================================================
# 11. PUBLICATION DATE ANALYSIS
# ============================================================

print("\n" + "=" * 90)
print("11. PUBLICATION DATE ANALYSIS")
print("=" * 90)

valid_dates = api_df[
    api_df["published_datetime"].notna()
].copy()

print("Valid publication dates :", len(valid_dates))
print("Invalid publication dates :", len(api_df) - len(valid_dates))

if len(valid_dates) > 0:

    yearly = (
        valid_dates["published_year"]
        .value_counts()
        .sort_index()
        .reset_index()
    )

    yearly.columns = ["year", "article_count"]

    print("\nArticles by publication year:")
    print(yearly)

    yearly.to_csv(
        OUTPUT_DIR / "11_publication_year.csv",
        index=False
    )

    plt.figure(figsize=(10, 6))

    plt.bar(
        yearly["year"].astype(str),
        yearly["article_count"]
    )

    plt.title("API Articles by Publication Year")
    plt.xlabel("Publication Year")
    plt.ylabel("Number of Articles")

    plt.tight_layout()

    plt.savefig(
        OUTPUT_DIR / "10_publication_year.png",
        dpi=200
    )

    plt.close()

# ============================================================
# 12. MULTIVARIATE CORRELATION ANALYSIS
# ============================================================

print("\n" + "=" * 90)
print("12. MULTIVARIATE CORRELATION ANALYSIS")
print("=" * 90)

numeric_columns = [
    "title_length",
    "description_length"
]

numeric_data = api_df[numeric_columns].copy()

correlation_matrix = numeric_data.corr()

print(correlation_matrix)

correlation_matrix.to_csv(
    OUTPUT_DIR / "12_correlation_matrix.csv"
)

plt.figure(figsize=(8, 6))

plt.imshow(
    correlation_matrix,
    interpolation="nearest"
)

plt.colorbar()

plt.xticks(
    range(len(correlation_matrix.columns)),
    correlation_matrix.columns,
    rotation=30,
    ha="right"
)

plt.yticks(
    range(len(correlation_matrix.columns)),
    correlation_matrix.columns
)

for i in range(len(correlation_matrix.columns)):
    for j in range(len(correlation_matrix.columns)):
        plt.text(
            j,
            i,
            f"{correlation_matrix.iloc[i, j]:.2f}",
            ha="center",
            va="center"
        )

plt.title("Correlation Heatmap - API Article Variables")

plt.tight_layout()

plt.savefig(
    OUTPUT_DIR / "11_correlation_heatmap.png",
    dpi=200
)

plt.close()

# ============================================================
# 13. DASHBOARD SUMMARY DATA
# ============================================================

print("\n" + "=" * 90)
print("13. DASHBOARD SUMMARY")
print("=" * 90)

dashboard_summary = pd.DataFrame({
    "metric": [
        "Total fused records",
        "Original records",
        "API-only records",
        "Number of API providers",
        "Number of news sources",
        "Number of search queries",
        "Valid API publication dates",
        "Missing API images"
    ],
    "value": [
        len(df),
        (df["record_type"] == "ORIGINAL").sum(),
        len(api_df),
        api_df["api"].nunique(),
        api_df["api_source"].nunique(),
        api_df["query"].nunique(),
        api_df["published_datetime"].notna().sum(),
        api_df["image"].isna().sum()
    ]
})

print(dashboard_summary)

dashboard_summary.to_csv(
    OUTPUT_DIR / "13_dashboard_summary.csv",
    index=False
)

# ============================================================
# FINAL
# ============================================================

print("\n" + "=" * 90)
print("PART E — EDA COMPLETED SUCCESSFULLY")
print("=" * 90)

print("\nOutput directory:")
print(OUTPUT_DIR)

print("\nGenerated graphs:")

for file in sorted(OUTPUT_DIR.glob("*.png")):
    print(" -", file.name)

print("\nGenerated analysis files:")

for file in sorted(OUTPUT_DIR.glob("*.csv")):
    print(" -", file.name)

print("\n" + "=" * 90)
print("READY FOR PHASE 1 REPORT - PART E")
print("=" * 90)