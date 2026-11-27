from pathlib import Path
import requests
import pandas as pd
from datetime import datetime, timezone
import time

from config import OPENWEATHER_API_KEY


# ============================================================
# OPENWEATHER API - LIVE WEATHER DATA COLLECTION
# UPDATED FOR ALL CPCB CITIES
# ============================================================

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "live_data"
OUTPUT_DIR.mkdir(exist_ok=True)

CPCB_FILE = DATA_DIR / "cpcb_historical_data.csv"
OUTPUT_FILE = OUTPUT_DIR / "openweather_current.csv"
COORDINATE_FILE = OUTPUT_DIR / "openweather_city_coordinates.csv"

WEATHER_URL = "https://api.openweathermap.org/data/2.5/weather"
GEOCODING_URL = "https://api.openweathermap.org/geo/1.0/direct"

# Number of seconds between API requests.
# This keeps the script gentle on API limits.
REQUEST_DELAY = 0.15


# ============================================================
# CHECK API KEY
# ============================================================

if not OPENWEATHER_API_KEY or len(OPENWEATHER_API_KEY.strip()) < 20:
    print("\nERROR: OpenWeather API key is missing or invalid.")
    print("Check config.py")
    raise SystemExit(1)

print("\nOpenWeather API key loaded successfully.")
print("API key length:", len(OPENWEATHER_API_KEY))


# ============================================================
# LOAD CITIES FROM CPCB DATASET
# ============================================================

def load_cpcb_cities():
    """Read all valid city names from the processed CPCB dataset."""

    if not CPCB_FILE.exists():
        print(f"\nERROR: CPCB dataset not found: {CPCB_FILE}")
        print("Create data/cpcb_historical_data.csv first.")
        raise SystemExit(1)

    try:
        df = pd.read_csv(
            CPCB_FILE,
            usecols=["City"],
            low_memory=False,
        )
    except Exception as exc:
        print(f"\nERROR: Could not read CPCB dataset: {exc}")
        raise SystemExit(1)

    cities = (
        df["City"]
        .dropna()
        .astype(str)
        .str.strip()
    )

    cities = cities[
        (cities != "") &
        (cities.str.lower() != "unknown")
    ]

    cities = sorted(cities.unique())

    if not cities:
        print("\nERROR: No valid cities were found in CPCB dataset.")
        raise SystemExit(1)

    return cities


CITIES = load_cpcb_cities()

print("=" * 90)
print("OPENWEATHER API - LIVE WEATHER DATA COLLECTION")
print("=" * 90)
print(f"\nCPCB dataset: {CPCB_FILE}")
print(f"Cities available from CPCB: {len(CITIES)}")
print("No fixed 11-city list is used.")


# ============================================================
# HELPER: SAFE NUMERIC VALUE
# ============================================================

def safe_number(value):
    try:
        if value is None or pd.isna(value):
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


# ============================================================
# LOAD / SAVE CACHED COORDINATES
# ============================================================

def load_cached_coordinates():
    if not COORDINATE_FILE.exists():
        return {}

    try:
        df = pd.read_csv(COORDINATE_FILE)
        required = {"City", "Latitude", "Longitude"}
        if not required.issubset(df.columns):
            return {}

        result = {}
        for _, row in df.iterrows():
            city = str(row["City"]).strip()
            lat = safe_number(row["Latitude"])
            lon = safe_number(row["Longitude"])

            if city and lat is not None and lon is not None:
                result[city] = {
                    "lat": lat,
                    "lon": lon,
                    "country": str(row.get("Country", "India")),
                    "state": str(row.get("State", "")),
                }

        return result

    except Exception as exc:
        print(f"Warning: could not read coordinate cache: {exc}")
        return {}


coordinate_cache = load_cached_coordinates()


def save_cached_coordinates(cache):
    rows = []

    for city, location in sorted(cache.items()):
        rows.append(
            {
                "City": city,
                "State": location.get("state", ""),
                "Country": location.get("country", "India"),
                "Latitude": location.get("lat"),
                "Longitude": location.get("lon"),
            }
        )

    pd.DataFrame(rows).to_csv(
        COORDINATE_FILE,
        index=False,
    )


# ============================================================
# GEOCODE MISSING CITIES
# ============================================================

def geocode_city(city):
    """Get real coordinates for an Indian city from OpenWeather."""

    params = {
        "q": f"{city},IN",
        "limit": 1,
        "appid": OPENWEATHER_API_KEY,
    }

    try:
        response = requests.get(
            GEOCODING_URL,
            params=params,
            timeout=15,
        )

        if response.status_code != 200:
            print(
                f"GEOCODING ERROR: {city} | "
                f"HTTP {response.status_code}"
            )
            return None

        results = response.json()

        if not results:
            print(f"GEOCODING: No result found for {city}")
            return None

        item = results[0]
        lat = safe_number(item.get("lat"))
        lon = safe_number(item.get("lon"))

        if lat is None or lon is None:
            print(f"GEOCODING: Invalid coordinates for {city}")
            return None

        country = str(item.get("country", ""))
        state = str(item.get("state", ""))

        return {
            "lat": lat,
            "lon": lon,
            "country": country,
            "state": state,
        }

    except requests.exceptions.Timeout:
        print(f"GEOCODING ERROR: Timeout for {city}")
        return None

    except requests.exceptions.RequestException as exc:
        print(f"GEOCODING ERROR: {city} | {exc}")
        return None

    except Exception as exc:
        print(f"GEOCODING ERROR: {city} | {exc}")
        return None


print("\nChecking coordinates...")

new_coordinates = 0

for index, city in enumerate(CITIES, start=1):

    if city in coordinate_cache:
        continue

    print(f"Geocoding [{index}/{len(CITIES)}]: {city}")

    location = geocode_city(city)

    if location is not None:
        coordinate_cache[city] = location
        new_coordinates += 1

    time.sleep(REQUEST_DELAY)

save_cached_coordinates(coordinate_cache)

print(
    f"\nCoordinate cache ready: {len(coordinate_cache)} cities"
)
print(
    f"New coordinates collected this run: {new_coordinates}"
)
print(f"Saved coordinate cache: {COORDINATE_FILE}")


# ============================================================
# FETCH LIVE WEATHER
# ============================================================

records = []
failed_cities = []

print("\nFetching live weather data...\n")

for index, city in enumerate(CITIES, start=1):

    print(f"[{index}/{len(CITIES)}] Processing: {city}")

    location = coordinate_cache.get(city)

    if location is None:
        print("  Status: SKIPPED - coordinates unavailable")
        failed_cities.append((city, "No coordinates"))
        continue

    params = {
        "lat": location["lat"],
        "lon": location["lon"],
        "appid": OPENWEATHER_API_KEY,
        "units": "metric",
    }

    try:
        response = requests.get(
            WEATHER_URL,
            params=params,
            timeout=15,
        )

        if response.status_code != 200:
            message = "Unknown error"

            try:
                message = response.json().get(
                    "message",
                    "Unknown error",
                )
            except Exception:
                pass

            print(
                f"  Status: ERROR | HTTP {response.status_code} | "
                f"{message}"
            )
            failed_cities.append((city, message))
            time.sleep(REQUEST_DELAY)
            continue

        data = response.json()

        weather_items = data.get("weather") or [{}]
        weather_item = weather_items[0] if weather_items else {}

        main = data.get("main") or {}
        wind = data.get("wind") or {}
        clouds = data.get("clouds") or {}
        rain = data.get("rain") or {}

        record = {
            "City": city,
            "Resolved_City": data.get("name", city),
            "Country": location.get("country", "IN"),
            "State": location.get("state", ""),
            "Timestamp": datetime.now(timezone.utc).strftime(
                "%Y-%m-%d %H:%M:%S UTC"
            ),
            "Latitude": location["lat"],
            "Longitude": location["lon"],
            "Temperature (°C)": main.get("temp"),
            "Feels_Like (°C)": main.get("feels_like"),
            "Humidity (%)": main.get("humidity"),
            "Pressure (hPa)": main.get("pressure"),
            "Min_Temperature (°C)": main.get("temp_min"),
            "Max_Temperature (°C)": main.get("temp_max"),
            "Wind_Speed (m/s)": wind.get("speed"),
            "Wind_Direction (deg)": wind.get("deg"),
            "Clouds (%)": clouds.get("all"),
            "Visibility (m)": data.get("visibility"),
            "Rain_1h (mm)": rain.get("1h", 0),
            "Rain_3h (mm)": rain.get("3h", 0),
            "Weather": weather_item.get("main"),
            "Weather_Description": weather_item.get("description"),
        }

        records.append(record)

        print(
            f"  Status: SUCCESS | "
            f"Temp={record['Temperature (°C)']} °C | "
            f"Humidity={record['Humidity (%)']}% | "
            f"Weather={record['Weather']}"
        )

    except requests.exceptions.Timeout:
        print("  Status: ERROR - request timed out")
        failed_cities.append((city, "Timeout"))

    except requests.exceptions.ConnectionError:
        print("  Status: ERROR - connection problem")
        failed_cities.append((city, "Connection error"))

    except requests.exceptions.RequestException as exc:
        print(f"  Status: ERROR - {exc}")
        failed_cities.append((city, str(exc)))

    except Exception as exc:
        print(f"  Status: ERROR - unexpected error: {exc}")
        failed_cities.append((city, str(exc)))

    time.sleep(REQUEST_DELAY)


# ============================================================
# CHECK RESULTS
# ============================================================

print("\n" + "=" * 90)
print("OPENWEATHER RESULTS")
print("=" * 90)

print(f"\nCPCB cities requested: {len(CITIES)}")
print(f"Successful weather records: {len(records)}")
print(f"Failed / unavailable cities: {len(failed_cities)}")

if failed_cities:
    print("\nCities without a real OpenWeather response:")
    for city, reason in failed_cities:
        print(f"- {city}: {reason}")

if not records:
    print("\nNO LIVE WEATHER DATA WAS RECEIVED.")
    print("The API key may be inactive, invalid, rate-limited, or unavailable.")
    raise SystemExit(1)


# ============================================================
# SAVE REAL RESULTS ONLY
# ============================================================

df = pd.DataFrame(records)

# Do not create placeholder rows for failed cities.
# Every row here represents a successful OpenWeather response.
df.to_csv(
    OUTPUT_FILE,
    index=False,
)


# ============================================================
# DISPLAY SUMMARY
# ============================================================

print("\n" + "=" * 90)
print("OPENWEATHER LIVE DATA")
print("=" * 90)

print(f"\nSuccessful cities collected: {len(df)}")
print(f"Output rows: {len(df)}")
print("\nSample of collected data:")

summary_columns = [
    "City",
    "Temperature (°C)",
    "Humidity (%)",
    "Pressure (hPa)",
    "Wind_Speed (m/s)",
    "Wind_Direction (deg)",
    "Rain_1h (mm)",
    "Weather",
]

available_summary_columns = [
    column
    for column in summary_columns
    if column in df.columns
]

print(
    df[available_summary_columns]
    .to_string(index=False)
)

print("\nSaved:")
print(OUTPUT_FILE)

print("\n" + "=" * 90)
print("OPENWEATHER API COLLECTION COMPLETE")
print("=" * 90)