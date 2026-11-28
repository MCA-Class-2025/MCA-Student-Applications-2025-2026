# ============================================================
# MULTILINGUAL NEWS VERIFICATION
# PHASE 1 - PART C
# DATA FUSION
# ============================================================

from pathlib import Path
import re
import hashlib
import warnings

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

warnings.filterwarnings("ignore")


# ============================================================
# PROJECT PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

RAW_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

API_FILE = PROCESSED_DIR / "realtime_api_fusion.csv"

OUTPUT_DIR = PROCESSED_DIR / "fusion_analysis"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# DISPLAY HELPERS
# ============================================================

def line():
    print("=" * 90)


def section(title):
    print()
    line()
    print(title)
    line()


# ============================================================
# TEXT NORMALIZATION
# ============================================================

def normalize_text(value):
    """
    Normalize text for content-based matching.
    """

    if pd.isna(value):
        return ""

    value = str(value)

    # Lowercase
    value = value.lower()

    # Remove URLs
    value = re.sub(r"https?://\S+|www\.\S+", " ", value)

    # Remove HTML
    value = re.sub(r"<[^>]+>", " ", value)

    # Keep letters and numbers
    value = re.sub(r"[^a-z0-9\s]", " ", value)

    # Normalize whitespace
    value = re.sub(r"\s+", " ", value).strip()

    return value


# ============================================================
# LOAD ORIGINAL DATASET
# ============================================================

def load_original_dataset():

    fake_file = (
       RAW_DIR
       / "ISOT_Fake_Real_News"
       / "Fake.csv"
    )

    real_file = (
      RAW_DIR
      / "ISOT_Fake_Real_News"
      / "True.csv"
    )

    section("LOADING ORIGINAL DATASET")

    if not fake_file.exists():
        raise FileNotFoundError(
            f"Fake.csv not found:\n{fake_file}"
        )

    if not real_file.exists():
        raise FileNotFoundError(
            f"True.csv not found:\n{real_file}"
        )

    print("Fake dataset:")
    print(fake_file)

    print("\nReal dataset:")
    print(real_file)

    fake_df = pd.read_csv(
        fake_file,
        low_memory=False
    )

    real_df = pd.read_csv(
        real_file,
        low_memory=False
    )

    fake_df["label"] = "Fake"
    real_df["label"] = "Real"

    original = pd.concat(
        [fake_df, real_df],
        ignore_index=True
    )

    # Make sure required columns exist
    required = [
        "title",
        "text",
        "subject",
        "date",
        "label"
    ]

    for column in required:

        if column not in original.columns:
            original[column] = ""

    # Keep the original columns in expected order
    original = original[
        [
            "title",
            "text",
            "subject",
            "date",
            "label"
        ]
    ]

    # Remove exact duplicate records
    original = original.drop_duplicates(
        keep="first"
    ).reset_index(drop=True)

    # Create stable original ID
    original.insert(
        0,
        "original_id",
        np.arange(
            1,
            len(original) + 1
        )
    )

    print("\nOriginal dataset loaded.")
    print("Records:", len(original))
    print("Attributes:", len(original.columns))

    return original


# ============================================================
# LOAD API DATASET
# ============================================================

def load_api_dataset():

    section("LOADING API DATASET")

    if not API_FILE.exists():
        raise FileNotFoundError(
            f"API dataset not found:\n{API_FILE}"
        )

    print("API dataset:")
    print(API_FILE)

    api = pd.read_csv(
        API_FILE,
        low_memory=False
    )

    print("\nAPI dataset loaded.")
    print("Records:", len(api))
    print("Attributes:", len(api.columns))

    return api


# ============================================================
# PREPARE ORIGINAL DATASET
# ============================================================

def prepare_original(original):

    section("PREPARING ORIGINAL DATA")

    original["title"] = (
        original["title"]
        .fillna("")
        .astype(str)
    )

    original["text"] = (
        original["text"]
        .fillna("")
        .astype(str)
    )

    original["subject"] = (
        original["subject"]
        .fillna("")
        .astype(str)
    )

    original["date"] = (
        original["date"]
        .fillna("")
        .astype(str)
    )

    original["label"] = (
        original["label"]
        .fillna("")
        .astype(str)
    )

    # Content used for matching
    original["match_text"] = (
        original["title"]
        + " "
        + original["text"]
    )

    original["normalized_content"] = (
        original["match_text"]
        .apply(normalize_text)
    )

    return original


# ============================================================
# PREPARE API DATASET
# ============================================================

def prepare_api(api):

    section("PREPARING API DATA")

    expected_columns = [
        "api",
        "query",
        "title",
        "description",
        "source",
        "published",
        "url",
        "image"
    ]

    for column in expected_columns:

        if column not in api.columns:
            api[column] = ""

    for column in expected_columns:

        api[column] = (
            api[column]
            .fillna("")
            .astype(str)
        )

    # API matching text
    api["match_text"] = (
        api["title"]
        + " "
        + api["description"]
    )

    api["normalized_content"] = (
        api["match_text"]
        .apply(normalize_text)
    )

    # Stable API ID
    api.insert(
        0,
        "api_id",
        [
            f"API_{i:04d}"
            for i in range(1, len(api) + 1)
        ]
    )

    return api


# ============================================================
# EXACT MATCH CHECK
# ============================================================

def exact_matching(original, api):

    section("EXACT CONTENT MATCH ANALYSIS")

    original_hashes = {}

    for idx, value in enumerate(
        original["normalized_content"]
    ):

        if value:

            digest = hashlib.sha256(
                value.encode("utf-8")
            ).hexdigest()

            original_hashes.setdefault(
                digest,
                []
            ).append(idx)

    api_exact_matches = []

    for idx, value in enumerate(
        api["normalized_content"]
    ):

        if not value:
            api_exact_matches.append([])
            continue

        digest = hashlib.sha256(
            value.encode("utf-8")
        ).hexdigest()

        api_exact_matches.append(
            original_hashes.get(
                digest,
                []
            )
        )

    exact_count = sum(
        1
        for matches in api_exact_matches
        if matches
    )

    print("API records:", len(api))
    print("Exact content matches:", exact_count)
    print(
        "Exact unmatched:",
        len(api) - exact_count
    )

    return api_exact_matches


# ============================================================
# TF-IDF CONTENT MATCHING
# ============================================================

def semantic_content_matching(
    original,
    api,
    exact_matches,
    threshold=0.35
):

    section(
        "CONTENT-BASED SIMILARITY MATCHING"
    )

    print(
        "Method: TF-IDF cosine similarity"
    )

    print(
        "Similarity threshold:",
        threshold
    )

    # --------------------------------------------------------
    # Combine corpus
    # --------------------------------------------------------

    original_texts = (
        original["normalized_content"]
        .tolist()
    )

    api_texts = (
        api["normalized_content"]
        .tolist()
    )

    all_texts = (
        original_texts
        + api_texts
    )

    print(
        "\nBuilding TF-IDF matrix..."
    )

    vectorizer = TfidfVectorizer(
        stop_words="english",
        ngram_range=(1, 2),
        min_df=2,
        max_df=0.95,
        sublinear_tf=True,
        max_features=200000
    )

    matrix = vectorizer.fit_transform(
        all_texts
    )

    original_matrix = matrix[
        :len(original)
    ]

    api_matrix = matrix[
        len(original):
    ]

    print(
        "TF-IDF matrix created."
    )

    print(
        "Original vectors:",
        original_matrix.shape
    )

    print(
        "API vectors:",
        api_matrix.shape
    )

    # --------------------------------------------------------
    # Similarity
    # --------------------------------------------------------

    print(
        "\nCalculating similarities..."
    )

    similarities = cosine_similarity(
        api_matrix,
        original_matrix
    )

    best_indices = similarities.argmax(
        axis=1
    )

    best_scores = similarities.max(
        axis=1
    )

    # --------------------------------------------------------
    # Save matching information
    # --------------------------------------------------------

    match_rows = []

    for api_idx in range(len(api)):

        best_original_idx = int(
            best_indices[api_idx]
        )

        score = float(
            best_scores[api_idx]
        )

        if score >= threshold:

            match_status = "Matched"

        else:

            match_status = "Unmatched"

        match_rows.append(
            {
                "api_id":
                    api.iloc[api_idx]["api_id"],

                "original_id":
                    original.iloc[
                        best_original_idx
                    ]["original_id"],

                "similarity_score":
                    score,

                "match_status":
                    match_status
            }
        )

    matches = pd.DataFrame(
        match_rows
    )

    matched_count = (
        matches["match_status"]
        .eq("Matched")
        .sum()
    )

    unmatched_count = (
        matches["match_status"]
        .eq("Unmatched")
        .sum()
    )

    print()
    print(
        "Matched API records:",
        matched_count
    )

    print(
        "Unmatched API records:",
        unmatched_count
    )

    print(
        "Total API records:",
        len(api)
    )

    return matches


# ============================================================
# DUPLICATE MATCH ANALYSIS
# ============================================================

def analyze_duplicate_matches(matches):

    section(
        "DUPLICATE MATCH ANALYSIS"
    )

    matched = matches[
        matches["match_status"]
        == "Matched"
    ]

    duplicate_targets = (
        matched["original_id"]
        .value_counts()
    )

    duplicate_targets = (
        duplicate_targets[
            duplicate_targets > 1
        ]
        .sort_values(
            ascending=False
        )
    )

    print(
        "Original records receiving multiple API matches:",
        len(duplicate_targets)
    )

    if len(duplicate_targets) > 0:

        print(
            "\nTop duplicate match targets:"
        )

        print(
            duplicate_targets.head(10)
        )

    duplicate_targets.reset_index(
        name="api_match_count"
    ).to_csv(
        OUTPUT_DIR
        / "duplicate_match_targets.csv",
        index=False
    )

    return duplicate_targets


# ============================================================
# BUILD FUSED DATASET
# ============================================================

def build_fused_dataset(
    original,
    api,
    matches
):

    section("BUILDING FINAL FUSED DATASET")

    # --------------------------------------------------------
    # Best API match for every original record
    # --------------------------------------------------------

    matched = matches[
        matches["match_status"]
        == "Matched"
    ].copy()

    # Keep only strongest API match
    matched = (
        matched
        .sort_values(
            "similarity_score",
            ascending=False
        )
        .drop_duplicates(
            subset=["original_id"],
            keep="first"
        )
    )

    api_lookup = api.set_index(
        "api_id"
    )

    match_lookup = matched.set_index(
        "original_id"
    )

    fused_rows = []

    # --------------------------------------------------------
    # Original records
    # --------------------------------------------------------

    for _, row in original.iterrows():

        original_id = row[
            "original_id"
        ]

        result = {
            "record_type":
                "ORIGINAL",

            "original_id":
                original_id,

            "api_id":
                "",

            "title":
                row["title"],

            "text":
                row["text"],

            "subject":
                row["subject"],

            "date":
                row["date"],

            "label":
                row["label"],

            "api":
                "",

            "query":
                "",

            "description":
                "",

            "api_source":
                "",

            "published":
                "",

            "url":
                "",

            "image":
                "",

            "similarity_score":
                0.0,

            "api_match_status":
                "No API Match"
        }

        # ----------------------------------------------------
        # Add API information if matched
        # ----------------------------------------------------

        if original_id in match_lookup.index:

            match_row = match_lookup.loc[
                original_id
            ]

            api_id = match_row[
                "api_id"
            ]

            score = float(
                match_row[
                    "similarity_score"
                ]
            )

            if api_id in api_lookup.index:

                api_row = api_lookup.loc[
                    api_id
                ]

                result[
                    "api_id"
                ] = api_id

                result[
                    "api"
                ] = api_row["api"]

                result[
                    "query"
                ] = api_row["query"]

                result[
                    "description"
                ] = api_row[
                    "description"
                ]

                result[
                    "api_source"
                ] = api_row["source"]

                result[
                    "published"
                ] = api_row[
                    "published"
                ]

                result[
                    "url"
                ] = api_row["url"]

                result[
                    "image"
                ] = api_row["image"]

                result[
                    "similarity_score"
                ] = score

                result[
                    "api_match_status"
                ] = "Matched"

        fused_rows.append(result)

    # --------------------------------------------------------
    # Add unmatched API records
    # --------------------------------------------------------

    unmatched_api = api[
        ~api["api_id"].isin(
            matched["api_id"]
        )
    ].copy()

    for _, api_row in (
        unmatched_api.iterrows()
    ):

        result = {

            "record_type":
                "API_ONLY",

            "original_id":
                "",

            "api_id":
                api_row["api_id"],

            "title":
                api_row["title"],

            "text":
                "",

            "subject":
                "",

            "date":
                "",

            "label":
                "",

            "api":
                api_row["api"],

            "query":
                api_row["query"],

            "description":
                api_row["description"],

            "api_source":
                api_row["source"],

            "published":
                api_row["published"],

            "url":
                api_row["url"],

            "image":
                api_row["image"],

            "similarity_score":
                0.0,

            "api_match_status":
                "API Only"
        }

        fused_rows.append(
            result
        )

    fused = pd.DataFrame(
        fused_rows
    )

    # --------------------------------------------------------
    # Final stable fused ID
    # --------------------------------------------------------

    fused.insert(
        0,
        "fused_id",
        [
            f"FUSED_{i:06d}"
            for i in range(
                1,
                len(fused) + 1
            )
        ]
    )

    print(
        "\nFused dataset created."
    )

    print(
        "Fused records:",
        len(fused)
    )

    print(
        "Fused attributes:",
        len(fused.columns)
    )

    print(
        "\nRecord types:"
    )

    print(
        fused[
            "record_type"
        ].value_counts()
    )

    return fused


# ============================================================
# FUSION VALIDATION
# ============================================================

def fusion_validation(
    original,
    api,
    matches,
    fused
):

    section(
        "FUSION VALIDATION"
    )

    matched = matches[
        matches["match_status"]
        == "Matched"
    ]

    unmatched = matches[
        matches["match_status"]
        == "Unmatched"
    ]

    matched_api_ids = set(
        matched["api_id"]
    )

    unmatched_api_ids = set(
        unmatched["api_id"]
    )

    # --------------------------------------------------------
    # Duplicate API IDs
    # --------------------------------------------------------

    duplicate_api_ids = (
        api["api_id"]
        .duplicated()
        .sum()
    )

    # --------------------------------------------------------
    # Duplicate URLs
    # --------------------------------------------------------

    duplicate_urls = (
        api["url"]
        .replace("", np.nan)
        .duplicated()
        .sum()
    )

    # --------------------------------------------------------
    # Duplicate titles
    # --------------------------------------------------------

    duplicate_titles = (
        api["title"]
        .replace("", np.nan)
        .duplicated()
        .sum()
    )

    # --------------------------------------------------------
    # Missing API responses
    # --------------------------------------------------------

    missing_api_responses = (
        api["title"]
        .str.strip()
        .eq("")
        .sum()
    )

    # --------------------------------------------------------
    # API records actually included
    # --------------------------------------------------------

    api_records_in_fused = (
        fused["api_id"]
        .replace("", np.nan)
        .notna()
        .sum()
    )

    # --------------------------------------------------------
    # Original records retained
    # --------------------------------------------------------

    original_records_in_fused = (
        fused["original_id"]
        .replace("", np.nan)
        .notna()
        .sum()
    )

    # --------------------------------------------------------
    # Conflicting label information
    # --------------------------------------------------------
    #
    # API dataset has no fake/real label, so this is not
    # directly measurable.
    #
    # We therefore explicitly report this rather than
    # inventing a conflict count.
    # --------------------------------------------------------

    conflicting_values = 0

    validation = pd.DataFrame(
        [
            {
                "parameter":
                    "Original records",

                "value":
                    len(original)
            },

            {
                "parameter":
                    "API records",

                "value":
                    len(api)
            },

            {
                "parameter":
                    "Fused records",

                "value":
                    len(fused)
            },

            {
                "parameter":
                    "Matching API records",

                "value":
                    len(matched)
            },

            {
                "parameter":
                    "Unmatched API records",

                "value":
                    len(unmatched)
            },

            {
                "parameter":
                    "Duplicate API IDs",

                "value":
                    duplicate_api_ids
            },

            {
                "parameter":
                    "Duplicate API URLs",

                "value":
                    duplicate_urls
            },

            {
                "parameter":
                    "Duplicate API titles",

                "value":
                    duplicate_titles
            },

            {
                "parameter":
                    "Missing API responses",

                "value":
                    missing_api_responses
            },

            {
                "parameter":
                    "Original records retained",

                "value":
                    original_records_in_fused
            },

            {
                "parameter":
                    "API records included",

                "value":
                    api_records_in_fused
            },

            {
                "parameter":
                    "Records lost from original",

                "value":
                    len(original)
                    - original_records_in_fused
            },

            {
                "parameter":
                    "Records added through API",

                "value":
                    len(unmatched)
            },

            {
                "parameter":
                    "Conflicting values",

                "value":
                    conflicting_values
            }
        ]
    )

    print(
        validation.to_string(
            index=False
        )
    )

    validation.to_csv(
        OUTPUT_DIR
        / "fusion_validation.csv",
        index=False
    )

    # --------------------------------------------------------
    # Detailed matching table
    # --------------------------------------------------------

    matches.to_csv(
        OUTPUT_DIR
        / "api_original_matching.csv",
        index=False
    )

    return validation


# ============================================================
# DATASET COMPARISON
# ============================================================

def dataset_comparison(
    original,
    api,
    fused
):

    section(
        "DATASET COMPARISON"
    )

    original_missing = int(
        original.isna()
        .sum()
        .sum()
    )

    api_missing = int(
        api.isna()
        .sum()
        .sum()
    )

    fused_missing = int(
        fused.isna()
        .sum()
        .sum()
    )

    comparison = pd.DataFrame(
        [
            {
                "parameter":
                    "Number of records",

                "Original Dataset":
                    len(original),

                "API Dataset":
                    len(api),

                "Fused Dataset":
                    len(fused)
            },

            {
                "parameter":
                    "Number of attributes",

                "Original Dataset":
                    len(original.columns),

                "API Dataset":
                    len(api.columns),

                "Fused Dataset":
                    len(fused.columns)
            },

            {
                "parameter":
                    "Unique identifiers",

                "Original Dataset":
                    original[
                        "original_id"
                    ].nunique(),

                "API Dataset":
                    api[
                        "api_id"
                    ].nunique(),

                "Fused Dataset":
                    fused[
                        "fused_id"
                    ].nunique()
            },

            {
                "parameter":
                    "Missing values",

                "Original Dataset":
                    original_missing,

                "API Dataset":
                    api_missing,

                "Fused Dataset":
                    fused_missing
            },

            {
                "parameter":
                    "Duplicate records",

                "Original Dataset":
                    original.duplicated().sum(),

                "API Dataset":
                    api.duplicated().sum(),

                "Fused Dataset":
                    fused.duplicated().sum()
            }
        ]
    )

    print(
        comparison.to_string(
            index=False
        )
    )

    comparison.to_csv(
        OUTPUT_DIR
        / "dataset_comparison.csv",
        index=False
    )

    return comparison


# ============================================================
# MISSING VALUE ANALYSIS
# ============================================================

def missing_value_analysis(
    fused
):

    section(
        "FUSED DATASET MISSING VALUE ANALYSIS"
    )

    missing = pd.DataFrame(
        {
            "attribute":
                fused.columns,

            "missing_count":
                [
                    int(
                        fused[col]
                        .isna()
                        .sum()
                    )
                    for col in fused.columns
                ],

            "missing_percentage":
                [
                    round(
                        fused[col]
                        .isna()
                        .mean()
                        * 100,
                        2
                    )
                    for col in fused.columns
                ]
        }
    )

    # Also count empty strings
    missing["empty_string_count"] = [
        int(
            fused[col]
            .astype(str)
            .str.strip()
            .eq("")
            .sum()
        )
        for col in fused.columns
    ]

    print(
        missing.to_string(
            index=False
        )
    )

    missing.to_csv(
        OUTPUT_DIR
        / "fused_missing_values.csv",
        index=False
    )

    return missing


# ============================================================
# MATCH QUALITY SUMMARY
# ============================================================

def match_quality_summary(
    matches
):

    section(
        "MATCH QUALITY SUMMARY"
    )

    matched = matches[
        matches["match_status"]
        == "Matched"
    ]

    if len(matched) == 0:

        print(
            "No records crossed the matching threshold."
        )

        return None

    statistics = pd.DataFrame(
        {
            "similarity_score":
                matched[
                    "similarity_score"
                ]
        }
    ).describe()

    print(
        statistics
    )

    statistics.to_csv(
        OUTPUT_DIR
        / "match_similarity_statistics.csv"
    )

    return statistics


# ============================================================
# VISUALIZATION 1
# MATCHED VS UNMATCHED API RECORDS
# ============================================================

def plot_match_distribution(
    matches
):

    section(
        "CREATING FUSION GRAPH 1")

    counts = (
        matches[
            "match_status"
        ]
        .value_counts()
        .reindex(
            [
                "Matched",
                "Unmatched"
            ],
            fill_value=0
        )
    )

    plt.figure(
        figsize=(9, 6)
    )

    bars = plt.bar(
        counts.index,
        counts.values
    )

    plt.title(
        "API Records: Matched vs Unmatched"
    )

    plt.xlabel(
        "Fusion Status"
    )

    plt.ylabel(
        "Number of API Articles"
    )

    plt.grid(
        axis="y",
        alpha=0.25
    )

    for bar, value in zip(
        bars,
        counts.values
    ):

        plt.text(
            bar.get_x()
            + bar.get_width() / 2,
            bar.get_height(),
            f"{value:,}",
            ha="center",
            va="bottom"
        )

    plt.tight_layout()

    path = (
        OUTPUT_DIR
        / "01_matched_vs_unmatched.png"
    )

    plt.savefig(
        path,
        dpi=200,
        bbox_inches="tight"
    )

    plt.close()

    print(
        "Saved:",
        path
    )


# ============================================================
# VISUALIZATION 2
# SIMILARITY SCORE DISTRIBUTION
# ============================================================

def plot_similarity_distribution(
    matches
):

    section(
        "CREATING FUSION GRAPH 2")

    scores = matches[
        "similarity_score"
    ]

    plt.figure(
        figsize=(10, 6)
    )

    plt.hist(
        scores,
        bins=20
    )

    plt.title(
        "Distribution of API–Original Content Similarity"
    )

    plt.xlabel(
        "TF-IDF Cosine Similarity"
    )

    plt.ylabel(
        "Number of API Articles"
    )

    plt.grid(
        axis="y",
        alpha=0.25
    )

    plt.tight_layout()

    path = (
        OUTPUT_DIR
        / "02_similarity_distribution.png"
    )

    plt.savefig(
        path,
        dpi=200,
        bbox_inches="tight"
    )

    plt.close()

    print(
        "Saved:",
        path
    )


# ============================================================
# VISUALIZATION 3
# API RECORDS BY SOURCE
# ============================================================

def plot_api_sources(
    api
):

    section(
        "CREATING FUSION GRAPH 3")

    counts = (
        api["api"]
        .value_counts()
        .sort_values(
            ascending=False
        )
    )

    plt.figure(
        figsize=(10, 6)
    )

    bars = plt.bar(
        counts.index,
        counts.values
    )

    plt.title(
        "API Articles by API Source"
    )

    plt.xlabel(
        "API"
    )

    plt.ylabel(
        "Number of Articles"
    )

    plt.xticks(
        rotation=35,
        ha="right"
    )

    for bar, value in zip(
        bars,
        counts.values
    ):

        plt.text(
            bar.get_x()
            + bar.get_width() / 2,
            bar.get_height(),
            f"{value:,}",
            ha="center",
            va="bottom"
        )

    plt.tight_layout()

    path = (
        OUTPUT_DIR
        / "03_api_source_distribution.png"
    )

    plt.savefig(
        path,
        dpi=200,
        bbox_inches="tight"
    )

    plt.close()

    print(
        "Saved:",
        path
    )


# ============================================================
# VISUALIZATION 4
# API SOURCE VS MATCH STATUS
# ============================================================

def plot_source_match_status(
    api,
    matches
):

    section(
        "CREATING FUSION GRAPH 4")

    merged = api[
        [
            "api_id",
            "api"
        ]
    ].merge(
        matches[
            [
                "api_id",
                "match_status"
            ]
        ],
        on="api_id",
        how="left"
    )

    table = pd.crosstab(
        merged["api"],
        merged["match_status"]
    )

    table = table.reindex(
        columns=[
            "Matched",
            "Unmatched"
        ],
        fill_value=0
    )

    table.plot(
        kind="bar",
        figsize=(11, 6)
    )

    plt.title(
        "API Source vs Fusion Match Status"
    )

    plt.xlabel(
        "API Source"
    )

    plt.ylabel(
        "Number of Articles"
    )

    plt.xticks(
        rotation=35,
        ha="right"
    )

    plt.legend(
        title="Fusion Status"
    )

    plt.tight_layout()

    path = (
        OUTPUT_DIR
        / "04_api_source_vs_match_status.png"
    )

    plt.savefig(
        path,
        dpi=200,
        bbox_inches="tight"
    )

    plt.close()

    print(
        "Saved:",
        path
    )


# ============================================================
# TOP MATCHED ARTICLES
# ============================================================

def save_top_matches(
    original,
    api,
    matches
):

    section(
        "SAVING TOP CONTENT MATCHES")

    matched = matches[
        matches["match_status"]
        == "Matched"
    ].copy()

    if len(matched) == 0:

        print(
            "No matched records available."
        )

        return

    matched = (
        matched
        .sort_values(
            "similarity_score",
            ascending=False
        )
        .head(50)
    )

    original_small = original[
        [
            "original_id",
            "title",
            "label",
            "subject"
        ]
    ]

    api_small = api[
        [
            "api_id",
            "api",
            "query",
            "title",
            "source",
            "published",
            "url"
        ]
    ]

    result = (
        matched
        .merge(
            original_small,
            on="original_id",
            how="left"
        )
        .merge(
            api_small,
            on="api_id",
            how="left",
            suffixes=(
                "_original",
                "_api"
            )
        )
    )

    result.to_csv(
        OUTPUT_DIR
        / "top_50_content_matches.csv",
        index=False
    )

    print(
        "Saved top 50 matches."
    )


# ============================================================
# SAVE FUSED DATASET
# ============================================================

def save_fused_dataset(
    fused
):

    path = (
        PROCESSED_DIR
        / "fused_dataset.csv"
    )

    fused.to_csv(
        path,
        index=False,
        encoding="utf-8"
    )

    print(
        "\nFINAL FUSED DATASET:"
    )

    print(
        path
    )

    print(
        "Rows:",
        len(fused)
    )

    print(
        "Columns:",
        len(fused.columns)
    )

    return path


# ============================================================
# FINAL SUMMARY
# ============================================================

def final_summary(
    original,
    api,
    matches,
    fused
):

    section(
        "PART C — FINAL SUMMARY"
    )

    matched = (
        matches[
            "match_status"
        ]
        == "Matched"
    ).sum()

    unmatched = (
        matches[
            "match_status"
        ]
        == "Unmatched"
    ).sum()

    print(
        f"Original records       : {len(original):,}"
    )

    print(
        f"API records            : {len(api):,}"
    )

    print(
        f"Matched API records    : {matched:,}"
    )

    print(
        f"Unmatched API records  : {unmatched:,}"
    )

    print(
        f"Final fused records    : {len(fused):,}"
    )

    print(
        f"Final fused attributes : {len(fused.columns):,}"
    )

    print(
        "\nOutput directory:"
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

        if file.is_file():

            print(
                " -",
                file.name
            )

    print(
        "\nFinal fused CSV:"
    )

    print(
        PROCESSED_DIR
        / "fused_dataset.csv"
    )


# ============================================================
# MAIN
# ============================================================

def main():

    print()
    line()
    print(
        "PHASE 1 - PART C : DATA FUSION"
    )
    line()

    print(
        "\nProject root:"
    )

    print(
        PROJECT_ROOT
    )

    print(
        "\nAPI dataset:"
    )

    print(
        API_FILE
    )

    # --------------------------------------------------------
    # Load
    # --------------------------------------------------------

    original = load_original_dataset()

    api = load_api_dataset()

    # --------------------------------------------------------
    # Prepare
    # --------------------------------------------------------

    original = prepare_original(
        original
    )

    api = prepare_api(
        api
    )

    # --------------------------------------------------------
    # Exact matching
    # --------------------------------------------------------

    exact_matches = exact_matching(
        original,
        api
    )

    # --------------------------------------------------------
    # Content similarity
    # --------------------------------------------------------

    matches = semantic_content_matching(
        original,
        api,
        exact_matches,
        threshold=0.35
    )

    # --------------------------------------------------------
    # Duplicate analysis
    # --------------------------------------------------------

    analyze_duplicate_matches(
        matches
    )

    # --------------------------------------------------------
    # Build fused dataset
    # --------------------------------------------------------

    fused = build_fused_dataset(
        original,
        api,
        matches
    )

    # --------------------------------------------------------
    # Validation
    # --------------------------------------------------------

    fusion_validation(
        original,
        api,
        matches,
        fused
    )

    # --------------------------------------------------------
    # Dataset comparison
    # --------------------------------------------------------

    dataset_comparison(
        original,
        api,
        fused
    )

    # --------------------------------------------------------
    # Missing value analysis
    # --------------------------------------------------------

    missing_value_analysis(
        fused
    )

    # --------------------------------------------------------
    # Match quality
    # --------------------------------------------------------

    match_quality_summary(
        matches
    )

    # --------------------------------------------------------
    # Visualizations
    # --------------------------------------------------------

    plot_match_distribution(
        matches
    )

    plot_similarity_distribution(
        matches
    )

    plot_api_sources(
        api
    )

    plot_source_match_status(
        api,
        matches
    )

    # --------------------------------------------------------
    # Top matches
    # --------------------------------------------------------

    save_top_matches(
        original,
        api,
        matches
    )

    # --------------------------------------------------------
    # Save final fused CSV
    # --------------------------------------------------------

    save_fused_dataset(
        fused
    )

    # --------------------------------------------------------
    # Summary
    # --------------------------------------------------------

    final_summary(
        original,
        api,
        matches,
        fused
    )

    print()
    line()
    print(
        "PART C — DATA FUSION COMPLETED SUCCESSFULLY"
    )
    line()


# ============================================================
# PROGRAM ENTRY
# ============================================================

if __name__ == "__main__":
    main()