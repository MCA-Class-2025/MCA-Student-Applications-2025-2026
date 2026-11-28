import pandas as pd
from pathlib import Path


# ==========================================
# CONFIGURATION
# ==========================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]
INPUT_FILE = PROJECT_ROOT / "dataset" / "raw" / "india_2000_2024_daily_weather.csv"
OUTPUT_FILE = PROJECT_ROOT / "dataset" / "processed" / "weather_cleaned.csv"


# ==========================================
# WEATHER CODE MAPPING
# ==========================================

WEATHER_CODE_MAP = {

    0: "Clear sky",

    1: "Mainly clear",

    2: "Partly cloudy",

    3: "Overcast",

    51: "Light drizzle",

    53: "Moderate drizzle",

    55: "Dense drizzle",

    61: "Slight rain",

    63: "Moderate rain",

    65: "Heavy rain"

}


# ==========================================
# LOAD DATASET
# ==========================================

print("Loading dataset...")

df = pd.read_csv(INPUT_FILE)

print("Dataset loaded successfully.")


# ==========================================
# BASIC INFORMATION
# ==========================================

print("\n========== DATASET INFORMATION ==========")

print("Rows:", len(df))

print("Columns:", len(df.columns))


# ==========================================
# REMOVE DUPLICATES
# ==========================================

duplicate_count = df.duplicated().sum()

print("\nDuplicate records:", duplicate_count)


if duplicate_count > 0:

    df = df.drop_duplicates()

    print(
        "Removed duplicates:",
        duplicate_count
    )


# ==========================================
# CONVERT DATE
# ==========================================

df["date"] = pd.to_datetime(
    df["date"],
    errors="coerce"
)


# ==========================================
# REMOVE INVALID DATES
# ==========================================

invalid_dates = df["date"].isnull().sum()

print("\nInvalid dates:", invalid_dates)


if invalid_dates > 0:

    df = df.dropna(
        subset=["date"]
    )


# ==========================================
# NUMERIC COLUMNS
# ==========================================

numeric_columns = [

    "temperature_2m_max",

    "temperature_2m_min",

    "apparent_temperature_max",

    "apparent_temperature_min",

    "precipitation_sum",

    "rain_sum",

    "weather_code",

    "wind_speed_10m_max",

    "wind_gusts_10m_max",

    "wind_direction_10m_dominant"

]


# ==========================================
# CONVERT NUMERIC COLUMNS
# ==========================================

for column in numeric_columns:

    df[column] = pd.to_numeric(
        df[column],
        errors="coerce"
    )


# ==========================================
# WEATHER CODE → DESCRIPTION
# ==========================================

df["weather_description"] = (

    df["weather_code"]
    .map(WEATHER_CODE_MAP)

)


# ==========================================
# CHECK UNKNOWN WEATHER CODES
# ==========================================

unknown_codes = (

    df[
        df["weather_description"].isnull()
    ]["weather_code"]
    .unique()

)


if len(unknown_codes) > 0:

    print(
        "\nWARNING: Unknown weather codes:"
    )

    print(unknown_codes)


else:

    print(
        "\nAll weather codes mapped successfully."
    )


# ==========================================
# CHECK MISSING VALUES
# ==========================================

print("\n========== MISSING VALUES ==========")

print(
    df.isnull().sum()
)


# ==========================================
# REMOVE ROWS WITH IMPORTANT MISSING DATA
# ==========================================

df = df.dropna(
    subset=[
        "city",
        "date",
        "temperature_2m_max",
        "temperature_2m_min",
        "weather_code"
    ]
)


# ==========================================
# SORT DATA
# ==========================================

df = df.sort_values(
    by=[
        "city",
        "date"
    ]
)


# ==========================================
# RESET INDEX
# ==========================================

df = df.reset_index(
    drop=True
)


# ==========================================
# SAVE CLEAN DATASET
# ==========================================

df.to_csv(
    OUTPUT_FILE,
    index=False
)


# ==========================================
# FINAL INFORMATION
# ==========================================

print("\n==========================================")

print("DATA CLEANING COMPLETED")

print("==========================================")

print(
    "Final records:",
    len(df)
)

print(
    "Final columns:",
    len(df.columns)
)

print(
    "Output:",
    OUTPUT_FILE
)

print("\nWeather code distribution:")

print(
    df["weather_description"]
    .value_counts()
)

print("\n==========================================")