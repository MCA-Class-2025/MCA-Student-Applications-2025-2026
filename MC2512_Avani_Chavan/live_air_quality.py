from pathlib import Path
import os
import requests
import pandas as pd


# ============================================================
# REAL-TIME AIR QUALITY DATA COLLECTOR
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

RESOURCE_ID = "3b01bcb8-0b14-4abf-b6f2-c1bfd384ba69"

API_KEY = os.getenv("DATA_GOV_API_KEY")

LOCATIONS_FILE = BASE_DIR / "locations.csv"

OUTPUT_DIR = BASE_DIR / "live_data"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_FILE = OUTPUT_DIR / "live_air_quality.csv"


# ============================================================
# HEADER
# ============================================================

print("=" * 80)
print("REAL-TIME CPCB AIR QUALITY DATA")
print("=" * 80)


# ============================================================
# CHECK API KEY
# ============================================================

if not API_KEY:

    print()
    print("=" * 80)
    print("DATA.GOV.IN API KEY REQUIRED")
    print("=" * 80)

    print("""
Set your API key first.

PowerShell:

$env:DATA_GOV_API_KEY="YOUR_API_KEY"

Then run:

python live_air_quality.py
""")

    raise SystemExit(1)


print()
print("Data.gov.in API key detected.")


# ============================================================
# LOAD LOCATIONS
# ============================================================

if not LOCATIONS_FILE.exists():

    raise FileNotFoundError(
        f"locations.csv not found:\n{LOCATIONS_FILE}"
    )


locations_df = pd.read_csv(
    LOCATIONS_FILE
)

locations_df.columns = [
    str(column).strip()
    for column in locations_df.columns
]


if "City" not in locations_df.columns:

    raise ValueError(
        "locations.csv must contain a 'City' column."
    )


configured_cities = (
    locations_df["City"]
    .dropna()
    .astype(str)
    .str.strip()
)

configured_cities = (
    configured_cities[
        configured_cities != ""
    ]
    .drop_duplicates()
    .tolist()
)


if not configured_cities:

    raise ValueError(
        "No cities found in locations.csv."
    )


print()
print(
    f"Configured locations: "
    f"{len(configured_cities)}"
)

print()
print("Configured cities:")

for city in configured_cities:
    print(f"- {city}")


# ============================================================
# API URL
# ============================================================

URL = (
    "https://api.data.gov.in/resource/"
    f"{RESOURCE_ID}"
)


# ============================================================
# REQUEST PARAMETERS
# ============================================================

params = {
    "api-key": API_KEY,
    "format": "json",
    "limit": 1000
}


# ============================================================
# REQUEST DATA
# ============================================================

print()
print("-" * 80)
print("REQUESTING CURRENT CPCB DATA")
print("-" * 80)

print()
print("Resource ID:")
print(RESOURCE_ID)

print()
print("Requesting current data...")


try:

    response = requests.get(
        URL,
        params=params,
        timeout=60
    )

    response.raise_for_status()

except requests.exceptions.Timeout:

    print()
    print("ERROR: Connection timed out.")
    print()
    print(
        "The data.gov.in server did not respond "
        "within the timeout period."
    )

    raise SystemExit(1)

except requests.exceptions.SSLError as error:

    print()
    print("ERROR: SSL connection failed.")
    print(error)

    raise SystemExit(1)

except requests.exceptions.ConnectionError as error:

    print()
    print("ERROR: Could not connect to data.gov.in.")
    print(error)

    raise SystemExit(1)

except requests.exceptions.HTTPError as error:

    print()
    print(
        "ERROR: data.gov.in returned an HTTP error."
    )

    print(
        "HTTP Status:",
        response.status_code
    )

    print(
        "Response:",
        response.text[:1000]
    )

    raise SystemExit(1)

except requests.exceptions.RequestException as error:

    print()
    print(
        "ERROR: API request failed."
    )

    print(error)

    raise SystemExit(1)


# ============================================================
# PARSE RESPONSE
# ============================================================

print()
print(
    "HTTP Status:",
    response.status_code
)


try:

    data = response.json()

except ValueError:

    print()
    print(
        "ERROR: API did not return valid JSON."
    )

    print(
        response.text[:2000]
    )

    raise SystemExit(1)


records = data.get(
    "records",
    []
)


if not records:

    print()
    print("=" * 80)
    print("NO CPCB RECORDS RETURNED")
    print("=" * 80)

    print()
    print("API response:")

    print(data)

    raise SystemExit(1)


df = pd.DataFrame(
    records
)


print()
print(
    "Records received:",
    len(df)
)


# ============================================================
# DISPLAY COLUMNS
# ============================================================

print()
print("Columns received:")

for column in df.columns:

    print(
        f"- {column}"
    )


# ============================================================
# CHECK CITY COLUMN
# ============================================================

if "city" not in df.columns:

    raise ValueError(
        "CPCB response does not contain a 'city' column."
    )


# ============================================================
# NORMALIZE CITY NAMES
# ============================================================

df["city"] = (
    df["city"]
    .astype(str)
    .str.strip()
)


df["_city_key"] = (
    df["city"]
    .str.lower()
    .str.replace(
        r"\s+",
        " ",
        regex=True
    )
)


configured_city_map = {
    city.lower().strip(): city
    for city in configured_cities
}


# ============================================================
# FIND CONFIGURED CITIES IN CPCB DATA
# ============================================================

returned_city_keys = set(
    df["_city_key"].dropna()
)


available_city_keys = (
    returned_city_keys
    .intersection(
        configured_city_map.keys()
    )
)


available_cities = [
    configured_city_map[key]
    for key in sorted(
        available_city_keys
    )
]


missing_cities = [
    city
    for city in configured_cities
    if city.lower().strip()
    not in available_city_keys
]


# ============================================================
# DISPLAY SOURCE CITIES
# ============================================================

print()
print("=" * 80)
print("CITIES RETURNED BY CPCB")
print("=" * 80)

source_cities = (
    df["city"]
    .dropna()
    .drop_duplicates()
    .tolist()
)

for city in source_cities:

    print(
        f"- {city}"
    )


# ============================================================
# DISPLAY MATCHING LOCATIONS
# ============================================================

print()
print("=" * 80)
print("CONFIGURED LOCATIONS WITH LIVE CPCB DATA")
print("=" * 80)

if available_cities:

    for city in available_cities:

        print(
            f"- {city}"
        )

else:

    print(
        "None of the configured locations "
        "were found in the CPCB response."
    )


# ============================================================
# DISPLAY UNAVAILABLE LOCATIONS
# ============================================================

print()
print("=" * 80)
print("CONFIGURED LOCATIONS WITHOUT CPCB DATA")
print("=" * 80)

if missing_cities:

    for city in missing_cities:

        print(
            f"- {city}"
        )

else:

    print(
        "All configured locations have CPCB data."
    )


# ============================================================
# KEEP ONLY CONFIGURED LOCATIONS
# ============================================================

df = df[
    df["_city_key"].isin(
        configured_city_map.keys()
    )
].copy()


if df.empty:

    print()
    print(
        "No configured location was found "
        "in the CPCB response."
    )

    print()
    print(
        "The CPCB resource may currently return "
        "a different set of cities."
    )

    raise SystemExit(1)


# ============================================================
# REMOVE INTERNAL COLUMN
# ============================================================

df.drop(
    columns=["_city_key"],
    inplace=True
)


# ============================================================
# TIMESTAMP
# ============================================================

if "last_update" in df.columns:

    df["last_update"] = pd.to_datetime(
        df["last_update"],
        errors="coerce"
    )


# ============================================================
# SAVE
# ============================================================

df.to_csv(
    OUTPUT_FILE,
    index=False
)


# ============================================================
# SUMMARY
# ============================================================

print()
print("=" * 80)
print("LIVE CPCB DATA RECEIVED")
print("=" * 80)


print()
print(
    "Records after location filtering:",
    len(df)
)


print()
print("Records by city:")

print(
    df["city"]
    .value_counts()
    .to_string()
)


if "last_update" in df.columns:

    print()
    print(
        "Latest timestamp:"
    )

    print(
        df["last_update"].max()
    )


if "pollutant_id" in df.columns:

    print()
    print(
        "Pollutants:"
    )

    print(
        sorted(
            df["pollutant_id"]
            .dropna()
            .astype(str)
            .unique()
            .tolist()
        )
    )


print()
print("Latest records:")

print(
    df.head(20).to_string(
        index=False
    )
)


# ============================================================
# SAVE MESSAGE
# ============================================================

print()
print("Saved:")
print(OUTPUT_FILE)

print()
print("=" * 80)
print("LIVE DATA COLLECTION COMPLETE")
print("=" * 80)

print()
print(
    f"CPCB locations available: "
    f"{len(available_cities)}"
)

print(
    f"Configured locations unavailable: "
    f"{len(missing_cities)}"
)

print("=" * 80)