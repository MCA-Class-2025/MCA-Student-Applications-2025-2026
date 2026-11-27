from pathlib import Path
import pandas as pd


# ============================================================
# OPENWEATHER LIVE DATA - INTEGRATION
# ============================================================

WEATHER_FILE = Path("live_data/openweather_current.csv")

OUTPUT_DIR = Path("live_data")
OUTPUT_DIR.mkdir(exist_ok=True)

OUTPUT_FILE = OUTPUT_DIR / "openweather_live_data.csv"


print("=" * 90)
print("OPENWEATHER LIVE DATA - INTEGRATION")
print("=" * 90)


# ------------------------------------------------------------
# 1. CHECK OPENWEATHER FILE
# ------------------------------------------------------------

if not WEATHER_FILE.exists():

    print("\nERROR: OpenWeather data file not found:")
    print(WEATHER_FILE)

    print("\nRun this first:")
    print("python openweather_api.py")

    raise SystemExit(1)


# ------------------------------------------------------------
# 2. LOAD DATA
# ------------------------------------------------------------

print("\nLoading:")
print(WEATHER_FILE)

df = pd.read_csv(
    WEATHER_FILE,
    low_memory=False
)


print("\nRows:", len(df))

print("\nColumns:")
for col in df.columns:
    print("-", col)


# ------------------------------------------------------------
# 3. CLEAN COLUMN NAMES
# ------------------------------------------------------------

df.columns = (
    df.columns
    .str.strip()
)


# ------------------------------------------------------------
# 4. CLEAN CITY
# ------------------------------------------------------------

if "City" in df.columns:

    df["City"] = (
        df["City"]
        .astype(str)
        .str.strip()
    )

else:

    print("\nERROR: City column not found.")

    raise SystemExit(1)


# ------------------------------------------------------------
# 5. TIMESTAMP
# ------------------------------------------------------------

if "Timestamp" in df.columns:

    df["Timestamp"] = pd.to_datetime(
        df["Timestamp"],
        errors="coerce",
        utc=True
    )


# ------------------------------------------------------------
# 6. NUMERIC COLUMNS
# ------------------------------------------------------------

numeric_columns = [
    "Temperature (°C)",
    "Humidity (%)",
    "Pressure (hPa)",
    "Wind_Speed (m/s)",
    "Wind_Direction (deg)",
    "Rain_1h (mm)"
]


for col in numeric_columns:

    if col in df.columns:

        df[col] = pd.to_numeric(
            df[col],
            errors="coerce"
        )


# ------------------------------------------------------------
# 7. REMOVE INVALID CITIES
# ------------------------------------------------------------

df = df.dropna(
    subset=["City"]
).copy()


# ------------------------------------------------------------
# 8. SAVE STANDARDIZED FILE
# ------------------------------------------------------------

df.to_csv(
    OUTPUT_FILE,
    index=False
)


# ------------------------------------------------------------
# 9. DISPLAY
# ------------------------------------------------------------

print("\n" + "=" * 90)
print("OPENWEATHER DATA READY")
print("=" * 90)

print("\nCities successfully collected:")

for city in sorted(df["City"].unique()):

    print("-", city)


print("\nData:")

print(
    df.to_string(
        index=False
    )
)


print("\nSaved:")
print(OUTPUT_FILE)

print("\n" + "=" * 90)
print("OPENWEATHER INTEGRATION COMPLETE")
print("=" * 90)