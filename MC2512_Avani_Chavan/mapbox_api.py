import os
import requests
from pathlib import Path
import pandas as pd


# ============================================================
# CONFIGURATION
# ============================================================

OUTPUT_FILE = Path("live_data/mapbox_locations.csv")

MAPBOX_TOKEN = os.getenv("MAPBOX_ACCESS_TOKEN")


# ============================================================
# HEADER
# ============================================================

print("=" * 80)
print("AIR QUALITY - MAPBOX LOCATION API")
print("=" * 80)


# ============================================================
# CHECK TOKEN
# ============================================================

if not MAPBOX_TOKEN:
    raise ValueError(
        "MAPBOX_ACCESS_TOKEN is not set.\n\n"
        "Run in PowerShell:\n"
        '$env:MAPBOX_ACCESS_TOKEN="YOUR_MAPBOX_TOKEN"'
    )

print()
print("Mapbox access token detected.")


# ============================================================
# CITY LOCATIONS
# ============================================================

cities = {
    "Mumbai": {
        "latitude": 19.0760,
        "longitude": 72.8777
    },
    "Pune": {
        "latitude": 18.5204,
        "longitude": 73.8567
    }
}


# ============================================================
# MAPBOX GEOCODING TEST
# ============================================================

records = []

for city, location in cities.items():

    print()
    print("-" * 80)
    print(f"Testing Mapbox location: {city}")

    url = (
        "https://api.mapbox.com/search/geocode/v6/forward"
    )

    params = {
        "q": city + ", India",
        "access_token": MAPBOX_TOKEN,
        "limit": 1
    }

    try:

        response = requests.get(
            url,
            params=params,
            timeout=30
        )

        response.raise_for_status()

        data = response.json()

        features = data.get("features", [])

        if not features:
            print(f"WARNING: No Mapbox result for {city}")
            continue

        coordinates = (
            features[0]
            .get("geometry", {})
            .get("coordinates", [])
        )

        if len(coordinates) != 2:
            print(f"WARNING: Invalid coordinates for {city}")
            continue

        longitude = coordinates[0]
        latitude = coordinates[1]

        records.append({
            "City": city,
            "Latitude": latitude,
            "Longitude": longitude
        })

        print(f"SUCCESS: Mapbox location received for {city}")
        print(f"Latitude : {latitude}")
        print(f"Longitude: {longitude}")

    except requests.exceptions.RequestException as e:

        print(
            f"ERROR: Mapbox request failed for {city}"
        )
        print(e)


# ============================================================
# CHECK RESULTS
# ============================================================

if not records:

    raise ValueError(
        "No location data received from Mapbox."
    )


# ============================================================
# SAVE
# ============================================================

df = pd.DataFrame(records)

OUTPUT_FILE.parent.mkdir(
    parents=True,
    exist_ok=True
)

df.to_csv(
    OUTPUT_FILE,
    index=False
)


# ============================================================
# DISPLAY
# ============================================================

print()
print("=" * 80)
print("MAPBOX LOCATION RESULTS")
print("=" * 80)

print()
print(df.to_string(index=False))

print()
print("Saved:")
print(OUTPUT_FILE)

print("=" * 80)
print("MAPBOX API TEST COMPLETE")
print("=" * 80)