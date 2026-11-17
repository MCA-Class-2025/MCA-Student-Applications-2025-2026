"""
DanceCompass AI - Exploratory Data Analysis

Reads the API-enriched master CSV and creates EDA charts/reports.

The master CSV is never modified.

Usage:
    python eda.py

Or:
    python eda.py path/to/dancecompass_merged.csv
"""

from pathlib import Path
import sys
import pandas as pd
import matplotlib.pyplot as plt


# ============================================================
# CONFIGURATION
# ============================================================

DEFAULT_CSV = Path("data/dancecompass_merged.csv")
OUTPUT_DIR = Path("data/eda")


# ============================================================
# HELPER FUNCTION
# ============================================================

def save_bar(
    series,
    title,
    xlabel,
    ylabel,
    output_path,
    rotate=0
):
    """
    Create and save a bar chart.
    """

    series = series.sort_values(ascending=False)

    fig, ax = plt.subplots(figsize=(9, 5))

    series.plot(
        kind="bar",
        ax=ax
    )

    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)

    if rotate:
        plt.xticks(
            rotation=rotate,
            ha="right"
        )

    fig.tight_layout()

    fig.savefig(
        output_path,
        dpi=180
    )

    plt.close(fig)


# ============================================================
# MAIN EDA
# ============================================================

def main():

    # --------------------------------------------------------
    # Read CSV path
    # --------------------------------------------------------

    if len(sys.argv) > 1:
        csv_path = Path(sys.argv[1])
    else:
        csv_path = DEFAULT_CSV

    # --------------------------------------------------------
    # Output directory
    # --------------------------------------------------------

    if len(sys.argv) > 2:
        output_dir = Path(sys.argv[2])
    else:
        output_dir = OUTPUT_DIR

    output_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    # --------------------------------------------------------
    # Load dataset
    # --------------------------------------------------------

    print("=" * 60)
    print("       DanceCompass AI - EDA")
    print("=" * 60)

    print(f"\nLoading dataset:")
    print(csv_path)

    df = pd.read_csv(csv_path)

    print("\nDataset loaded successfully.")

    print(f"Rows    : {len(df)}")
    print(f"Columns : {len(df.columns)}")

    # --------------------------------------------------------
    # Required columns
    # --------------------------------------------------------

    required_columns = [

        "name",
        "category",
        "learning_difficulty",
        "energy_level",

        "country_code",

        "word_count",
        "character_count",
        "average_word_length",

        "wikidata_found",
        "wikipedia_found",
        "location_found",
        "openlibrary_found",
        "musicbrainz_found"
    ]

    missing_columns = [
        column
        for column in required_columns
        if column not in df.columns
    ]

    if missing_columns:

        raise ValueError(
            f"\nMissing required columns:\n"
            f"{missing_columns}"
        )

    # ========================================================
    # 1. DATASET QUALITY CHECK
    # ========================================================

    print("\n")
    print("-" * 60)
    print("DATASET QUALITY CHECK")
    print("-" * 60)

    duplicate_ids = df["id"].duplicated().sum()
    duplicate_names = df["name"].duplicated().sum()

    print(
        f"Duplicate IDs   : {duplicate_ids}"
    )

    print(
        f"Duplicate Names : {duplicate_names}"
    )

    # ========================================================
    # 2. CATEGORY DISTRIBUTION
    # ========================================================

    print("\n")
    print("-" * 60)
    print("1. CATEGORY DISTRIBUTION")
    print("-" * 60)

    category_counts = (
        df["category"]
        .value_counts()
    )

    print(category_counts)

    save_bar(
        category_counts,

        "Dance Forms by Category",

        "Category",

        "Number of Dance Forms",

        output_dir /
        "01_category_distribution.png",

        20
    )

    # ========================================================
    # 3. LEARNING DIFFICULTY
    # ========================================================

    print("\n")
    print("-" * 60)
    print("2. LEARNING DIFFICULTY")
    print("-" * 60)

    difficulty_counts = (
        df["learning_difficulty"]
        .value_counts()
    )

    print(difficulty_counts)

    save_bar(
        difficulty_counts,

        "Learning Difficulty Distribution",

        "Learning Difficulty",

        "Number of Dance Forms",

        output_dir /
        "02_learning_difficulty.png",

        20
    )

    # ========================================================
    # 4. ENERGY LEVEL
    # ========================================================

    print("\n")
    print("-" * 60)
    print("3. ENERGY LEVEL")
    print("-" * 60)

    energy_counts = (
        df["energy_level"]
        .value_counts()
    )

    print(energy_counts)

    save_bar(
        energy_counts,

        "Energy Level Distribution",

        "Energy Level",

        "Number of Dance Forms",

        output_dir /
        "03_energy_level.png",

        20
    )

    # ========================================================
    # 5. COUNTRY DISTRIBUTION
    # ========================================================

    print("\n")
    print("-" * 60)
    print("4. COUNTRY DISTRIBUTION")
    print("-" * 60)

    country_labels = {

        "in": "India",

        "us": "United States",

        "cu": "Cuba",

        "it": "Italy",

        "es": "Spain",

        "ar": "Argentina",

        "eg": "Egypt",

        "at": "Austria"
    }

    country_counts = (
        df["country_code"]
        .fillna("unknown")
        .map(
            lambda x:
            country_labels.get(
                str(x).lower(),
                str(x).upper()
            )
        )
        .value_counts()
    )

    print(country_counts)

    save_bar(
        country_counts,

        "Dance Forms by Country",

        "Country",

        "Number of Dance Forms",

        output_dir /
        "04_country_distribution.png",

        20
    )

    # ========================================================
    # 6. TEXT LENGTH
    # ========================================================

    print("\n")
    print("-" * 60)
    print("5. TEXT EDA")
    print("-" * 60)

    print(
        f"Average Word Count       : "
        f"{df['word_count'].mean():.2f}"
    )

    print(
        f"Average Character Count  : "
        f"{df['character_count'].mean():.2f}"
    )

    print(
        f"Average Word Length     : "
        f"{df['average_word_length'].mean():.2f}"
    )

    text_df = (
        df[
            [
                "name",
                "word_count"
            ]
        ]
        .sort_values(
            "word_count",
            ascending=False
        )
    )

    fig, ax = plt.subplots(
        figsize=(11, 6)
    )

    ax.bar(
        text_df["name"],
        text_df["word_count"]
    )

    ax.set_title(
        "Combined Text Length by Dance Form"
    )

    ax.set_xlabel(
        "Dance Form"
    )

    ax.set_ylabel(
        "Word Count"
    )

    plt.xticks(
        rotation=60,
        ha="right"
    )

    fig.tight_layout()

    fig.savefig(
        output_dir /
        "05_text_word_count.png",

        dpi=180
    )

    plt.close(fig)

    # ========================================================
    # 7. API COVERAGE
    # ========================================================

    print("\n")
    print("-" * 60)
    print("6. API ENRICHMENT COVERAGE")
    print("-" * 60)

    api_columns = {

        "Wikidata":
            "wikidata_found",

        "Wikipedia":
            "wikipedia_found",

        "Nominatim":
            "location_found",

        "Open Library":
            "openlibrary_found",

        "MusicBrainz":
            "musicbrainz_found"
    }

    coverage = {}

    for api_name, column in api_columns.items():

        successful_records = int(
            df[column]
            .fillna(False)
            .astype(bool)
            .sum()
        )

        coverage[api_name] = (
            successful_records
        )

        percentage = (
            successful_records /
            len(df)
        ) * 100

        print(
            f"{api_name:<15}"
            f"{successful_records}/{len(df)}"
            f" ({percentage:.1f}%)"
        )

    # --------------------------------------------------------
    # API coverage chart
    # --------------------------------------------------------

    coverage_series = pd.Series(
        coverage
    )

    fig, ax = plt.subplots(
        figsize=(9, 5)
    )

    ax.bar(
        coverage_series.index,
        coverage_series.values
    )

    ax.set_title(
        "API Enrichment Coverage"
    )

    ax.set_xlabel(
        "API Source"
    )

    ax.set_ylabel(
        "Successful Records (out of 20)"
    )

    ax.set_ylim(
        0,
        len(df)
    )

    for i, value in enumerate(
        coverage_series.values
    ):

        ax.text(
            i,
            value + 0.25,
            f"{value}/{len(df)}",
            ha="center"
        )

    fig.tight_layout()

    fig.savefig(
        output_dir /
        "06_api_coverage.png",

        dpi=180
    )

    plt.close(fig)

    # ========================================================
    # 8. SUMMARY CSV
    # ========================================================

    summary = pd.DataFrame(
        [
            {

                "rows":
                    len(df),

                "columns":
                    len(df.columns),

                "duplicate_ids":
                    int(
                        df["id"]
                        .duplicated()
                        .sum()
                    ),

                "duplicate_names":
                    int(
                        df["name"]
                        .duplicated()
                        .sum()
                    ),

                "average_word_count":
                    round(
                        df["word_count"]
                        .mean(),
                        2
                    ),

                "average_character_count":
                    round(
                        df["character_count"]
                        .mean(),
                        2
                    ),

                "average_word_length":
                    round(
                        df["average_word_length"]
                        .mean(),
                        2
                    ),

                "sentence_count_unique_values":
                    ", ".join(
                        str(value)
                        for value in
                        sorted(
                            df[
                                "sentence_count"
                            ]
                            .dropna()
                            .unique()
                        )
                    )
            }
        ]
    )

    summary.to_csv(
        output_dir /
        "eda_summary.csv",

        index=False
    )

    # ========================================================
    # 9. API COVERAGE CSV
    # ========================================================

    coverage_df = pd.DataFrame(
        {

            "api":
                list(
                    coverage.keys()
                ),

            "successful_records":
                list(
                    coverage.values()
                ),

            "total_records":
                len(df),

            "coverage_percent":
                [
                    round(
                        value /
                        len(df) *
                        100,
                        1
                    )

                    for value
                    in coverage.values()
                ]
        }
    )

    coverage_df.to_csv(
        output_dir /
        "api_coverage.csv",

        index=False
    )

    # ========================================================
    # 10. CATEGORY SUMMARY
    # ========================================================

    category_counts.rename(
        "count"
    ).to_csv(
        output_dir /
        "category_summary.csv"
    )

    # ========================================================
    # 11. DIFFICULTY SUMMARY
    # ========================================================

    difficulty_counts.rename(
        "count"
    ).to_csv(
        output_dir /
        "difficulty_summary.csv"
    )

    # ========================================================
    # 12. ENERGY SUMMARY
    # ========================================================

    energy_counts.rename(
        "count"
    ).to_csv(
        output_dir /
        "energy_summary.csv"
    )

    # ========================================================
    # 13. COUNTRY SUMMARY
    # ========================================================

    country_counts.rename(
        "count"
    ).to_csv(
        output_dir /
        "country_summary.csv"
    )

    # ========================================================
    # COMPLETE
    # ========================================================

    print("\n")
    print("=" * 60)
    print("EDA COMPLETE")
    print("=" * 60)

    print(
        f"\nInput CSV:"
        f"\n{csv_path}"
    )

    print(
        f"\nEDA output:"
        f"\n{output_dir.resolve()}"
    )

    print("\nGenerated files:")

    for file in sorted(
        output_dir.iterdir()
    ):

        print(
            f"  - {file.name}"
        )


# ============================================================
# PROGRAM ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()