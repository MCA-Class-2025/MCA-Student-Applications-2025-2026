import os
import pandas as pd
import matplotlib.pyplot as plt


# ============================================================
# STEP 3 - EDA VISUALIZATION
# ============================================================

print("=" * 80)
print("STEP 3 - EDA VISUALIZATION")
print("=" * 80)


# ------------------------------------------------------------
# Project path
# ------------------------------------------------------------

PROJECT_ROOT = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)


# ------------------------------------------------------------
# Dataset path
# ------------------------------------------------------------

DATASET_PATH = os.path.join(
    PROJECT_ROOT,
    "datasets",
    "fused_knowledge_dataset.csv"
)


# ------------------------------------------------------------
# Results directory
# ------------------------------------------------------------

RESULTS_DIR = os.path.join(
    PROJECT_ROOT,
    "ml_assignment",
    "results"
)

FIGURES_DIR = os.path.join(
    RESULTS_DIR,
    "figures"
)

os.makedirs(FIGURES_DIR, exist_ok=True)


print("\nDataset:")
print(DATASET_PATH)

print("\nFigures will be saved to:")
print(FIGURES_DIR)


# ------------------------------------------------------------
# Load dataset
# ------------------------------------------------------------

if not os.path.exists(DATASET_PATH):

    print("\nERROR: Dataset not found.")
    exit()


df = pd.read_csv(DATASET_PATH)


print("\nDataset loaded successfully.")

print(
    "Rows:",
    len(df)
)

print(
    "Columns:",
    len(df.columns)
)


# ============================================================
# GRAPH 1 - SOURCE TYPE DISTRIBUTION
# ============================================================

print("\nCreating Graph 1 - Source Distribution...")


source_counts = df["source_type"].value_counts()


plt.figure(figsize=(10, 6))

source_counts.plot(
    kind="bar"
)

plt.title(
    "Distribution of Records by Data Source"
)

plt.xlabel(
    "Data Source"
)

plt.ylabel(
    "Number of Records"
)

plt.xticks(
    rotation=45,
    ha="right"
)

plt.tight_layout()


graph_path = os.path.join(
    FIGURES_DIR,
    "01_source_distribution.png"
)

plt.savefig(
    graph_path,
    dpi=300
)

plt.close()


print(
    "Saved:",
    graph_path
)


# ============================================================
# GRAPH 2 - MISSING VALUES
# ============================================================

print("\nCreating Graph 2 - Missing Values...")


missing_values = df.isnull().sum()


plt.figure(figsize=(10, 6))

missing_values.plot(
    kind="bar"
)

plt.title(
    "Missing Values by Column"
)

plt.xlabel(
    "Column"
)

plt.ylabel(
    "Number of Missing Values"
)

plt.xticks(
    rotation=45,
    ha="right"
)

plt.tight_layout()


graph_path = os.path.join(
    FIGURES_DIR,
    "02_missing_values.png"
)

plt.savefig(
    graph_path,
    dpi=300
)

plt.close()


print(
    "Saved:",
    graph_path
)


# ============================================================
# GRAPH 3 - UNIQUE VALUES
# ============================================================

print("\nCreating Graph 3 - Unique Values...")


unique_values = df.nunique()


plt.figure(figsize=(10, 6))

unique_values.plot(
    kind="bar"
)

plt.title(
    "Number of Unique Values per Column"
)

plt.xlabel(
    "Column"
)

plt.ylabel(
    "Number of Unique Values"
)

plt.xticks(
    rotation=45,
    ha="right"
)

plt.tight_layout()


graph_path = os.path.join(
    FIGURES_DIR,
    "03_unique_values.png"
)

plt.savefig(
    graph_path,
    dpi=300
)

plt.close()


print(
    "Saved:",
    graph_path
)


# ============================================================
# GRAPH 4 - TOP TITLES
# ============================================================

print("\nCreating Graph 4 - Top Titles...")


top_titles = (
    df["title"]
    .value_counts()
    .head(10)
)


plt.figure(figsize=(12, 7))

top_titles.plot(
    kind="bar"
)

plt.title(
    "Top 10 Most Frequent Document Titles"
)

plt.xlabel(
    "Document Title"
)

plt.ylabel(
    "Frequency"
)

plt.xticks(
    rotation=60,
    ha="right"
)

plt.tight_layout()


graph_path = os.path.join(
    FIGURES_DIR,
    "04_top_titles.png"
)

plt.savefig(
    graph_path,
    dpi=300
)

plt.close()


print(
    "Saved:",
    graph_path
)


# ============================================================
# GRAPH 5 - CONTENT LENGTH
# ============================================================

print("\nCreating Graph 5 - Content Length...")


content_length = (
    df["content"]
    .fillna("")
    .astype(str)
    .str.len()
)


plt.figure(figsize=(10, 6))

plt.hist(
    content_length,
    bins=20
)

plt.title(
    "Distribution of Content Length"
)

plt.xlabel(
    "Content Length (Characters)"
)

plt.ylabel(
    "Number of Records"
)

plt.tight_layout()


graph_path = os.path.join(
    FIGURES_DIR,
    "05_content_length_distribution.png"
)

plt.savefig(
    graph_path,
    dpi=300
)

plt.close()


print(
    "Saved:",
    graph_path
)


# ============================================================
# GRAPH 6 - URL AVAILABILITY
# ============================================================

print("\nCreating Graph 6 - URL Availability...")


url_status = pd.Series({
    "URL Available": df["url"].notnull().sum(),
    "URL Missing": df["url"].isnull().sum()
})


plt.figure(figsize=(8, 6))

url_status.plot(
    kind="bar"
)

plt.title(
    "URL Availability"
)

plt.xlabel(
    "URL Status"
)

plt.ylabel(
    "Number of Records"
)

plt.xticks(
    rotation=0
)

plt.tight_layout()


graph_path = os.path.join(
    FIGURES_DIR,
    "06_url_availability.png"
)

plt.savefig(
    graph_path,
    dpi=300
)

plt.close()


print(
    "Saved:",
    graph_path
)


# ============================================================
# GRAPH 7 - LANGUAGE DISTRIBUTION
# ============================================================

print("\nCreating Graph 7 - Language Distribution...")


language_counts = (
    df["language"]
    .dropna()
    .value_counts()
)


if len(language_counts) > 0:

    plt.figure(figsize=(8, 6))

    language_counts.plot(
        kind="bar"
    )

    plt.title(
        "Language Distribution"
    )

    plt.xlabel(
        "Language"
    )

    plt.ylabel(
        "Number of Records"
    )

    plt.xticks(
        rotation=0
    )

    plt.tight_layout()


    graph_path = os.path.join(
        FIGURES_DIR,
        "07_language_distribution.png"
    )

    plt.savefig(
        graph_path,
        dpi=300
    )

    plt.close()


    print(
        "Saved:",
        graph_path
    )

else:

    print(
        "No language data available for visualization."
    )


# ============================================================
# GRAPH 8 - MODIFIED DATE DISTRIBUTION
# ============================================================

print("\nCreating Graph 8 - Modified Date Distribution...")


dates = pd.to_datetime(
    df["modified_time"],
    errors="coerce",
    utc=True
)


dates = dates.dropna()


if len(dates) > 0:

    monthly_counts = (
        dates.dt.to_period("M")
        .astype(str)
        .value_counts()
        .sort_index()
    )


    plt.figure(figsize=(10, 6))

    monthly_counts.plot(
        kind="bar"
    )

    plt.title(
        "Records by Modification Month"
    )

    plt.xlabel(
        "Month"
    )

    plt.ylabel(
        "Number of Records"
    )

    plt.xticks(
        rotation=45,
        ha="right"
    )

    plt.tight_layout()


    graph_path = os.path.join(
        FIGURES_DIR,
        "08_modification_month.png"
    )

    plt.savefig(
        graph_path,
        dpi=300
    )

    plt.close()


    print(
        "Saved:",
        graph_path
    )

else:

    print(
        "No valid modification dates available."
    )


# ============================================================
# FINAL
# ============================================================

print("\n")
print("=" * 80)

print(
    "STEP 3 EDA VISUALIZATION COMPLETED"
)

print("=" * 80)

print(
    "\nAll graphs are stored in:"
)

print(
    FIGURES_DIR
)

print("\nGenerated files:")

for filename in sorted(
    os.listdir(FIGURES_DIR)
):

    print(
        "-",
        filename
    )

print("\n" + "=" * 80)