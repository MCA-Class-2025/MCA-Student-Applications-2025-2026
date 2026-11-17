import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt


# ============================================================
# STEP 9 - DATA QUALITY AND OUTLIER ANALYSIS
# ============================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DATASET_PATH = os.path.join(
    BASE_DIR,
    "results",
    "ml_ready_dataset.csv"
)

RESULTS_DIR = os.path.join(
    BASE_DIR,
    "results"
)

FIGURES_DIR = os.path.join(
    RESULTS_DIR,
    "figures"
)

os.makedirs(FIGURES_DIR, exist_ok=True)


print("=" * 80)
print("STEP 9 - DATA QUALITY AND OUTLIER ANALYSIS")
print("=" * 80)

print("\nDataset:")
print(DATASET_PATH)


# ============================================================
# 1. LOAD DATASET
# ============================================================

df = pd.read_csv(DATASET_PATH)

print("\nDataset loaded successfully.")
print("Rows:", len(df))
print("Columns:", len(df.columns))


# ============================================================
# 2. NUMERICAL COLUMNS
# ============================================================

numeric_columns = df.select_dtypes(
    include=[np.number]
).columns.tolist()

print("\n" + "=" * 80)
print("1. NUMERICAL COLUMNS")
print("=" * 80)

for column in numeric_columns:
    print("-", column)


# ============================================================
# 3. OUTLIER ANALYSIS USING IQR
# ============================================================

print("\n" + "=" * 80)
print("2. IQR OUTLIER ANALYSIS")
print("=" * 80)

outlier_summary = []

for column in numeric_columns:

    Q1 = df[column].quantile(0.25)
    Q3 = df[column].quantile(0.75)

    IQR = Q3 - Q1

    lower_bound = Q1 - 1.5 * IQR
    upper_bound = Q3 + 1.5 * IQR

    outliers = df[
        (df[column] < lower_bound) |
        (df[column] > upper_bound)
    ]

    outlier_count = len(outliers)

    outlier_summary.append({
        "column": column,
        "Q1": Q1,
        "Q3": Q3,
        "IQR": IQR,
        "lower_bound": lower_bound,
        "upper_bound": upper_bound,
        "outlier_count": outlier_count
    })

    print("\nColumn:", column)
    print("Q1:", Q1)
    print("Q3:", Q3)
    print("IQR:", IQR)
    print("Lower bound:", lower_bound)
    print("Upper bound:", upper_bound)
    print("Number of outliers:", outlier_count)


# ============================================================
# 4. SAVE OUTLIER SUMMARY
# ============================================================

outlier_df = pd.DataFrame(outlier_summary)

outlier_path = os.path.join(
    RESULTS_DIR,
    "outlier_analysis.csv"
)

outlier_df.to_csv(
    outlier_path,
    index=False
)

print("\nOutlier summary saved to:")
print(outlier_path)


# ============================================================
# 5. BOXPLOTS
# ============================================================

print("\n" + "=" * 80)
print("3. CREATING BOXPLOTS")
print("=" * 80)


important_columns = [
    "content_length",
    "title_length",
    "content_word_count",
    "title_word_count",
    "metadata_length"
]


for column in important_columns:

    if column not in df.columns:
        continue

    plt.figure(figsize=(8, 5))

    plt.boxplot(
        df[column].dropna()
    )

    plt.title(
        f"Boxplot of {column}"
    )

    plt.ylabel(column)

    plt.tight_layout()

    filename = f"boxplot_{column}.png"

    filepath = os.path.join(
        FIGURES_DIR,
        filename
    )

    plt.savefig(filepath, dpi=300)

    plt.close()

    print("Saved:", filepath)


# ============================================================
# 6. CONSISTENCY CHECK
# ============================================================

print("\n" + "=" * 80)
print("4. CONSISTENCY CHECK")
print("=" * 80)


print("\nSource type values:")

for value in sorted(
    df["source_type"].dropna().unique()
):
    print("-", value)


print("\nLanguage values:")

for value in sorted(
    df["language"].dropna().unique()
):
    print("-", value)


# ============================================================
# 7. MISSING VALUES
# ============================================================

print("\n" + "=" * 80)
print("5. MISSING VALUE CHECK")
print("=" * 80)

missing = df.isnull().sum()

print(missing)


# ============================================================
# 8. DUPLICATE CHECK
# ============================================================

print("\n" + "=" * 80)
print("6. DUPLICATE CHECK")
print("=" * 80)

duplicates = df.duplicated().sum()

print("Duplicate records:", duplicates)


# ============================================================
# 9. FINAL SUMMARY
# ============================================================

print("\n" + "=" * 80)
print("STEP 9 COMPLETED")
print("=" * 80)

print("\nGenerated files:")
print("1.", outlier_path)

print("\nBoxplot files were saved in:")
print(FIGURES_DIR)

print("\n" + "=" * 80)