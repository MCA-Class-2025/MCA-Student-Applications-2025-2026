
import pandas as pd
import os

# -----------------------------------------
# PART F: BEFORE FUSION VS AFTER FUSION
# -----------------------------------------

files = {
    "Original WDI": "wdi_country_baseline_multiyear.csv",
    "Fused Dataset": "data/fused_country_intelligence.csv",
    "REST Countries": "data/rest_countries.csv",
    "Open-Meteo": "data/open_meteo_weather.csv",
    "Frankfurter": "data/frankfurter_rates.csv",
    "OpenAQ": "data/openaq_air_quality.csv",
    "Nager.Date": "data/nager_holidays.csv"
}

data = {}

for name, path in files.items():
    if os.path.exists(path):
        data[name] = pd.read_csv(path, low_memory=False)
    else:
        print(f"File not found: {path}")

wdi = data["Original WDI"]
fused = data["Fused Dataset"]

# -----------------------------------------
# 1. DATASET COMPARISON
# -----------------------------------------

comparison = []

for name, df in data.items():

    if "Country Code" in df.columns:
        key = "Country Code"
    elif "ISO Alpha-3" in df.columns:
        key = "ISO Alpha-3"
    elif "ISO Alpha-2" in df.columns:
        key = "ISO Alpha-2"
    else:
        key = None

    unique_countries = (
        df[key].nunique()
        if key else "Not available"
    )

    comparison.append({
        "Dataset": name,
        "Rows": len(df),
        "Columns": len(df.columns),
        "Unique Country Codes": unique_countries,
        "Missing Cells": int(df.isna().sum().sum()),
        "Duplicate Rows": int(df.duplicated().sum())
    })

comparison_df = pd.DataFrame(comparison)
comparison_df.to_csv("data/part_f_dataset_comparison.csv", index=False)

print("\n========== DATASET COMPARISON ==========")
print(comparison_df.to_string(index=False))

# -----------------------------------------
# 2. ATTRIBUTE COMPARISON
# -----------------------------------------

wdi_columns = set(wdi.columns)
fused_columns = set(fused.columns)

shared_columns = sorted(wdi_columns.intersection(fused_columns))
new_columns = sorted(fused_columns - wdi_columns)

print("\n========== SHARED ATTRIBUTES ==========")
for col in shared_columns:
    print("-", col)

print("\n========== NEW ATTRIBUTES IN FUSED DATASET ==========")
for col in new_columns:
    print("-", col)

print("\nTotal shared attributes:", len(shared_columns))
print("Total new attributes:", len(new_columns))

# -----------------------------------------
# 3. COUNTRY COVERAGE BY API
# -----------------------------------------

api_key_columns = {
    "REST Countries": "ISO Alpha-3",
    "Open-Meteo": "ISO Alpha-3",
    "Frankfurter": "ISO Alpha-3",
    "OpenAQ": "ISO Alpha-3",
    "Nager.Date": "Country Code"
}

coverage = []

for api_name, key in api_key_columns.items():

    if api_name not in data:
        continue

    df = data[api_name]

    if key in df.columns:
        coverage.append({
            "API": api_name,
            "Records": len(df),
            "Unique Country Codes": df[key].nunique()
        })

coverage_df = pd.DataFrame(coverage)
coverage_df.to_csv("data/part_f_api_coverage.csv", index=False)

print("\n========== API COUNTRY COVERAGE ==========")
print(coverage_df.to_string(index=False))

# -----------------------------------------
# 4. FUSED DATASET MISSING VALUES
# -----------------------------------------

missing = pd.DataFrame({
    "Column": fused.columns,
    "Missing Values": fused.isna().sum().values,
    "Missing Percentage": (
        fused.isna().mean().values * 100
    ).round(2)
})

missing = missing.sort_values(
    by="Missing Percentage",
    ascending=False
)

missing.to_csv("data/part_f_missing_values.csv", index=False)

print("\n========== TOP 15 MISSING VALUE COLUMNS ==========")
print(missing.head(15).to_string(index=False))

# -----------------------------------------
# 5. DUPLICATE COUNTRY CHECK
# -----------------------------------------

print("\n========== DUPLICATE COUNTRY CHECK ==========")

if "Country Code" in fused.columns:
    print(
        "Fused duplicate country codes:",
        fused["Country Code"].duplicated().sum()
    )

if "Country Code" in wdi.columns and "Year" in wdi.columns:
    print(
        "WDI duplicate country-year records:",
        wdi.duplicated(subset=["Country Code", "Year"]).sum()
    )

# -----------------------------------------
# 6. COUNTRY OVERLAP
# -----------------------------------------

if "Country Code" in wdi.columns and "Country Code" in fused.columns:

    wdi_countries = set(wdi["Country Code"].dropna().astype(str))
    fused_countries = set(fused["Country Code"].dropna().astype(str))

    matched = wdi_countries.intersection(fused_countries)
    only_wdi = wdi_countries - fused_countries
    only_fused = fused_countries - wdi_countries

    print("\n========== COUNTRY OVERLAP ==========")
    print("Unique WDI country codes:", len(wdi_countries))
    print("Unique fused country codes:", len(fused_countries))
    print("Matching country codes:", len(matched))
    print("Only in WDI:", len(only_wdi))
    print("Only in fused dataset:", len(only_fused))

print("\n========== PART F ANALYSIS COMPLETE ==========")
print("Three CSV reports have been saved inside the data folder.")
