import os
import pandas as pd
import numpy as np


# ============================================================
# STEP 4 - PREPARE DATASET FOR MACHINE LEARNING
# ============================================================

print("=" * 80)
print("STEP 4 - PREPARING DATASET FOR MACHINE LEARNING")
print("=" * 80)


# ------------------------------------------------------------
# Project paths
# ------------------------------------------------------------

PROJECT_ROOT = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

DATASET_PATH = os.path.join(
    PROJECT_ROOT,
    "datasets",
    "fused_knowledge_dataset.csv"
)

RESULTS_DIR = os.path.join(
    PROJECT_ROOT,
    "ml_assignment",
    "results"
)

os.makedirs(RESULTS_DIR, exist_ok=True)


# ------------------------------------------------------------
# Load original dataset
# ------------------------------------------------------------

print("\nLoading original dataset...")

df = pd.read_csv(DATASET_PATH)

print("Dataset loaded successfully.")
print("Rows:", len(df))
print("Columns:", len(df.columns))


# ============================================================
# 1. CREATE ML FEATURES
# ============================================================

print("\n" + "=" * 80)
print("CREATING MACHINE LEARNING FEATURES")
print("=" * 80)


# ------------------------------------------------------------
# Source type
# ------------------------------------------------------------

df["source_type"] = (
    df["source_type"]
    .fillna("Unknown")
    .astype(str)
)


# ------------------------------------------------------------
# Title
# ------------------------------------------------------------

df["title"] = (
    df["title"]
    .fillna("")
    .astype(str)
)


# ------------------------------------------------------------
# Content
# ------------------------------------------------------------

df["content"] = (
    df["content"]
    .fillna("")
    .astype(str)
)


# ------------------------------------------------------------
# URL
# ------------------------------------------------------------

df["url"] = (
    df["url"]
    .fillna("")
    .astype(str)
)


# ------------------------------------------------------------
# Language
# ------------------------------------------------------------

df["language"] = (
    df["language"]
    .fillna("Unknown")
    .astype(str)
)


# ------------------------------------------------------------
# Metadata
# ------------------------------------------------------------

df["metadata"] = (
    df["metadata"]
    .fillna("")
    .astype(str)
)


# ============================================================
# 2. TEXT-BASED NUMERICAL FEATURES
# ============================================================

print("\nCreating numerical features...")


# Content length

df["content_length"] = (
    df["content"]
    .str.len()
)


# Title length

df["title_length"] = (
    df["title"]
    .str.len()
)


# Number of words in content

df["content_word_count"] = (
    df["content"]
    .str.split()
    .str.len()
)


# Number of words in title

df["title_word_count"] = (
    df["title"]
    .str.split()
    .str.len()
)


# Number of characters in metadata

df["metadata_length"] = (
    df["metadata"]
    .str.len()
)


# URL availability

df["has_url"] = (
    df["url"].str.strip() != ""
).astype(int)


# ============================================================
# 3. DATE FEATURES
# ============================================================

print("Creating date features...")


df["modified_time_parsed"] = pd.to_datetime(
    df["modified_time"],
    errors="coerce",
    utc=True
)


df["modified_year"] = (
    df["modified_time_parsed"]
    .dt.year
    .fillna(0)
    .astype(int)
)


df["modified_month"] = (
    df["modified_time_parsed"]
    .dt.month
    .fillna(0)
    .astype(int)
)


df["modified_day"] = (
    df["modified_time_parsed"]
    .dt.day
    .fillna(0)
    .astype(int)
)


# ============================================================
# 4. SOURCE TYPE ENCODING
# ============================================================

print("Encoding source type...")


source_mapping = {
    source: index
    for index, source in enumerate(
        sorted(df["source_type"].unique())
    )
}


df["source_type_encoded"] = (
    df["source_type"]
    .map(source_mapping)
    .astype(int)
)


print("\nSource type encoding:")

for source, value in source_mapping.items():
    print(
        f"{source} -> {value}"
    )


# ============================================================
# 5. LANGUAGE ENCODING
# ============================================================

print("\nEncoding language...")


language_mapping = {
    language: index
    for index, language in enumerate(
        sorted(df["language"].unique())
    )
}


df["language_encoded"] = (
    df["language"]
    .map(language_mapping)
    .astype(int)
)


print("\nLanguage encoding:")

for language, value in language_mapping.items():
    print(
        f"{language} -> {value}"
    )


# ============================================================
# 6. CREATE ML DATASET
# ============================================================

print("\nCreating final ML dataset...")


ml_columns = [
    "source_type",
    "title",
    "content",
    "url",
    "language",
    "modified_time",
    "metadata",

    "content_length",
    "title_length",
    "content_word_count",
    "title_word_count",
    "metadata_length",
    "has_url",

    "modified_year",
    "modified_month",
    "modified_day",

    "source_type_encoded",
    "language_encoded"
]


ml_df = df[ml_columns].copy()


# ============================================================
# 7. HANDLE INVALID NUMERICAL VALUES
# ============================================================

numeric_columns = [
    "content_length",
    "title_length",
    "content_word_count",
    "title_word_count",
    "metadata_length",
    "has_url",
    "modified_year",
    "modified_month",
    "modified_day",
    "source_type_encoded",
    "language_encoded"
]


for column in numeric_columns:

    ml_df[column] = pd.to_numeric(
        ml_df[column],
        errors="coerce"
    )

    ml_df[column] = (
        ml_df[column]
        .replace(
            [np.inf, -np.inf],
            np.nan
        )
        .fillna(0)
    )


# ============================================================
# 8. SAVE ML DATASET
# ============================================================

OUTPUT_PATH = os.path.join(
    RESULTS_DIR,
    "ml_ready_dataset.csv"
)


ml_df.to_csv(
    OUTPUT_PATH,
    index=False
)


# ============================================================
# 9. DISPLAY INFORMATION
# ============================================================

print("\n" + "=" * 80)
print("ML DATASET CREATED SUCCESSFULLY")
print("=" * 80)


print("\nOutput file:")
print(OUTPUT_PATH)


print("\nDataset shape:")

print(
    "Rows:",
    ml_df.shape[0]
)

print(
    "Columns:",
    ml_df.shape[1]
)


print("\nML dataset columns:")

for number, column in enumerate(
    ml_df.columns,
    start=1
):

    print(
        f"{number}. {column}"
    )


print("\nNumerical feature summary:")

print(
    ml_df[numeric_columns].describe()
)


print("\nMissing values:")

print(
    ml_df.isnull().sum()
)


print("\nFirst 5 records:")

print(
    ml_df.head()
)


print("\n" + "=" * 80)
print("STEP 4 COMPLETED")
print("=" * 80)

print(
    "\nML-ready dataset saved successfully."
)

print(
    "Location:",
    OUTPUT_PATH
)

print("=" * 80)