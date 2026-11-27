import requests
import pandas as pd
import os
import time


# =========================================================
# CONFIGURATION
# =========================================================

INPUT_FILE = "dataset/cities_master.csv"
OUTPUT_FILE = "api_data/overpass_waste_facilities.csv"

# Multiple Overpass servers
# If one server fails, another server will be tried.
OVERPASS_SERVERS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.private.coffee/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter"
]

# Search radius around each city
SEARCH_RADIUS = 30000  # 30 km


# =========================================================
# LOAD CITY DATA
# =========================================================

cities = pd.read_csv(INPUT_FILE)

cities = cities.drop_duplicates(
    subset=["City"]
).reset_index(drop=True)


# =========================================================
# CHECK LATITUDE / LONGITUDE COLUMNS
# =========================================================

# Support different possible column names
column_map = {}

for col in cities.columns:

    clean = col.strip().lower()

    if clean in ["latitude", "lat"]:
        column_map["Latitude"] = col

    elif clean in ["longitude", "lon", "lng"]:
        column_map["Longitude"] = col


if "Latitude" not in column_map or "Longitude" not in column_map:

    print("\nERROR:")
    print("Latitude and Longitude columns were not found")
    print("Available columns:")
    print(list(cities.columns))
    exit()


LAT_COL = column_map["Latitude"]
LON_COL = column_map["Longitude"]


# =========================================================
# HEADER
# =========================================================

print("\n========================================")
print(" OPENSTREETMAP OVERPASS WASTE API")
print("========================================")

print(
    f"Cities to process: {len(cities)}"
)

print(
    f"Search radius: {SEARCH_RADIUS / 1000:.0f} km"
)


# =========================================================
# CREATE OUTPUT DIRECTORY
# =========================================================

os.makedirs(
    "api_data",
    exist_ok=True
)


# =========================================================
# REQUEST HEADERS
# =========================================================

headers = {
    "User-Agent": (
        "SmartWasteAssistant/1.0 "
        "(educational waste-management project)"
    )
}


# =========================================================
# STORAGE
# =========================================================

records = []


# =========================================================
# FUNCTION: QUERY OVERPASS
# =========================================================

def query_overpass(latitude, longitude):

    # -----------------------------------------------------
    # LIGHTWEIGHT QUERY
    # -----------------------------------------------------

    query = f"""
    [out:json][timeout:25];

    (
        nwr["amenity"="recycling"]
            (around:{SEARCH_RADIUS},{latitude},{longitude});

        nwr["amenity"="waste_disposal"]
            (around:{SEARCH_RADIUS},{latitude},{longitude});

        nwr["amenity"="waste_transfer_station"]
            (around:{SEARCH_RADIUS},{latitude},{longitude});

        nwr["amenity"="waste_dump_site"]
            (around:{SEARCH_RADIUS},{latitude},{longitude});

        nwr["landuse"="landfill"]
            (around:{SEARCH_RADIUS},{latitude},{longitude});
    );

    out center tags;
    """


    # -----------------------------------------------------
    # TRY MULTIPLE SERVERS
    # -----------------------------------------------------

    for server_index, server in enumerate(
        OVERPASS_SERVERS,
        start=1
    ):

        try:

            print(
                f"   Trying Overpass server "
                f"{server_index}/{len(OVERPASS_SERVERS)}..."
            )


            response = requests.post(

                server,

                data={
                    "data": query
                },

                headers=headers,

                timeout=45
            )


            # -------------------------------------------------
            # SUCCESS
            # -------------------------------------------------

            if response.status_code == 200:

                try:

                    return response.json()

                except ValueError:

                    print(
                        "   Server returned invalid JSON."
                    )


            # -------------------------------------------------
            # SERVER BUSY / ERROR
            # -------------------------------------------------

            elif response.status_code in [
                429,
                500,
                502,
                503,
                504
            ]:

                print(
                    f"   Server returned "
                    f"HTTP {response.status_code}"
                )

                print(
                    "   Trying another server..."
                )

                time.sleep(3)


            else:

                print(
                    f"   HTTP {response.status_code}"
                )

                print(
                    "   Trying another server..."
                )


        except requests.exceptions.Timeout:

            print(
                "   Server timeout."
            )

            print(
                "   Trying another server..."
            )


        except requests.exceptions.RequestException as error:

            print(
                f"   Connection error: {error}"
            )

            print(
                "   Trying another server..."
            )


        time.sleep(2)


    # -----------------------------------------------------
    # ALL SERVERS FAILED
    # -----------------------------------------------------

    return None


# =========================================================
# PROCESS CITIES
# =========================================================

for index, row in cities.iterrows():

    city = str(
        row["City"]
    ).strip()


    # -----------------------------------------------------
    # GET COORDINATES
    # -----------------------------------------------------

    try:

        latitude = float(
            row[LAT_COL]
        )

        longitude = float(
            row[LON_COL]
        )

    except Exception:

        print(
            f"\n[{index + 1}/{len(cities)}] "
            f"{city} - Invalid coordinates"
        )

        continue


    print(
        f"\n[{index + 1}/{len(cities)}] "
        f"Searching waste facilities in {city}..."
    )

    print(
        f"   Coordinates: "
        f"{latitude}, {longitude}"
    )


    # -----------------------------------------------------
    # QUERY API
    # -----------------------------------------------------

    data = query_overpass(
        latitude,
        longitude
    )


    # -----------------------------------------------------
    # API FAILED
    # -----------------------------------------------------

    if data is None:

        print(
            "   FAILED: All Overpass servers unavailable."
        )

        continue


    # -----------------------------------------------------
    # GET ELEMENTS
    # -----------------------------------------------------

    elements = data.get(
        "elements",
        []
    )


    print(
        f"   Found: {len(elements)} facilities"
    )


    # -----------------------------------------------------
    # PROCESS ELEMENTS
    # -----------------------------------------------------

    for element in elements:

        tags = element.get(
            "tags",
            {}
        )


        # -------------------------------------------------
        # COORDINATES
        # -------------------------------------------------

        element_latitude = element.get(
            "lat"
        )

        element_longitude = element.get(
            "lon"
        )


        # Ways / relations
        if element_latitude is None:

            center = element.get(
                "center",
                {}
            )

            element_latitude = center.get(
                "lat"
            )

            element_longitude = center.get(
                "lon"
            )


        # -------------------------------------------------
        # FACILITY TYPE
        # -------------------------------------------------

        facility_type = (
            tags.get("amenity")
            or tags.get("landuse")
            or "unknown"
        )


        # -------------------------------------------------
        # STORE RECORD
        # -------------------------------------------------

        records.append({

            "Search_City": city,

            "Facility_Name": tags.get(
                "name",
                "Unnamed facility"
            ),

            "Facility_Type": facility_type,

            "Recycling_Type": tags.get(
                "recycling_type",
                ""
            ),

            "Waste_Type": tags.get(
                "waste",
                ""
            ),

            "Operator": tags.get(
                "operator",
                ""
            ),

            "Opening_Hours": tags.get(
                "opening_hours",
                ""
            ),

            "Street": tags.get(
                "addr:street",
                ""
            ),

            "City": tags.get(
                "addr:city",
                city
            ),

            "State": tags.get(
                "addr:state",
                ""
            ),

            "Postcode": tags.get(
                "addr:postcode",
                ""
            ),

            "Latitude": element_latitude,

            "Longitude": element_longitude,

            "OSM_ID": element.get(
                "id"
            ),

            "OSM_Type": element.get(
                "type"
            ),

            "API_Source": (
                "OpenStreetMap "
                "Overpass API"
            )

        })


    # -----------------------------------------------------
    # DELAY BETWEEN CITIES
    # -----------------------------------------------------

    time.sleep(2)


# =========================================================
# CREATE DATAFRAME
# =========================================================

if records:

    df = pd.DataFrame(
        records
    )

else:

    df = pd.DataFrame()


# =========================================================
# REMOVE DUPLICATES
# =========================================================

if not df.empty:

    df = df.drop_duplicates(
        subset=[
            "OSM_Type",
            "OSM_ID"
        ]
    ).reset_index(
        drop=True
    )


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
print(" OVERPASS WASTE COLLECTION COMPLETED")
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


# =========================================================
# SHOW FIRST 5 RECORDS
# =========================================================

if not df.empty:

    print("\nFirst 5 records:")

    print(
        df.head()
    )

    print("\nColumn names:")

    print(
        list(df.columns)
    )

else:

    print(
        "\n⚠️ No waste facilities were collected."
    )


print(
    "\n✅ Waste API #5 process completed!"
)