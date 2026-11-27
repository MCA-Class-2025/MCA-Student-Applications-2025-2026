import os
import requests
import pandas as pd
from pathlib import Path
from datetime import datetime, timezone


# ============================================================
# CONFIGURATION
# ============================================================

API_KEY = os.getenv("OPENWEATHER_API_KEY")

OUTPUT_DIR = Path("live_data")
OUTPUT_DIR.mkdir(exist_ok=True)

OUTPUT_FILE = OUTPUT_DIR / "live_weather_data.csv"

CITIES = {
    "Mumbai": {
        "lat": 19.0760,
        "lon": 72.8777
    },
    "Pune": {
        "lat": 18.5204,
        "lon": 73.8567
    }
}

BASE_URL = "https://api.openweathermap.org/data/2.5/weather"


# ============================================================
# HEADER
# ============================================================

print("=" * 80)
print("AIR QUALITY - REAL-TIME WEATHER API")
print("=" * 80)


# ============================================================
# CHECK API KEY
# ============================================================

if not API_KEY:
    print()
    print("ERROR: OPENWEATHER_API_KEY is not set.")
    print()
    print("Run this in PowerShell:")
    print('$env:OPENWEATHER_API_KEY="YOUR_API_KEY"')
    print()
    raise SystemExit(1)


print()
print("OpenWeather API key detected.")
print()


# ============================================================
# FUNCTION: GET WEATHER
# ============================================================

def get_weather(city, latitude, longitude):

    params = {
        "lat": latitude,
        "lon": longitude,
        "appid": API_KEY,
        "units": "metric"
    }

    try:

        response = requests.get(
            BASE_URL,
            params=params,
            timeout=30
        )

        response.raise_for_status()

        data = response.json()

        return {
            "City": city,
            "Timestamp": datetime.now(timezone.utc),
            "AT (°C)": data["main"]["temp"],
            "RH (%)": data["main"]["humidity"],
            "WS (m/s)": data["wind"]["speed"],
            "WD (deg)": data["wind"].get("deg", None),
            "Pressure (hPa)": data["main"].get("pressure", None),
            "Clouds (%)": data.get("clouds", {}).get("all", None),
            "Weather": data["weather"][0]["description"]
            if data.get("weather")
            else None
        }

    except requests.exceptions.Timeout:

        print(f"ERROR: Request timed out for {city}")
        return None

    except requests.exceptions.RequestException as e:

        print(f"ERROR: API request failed for {city}")
        print(e)
        return None

    except (KeyError, TypeError, ValueError) as e:

        print(f"ERROR: Invalid API response for {city}")
        print(e)
        return None


# ============================================================
# GET DATA FOR ALL CITIES
# ============================================================

records = []

for city, location in CITIES.items():

    print("-" * 80)
    print(f"Requesting weather data for: {city}")

    result = get_weather(
        city,
        location["lat"],
        location["lon"]
    )

    if result is not None:

        records.append(result)

        print(f"Temperature : {result['AT (°C)']} °C")
        print(f"Humidity    : {result['RH (%)']} %")
        print(f"Wind Speed  : {result['WS (m/s)']} m/s")
        print(f"Wind Dir.   : {result['WD (deg)']}°")
        print(f"Pressure    : {result['Pressure (hPa)']} hPa")
        print(f"Clouds      : {result['Clouds (%)']} %")
        print(f"Condition   : {result['Weather']}")


# ============================================================
# SAVE DATA
# ============================================================

if not records:

    print()
    print("ERROR: No weather data received.")
    raise SystemExit(1)


df = pd.DataFrame(records)

df["Timestamp"] = pd.to_datetime(
    df["Timestamp"],
    utc=True
)

df = df.sort_values(
    ["City", "Timestamp"]
).reset_index(drop=True)


# ============================================================
# DISPLAY
# ============================================================

print()
print("=" * 80)
print("REAL-TIME WEATHER DATA")
print("=" * 80)

print()

print(
    df.to_string(
        index=False
    )
)


# ============================================================
# SAVE
# ============================================================

df.to_csv(
    OUTPUT_FILE,
    index=False
)

print()
print("=" * 80)
print("WEATHER API COMPLETE")
print("=" * 80)

print()
print("Rows:", len(df))
print("Cities:", ", ".join(df["City"].unique()))

print()
print("Saved:")
print(OUTPUT_FILE)

print("=" * 80)