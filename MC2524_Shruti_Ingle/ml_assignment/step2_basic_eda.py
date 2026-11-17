import os
import pandas as pd


# ============================================================
# STEP 2: EXPLORATORY DATA ANALYSIS
# ============================================================

print("=" * 80)
print("STEP 2 - EXPLORATORY DATA ANALYSIS (EDA)")
print("=" * 80)


# ------------------------------------------------------------
# 1. Locate project directory
# ------------------------------------------------------------

PROJECT_ROOT = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)


# ------------------------------------------------------------
# 2. Dataset path
# ------------------------------------------------------------

DATASET_PATH = os.path.join(
    PROJECT_ROOT,
    "datasets",
    "fused_knowledge_dataset.csv"
)


print("\nDataset:")
print(DATASET_PATH)


# ------------------------------------------------------------
# 3. Check dataset
# ------------------------------------------------------------

if not os.path.exists(DATASET_PATH):

    print("\nERROR: Dataset not found!")

    print(
        "\nExpected location:"
    )

    print(DATASET_PATH)

    exit()


# ------------------------------------------------------------
# 4. Load dataset
# ------------------------------------------------------------

df = pd.read_csv(DATASET_PATH)


print("\nDataset loaded successfully.")


# ============================================================
# SECTION A - BASIC DATASET INFORMATION
# ============================================================

print("\n")
print("=" * 80)
print("A. BASIC DATASET INFORMATION")
print("=" * 80)


print("\nNumber of rows:", df.shape[0])

print("Number of columns:", df.shape[1])


print("\nColumn names:")

for column in df.columns:
    print("-", column)


# ============================================================
# SECTION B - DATA TYPES
# ============================================================

print("\n")
print("=" * 80)
print("B. DATA TYPES")
print("=" * 80)

print(df.dtypes)


# ============================================================
# SECTION C - MISSING VALUE ANALYSIS
# ============================================================

print("\n")
print("=" * 80)
print("C. MISSING VALUE ANALYSIS")
print("=" * 80)


missing = df.isnull().sum()

missing_percentage = (
    df.isnull().sum() / len(df) * 100
)


missing_table = pd.DataFrame({
    "Missing Values": missing,
    "Missing Percentage": missing_percentage.round(2)
})


print(missing_table)


# ============================================================
# SECTION D - DUPLICATE ANALYSIS
# ============================================================

print("\n")
print("=" * 80)
print("D. DUPLICATE ANALYSIS")
print("=" * 80)


duplicate_count = df.duplicated().sum()

print(
    "Number of duplicate rows:",
    duplicate_count
)


# ============================================================
# SECTION E - UNIQUE VALUE ANALYSIS
# ============================================================

print("\n")
print("=" * 80)
print("E. UNIQUE VALUE ANALYSIS")
print("=" * 80)


for column in df.columns:

    unique_count = df[column].nunique()

    print(
        f"{column}: {unique_count} unique values"
    )


# ============================================================
# SECTION F - SOURCE TYPE ANALYSIS
# ============================================================

print("\n")
print("=" * 80)
print("F. DATA SOURCE DISTRIBUTION")
print("=" * 80)


source_counts = df["source_type"].value_counts()


print(source_counts)


print("\nSource percentages:")


source_percentage = (
    df["source_type"]
    .value_counts(normalize=True)
    * 100
)


print(source_percentage.round(2))


# ============================================================
# SECTION G - TITLE ANALYSIS
# ============================================================

print("\n")
print("=" * 80)
print("G. TITLE ANALYSIS")
print("=" * 80)


print(
    "Number of unique titles:",
    df["title"].nunique()
)


print("\nMost frequent titles:")

print(
    df["title"]
    .value_counts()
    .head(10)
)


# ============================================================
# SECTION H - CONTENT ANALYSIS
# ============================================================

print("\n")
print("=" * 80)
print("H. CONTENT ANALYSIS")
print("=" * 80)


content_missing = df["content"].isnull().sum()


print(
    "Missing content values:",
    content_missing
)


content_length = (
    df["content"]
    .fillna("")
    .astype(str)
    .str.len()
)


print(
    "\nMinimum content length:",
    content_length.min()
)


print(
    "Maximum content length:",
    content_length.max()
)


print(
    "Average content length:",
    round(content_length.mean(), 2)
)


print(
    "Median content length:",
    round(content_length.median(), 2)
)


# ============================================================
# SECTION I - URL ANALYSIS
# ============================================================

print("\n")
print("=" * 80)
print("I. URL ANALYSIS")
print("=" * 80)


url_missing = df["url"].isnull().sum()

url_present = df["url"].notnull().sum()


print(
    "URLs available:",
    url_present
)


print(
    "URLs missing:",
    url_missing
)


# ============================================================
# SECTION J - LANGUAGE ANALYSIS
# ============================================================

print("\n")
print("=" * 80)
print("J. LANGUAGE ANALYSIS")
print("=" * 80)


print(
    "Non-null language values:",
    df["language"].notnull().sum()
)


print(
    "Missing language values:",
    df["language"].isnull().sum()
)


if df["language"].notnull().sum() > 0:

    print("\nLanguage distribution:")

    print(
        df["language"]
        .value_counts()
    )


# ============================================================
# SECTION K - MODIFIED TIME ANALYSIS
# ============================================================

print("\n")
print("=" * 80)
print("K. MODIFIED TIME ANALYSIS")
print("=" * 80)


print(
    "Available modified times:",
    df["modified_time"].notnull().sum()
)


print(
    "Missing modified times:",
    df["modified_time"].isnull().sum()
)


# Convert modified_time to datetime

df["modified_time_parsed"] = pd.to_datetime(
    df["modified_time"],
    errors="coerce",
    utc=True
)


print(
    "\nSuccessfully parsed dates:",
    df["modified_time_parsed"].notnull().sum()
)


if df["modified_time_parsed"].notnull().sum() > 0:

    print(
        "\nEarliest modification date:"
    )

    print(
        df["modified_time_parsed"].min()
    )


    print(
        "\nLatest modification date:"
    )

    print(
        df["modified_time_parsed"].max()
    )


# ============================================================
# SECTION L - NUMERICAL COLUMN ANALYSIS
# ============================================================

print("\n")
print("=" * 80)
print("L. NUMERICAL COLUMN ANALYSIS")
print("=" * 80)


numerical_columns = df.select_dtypes(
    include=["number"]
).columns


if len(numerical_columns) == 0:

    print(
        "No numerical columns are currently present."
    )

else:

    print(
        "Numerical columns:"
    )

    print(
        list(numerical_columns)
    )

    print(
        "\nStatistical summary:"
    )

    print(
        df[numerical_columns].describe()
    )


# ============================================================
# SECTION M - CATEGORICAL COLUMN ANALYSIS
# ============================================================

print("\n")
print("=" * 80)
print("M. CATEGORICAL COLUMN ANALYSIS")
print("=" * 80)


categorical_columns = df.select_dtypes(
    include=["object"]
).columns


print(
    "Categorical/Text columns:"
)


for column in categorical_columns:

    print(
        f"\n{column}"
    )

    print(
        "Unique values:",
        df[column].nunique()
    )


# ============================================================
# SECTION N - CORRELATION ANALYSIS
# ============================================================

print("\n")
print("=" * 80)
print("N. CORRELATION ANALYSIS")
print("=" * 80)


if len(numerical_columns) >= 2:

    correlation = df[
        numerical_columns
    ].corr()

    print(correlation)

else:

    print(
        "Correlation analysis cannot be performed because "
        "there are fewer than two numerical columns."
    )


# ============================================================
# SECTION O - DATASET SUMMARY
# ============================================================

print("\n")
print("=" * 80)
print("O. FINAL EDA SUMMARY")
print("=" * 80)


print(
    "\nTotal records:",
    len(df)
)


print(
    "Total features:",
    len(df.columns)
)


print(
    "Duplicate records:",
    df.duplicated().sum()
)


print(
    "Total missing values:",
    df.isnull().sum().sum()
)


print(
    "Data sources:",
    df["source_type"].nunique()
)


print(
    "Unique titles:",
    df["title"].nunique()
)


print(
    "Unique content records:",
    df["content"].nunique()
)


print("\n" + "=" * 80)

print("STEP 2 EDA COMPLETED")

print("=" * 80)