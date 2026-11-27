from pathlib import Path
import os
import time
import requests
import pandas as pd


# ============================================================
# CONFIGURATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

LOCATIONS_FILE = BASE_DIR / "locations.csv"
OUTPUT_FILE = BASE_DIR / "live_data" / "api_weather_data.csv"

API_URL = "https://api.openweathermap.org/data/2.5/weather"
API_KEY_ENV = "OPENWEATHER_API_KEY"

REQUEST_TIMEOUT = 30
REQUEST_DELAY_SECONDS = 0.2


# ============================================================
# HEADER
# ============================================================

print("=" * 80)
print("AIR QUALITY - EXTERNAL API MANAGER")
print("=" * 80)


# ============================================================
# CHECK CONFIGURATION
# ============================================================

if not LOCATIONS_FILE.exists():
    raise FileNotFoundError(
        f"Location configuration file not found:\n{LOCATIONS_FILE}\n\n"
        "Create locations.csv in the project root."
    )

api_key = os.getenv(API_KEY_ENV)

if not api_key:
    print()
    print("ERROR: OPENWEATHER_API_KEY is not loaded.")
    print()
    print("PowerShell:")
    print('$env:OPENWEATHER_API_KEY="YOUR_API_KEY"')
    print()
    raise SystemExit(1)

print()
print("Starting external API manager...")

print()
print("-" * 80)
print("CHECKING OPENWEATHER API")
print("-" * 80)

print("OpenWeather API key detected.")


# ============================================================
# LOAD LOCATIONS
# ============================================================

locations = pd.read_csv(LOCATIONS_FILE)

locations.columns = [
    str(column).strip()
    for column in locations.columns
]

required_columns = [
    "City",
    "Latitude",
    "Longitude",
]

missing_columns = [
    column
    for column in required_columns
    if column not in locations.columns
]

if missing_columns:
    raise ValueError(
        "locations.csv is missing required columns:\n"
        + "\n".join(f"- {column}" for column in missing_columns)
    )

locations["City"] = (
    locations["City"]
    .astype(str)
    .str.strip()
)

locations["Latitude"] = pd.to_numeric(
    locations["Latitude"],
    errors="coerce"
)

locations["Longitude"] = pd.to_numeric(
    locations["Longitude"],
    errors="coerce"
)

locations = locations.dropna(
    subset=["City", "Latitude", "Longitude"]
)

locations = locations[
    locations["City"].ne("")
]

locations = locations.drop_duplicates(
    subset=["City"],
    keep="first"
)

if locations.empty:
    raise ValueError(
        "locations.csv does not contain any valid locations."
    )

print()
print(
    f"Locations configured: {len(locations)}"
)

print()
print("Configured locations:")

for city in locations["City"]:
    print(f"- {city}")


# ============================================================
# FETCH WEATHER
# ============================================================

weather_records = []

print()
print("-" * 80)
print("REQUESTING REAL-TIME WEATHER DATA")
print("-" * 80)

for _, location in locations.iterrows():

    city = location["City"]
    latitude = float(location["Latitude"])
    longitude = float(location["Longitude"])

    print()
    print(
        f"Requesting real-time weather data for: {city}"
    )

    params = {
        "lat": latitude,
        "lon": longitude,
        "appid": api_key,
        "units": "metric",
    }

    try:

        response = requests.get(
            API_URL,
            params=params,
            timeout=REQUEST_TIMEOUT,
        )

        response.raise_for_status()

        data = response.json()

        main = data.get("main", {})
        wind = data.get("wind", {})

        timestamp = pd.Timestamp.now(
            tz="UTC"
        )

        record = {
            "City": city,
            "Timestamp": timestamp,
            "Latitude": latitude,
            "Longitude": longitude,
            "AT (°C)": main.get("temp"),
            "RH (%)": main.get("humidity"),
            "WS (m/s)": wind.get("speed"),
            "WD (deg)": wind.get("deg"),
        }

        required_weather = [
            "AT (°C)",
            "RH (%)",
            "WS (m/s)",
            "WD (deg)",
        ]

        missing_weather = [
            column
            for column in required_weather
            if record[column] is None
        ]

        if missing_weather:

            print(
                "WARNING: Weather response incomplete "
                f"for {city}:"
            )

            for column in missing_weather:
                print(f"- {column}")

            continue

        weather_records.append(record)

        print(
            f"SUCCESS: Weather data received for {city}"
        )

        print(
            f"  Temperature : {record['AT (°C)']:.2f} °C"
        )
        print(
            f"  Humidity    : {record['RH (%)']} %"
        )
        print(
            f"  Wind Speed  : {record['WS (m/s)']:.2f} m/s"
        )
        print(
            f"  Wind Dir.   : {record['WD (deg)']}°"
        )

    except requests.exceptions.HTTPError as error:

        status_code = (
            response.status_code
            if "response" in locals()
            else "unknown"
        )

        print(
            f"ERROR: API request failed for {city}"
        )

        print(
            f"HTTP status: {status_code}"
        )

        try:
            error_message = response.json().get(
                "message",
                str(error),
            )
        except Exception:
            error_message = str(error)

        print(
            f"API message: {error_message}"
        )

    except requests.exceptions.Timeout:

        print(
            f"ERROR: Request timed out for {city}"
        )

    except requests.exceptions.RequestException as error:

        print(
            f"ERROR: API request failed for {city}"
        )

        print(
            f"Details: {error}"
        )

    except Exception as error:

        print(
            f"ERROR: Unexpected error for {city}"
        )

        print(
            f"Details: {error}"
        )

    time.sleep(REQUEST_DELAY_SECONDS)


# ============================================================
# SAVE RESULTS
# ============================================================

print()
print("=" * 80)
print("WEATHER API RESULTS")
print("=" * 80)

if not weather_records:

    print()
    print(
        "ERROR: No weather data was received."
    )

    raise SystemExit(1)

weather_df = pd.DataFrame(
    weather_records
)

weather_df["Timestamp"] = pd.to_datetime(
    weather_df["Timestamp"],
    utc=True,
    errors="coerce",
)

weather_df = weather_df.sort_values(
    "City"
)

print()
print("Real-time weather data:")

display_columns = [
    "City",
    "Timestamp",
    "AT (°C)",
    "RH (%)",
    "WS (m/s)",
    "WD (deg)",
]

print(
    weather_df[display_columns].to_string(
        index=False
    )
)


# ============================================================
# SAVE CSV
# ============================================================

OUTPUT_FILE.parent.mkdir(
    parents=True,
    exist_ok=True,
)

weather_df.to_csv(
    OUTPUT_FILE,
    index=False,
)

print()
print("Weather data saved:")
print(OUTPUT_FILE)

print()
print("=" * 80)
print("API MANAGER COMPLETE")
print("=" * 80)

print()
print(
    f"Successful locations: {len(weather_df)}"
)

print(
    f"Failed/unavailable locations: "
    f"{len(locations) - len(weather_df)}"
)

print("=" * 80)