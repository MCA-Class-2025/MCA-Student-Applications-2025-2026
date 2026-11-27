from pathlib import Path
import pandas as pd


# ============================================================
# REAL-TIME CPCB DATA PROCESSING
# ============================================================

INPUT_FILE = Path(
    "data/3b01bcb8-0b14-4abf-b6f2-c1bfd384ba69.csv"
)

OUTPUT_DIR = Path("live_data")
OUTPUT_DIR.mkdir(exist_ok=True)

OUTPUT_FILE = OUTPUT_DIR / "live_air_quality_processed.csv"


print("=" * 80)
print("REAL-TIME CPCB AIR QUALITY - DATA PROCESSING")
print("=" * 80)


# ------------------------------------------------------------
# 1. CHECK FILE
# ------------------------------------------------------------

if not INPUT_FILE.exists():
    print("\nERROR: Real-time CSV file not found:")
    print(INPUT_FILE)
    raise SystemExit


# ------------------------------------------------------------
# 2. LOAD DATA
# ------------------------------------------------------------

print("\nLoading:", INPUT_FILE)

df = pd.read_csv(INPUT_FILE, low_memory=False)

print("Original rows:", len(df))
print("Original columns:", len(df.columns))


# ------------------------------------------------------------
# 3. CLEAN COLUMN NAMES
# ------------------------------------------------------------

df.columns = df.columns.str.strip().str.lower()

print("\nColumns:")
print(df.columns.tolist())


# ------------------------------------------------------------
# 4. BASIC CLEANING
# ------------------------------------------------------------

required_columns = [
    "country",
    "state",
    "city",
    "station",
    "last_update",
    "pollutant_id",
    "pollutant_min",
    "pollutant_max",
    "pollutant_avg"
]

missing_columns = [
    col for col in required_columns
    if col not in df.columns
]

if missing_columns:
    print("\nERROR: Missing columns:")
    print(missing_columns)
    raise SystemExit


# ------------------------------------------------------------
# 5. CLEAN TEXT VALUES
# ------------------------------------------------------------

for col in [
    "country",
    "state",
    "city",
    "station",
    "pollutant_id"
]:
    df[col] = df[col].astype(str).str.strip()


# ------------------------------------------------------------
# 6. CONVERT NUMERIC VALUES
# ------------------------------------------------------------

numeric_columns = [
    "pollutant_min",
    "pollutant_max",
    "pollutant_avg",
    "latitude",
    "longitude"
]

for col in numeric_columns:
    if col in df.columns:
        df[col] = pd.to_numeric(
            df[col],
            errors="coerce"
        )


# ------------------------------------------------------------
# 7. CONVERT TIMESTAMP
# ------------------------------------------------------------

df["last_update"] = pd.to_datetime(
    df["last_update"],
    errors="coerce"
)


# ------------------------------------------------------------
# 8. REMOVE INVALID ROWS
# ------------------------------------------------------------

before = len(df)

df = df.dropna(
    subset=[
        "city",
        "station",
        "pollutant_id",
        "pollutant_avg"
    ]
)

removed = before - len(df)

print("\nInvalid rows removed:", removed)


# ------------------------------------------------------------
# 9. SHOW AVAILABLE CITIES
# ------------------------------------------------------------

print("\nAvailable cities:")

cities = sorted(
    df["city"].dropna().unique()
)

for city in cities:
    print("-", city)


# ------------------------------------------------------------
# 10. NORMALIZE POLLUTANT NAMES
# ------------------------------------------------------------

def normalize_pollutant(value):

    value = str(value).upper().strip()

    mapping = {
        "PM2.5": "PM2.5",
        "PM25": "PM2.5",
        "PM10": "PM10",
        "NO2": "NO2",
        "SO2": "SO2",
        "CO": "CO",
        "O3": "O3",
        "OZONE": "O3",
        "NH3": "NH3"
    }

    return mapping.get(value, value)


df["pollutant_id"] = df["pollutant_id"].apply(
    normalize_pollutant
)


# ------------------------------------------------------------
# 11. FILTER PUNE + MUMBAI
# ------------------------------------------------------------

target_cities = [
    "Pune",
    "Mumbai"
]

live_df = df[
    df["city"].isin(target_cities)
].copy()


print("\nRows for Pune + Mumbai:", len(live_df))


# ------------------------------------------------------------
# 12. CONVERT POLLUTANTS FROM ROWS TO COLUMNS
# ------------------------------------------------------------

pivot_df = live_df.pivot_table(
    index=[
        "city",
        "station",
        "last_update"
    ],
    columns="pollutant_id",
    values="pollutant_avg",
    aggfunc="mean"
).reset_index()


# Remove pivot column index name

pivot_df.columns.name = None


# ------------------------------------------------------------
# 13. RENAME POLLUTANT COLUMNS
# ------------------------------------------------------------

rename_map = {
    "PM2.5": "PM2.5 (µg/m³)",
    "PM10": "PM10 (µg/m³)",
    "NO2": "NO2 (µg/m³)",
    "SO2": "SO2 (µg/m³)",
    "CO": "CO (mg/m³)",
    "O3": "Ozone (µg/m³)",
    "NH3": "NH3 (µg/m³)"
}

pivot_df = pivot_df.rename(
    columns=rename_map
)


# ------------------------------------------------------------
# 14. SORT
# ------------------------------------------------------------

pivot_df = pivot_df.sort_values(
    ["city", "last_update"]
)


# ------------------------------------------------------------
# 15. SAVE
# ------------------------------------------------------------

pivot_df.to_csv(
    OUTPUT_FILE,
    index=False
)


# ------------------------------------------------------------
# 16. DISPLAY RESULT
# ------------------------------------------------------------

print("\n" + "=" * 80)
print("PROCESSED LIVE DATA")
print("=" * 80)

print("\nRows:", len(pivot_df))
print("Columns:", len(pivot_df.columns))

print("\nCities:")

print(
    pivot_df["city"]
    .value_counts()
)


print("\nColumns:")

for col in pivot_df.columns:
    print("-", col)


print("\nLatest records:")

print(
    pivot_df.tail(10).to_string(index=False)
)


print("\nSaved:")
print(OUTPUT_FILE)

print("\n" + "=" * 80)
print("LIVE DATA PROCESSING COMPLETE")
print("=" * 80)