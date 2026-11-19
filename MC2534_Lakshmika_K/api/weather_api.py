import os
import time
import pandas as pd
import requests
from dotenv import load_dotenv


# =========================================================
# CONFIGURATION
# =========================================================

load_dotenv()

API_KEY = os.getenv("WEATHER_API_KEY")

BASE_URL = "https://api.weatherapi.com/v1/current.json"

INPUT_FILE = "dataset/cities_master.csv"

OUTPUT_FILE = "api_data/weather_api.csv"


# =========================================================
# CHECK API KEY
# =========================================================

if not API_KEY:
    raise ValueError(
        "WEATHER_API_KEY not found in .env file."
    )


# =========================================================
# LOAD CITY DATASET
# =========================================================

cities = pd.read_csv(INPUT_FILE)

print("\n========================================")
print(" WEATHER API DATA COLLECTION")
print("========================================")

print(f"Cities found: {len(cities)}")


# =========================================================
# REMOVE DUPLICATE CITIES
# =========================================================

cities = cities.drop_duplicates(
    subset=["City"]
).reset_index(drop=True)

print(
    f"Unique cities: {len(cities)}"
)


# =========================================================
# FETCH WEATHER DATA
# =========================================================

weather_records = []


for index, row in cities.iterrows():

    city = str(row["City"]).strip()

    print(
        f"[{index + 1}/{len(cities)}] Fetching weather for {city}..."
    )

    params = {
        "key": API_KEY,
        "q": city,
        "aqi": "yes"
    }

    try:

        response = requests.get(
            BASE_URL,
            params=params,
            timeout=15
        )

        response.raise_for_status()

        data = response.json()

        location = data.get(
            "location",
            {}
        )

        current = data.get(
            "current",
            {}
        )

        condition = current.get(
            "condition",
            {}
        )

        air_quality = current.get(
            "air_quality",
            {}
        )

        record = {

            # Location
            "City": location.get(
                "name",
                city
            ),

            "State": row.get(
                "State",
                ""
            ),

            "Region": row.get(
                "Region",
                ""
            ),

            "Latitude": location.get(
                "lat"
            ),

            "Longitude": location.get(
                "lon"
            ),

            # Weather
            "Last_Updated": current.get(
                "last_updated"
            ),

            "Temperature_C": current.get(
                "temp_c"
            ),

            "Feels_Like_C": current.get(
                "feelslike_c"
            ),

            "Humidity_Percent": current.get(
                "humidity"
            ),

            "Wind_KPH": current.get(
                "wind_kph"
            ),

            "Wind_Direction": current.get(
                "wind_dir"
            ),

            "Pressure_MB": current.get(
                "pressure_mb"
            ),

            "Precipitation_MM": current.get(
                "precip_mm"
            ),

            "Cloud_Percent": current.get(
                "cloud"
            ),

            "Visibility_KM": current.get(
                "vis_km"
            ),

            "UV_Index": current.get(
                "uv"
            ),

            "Gust_KPH": current.get(
                "gust_kph"
            ),

            "Weather_Condition": condition.get(
                "text"
            ),

            # Air quality returned by WeatherAPI
            "US_EPA_AQI": air_quality.get(
                "us-epa-index"
            ),

            "PM2_5": air_quality.get(
                "pm2_5"
            ),

            "PM10": air_quality.get(
                "pm10"
            ),

            "CO": air_quality.get(
                "co"
            ),

            "NO2": air_quality.get(
                "no2"
            ),

            "SO2": air_quality.get(
                "so2"
            ),

            "O3": air_quality.get(
                "o3"
            ),

            "API_Source": "WeatherAPI"

        }

        weather_records.append(record)

    except requests.exceptions.HTTPError as error:

        print(
            f"   ❌ API error for {city}: {error}"
        )

    except requests.exceptions.RequestException as error:

        print(
            f"   ❌ Network error for {city}: {error}"
        )

    except Exception as error:

        print(
            f"   ❌ Unexpected error for {city}: {error}"
        )

    # Small delay between requests
    time.sleep(0.2)


# =========================================================
# CREATE DATAFRAME
# =========================================================

weather_df = pd.DataFrame(
    weather_records
)


# =========================================================
# SAVE CSV
# =========================================================

os.makedirs(
    "api_data",
    exist_ok=True
)

weather_df.to_csv(
    OUTPUT_FILE,
    index=False
)


# =========================================================
# SUMMARY
# =========================================================

print("\n========================================")
print(" WEATHER API COLLECTION COMPLETED")
print("========================================")

print(
    f"Successful records: {len(weather_df)}"
)

print(
    f"CSV saved at: {OUTPUT_FILE}"
)

print("\nColumns collected:")

for column in weather_df.columns:

    print(
        f" - {column}"
    )

print("\nFirst 5 records:")

print(
    weather_df.head()
)

print("\n✅ Weather API CSV created successfully!")