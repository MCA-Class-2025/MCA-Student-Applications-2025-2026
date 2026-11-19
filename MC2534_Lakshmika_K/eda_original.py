import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

# ==========================================
# ORIGINAL DATASET EDA
# ==========================================

# Change this ONLY if needed
FILE = "dataset/Waste_Management_India_20K.csv"

print("\n========================================")
print("      ORIGINAL DATASET - EDA")
print("========================================")

# Load dataset
df = pd.read_csv(FILE)

# ==========================================
# 1. BASIC INFORMATION
# ==========================================

print("\n--- DATASET SHAPE ---")
print("Rows:", df.shape[0])
print("Columns:", df.shape[1])

print("\n--- COLUMN NAMES ---")
print(list(df.columns))

print("\n--- DATA TYPES ---")
print(df.dtypes)

# ==========================================
# 2. MISSING VALUES
# ==========================================

print("\n--- MISSING VALUES ---")

missing = df.isnull().sum()
missing_percent = (missing / len(df)) * 100

missing_table = pd.DataFrame({
    "Missing_Values": missing,
    "Missing_Percentage": missing_percent
})

print(
    missing_table[
        missing_table["Missing_Values"] > 0
    ].sort_values(
        "Missing_Values",
        ascending=False
    )
)

# ==========================================
# 3. DUPLICATES
# ==========================================

print("\n--- DUPLICATE RECORDS ---")

duplicates = df.duplicated().sum()

print("Duplicate records:", duplicates)

# ==========================================
# 4. UNIQUE VALUES
# ==========================================

print("\n--- UNIQUE VALUES ---")

print(df.nunique())

# ==========================================
# 5. DESCRIPTIVE STATISTICS
# ==========================================

print("\n--- DESCRIPTIVE STATISTICS ---")

print(
    df.describe(
        include="all"
    ).transpose()
)

# ==========================================
# 6. FIRST 5 RECORDS
# ==========================================

print("\n--- FIRST 5 RECORDS ---")

print(df.head())

# ==========================================
# 7. NUMERICAL COLUMNS
# ==========================================

numeric_columns = df.select_dtypes(
    include="number"
).columns.tolist()

print("\n--- NUMERICAL COLUMNS ---")
print(numeric_columns)

# ==========================================
# 8. HISTOGRAMS
# ==========================================

for column in numeric_columns:

    plt.figure(figsize=(8, 5))

    plt.hist(
        df[column].dropna(),
        bins=30
    )

    plt.title(
        f"Distribution of {column}"
    )

    plt.xlabel(column)
    plt.ylabel("Frequency")

    plt.tight_layout()

    plt.show()

# ==========================================
# 9. BOXPLOTS
# ==========================================

for column in numeric_columns:

    plt.figure(figsize=(8, 5))

    plt.boxplot(
        df[column].dropna()
    )

    plt.title(
        f"Boxplot of {column}"
    )

    plt.ylabel(column)

    plt.tight_layout()

    plt.show()

# ==========================================
# 10. CATEGORICAL ANALYSIS
# ==========================================

categorical_columns = df.select_dtypes(
    include=["object", "category"]
).columns.tolist()

print("\n--- CATEGORICAL COLUMNS ---")
print(categorical_columns)

# Show top categories for first few categorical columns

for column in categorical_columns[:5]:

    print(
        f"\nTop values in {column}:"
    )

    print(
        df[column]
        .value_counts()
        .head(10)
    )

# ==========================================
# 11. CORRELATION
# ==========================================

if len(numeric_columns) >= 2:

    plt.figure(
        figsize=(10, 7)
    )

    correlation = df[
        numeric_columns
    ].corr()

    sns.heatmap(
        correlation,
        annot=True,
        cmap="coolwarm"
    )

    plt.title(
        "Correlation Heatmap - Original Dataset"
    )

    plt.tight_layout()

    plt.show()

print("\n========================================")
print("        ORIGINAL EDA COMPLETED")
print("========================================")