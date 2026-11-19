import pandas as pd
import requests
import os
import time


# =========================================================
# FILE PATHS
# =========================================================

INPUT_FILE = "dataset/cities_master.csv"
OUTPUT_FILE = "api_data/openmeteo_air_quality.csv"

API_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"


# =========================================================
# LOAD CITY DATASET
# =========================================================

cities = pd.read_csv(INPUT_FILE)

cities = cities.drop_duplicates(
    subset=["City"]
).reset_index(drop=True)


print("\n========================================")
print(" OPEN-METEO AIR QUALITY API")
print("========================================")

print(f"Unique cities: {len(cities)}")


# =========================================================
# CREATE OUTPUT DIRECTORY
# =========================================================

os.makedirs(
    "api_data",
    exist_ok=True
)


# =========================================================
# FETCH AIR QUALITY DATA
# =========================================================

records = []


for index, row in cities.iterrows():

    city = str(row["City"]).strip()

    latitude = float(row["Latitude"])
    longitude = float(row["Longitude"])

    print(
        f"[{index + 1}/{len(cities)}] Fetching {city}..."
    )

    params = {

        "latitude": latitude,

        "longitude": longitude,

        "current": (
            "pm10,"
            "pm2_5,"
            "carbon_monoxide,"
            "carbon_dioxide,"
            "nitrogen_dioxide,"
            "sulphur_dioxide,"
            "ozone,"
            "dust,"
            "uv_index,"
            "european_aqi,"
            "us_aqi"
        ),

        "timezone": "auto"
    }


    try:

        response = requests.get(
            API_URL,
            params=params,
            timeout=20
        )

        response.raise_for_status()

        data = response.json()


        # ---------------------------------------------
        # Current air quality data
        # ---------------------------------------------

        current = data.get(
            "current",
            {}
        )


        # ---------------------------------------------
        # Create one record for each city
        # ---------------------------------------------

        record = {

            "City": city,

            "State": row.get(
                "State",
                ""
            ),

            "Region": row.get(
                "Region",
                ""
            ),

            "Latitude": latitude,

            "Longitude": longitude,

            "PM10": current.get(
                "pm10"
            ),

            "PM2_5": current.get(
                "pm2_5"
            ),

            "Carbon_Monoxide": current.get(
                "carbon_monoxide"
            ),

            "Carbon_Dioxide": current.get(
                "carbon_dioxide"
            ),

            "Nitrogen_Dioxide": current.get(
                "nitrogen_dioxide"
            ),

            "Sulphur_Dioxide": current.get(
                "sulphur_dioxide"
            ),

            "Ozone": current.get(
                "ozone"
            ),

            "Dust": current.get(
                "dust"
            ),

            "UV_Index": current.get(
                "uv_index"
            ),

            "European_AQI": current.get(
                "european_aqi"
            ),

            "US_AQI": current.get(
                "us_aqi"
            ),

            "Observation_Time": current.get(
                "time"
            ),

            "API_Source": "Open-Meteo Air Quality"

        }


        records.append(record)


    except requests.exceptions.RequestException as error:

        print(
            f"   ERROR for {city}: {error}"
        )


    except Exception as error:

        print(
            f"   ERROR for {city}: {error}"
        )


    time.sleep(0.2)


# =========================================================
# CREATE DATAFRAME
# =========================================================

df = pd.DataFrame(records)


# =========================================================
# SAVE CSV
# =========================================================

df.to_csv(
    OUTPUT_FILE,
    index=False
)


# =========================================================
# FINAL RESULT
# =========================================================

print("\n========================================")
print(" OPEN-METEO COLLECTION COMPLETED")
print("========================================")

print(
    f"Successful records: {len(df)}"
)

print(
    f"Columns collected: {len(df.columns)}"
)

print(
    f"CSV saved at: {OUTPUT_FILE}"
)

print("\nFirst 5 records:")

print(
    df.head()
)

print(
    "\n✅ Open-Meteo Air Quality API #3 CSV created successfully!"
)