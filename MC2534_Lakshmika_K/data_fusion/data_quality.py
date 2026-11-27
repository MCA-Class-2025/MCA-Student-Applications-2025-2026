import pandas as pd
import numpy as np

# ==========================================
# LOAD FUSED DATASET
# ==========================================

FILE = "api_data/final_fused_waste_dataset.csv"

df = pd.read_csv(FILE)

print("\n========================================")
print("       DATA QUALITY ASSESSMENT")
print("========================================")


# ==========================================
# 1. STRUCTURAL CHECKS
# ==========================================

print("\n--- STRUCTURAL CHECKS ---")

print("Dataset dimensions:")
print("Rows    :", df.shape[0])
print("Columns :", df.shape[1])

print("\nData types:")
print(df.dtypes.to_string())

print("\nUnique values:")
for col in df.columns:
    print(f"{col}: {df[col].nunique(dropna=True)}")

print("\nDuplicate complete records:")
print(df.duplicated().sum())

if "Record_ID" in df.columns:
    print("\nDuplicate Record_ID:")
    print(df["Record_ID"].duplicated().sum())


# ==========================================
# 2. MISSING DATA
# ==========================================

print("\n--- MISSING DATA ---")

missing_count = df.isnull().sum()
missing_percentage = (
    df.isnull().sum() / len(df) * 100
)

missing_table = pd.DataFrame({
    "Missing Count": missing_count,
    "Missing Percentage": missing_percentage.round(2)
})

missing_table = missing_table[
    missing_table["Missing Count"] > 0
].sort_values(
    "Missing Count",
    ascending=False
)

if len(missing_table) == 0:
    print("No missing values found.")

else:
    print(missing_table.to_string())

    print("\nAttribute with maximum missing data:")
    print(missing_table.index[0])


# ==========================================
# 3. CATEGORICAL CONSISTENCY
# ==========================================

print("\n--- CATEGORICAL CONSISTENCY ---")

categorical_columns = df.select_dtypes(
    include=["object"]
).columns

for col in categorical_columns:

    print(f"\n{col}")

    values = df[col].dropna().astype(str)

    print("Unique values:", values.nunique())

    print(
        values.value_counts().head(10).to_string()
    )


# ==========================================
# 4. NUMERICAL CONSISTENCY
# ==========================================

print("\n--- NUMERICAL CONSISTENCY ---")

numeric_columns = df.select_dtypes(
    include=np.number
).columns

for col in numeric_columns:

    negative_count = (
        (df[col] < 0).sum()
    )

    print(
        f"{col}: Negative values = "
        f"{negative_count}"
    )


# ==========================================
# 5. OUTLIER DETECTION USING IQR
# ==========================================

print("\n--- OUTLIER DETECTION (IQR) ---")

outlier_results = []

for col in numeric_columns:

    series = df[col].dropna()

    if len(series) == 0:
        continue

    Q1 = series.quantile(0.25)
    Q3 = series.quantile(0.75)

    IQR = Q3 - Q1

    lower_bound = Q1 - 1.5 * IQR
    upper_bound = Q3 + 1.5 * IQR

    outliers = (
        (series < lower_bound)
        |
        (series > upper_bound)
    )

    count = outliers.sum()

    outlier_results.append({
        "Attribute": col,
        "Q1": round(Q1, 2),
        "Q3": round(Q3, 2),
        "IQR": round(IQR, 2),
        "Lower Bound": round(lower_bound, 2),
        "Upper Bound": round(upper_bound, 2),
        "Outlier Count": int(count)
    })

outlier_df = pd.DataFrame(
    outlier_results
)

print(
    outlier_df.to_string(index=False)
)


# ==========================================
# 6. DESCRIPTIVE STATISTICS
# ==========================================

print("\n--- NUMERICAL SUMMARY ---")

print(
    df[numeric_columns].describe().T[
        [
            "count",
            "mean",
            "std",
            "min",
            "25%",
            "50%",
            "75%",
            "max"
        ]
    ].round(2).to_string()
)


# ==========================================
# FINAL SUMMARY
# ==========================================

print("\n========================================")
print("       DATA QUALITY SUMMARY")
print("========================================")

print("Rows              :", df.shape[0])
print("Columns           :", df.shape[1])
print("Duplicate records :", df.duplicated().sum())

print(
    "Total missing values:",
    int(df.isnull().sum().sum())
)

print(
    "Total numeric attributes:",
    len(numeric_columns)
)

print(
    "Total categorical attributes:",
    len(categorical_columns)
)

print("\n========================================")
print("       QUALITY ASSESSMENT COMPLETED")
print("========================================")