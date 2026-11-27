from pathlib import Path
import time
from urllib.parse import quote

import requests
import pandas as pd

from config import WAQI_API_KEY


# ============================================================
# WAQI API - REAL-TIME AIR QUALITY DATA COLLECTION
# Uses cities from the CPCB historical dataset instead of the
# old fixed 11-city list.
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

DATA_DIR = BASE_DIR / "data"
LIVE_DIR = BASE_DIR / "live_data"

LIVE_DIR.mkdir(exist_ok=True)

CPCB_FILE = DATA_DIR / "cpcb_historical_data.csv"
OUTPUT_FILE = LIVE_DIR / "waqi_live_data.csv"

BASE_URL = "https://api.waqi.info/feed"


# ============================================================
# LOAD CITIES FROM CPCB DATASET
# ============================================================

def load_cpcb_cities():
    if not CPCB_FILE.exists():
        print("\nERROR: CPCB historical dataset was not found.")
        print(f"Expected file: {CPCB_FILE}")
        raise SystemExit(1)

    try:
        df = pd.read_csv(
            CPCB_FILE,
            usecols=["City"],
            low_memory=False
        )
    except Exception as exc:
        print("\nERROR: Could not read CPCB historical dataset.")
        print(exc)
        raise SystemExit(1)

    cities = (
        df["City"]
        .dropna()
        .astype(str)
        .str.strip()
    )

    cities = cities[
        (cities != "")
        & (cities.str.lower() != "unknown")
    ]

    # Remove duplicate names and sort
    cities = sorted(cities.unique().tolist())

    return cities


CITIES = load_cpcb_cities()


# ============================================================
# CHECK API KEY
# ============================================================

if not WAQI_API_KEY or not str(WAQI_API_KEY).strip():

    print("\nERROR: WAQI API key is missing.")
    print("Add WAQI_API_KEY to config.py")

    raise SystemExit(1)


# ============================================================
# HEADER
# ============================================================

print("=" * 90)
print("WAQI API - LIVE AIR QUALITY DATA COLLECTION")
print("=" * 90)

print("\nCPCB cities available:", len(CITIES))
print("WAQI will be queried for all available cities.")

print("\nFirst cities:")
for city in CITIES[:20]:
    print("-", city)

if len(CITIES) > 20:
    print(f"... and {len(CITIES) - 20} more cities")


# ============================================================
# FETCH DATA
# ============================================================

records = []
failed_cities = []

print("\nFetching WAQI live air-quality data...")


for number, city in enumerate(CITIES, start=1):

    print(f"\n[{number}/{len(CITIES)}] Processing: {city}")

    # URL-encode city name so spaces/special characters are safe.
    encoded_city = quote(city, safe="")

    url = f"{BASE_URL}/{encoded_city}/"

    params = {
        "token": WAQI_API_KEY
    }

    try:

        response = requests.get(
            url,
            params=params,
            timeout=20
        )

        # ----------------------------------------------------
        # CHECK HTTP RESPONSE
        # ----------------------------------------------------

        if response.status_code != 200:

            print("ERROR: HTTP request failed.")
            print("Status code:", response.status_code)

            failed_cities.append(
                (city, f"HTTP {response.status_code}")
            )

            continue

        result = response.json()

        # ----------------------------------------------------
        # CHECK WAQI RESPONSE
        # ----------------------------------------------------

        if result.get("status") != "ok":

            reason = result.get(
                "data",
                "Unknown WAQI error"
            )

            print("ERROR: WAQI did not return valid data.")
            print("Reason:", reason)

            failed_cities.append(
                (city, str(reason))
            )

            continue

        data = result.get("data") or {}

        iaqi = data.get("iaqi") or {}
        city_info = data.get("city") or {}

        # ----------------------------------------------------
        # LOCATION
        # ----------------------------------------------------

        geo = city_info.get("geo") or []

        latitude = None
        longitude = None

        if isinstance(geo, (list, tuple)) and len(geo) == 2:

            try:
                latitude = float(geo[0])
                longitude = float(geo[1])
            except (TypeError, ValueError):
                pass

        # ----------------------------------------------------
        # HELPER TO READ WAQI MEASUREMENTS
        # ----------------------------------------------------

        def get_iaqi_value(name):
            value = iaqi.get(name)

            if isinstance(value, dict):
                return value.get("v")

            return value

        pm25 = get_iaqi_value("pm25")
        pm10 = get_iaqi_value("pm10")
        no2 = get_iaqi_value("no2")
        so2 = get_iaqi_value("so2")
        o3 = get_iaqi_value("o3")
        co = get_iaqi_value("co")

        temperature = get_iaqi_value("t")
        humidity = get_iaqi_value("h")
        pressure = get_iaqi_value("p")

        aqi = data.get("aqi")

        # ----------------------------------------------------
        # DO NOT SAVE A COMPLETELY EMPTY SUCCESS RESPONSE
        # ----------------------------------------------------

        if (
            aqi is None
            and pm25 is None
            and pm10 is None
            and no2 is None
            and so2 is None
            and o3 is None
            and co is None
        ):

            print(
                "SKIPPED: WAQI response contained no usable "
                "air-quality measurement."
            )

            failed_cities.append(
                (city, "No usable air-quality measurement")
            )

            continue

        # ----------------------------------------------------
        # CREATE RECORD
        # ----------------------------------------------------

        record = {
            "City": city,
            "WAQI_Station": city_info.get("name"),
            "Latitude": latitude,
            "Longitude": longitude,
            "AQI": aqi,
            "PM2.5": pm25,
            "PM10": pm10,
            "NO2": no2,
            "SO2": so2,
            "O3": o3,
            "CO": co,
            "Temperature": temperature,
            "Humidity": humidity,
            "Pressure": pressure,
            "Timestamp": (
                data.get("time") or {}
            ).get("s")
        }

        records.append(record)

        # ----------------------------------------------------
        # DISPLAY RESULT
        # ----------------------------------------------------

        print("Status: SUCCESS")

        print(
            "Station:",
            record["WAQI_Station"]
        )

        print(
            "AQI:",
            record["AQI"]
        )

        print(
            "PM2.5:",
            record["PM2.5"]
        )

        # Small delay to avoid hammering the service.
        time.sleep(0.25)

    except requests.exceptions.Timeout:

        print(
            f"ERROR: Request timed out for {city}"
        )

        failed_cities.append(
            (city, "Request timeout")
        )

    except requests.exceptions.ConnectionError:

        print(
            f"ERROR: Internet connection problem for {city}"
        )

        failed_cities.append(
            (city, "Connection error")
        )

    except requests.exceptions.RequestException as exc:

        print(
            f"ERROR: Request failed for {city}"
        )

        print(exc)

        failed_cities.append(
            (city, str(exc))
        )

    except ValueError as exc:

        print(
            f"ERROR: WAQI returned invalid JSON for {city}"
        )

        print(exc)

        failed_cities.append(
            (city, "Invalid JSON")
        )

    except Exception as exc:

        print(
            f"ERROR: Unexpected error for {city}"
        )

        print(exc)

        failed_cities.append(
            (city, str(exc))
        )


# ============================================================
# CHECK RESULTS
# ============================================================

if not records:

    print("\n" + "=" * 90)
    print("NO WAQI DATA RECEIVED")
    print("=" * 90)

    print(
        "\nPossible reasons:"
    )

    print(
        "1. WAQI API key is incorrect"
    )

    print(
        "2. WAQI API key is not active"
    )

    print(
        "3. The WAQI station/city is unavailable"
    )

    print(
        "4. API request limit reached"
    )

    print(
        "5. Internet connection problem"
    )

    raise SystemExit(1)


# ============================================================
# CREATE DATAFRAME
# ============================================================

df = pd.DataFrame(records)


# ============================================================
# CLEAN BASIC TYPES
# ============================================================

numeric_columns = [
    "Latitude",
    "Longitude",
    "AQI",
    "PM2.5",
    "PM10",
    "NO2",
    "SO2",
    "O3",
    "CO",
    "Temperature",
    "Humidity",
    "Pressure",
]

for column in numeric_columns:

    if column in df.columns:
        df[column] = pd.to_numeric(
            df[column],
            errors="coerce"
        )


# ============================================================
# SORT
# ============================================================

df = df.sort_values(
    "City"
).reset_index(drop=True)


# ============================================================
# SAVE
# ============================================================

df.to_csv(
    OUTPUT_FILE,
    index=False
)


# ============================================================
# DISPLAY SUMMARY
# ============================================================

successful_count = len(df)
failed_count = len(failed_cities)

print("\n" + "=" * 90)
print("WAQI COLLECTION SUMMARY")
print("=" * 90)

print(
    f"\nCPCB cities requested : {len(CITIES)}"
)

print(
    f"Successful WAQI records: {successful_count}"
)

print(
    f"Failed/unavailable cities: {failed_count}"
)

print(
    f"\nSaved: {OUTPUT_FILE}"
)


# ============================================================
# DISPLAY DATA
# ============================================================

display_columns = [
    "City",
    "WAQI_Station",
    "AQI",
    "PM2.5",
    "PM10",
    "NO2",
    "SO2",
    "O3",
    "CO",
    "Timestamp",
]

display_columns = [
    column
    for column in display_columns
    if column in df.columns
]

print("\n" + "=" * 90)
print("REAL WAQI DATA")
print("=" * 90)

print(
    df[display_columns]
    .to_string(index=False)
)


# ============================================================
# FAILED CITY SUMMARY
# ============================================================

if failed_cities:

    print("\n" + "=" * 90)
    print("CITIES WITHOUT USABLE WAQI DATA")
    print("=" * 90)

    for city, reason in failed_cities:
        print(
            f"- {city}: {reason}"
        )


print("\n" + "=" * 90)
print("WAQI API COLLECTION COMPLETE")
print("=" * 90)