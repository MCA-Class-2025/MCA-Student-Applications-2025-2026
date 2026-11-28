import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path


# ============================================================
# PROJECT PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

API_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "realtime_api_fusion.csv"
)

OUTPUT_DIR = (
    PROJECT_ROOT
    / "data"
    / "api_analysis"
)

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# ============================================================
# LOAD DATA
# ============================================================

print("\n" + "=" * 80)
print("PART B — API DATA ANALYSIS")
print("=" * 80)

print("\nProject root:")
print(PROJECT_ROOT)

print("\nAPI dataset:")
print(API_FILE)


if not API_FILE.exists():

    print("\nERROR: API dataset not found.")

    print(
        "\nExpected file:"
    )

    print(API_FILE)

    raise SystemExit(1)


df = pd.read_csv(
    API_FILE,
    low_memory=False
)


# ============================================================
# BASIC INFORMATION
# ============================================================

print("\n" + "=" * 80)
print("1. BASIC DATASET INFORMATION")
print("=" * 80)

print(
    "\nNumber of records:",
    len(df)
)

print(
    "Number of attributes:",
    len(df.columns)
)

print(
    "\nColumns:"
)

for index, column in enumerate(
    df.columns,
    start=1
):
    print(
        f"{index}. {column}"
    )


# ============================================================
# DATA TYPES
# ============================================================

print("\n" + "=" * 80)
print("2. DATA TYPES")
print("=" * 80)

print(
    df.dtypes
)


# ============================================================
# API DISTRIBUTION
# ============================================================

print("\n" + "=" * 80)
print("3. API SOURCE DISTRIBUTION")
print("=" * 80)

if "api" in df.columns:

    api_counts = (
        df["api"]
        .fillna("Unknown")
        .astype(str)
        .str.strip()
        .replace("", "Unknown")
        .value_counts()
    )

    print(
        "\nArticles by API:"
    )

    print(
        api_counts
    )

    api_counts.to_csv(
        OUTPUT_DIR
        / "api_distribution.csv",
        header=["article_count"]
    )

else:

    print(
        "\nWARNING: 'api' column not found."
    )


# ============================================================
# QUERY DISTRIBUTION
# ============================================================

print("\n" + "=" * 80)
print("4. SEARCH QUERY DISTRIBUTION")
print("=" * 80)

if "query" in df.columns:

    query_counts = (
        df["query"]
        .fillna("Unknown")
        .astype(str)
        .str.strip()
        .replace("", "Unknown")
        .value_counts()
    )

    print(
        "\nArticles by search query:"
    )

    print(
        query_counts
    )

    query_counts.to_csv(
        OUTPUT_DIR
        / "query_distribution.csv",
        header=["article_count"]
    )


# ============================================================
# MISSING VALUES
# ============================================================

print("\n" + "=" * 80)
print("5. MISSING VALUE ANALYSIS")
print("=" * 80)

missing_count = df.isnull().sum()

missing_percentage = (
    df.isnull().mean() * 100
).round(2)

missing_table = pd.DataFrame({
    "missing_count": missing_count,
    "missing_percentage": missing_percentage
})

print(
    "\nMissing values:"
)

print(
    missing_table
)

missing_table.to_csv(
    OUTPUT_DIR
    / "missing_values.csv"
)


# ============================================================
# EMPTY STRINGS
# ============================================================

print("\n" + "=" * 80)
print("6. EMPTY STRING ANALYSIS")
print("=" * 80)

empty_counts = {}

for column in df.columns:

    empty_counts[column] = (
        df[column]
        .fillna("")
        .astype(str)
        .str.strip()
        .eq("")
        .sum()
    )

empty_table = pd.Series(
    empty_counts,
    name="empty_string_count"
)

print(
    empty_table
)

empty_table.to_csv(
    OUTPUT_DIR
    / "empty_strings.csv"
)


# ============================================================
# DUPLICATE ROWS
# ============================================================

print("\n" + "=" * 80)
print("7. DUPLICATE RECORD ANALYSIS")
print("=" * 80)

duplicate_rows = df.duplicated().sum()

print(
    "\nExact duplicate rows:",
    duplicate_rows
)


# ============================================================
# DUPLICATE URLS
# ============================================================

if "url" in df.columns:

    duplicate_urls = (
        df["url"]
        .dropna()
        .astype(str)
        .str.strip()
        .str.lower()
        .duplicated()
        .sum()
    )

    print(
        "Duplicate URLs:",
        duplicate_urls
    )


# ============================================================
# DUPLICATE TITLES
# ============================================================

if "title" in df.columns:

    duplicate_titles = (
        df["title"]
        .dropna()
        .astype(str)
        .str.strip()
        .str.lower()
        .duplicated()
        .sum()
    )

    print(
        "Duplicate titles:",
        duplicate_titles
    )


# ============================================================
# UNIQUE VALUES
# ============================================================

print("\n" + "=" * 80)
print("8. UNIQUE VALUE ANALYSIS")
print("=" * 80)

unique_table = pd.DataFrame({
    "column": df.columns,
    "unique_values": [
        df[column].nunique(dropna=True)
        for column in df.columns
    ]
})

print(
    unique_table
)

unique_table.to_csv(
    OUTPUT_DIR
    / "unique_values.csv",
    index=False
)


# ============================================================
# DATE ANALYSIS
# ============================================================

if "published" in df.columns:

    print("\n" + "=" * 80)
    print("9. PUBLICATION DATE ANALYSIS")
    print("=" * 80)

    dates = pd.to_datetime(
        df["published"],
        errors="coerce",
        utc=True
    )

    print(
        "\nValid publication dates:",
        dates.notna().sum()
    )

    print(
        "Invalid/missing publication dates:",
        dates.isna().sum()
    )

    if dates.notna().any():

        print(
            "Earliest publication:",
            dates.min()
        )

        print(
            "Latest publication:",
            dates.max()
        )


# ============================================================
# SOURCE DISTRIBUTION
# ============================================================

if "source" in df.columns:

    print("\n" + "=" * 80)
    print("10. NEWS SOURCE DISTRIBUTION")
    print("=" * 80)

    source_counts = (
        df["source"]
        .fillna("Unknown")
        .astype(str)
        .str.strip()
        .replace("", "Unknown")
        .value_counts()
    )

    print(
        "\nTop news sources:"
    )

    print(
        source_counts.head(20)
    )

    source_counts.to_csv(
        OUTPUT_DIR
        / "source_distribution.csv",
        header=["article_count"]
    )


# ============================================================
# TEXT LENGTH ANALYSIS
# ============================================================

print("\n" + "=" * 80)
print("11. TEXT LENGTH ANALYSIS")
print("=" * 80)

text_columns = []

for column in [
    "title",
    "description"
]:

    if column in df.columns:

        text_columns.append(
            column
        )

        df[
            f"{column}_length"
        ] = (
            df[column]
            .fillna("")
            .astype(str)
            .str.len()
        )

        print(
            f"\n{column} length statistics:"
        )

        print(
            df[
                f"{column}_length"
            ].describe()
        )


# ============================================================
# SAVE TEXT STATISTICS
# ============================================================

text_stats = {}

for column in text_columns:

    length_column = (
        f"{column}_length"
    )

    text_stats[column] = {
        "mean": round(
            df[length_column].mean(),
            2
        ),
        "median": round(
            df[length_column].median(),
            2
        ),
        "std": round(
            df[length_column].std(),
            2
        ),
        "minimum": int(
            df[length_column].min()
        ),
        "maximum": int(
            df[length_column].max()
        )
    }

text_stats_df = pd.DataFrame(
    text_stats
).T

text_stats_df.to_csv(
    OUTPUT_DIR
    / "text_length_statistics.csv"
)


# ============================================================
# GRAPH 1 — API DISTRIBUTION
# ============================================================

if "api" in df.columns:

    plt.figure(
        figsize=(10, 6)
    )

    api_counts.plot(
        kind="bar"
    )

    plt.title(
        "Articles Collected by API Source"
    )

    plt.xlabel(
        "API Source"
    )

    plt.ylabel(
        "Number of Articles"
    )

    plt.xticks(
        rotation=45,
        ha="right"
    )

    plt.tight_layout()

    plt.savefig(
        OUTPUT_DIR
        / "01_api_distribution.png",
        dpi=300
    )

    plt.show()


# ============================================================
# GRAPH 2 — NEWS SOURCE DISTRIBUTION
# ============================================================

if "source" in df.columns:

    top_sources = (
        source_counts
        .head(10)
        .sort_values()
    )

    plt.figure(
        figsize=(10, 6)
    )

    top_sources.plot(
        kind="barh"
    )

    plt.title(
        "Top 10 News Sources"
    )

    plt.xlabel(
        "Number of Articles"
    )

    plt.ylabel(
        "News Source"
    )

    plt.tight_layout()

    plt.savefig(
        OUTPUT_DIR
        / "02_top_news_sources.png",
        dpi=300
    )

    plt.show()


# ============================================================
# GRAPH 3 — TITLE LENGTH DISTRIBUTION
# ============================================================

if "title_length" in df.columns:

    plt.figure(
        figsize=(10, 6)
    )

    df[
        "title_length"
    ].plot(
        kind="hist",
        bins=30
    )

    plt.title(
        "Distribution of News Article Title Length"
    )

    plt.xlabel(
        "Title Length (Characters)"
    )

    plt.ylabel(
        "Number of Articles"
    )

    plt.tight_layout()

    plt.savefig(
        OUTPUT_DIR
        / "03_title_length_distribution.png",
        dpi=300
    )

    plt.show()


# ============================================================
# GRAPH 4 — ARTICLES BY QUERY
# ============================================================

if "query" in df.columns:

    top_queries = (
        query_counts
        .head(10)
        .sort_values()
    )

    plt.figure(
        figsize=(10, 6)
    )

    top_queries.plot(
        kind="barh"
    )

    plt.title(
        "Articles Retrieved by Search Query"
    )

    plt.xlabel(
        "Number of Articles"
    )

    plt.ylabel(
        "Search Query"
    )

    plt.tight_layout()

    plt.savefig(
        OUTPUT_DIR
        / "04_query_distribution.png",
        dpi=300
    )

    plt.show()


# ============================================================
# SAMPLE RECORDS
# ============================================================

print("\n" + "=" * 80)
print("12. SAMPLE API RECORDS")
print("=" * 80)

print(
    df.head(5).to_string()
)


df.head(10).to_csv(
    OUTPUT_DIR
    / "sample_api_records.csv",
    index=False
)


# ============================================================
# FINAL SUMMARY
# ============================================================

print("\n" + "=" * 80)
print("PART B ANALYSIS COMPLETED")
print("=" * 80)

print(
    "\nRecords:",
    len(df)
)

print(
    "Attributes:",
    len(df.columns)
)

print(
    "Exact duplicate rows:",
    duplicate_rows
)

print(
    "\nAnalysis files saved in:"
)

print(
    OUTPUT_DIR
)

print(
    "\nGenerated files:"
)

for file in sorted(
    OUTPUT_DIR.iterdir()
):

    print(
        " -",
        file.name
    )

print(
    "\n" + "=" * 80
)