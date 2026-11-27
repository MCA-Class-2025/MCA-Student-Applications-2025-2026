import pandas as pd
import requests
import os
import time
from dotenv import load_dotenv

# =========================================================
# LOAD API KEY
# =========================================================

load_dotenv()

API_KEY = os.getenv("GEOAPIFY_API_KEY")

if not API_KEY:
    raise ValueError(
        "GEOAPIFY_API_KEY not found in .env file"
    )


# =========================================================
# FILE PATHS
# =========================================================

INPUT_FILE = "dataset/cities_master.csv"
OUTPUT_FILE = "api_data/geoapify_recycling.csv"

API_URL = "https://api.geoapify.com/v2/places"


# =========================================================
# LOAD CITY DATA
# =========================================================

cities = pd.read_csv(INPUT_FILE)

cities = cities.drop_duplicates(
    subset=["City"]
).reset_index(drop=True)

print("\n========================================")
print(" GEOAPIFY RECYCLING FACILITY COLLECTION")
print("========================================")

print(f"Cities to process: {len(cities)}")


# =========================================================
# OUTPUT DIRECTORY
# =========================================================

os.makedirs(
    "api_data",
    exist_ok=True
)


# =========================================================
# FETCH RECYCLING FACILITIES
# =========================================================

records = []


for index, row in cities.iterrows():

    city = str(row["City"]).strip()

    latitude = float(row["Latitude"])
    longitude = float(row["Longitude"])

    print(
        f"[{index + 1}/{len(cities)}] Searching recycling facilities near {city}..."
    )

    params = {

        "categories": (
            "service.recycling,"
            "service.recycling.centre,"
            "service.recycling.bin"
        ),

        "filter": f"circle:{longitude},{latitude},15000",

        "bias": f"proximity:{longitude},{latitude}",

        "limit": 20,

        "apiKey": API_KEY

    }


    try:

        response = requests.get(
            API_URL,
            params=params,
            timeout=30
        )

        response.raise_for_status()

        data = response.json()

        features = data.get(
            "features",
            []
        )


        # =================================================
        # SAVE EACH FACILITY
        # =================================================

        for feature in features:

            properties = feature.get(
                "properties",
                {}
            )

            geometry = feature.get(
                "geometry",
                {}
            )

            coordinates = geometry.get(
                "coordinates",
                [None, None]
            )


            records.append({

                "Search_City": city,

                "City": properties.get(
                    "city",
                    ""
                ),

                "State": properties.get(
                    "state",
                    ""
                ),

                "Name": properties.get(
                    "name",
                    "Recycling Facility"
                ),

                "Address": properties.get(
                    "formatted",
                    ""
                ),

                "Latitude": properties.get(
                    "lat",
                    coordinates[1]
                    if len(coordinates) > 1
                    else None
                ),

                "Longitude": properties.get(
                    "lon",
                    coordinates[0]
                    if len(coordinates) > 0
                    else None
                ),

                "Categories": ",".join(
                    properties.get(
                        "categories",
                        []
                    )
                )
                if isinstance(
                    properties.get("categories", []),
                    list
                )
                else properties.get(
                    "categories",
                    ""
                ),

                "Distance_Meters": properties.get(
                    "distance",
                    ""
                ),

                "Place_ID": properties.get(
                    "place_id",
                    ""
                ),

                "API_Source": "Geoapify Places API"

            })


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
# FINAL OUTPUT
# =========================================================

print("\n========================================")
print(" GEOAPIFY COLLECTION COMPLETED")
print("========================================")

print(
    f"Facilities collected: {len(df)}"
)

print(
    f"Columns collected: {len(df.columns)}"
)

print(
    f"CSV saved at: {OUTPUT_FILE}"
)


if len(df) > 0:

    print("\nFirst 5 records:")

    print(
        df.head()
    )

else:

    print(
        "\n⚠️ No recycling facilities found."
    )


print(
    "\n✅ Geoapify API #4 CSV created successfully!"
)