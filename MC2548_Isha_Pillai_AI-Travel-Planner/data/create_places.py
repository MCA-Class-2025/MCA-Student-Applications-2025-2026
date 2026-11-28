import sys
import os

sys.path.append(
    os.path.dirname(
        os.path.dirname(
            os.path.abspath(__file__)
        )
    )
)

import pandas as pd
from services.geoapify_service import get_places


# --------------------------------------------------
# 1. Read original travel dataset
# --------------------------------------------------

input_file = "data/Travel details dataset.csv"

df = pd.read_csv(
    input_file,
    sep="\t",
    encoding="utf-8-sig"
)

places_records = []


# --------------------------------------------------
# 2. Coordinates for destinations
# --------------------------------------------------

coordinates = {

    # Major cities
    "London": (51.5074, -0.1278),
    "Phuket": (7.8804, 98.3923),
    "Bali": (-8.4095, 115.1889),
    "New York": (40.7128, -74.0060),
    "New York City": (40.7128, -74.0060),
    "Tokyo": (35.6762, 139.6503),
    "Paris": (48.8566, 2.3522),
    "Sydney": (-33.8688, 151.2093),
    "Rio de Janeiro": (-22.9068, -43.1729),
    "Amsterdam": (52.3676, 4.9041),
    "Dubai": (25.2048, 55.2708),
    "Barcelona": (41.3874, 2.1686),
    "Honolulu": (21.3099, -157.8581),
    "Berlin": (52.5200, 13.4050),
    "Marrakech": (31.6295, -7.9811),
    "Edinburgh": (55.9533, -3.1883),
    "Rome": (41.9028, 12.4964),
    "Bangkok": (13.7563, 100.5018),
    "Vancouver": (49.2827, -123.1207),
    "Seoul": (37.5665, 126.9780),
    "Los Angeles": (34.0522, -118.2437),
    "Cape Town": (-33.9249, 18.4241),
    "Cancun": (21.1619, -86.8515),
    "Athens": (37.9838, 23.7275),
    "Phnom Penh": (11.5564, 104.9282),
    "Santorini": (36.3932, 25.4615),
    "Auckland": (-36.8509, 174.7645),

    # Country-level destinations
    # Use a representative major city
    "Japan": (35.6762, 139.6503),
    "Thailand": (13.7563, 100.5018),
    "France": (48.8566, 2.3522),
    "Australia": (-33.8688, 151.2093),
    "Brazil": (-22.9068, -43.1729),
    "Greece": (37.9838, 23.7275),
    "Egypt": (30.0444, 31.2357),
    "Mexico": (21.1619, -86.8515),
    "Italy": (41.9028, 12.4964),
    "Spain": (41.3874, 2.1686),
    "Canada": (49.2827, -123.1207),

    # Other variations
    "Hawaii": (21.3099, -157.8581),
}


# --------------------------------------------------
# 3. Words that usually indicate irrelevant places
# --------------------------------------------------

excluded_words = [

    # Businesses / services
    "massage",
    "spa",
    "salon",
    "restaurant",
    "cafe",
    "bar",
    "pub",
    "hotel",
    "hostel",
    "shop",
    "store",
    "market",
    "clinic",
    "hospital",
    "office",
    "school",
    "academy",
    "gym",
    "fitness",
    "aerobic",

    # Transport / infrastructure
    "station",
    "parking",
    "garage",
    "airport",
    "terminal",
    "bus stop",
    "fuel",
    "petrol",

    # Random objects / infrastructure
    "roller",
    "buoy",
    "cab tree",
    "traffic",
    "sign",
    "pole",
    "bench",
    "table",

    # Other obviously poor attraction results
    "disco",
    "seafood"
]


# --------------------------------------------------
# 4. Categories we actually want
# --------------------------------------------------

useful_categories = [

    "tourism.sights",
    "tourism.sights.memorial",
    "tourism.sights.monument",
    "tourism.sights.castle",
    "tourism.attraction",
    "entertainment.museum",
    "entertainment.culture",
    "heritage"
]


# --------------------------------------------------
# 5. Process every trip
# --------------------------------------------------

for _, row in df.iterrows():

    trip_id = int(row["Trip ID"])

    destination_value = row["Destination"]

    # Handle missing destinations
    if pd.isna(destination_value):

        print(
            f"Skipping Trip {trip_id} - "
            f"destination missing"
        )

        continue

    destination = str(
        destination_value
    ).strip()

    # Get city name
    city = destination.split(",")[0].strip()

    # Special cases
    if city == "Hawaii":
        city = "Honolulu"

    coords = coordinates.get(city)

    if coords is None:

        print(
            f"Skipping Trip {trip_id} - "
            f"coordinates not available for "
            f"{destination}"
        )

        continue

    lat, lon = coords

    print(
        f"Getting places for Trip {trip_id}: "
        f"{destination} → {city}"
    )


    # --------------------------------------------------
    # 6. Call Geoapify
    # --------------------------------------------------

    data = get_places(
        lat,
        lon
    )

    if data is None:

        print(
            f"Skipping Trip {trip_id} - "
            f"Geoapify API failed"
        )

        continue

    features = data.get(
        "features",
        []
    )

    if not features:

        print(
            f"Skipping Trip {trip_id} - "
            f"no places found"
        )

        continue


    # --------------------------------------------------
    # 7. Extract and filter places
    # --------------------------------------------------

    for feature in features:

        properties = feature.get(
            "properties",
            {}
        )

        name = properties.get(
            "name"
        )

        address = properties.get(
            "formatted"
        )

        category = properties.get(
            "categories"
        )


        # ----------------------------------------------
        # Basic validation
        # ----------------------------------------------

        if not name:
            continue

        if not address:
            continue

        if not category:
            continue


        # ----------------------------------------------
        # Convert category to text
        # ----------------------------------------------

        if isinstance(category, list):

            category_text = ", ".join(
                category
            )

        else:

            category_text = str(
                category
            )


        category_lower = (
            category_text.lower()
        )


        # ----------------------------------------------
        # Keep only travel-related categories
        # ----------------------------------------------

        category_is_useful = any(
            useful_category in category_lower
            for useful_category
            in useful_categories
        )

        if not category_is_useful:
            continue


        # ----------------------------------------------
        # Filter irrelevant names
        # ----------------------------------------------

        name_lower = (
            str(name)
            .strip()
            .lower()
        )

        should_exclude = any(
            word in name_lower
            for word in excluded_words
        )

        if should_exclude:
            continue


        # ----------------------------------------------
        # Coordinates
        # ----------------------------------------------

        geometry = feature.get(
            "geometry",
            {}
        )

        coords = geometry.get(
            "coordinates",
            []
        )

        longitude = (
            coords[0]
            if len(coords) > 0
            else None
        )

        latitude = (
            coords[1]
            if len(coords) > 1
            else None
        )

        if latitude is None:
            continue

        if longitude is None:
            continue


        # ----------------------------------------------
        # Add place
        # ----------------------------------------------

        places_records.append({

            "Place_ID": (
                f"P{len(places_records) + 1:04d}"
            ),

            "Trip_ID": trip_id,

            "Destination": destination,

            "Place_Name": name,

            "Category": category_text,

            "Address": address,

            "Latitude": latitude,

            "Longitude": longitude
        })


# --------------------------------------------------
# 8. Create DataFrame
# --------------------------------------------------

places_df = pd.DataFrame(
    places_records
)


# --------------------------------------------------
# 9. Clean dataset
# --------------------------------------------------

if not places_df.empty:

    places_df = places_df.dropna()

    for column in places_df.columns:

        places_df = places_df[
            places_df[column]
            .astype(str)
            .str.strip()
            .ne("")
        ]


# --------------------------------------------------
# 10. Remove duplicate places
# --------------------------------------------------

if not places_df.empty:

    places_df = places_df.drop_duplicates(
        subset=[
            "Trip_ID",
            "Place_Name",
            "Latitude",
            "Longitude"
        ],
        keep="first"
    )


# --------------------------------------------------
# 11. Save dataset
# --------------------------------------------------

output_file = "data/places.csv"

places_df.to_csv(
    output_file,
    index=False,
    encoding="utf-8-sig"
)


# --------------------------------------------------
# 12. Display results
# --------------------------------------------------

print("\n--------------------------------")
print("Clean places.csv created!")
print("--------------------------------")

print(
    "Number of records:",
    len(places_df)
)

print("\nColumns:")

print(
    list(places_df.columns)
)

print("\nFirst 20 records:")

if not places_df.empty:

    print(
        places_df.head(20).to_string(
            index=False
        )
    )

else:

    print("No places found.")