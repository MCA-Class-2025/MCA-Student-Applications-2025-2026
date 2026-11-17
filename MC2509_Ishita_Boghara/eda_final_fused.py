import pandas as pd
import matplotlib.pyplot as plt
import os

# ============================================================
# SETUP
# ============================================================

DATA_FILE = "data/final_fused_dataset.csv"
OUTPUT_DIR = "eda_outputs"

os.makedirs(OUTPUT_DIR, exist_ok=True)

# Load dataset
df = pd.read_csv(DATA_FILE)

print("=" * 60)
print("FINAL FUSED DATASET - EDA")
print("=" * 60)

print("\nDATASET SHAPE:")
print(df.shape)

print("\nDUPLICATE ROWS:")
print(df.duplicated().sum())


# ============================================================
# 1. MISSING VALUES
# ============================================================

missing = df.isnull().sum()
missing = missing[missing > 0].sort_values(ascending=False)

print("\nMISSING VALUES:")
print(missing)

plt.figure(figsize=(12, 7))
missing.plot(kind="bar")
plt.title("Missing Values in Final Fused Dataset")
plt.xlabel("Columns")
plt.ylabel("Number of Missing Values")
plt.xticks(rotation=90)
plt.tight_layout()
plt.savefig(f"{OUTPUT_DIR}/01_missing_values.png")
plt.close()


# ============================================================
# 2. TOP 10 BOOK CATEGORIES
# ============================================================

top_categories = df["categories"].value_counts().head(10)

print("\nTOP 10 CATEGORIES:")
print(top_categories)

plt.figure(figsize=(10, 6))
top_categories.plot(kind="bar")
plt.title("Top 10 Book Categories")
plt.xlabel("Category")
plt.ylabel("Number of Books")
plt.xticks(rotation=45, ha="right")
plt.tight_layout()
plt.savefig(f"{OUTPUT_DIR}/02_top_categories.png")
plt.close()


# ============================================================
# 3. AVERAGE RATING DISTRIBUTION
# ============================================================

plt.figure(figsize=(10, 6))
df["average_rating"].dropna().plot(kind="hist", bins=30)
plt.title("Distribution of Average Book Ratings")
plt.xlabel("Average Rating")
plt.ylabel("Frequency")
plt.tight_layout()
plt.savefig(f"{OUTPUT_DIR}/03_average_rating_distribution.png")
plt.close()


# ============================================================
# 4. NUMBER OF PAGES DISTRIBUTION
# ============================================================

plt.figure(figsize=(10, 6))
df["num_pages"].dropna().plot(kind="hist", bins=40)
plt.title("Distribution of Number of Pages")
plt.xlabel("Number of Pages")
plt.ylabel("Frequency")
plt.tight_layout()
plt.savefig(f"{OUTPUT_DIR}/04_pages_distribution.png")
plt.close()


# ============================================================
# 5. PUBLICATION YEAR DISTRIBUTION
# ============================================================

plt.figure(figsize=(10, 6))
df["published_year"].dropna().plot(kind="hist", bins=30)
plt.title("Distribution of Published Years")
plt.xlabel("Published Year")
plt.ylabel("Frequency")
plt.tight_layout()
plt.savefig(f"{OUTPUT_DIR}/05_published_year_distribution.png")
plt.close()


# ============================================================
# 6. RATINGS COUNT DISTRIBUTION
# LOG TRANSFORMATION
# ============================================================

ratings_log = (
    df["ratings_count"]
    .dropna()
    .apply(lambda x: 0 if x <= 0 else __import__("math").log10(x))
)

plt.figure(figsize=(10, 6))
ratings_log.plot(kind="hist", bins=40)
plt.title("Distribution of Ratings Count (Log Scale)")
plt.xlabel("log10(Ratings Count)")
plt.ylabel("Frequency")
plt.tight_layout()
plt.savefig(f"{OUTPUT_DIR}/06_ratings_count_log_distribution.png")
plt.close()


# ============================================================
# 7. CORRELATION MATRIX
# ============================================================

numeric_columns = ["published_year", "average_rating", "num_pages", "ratings_count"]

corr = df[numeric_columns].corr()

print("\nCORRELATION MATRIX:")
print(corr)

plt.figure(figsize=(8, 6))

plt.imshow(corr.values)
plt.colorbar()

plt.xticks(range(len(corr.columns)), corr.columns, rotation=45, ha="right")

plt.yticks(range(len(corr.index)), corr.index)

for i in range(len(corr.index)):
    for j in range(len(corr.columns)):
        plt.text(j, i, round(corr.iloc[i, j], 2), ha="center", va="center")

plt.title("Correlation Matrix")
plt.tight_layout()
plt.savefig(f"{OUTPUT_DIR}/07_correlation_matrix.png")
plt.close()


# ============================================================
# 8. API SOURCE COUNT DISTRIBUTION
# ============================================================

api_df = df[df["api_data_available"] == True]

source_counts = api_df["source_count"].value_counts().sort_index()

print("\nAPI SOURCE COUNT DISTRIBUTION:")
print(source_counts)

plt.figure(figsize=(8, 6))
source_counts.plot(kind="bar")
plt.title("Number of APIs Successfully Providing Data")
plt.xlabel("Number of Successful APIs")
plt.ylabel("Number of Enriched Records")
plt.xticks(rotation=0)
plt.tight_layout()
plt.savefig(f"{OUTPUT_DIR}/08_api_source_distribution.png")
plt.close()


# ============================================================
# 9. BEFORE VS AFTER DATASET COMPARISON
# ============================================================

comparison = pd.DataFrame(
    {
        "Dataset": ["Original Kaggle Dataset", "Final Fused Dataset"],
        "Rows": [6810, len(df)],
        "Columns": [12, len(df.columns)],
    }
)

print("\nBEFORE VS AFTER COMPARISON:")
print(comparison.to_string(index=False))

comparison.to_csv(f"{OUTPUT_DIR}/dataset_comparison.csv", index=False)

plt.figure(figsize=(8, 6))

x = range(len(comparison))

plt.bar([i - 0.2 for i in x], comparison["Rows"], width=0.4, label="Rows")

plt.bar([i + 0.2 for i in x], comparison["Columns"], width=0.4, label="Columns")

plt.xticks(x, comparison["Dataset"], rotation=15)

plt.ylabel("Count")
plt.title("Original Dataset vs Final Fused Dataset")
plt.legend()

plt.tight_layout()
plt.savefig(f"{OUTPUT_DIR}/09_before_after_comparison.png")
plt.close()


# ============================================================
# 10. API ENRICHMENT SUMMARY
# ============================================================

total_records = len(df)
enriched_records = df["api_data_available"].sum()

print("\nAPI ENRICHMENT SUMMARY:")
print("Total Records:", total_records)
print("API Enriched Records:", enriched_records)
print(
    "API Enrichment Percentage:",
    round((enriched_records / total_records) * 100, 2),
    "%",
)

# ============================================================
# OUTLIER ANALYSIS
# ============================================================

print("\nOUTLIER ANALYSIS (IQR METHOD):")

outlier_columns = ["average_rating", "num_pages", "ratings_count", "download_count"]

for col in outlier_columns:
    values = df[col].dropna()

    if len(values) == 0:
        print(f"\n{col}: No data available")
        continue

    Q1 = values.quantile(0.25)
    Q3 = values.quantile(0.75)
    IQR = Q3 - Q1

    lower_bound = Q1 - 1.5 * IQR
    upper_bound = Q3 + 1.5 * IQR

    outliers = values[(values < lower_bound) | (values > upper_bound)]

    print(f"\n{col}")
    print("Q1:", Q1)
    print("Q3:", Q3)
    print("IQR:", IQR)
    print("Lower Bound:", lower_bound)
    print("Upper Bound:", upper_bound)
    print("Number of Outliers:", len(outliers))
    

print("\n" + "=" * 60)
print("EDA COMPLETED SUCCESSFULLY")
print("=" * 60)

print(f"\nAll graphs saved inside: {OUTPUT_DIR}")
