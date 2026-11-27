from pathlib import Path
import pandas as pd
import re

# ============================================================
# CPCB HISTORICAL DATA PROCESSOR
# Reads all raw_data_hourly_*.csv files
# Extracts station, city, timestamp and PM2.5
# Creates one clean historical dataset
# ============================================================

PROJECT_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = PROJECT_DIR / "data"
OUTPUT_FILE = OUTPUT_DIR / "cpcb_historical_data.csv"

OUTPUT_DIR.mkdir(exist_ok=True)

# Find all CPCB hourly files anywhere inside the project
files = list(PROJECT_DIR.rglob("raw_data_hourly*.csv"))

print("=" * 80)
print("CPCB HISTORICAL DATA PROCESSOR")
print("=" * 80)

print(f"\nCPCB files found: {len(files)}")

if not files:
    print("\nERROR: No CPCB files found.")
    print("Make sure the raw_data_hourly_*.csv files are inside your project folder.")
    raise SystemExit(1)


# ------------------------------------------------------------
# Extract station and city from filename
#
# Example:
# raw_data_hourly_alandi,_pune_-_iitm_1H.csv
#
# Location = Alandi
# City     = Pune
# ------------------------------------------------------------

def extract_location(filename):

    name = filename

    # Remove prefix and suffix
    name = re.sub(r"^raw_data_hourly_", "", name, flags=re.IGNORECASE)
    name = re.sub(r"_1H\.csv$", "", name, flags=re.IGNORECASE)

    # Separate location and remaining information
    # Example:
    # alandi,_pune_-_iitm
    match = re.match(r"(.+?),_([^_]+?)_-_", name)

    if match:
        location = match.group(1)
        city = match.group(2)
    else:
        # Fallback if filename has an unexpected format
        location = name
        city = "Unknown"

    location = location.replace("_", " ").strip()
    city = city.replace("_", " ").strip()

    # Clean capitalization
    location = location.title()
    city = city.title()

    return location, city


# ------------------------------------------------------------
# Process files
# ------------------------------------------------------------

all_data = []

successful_files = 0
failed_files = 0

for index, file in enumerate(files, 1):

    try:

        df = pd.read_csv(file)

        # Clean column names
        df.columns = [str(col).strip() for col in df.columns]

        # Check required columns
        if "Timestamp" not in df.columns:
            print(f"[SKIP] {file.name} -> Timestamp column missing")
            failed_files += 1
            continue

        if "PM2.5 (µg/m³)" not in df.columns:
            print(f"[SKIP] {file.name} -> PM2.5 column missing")
            failed_files += 1
            continue

        location, city = extract_location(file.name)

        # Convert timestamp
        df["Timestamp"] = pd.to_datetime(
            df["Timestamp"],
            errors="coerce"
        )

        # Convert PM2.5 to numeric
        df["PM2.5 (µg/m³)"] = pd.to_numeric(
            df["PM2.5 (µg/m³)"],
            errors="coerce"
        )

        # Keep only valid records
        df = df.dropna(
            subset=["Timestamp", "PM2.5 (µg/m³)"]
        )

        # Remove impossible PM2.5 values
        df = df[
            (df["PM2.5 (µg/m³)"] >= 0)
            & (df["PM2.5 (µg/m³)"] <= 1000)
        ]

        if df.empty:
            print(f"[SKIP] {file.name} -> No valid PM2.5 records")
            failed_files += 1
            continue

        # Add location information
        df["Location"] = location
        df["City"] = city
        df["Source_File"] = file.name

        # Select useful fields
        columns = [
            "City",
            "Location",
            "Timestamp",
            "PM2.5 (µg/m³)",
            "PM10 (µg/m³)",
            "NO2 (µg/m³)",
            "SO2 (µg/m³)",
            "CO (mg/m³)",
            "Ozone (µg/m³)",
            "NH3 (µg/m³)",
            "AT (°C)",
            "RH (%)",
            "WS (m/s)",
            "WD (deg)",
            "RF (mm)",
            "Source_File"
        ]

        # Keep only columns that actually exist
        available_columns = [
            col for col in columns
            if col in df.columns
        ]

        df = df[available_columns]

        all_data.append(df)

        successful_files += 1

        print(
            f"[{index}/{len(files)}] "
            f"{city} - {location}: "
            f"{len(df)} valid records"
        )

    except Exception as e:

        failed_files += 1

        print(
            f"[ERROR] {file.name}: {e}"
        )


# ------------------------------------------------------------
# Combine all files
# ------------------------------------------------------------

if not all_data:
    print("\nERROR: No valid CPCB data was processed.")
    raise SystemExit(1)

combined = pd.concat(
    all_data,
    ignore_index=True
)


# ------------------------------------------------------------
# Remove exact duplicates
# ------------------------------------------------------------

combined = combined.drop_duplicates(
    subset=[
        "City",
        "Location",
        "Timestamp"
    ]
)


# ------------------------------------------------------------
# Sort data
# ------------------------------------------------------------

combined = combined.sort_values(
    by=[
        "City",
        "Location",
        "Timestamp"
    ]
).reset_index(drop=True)


# ------------------------------------------------------------
# Save CSV
# ------------------------------------------------------------

combined.to_csv(
    OUTPUT_FILE,
    index=False
)


# ------------------------------------------------------------
# Summary
# ------------------------------------------------------------

unique_cities = sorted(
    combined["City"].dropna().unique()
)

unique_locations = sorted(
    combined["Location"].dropna().unique()
)

print("\n" + "=" * 80)
print("PROCESSING COMPLETE")
print("=" * 80)

print(f"\nFiles found          : {len(files)}")
print(f"Files processed      : {successful_files}")
print(f"Files skipped/failed : {failed_files}")

print(f"\nUnique cities        : {len(unique_cities)}")
print(f"Unique locations     : {len(unique_locations)}")
print(f"Total records        : {len(combined)}")

print(f"\nOutput file:")
print(OUTPUT_FILE)

print("\nCities available:")

for number, city in enumerate(unique_cities, 1):
    print(f"{number:3}. {city}")

print("\n" + "=" * 80)
print("CPCB HISTORICAL DATASET CREATED SUCCESSFULLY")
print("=" * 80)