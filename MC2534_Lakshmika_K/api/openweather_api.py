import os
import time
import pandas as pd
import requests
from dotenv import load_dotenv

# =========================================================
# LOAD ENVIRONMENT VARIABLES
# =========================================================

load_dotenv()

API_KEY = os.getenv("OPENWEATHER_API_KEY")

BASE_URL = "https://api.openweathermap.org/data/2.5/weather"

INPUT_FILE = "dataset/cities_master.csv"
OUTPUT_FILE = "api_data/openweather_api.csv"


# =========================================================
# CHECK API KEY
# =========================================================

if not API_KEY:
    raise ValueError(
        "OPENWEATHER_API_KEY not found in .env file"
    )


# =========================================================
# LOAD CITY DATASET
# =========================================================

cities = pd.read_csv(INPUT_FILE)

cities = cities.drop_duplicates(
    subset=["City"]
).reset_index(drop=True)


print("\n========================================")
print(" OPENWEATHER API DATA COLLECTION")
print("========================================")

print(f"Unique cities: {len(cities)}")


# =========================================================
# FETCH DATA
# =========================================================

records = []

for index, row in cities.iterrows():

    city = str(row["City"]).strip()

    latitude = row["Latitude"]
    longitude = row["Longitude"]

    print(
        f"[{index + 1}/{len(cities)}] Fetching {city}..."
    )

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
            timeout=15
        )

        response.raise_for_status()

        data = response.json()

        # -----------------------------
        # Extract sections
        # -----------------------------

        coord = data.get("coord", {})

        weather = data.get(
            "weather",
            [{}]
        )[0]

        main = data.get(
            "main",
            {}
        )

        wind = data.get(
            "wind",
            {}
        )

        clouds = data.get(
            "clouds",
            {}
        )

        rain = data.get(
            "rain",
            {}
        )

        sys_data = data.get(
            "sys",
            {}
        )

        # -----------------------------
        # Create record
        # -----------------------------

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

            "Latitude": coord.get(
                "lat"
            ),

            "Longitude": coord.get(
                "lon"
            ),

            "Temperature_C": main.get(
                "temp"
            ),

            "Feels_Like_C": main.get(
                "feels_like"
            ),

            "Minimum_Temperature_C": main.get(
                "temp_min"
            ),

            "Maximum_Temperature_C": main.get(
                "temp_max"
            ),

            "Pressure_hPa": main.get(
                "pressure"
            ),

            "Humidity_Percent": main.get(
                "humidity"
            ),

            "Visibility_Meters": data.get(
                "visibility"
            ),

            "Wind_Speed_mps": wind.get(
                "speed"
            ),

            "Wind_Direction_Degrees": wind.get(
                "deg"
            ),

            "Wind_Gust_mps": wind.get(
                "gust"
            ),

            "Cloudiness_Percent": clouds.get(
                "all"
            ),

            "Rain_1h_MM": rain.get(
                "1h",
                0
            ),

            "Weather_ID": weather.get(
                "id"
            ),

            "Weather_Main": weather.get(
                "main"
            ),

            "Weather_Description": weather.get(
                "description"
            ),

            "Weather_Icon": weather.get(
                "icon"
            ),

            "Country": sys_data.get(
                "country"
            ),

            "Sunrise": sys_data.get(
                "sunrise"
            ),

            "Sunset": sys_data.get(
                "sunset"
            ),

            "Observation_Time": data.get(
                "dt"
            ),

            "Timezone_Seconds": data.get(
                "timezone"
            ),

            "API_Source": "OpenWeather"
        }

        records.append(record)

    except requests.exceptions.HTTPError as error:

        print(
            f"   ERROR for {city}: {error}"
        )

    except requests.exceptions.RequestException as error:

        print(
            f"   NETWORK ERROR for {city}: {error}"
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
# CREATE OUTPUT DIRECTORY
# =========================================================

os.makedirs(
    "api_data",
    exist_ok=True
)


# =========================================================
# SAVE CSV
# =========================================================

df.to_csv(
    OUTPUT_FILE,
    index=False
)


# =========================================================
# FINAL OUTPUT
# =========================================================

print("\n========================================")
print(" OPENWEATHER COLLECTION COMPLETED")
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
    "\nWeather API #2 CSV created successfully!"
)