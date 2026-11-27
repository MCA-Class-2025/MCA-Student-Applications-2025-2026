import json
import pandas as pd
import numpy as np

print("--- STARTING DATA FUSION PIPELINE ---")

# 1. Load baseline WHR dataset
df_base = pd.read_csv("data/original_dataset.csv")
print(f"Loaded Baseline Dataset: {df_base.shape[0]} rows, {df_base.shape[1]} columns")

# 2. Load collected API records
with open("data/api_data_raw.json", "r", encoding="utf-8") as f:
    api_records = json.load(f)

df_api = pd.DataFrame(api_records)
print(f"Loaded API Intelligence: {df_api.shape[0]} records, {df_api.shape[1]} attributes")

# 3. Perform Left Join on 'country' (preserving baseline cardinality)
df_fused = pd.merge(df_base, df_api, on="country", how="left")

# 4. Data Fusion Validation (Part C Checklist)
print("\n--- FUSION VALIDATION (Part C) ---")
print(f"Pre-merge row count: {len(df_base)}")
print(f"Post-merge row count: {len(df_fused)}")
assert len(df_base) == len(df_fused), "Integrity Alert: Row count mismatch after join!"

# Check for duplicates on primary key
dup_count = df_fused["country"].duplicated().sum()
print(f"Duplicate primary keys ('country'): {dup_count}")
assert dup_count == 0, "Integrity Alert: Duplicate records detected!"

# Check ISO3 mapping coverage
iso_coverage = (df_fused["iso3"].notna().sum() / len(df_fused)) * 100
print(f"ISO-3 Common Key Match Rate: {iso_coverage:.1f}%")

# 5. Data Quality & Cleansing (Part D Checklist)
print("\n--- DATA QUALITY ASSESSMENT (Part D) ---")
print("Null values per column:")
nulls = df_fused.isnull().sum()
for col, val in nulls[nulls > 0].items():
    print(f" - {col}: {val} missing ({val/len(df_fused)*100:.1f}%)")

# Handle numeric nulls with regional or global median imputation where appropriate
numeric_cols = [
    "exchange_rate_usd", "wb_gdp_usd", "wb_life_expectancy",
    "annual_mean_temp_c", "annual_precipitation_mm"
]
for col in numeric_cols:
    if col in df_fused.columns and df_fused[col].isnull().sum() > 0:
        median_val = df_fused[col].median()
        df_fused[col] = df_fused[col].fillna(median_val)
        print(f" Imputed missing values in '{col}' using median: {median_val:.2f}")

# Clean textual fields
df_fused["capital"] = df_fused["capital"].fillna("Not Available")
df_fused["region"] = df_fused["region"].fillna("Global")
df_fused["currency_code"] = df_fused["currency_code"].fillna("N/A")
df_fused["wiki_summary"] = df_fused["wiki_summary"].fillna(
    df_fused["country"] + " is an officially recognized sovereign nation."
)

# 6. Export Final Fused Dataset
output_path = "data/fused_dataset.csv"
df_fused.to_csv(output_path, index=False)

print("\n--- DATA FUSION COMPLETE ---")
print(f"Saved fused dataset to: {output_path}")
print(f"Final Dimension: {df_fused.shape[0]} rows x {df_fused.shape[1]} columns")
print("\nSample Preview (First 3 Rows):")
print(df_fused[["country", "happiness_score", "capital", "currency_code", "annual_mean_temp_c", "wb_life_expectancy"]].head(3))