import pandas as pd


FUSION_FILE = "data/final_fusion.csv"


def get_destination_context(destination):

    # ----------------------------------------
    # Load fusion dataset
    # ----------------------------------------

    df = pd.read_csv(
        FUSION_FILE,
        encoding="utf-8-sig"
    )

    destination = str(
        destination
    ).lower().strip()


    # ----------------------------------------
    # Find destination
    # ----------------------------------------

    result = df[
        df["Destination"]
        .astype(str)
        .str.lower()
        .str.contains(
            destination,
            na=False,
            regex=False
        )
    ]

    if result.empty:
        return None


    # ----------------------------------------
    # Use first row for common destination data
    # ----------------------------------------

    row = result.iloc[0]


    # ----------------------------------------
    # Collect places from ALL matching rows
    # ----------------------------------------

    places = []

    for value in result["Places_List"]:

        if pd.isna(value):
            continue

        places_text = str(value).strip()

        if not places_text:
            continue

        if places_text.lower() in [
            "not available",
            "nan",
            "none"
        ]:
            continue


        for place in places_text.split("|"):

            place = place.strip()

            if not place:
                continue

            if place.lower() in [
                "not available",
                "nan",
                "none"
            ]:
                continue

            places.append(place)


    # ----------------------------------------
    # Remove duplicate places
    # ----------------------------------------

    unique_places = []

    seen = set()

    for place in places:

        key = place.lower()

        if key not in seen:

            seen.add(key)

            unique_places.append(place)


    # ----------------------------------------
    # Remove obvious Geoapify noise
    # ----------------------------------------

    excluded_places = {
        "boat model",
        "victory hand",
        "pen",
        "seawings airplane counter"
    }

    places = [
        place
        for place in unique_places
        if place.lower().strip()
        not in excluded_places
    ]


    # ----------------------------------------
    # Limit place list
    # ----------------------------------------

    places = places[:30]


    # ========================================
    # CREATE CONTEXT
    # ========================================

    context = {

        "destination": str(
            row["Destination"]
        ),


        # ------------------------------------
        # WEATHER
        # Convert NumPy values to Python types
        # ------------------------------------

        "weather": {

            "temperature_c":
                float(row["Weather_Temperature_C"]),

            "feels_like_c":
                float(row["Weather_Feels_Like_C"]),

            "humidity":
                int(row["Weather_Humidity"]),

            "condition":
                str(row["Weather_Condition"]),

            "wind_speed":
                float(row["Weather_Wind_Speed"])
        },


        # ------------------------------------
        # CURRENCY
        # Convert NumPy values to Python types
        # ------------------------------------

        "currency": {

            "from":
                str(row["Currency_From"]),

            "to":
                str(row["Currency_To"]),

            "amount_inr":
                int(row["Currency_Amount_INR"]),

            "exchange_rate":
                float(row["Currency_Exchange_Rate"]),

            "converted_amount":
                float(row["Currency_Converted_Amount"])
        },


        # ------------------------------------
        # PLACES
        # ------------------------------------

        "places": places,


        # ------------------------------------
        # IMAGE
        # Convert photo ID to Python int
        # ------------------------------------

        "image": {

            "photo_id":
                int(row["Pexels_Photo_ID"]),

            "photographer":
                str(row["Pexels_Photographer"]),

            "image_url":
                str(row["Pexels_Image_URL"]),

            "pexels_url":
                str(row["Pexels_Page_URL"])
        },


        # ------------------------------------
        # FLIGHT
        # ------------------------------------

        "flight": {

            "date":
                str(row["Flight_Date"]),

            "status":
                str(row["Flight_Status"]),

            "departure":
                str(row["Flight_Departure_IATA"]),

            "arrival":
                str(row["Flight_Arrival_IATA"]),

            "airline":
                str(row["Flight_Airline"]),

            "flight_number":
                str(row["Flight_Number"])
        },


        # ------------------------------------
        # ACCOMMODATION
        # ------------------------------------

        "accommodation": {

            "type":
                str(
                    row["Accommodation_type"]
                    if "Accommodation_type" in row
                    else row["Accommodation type"]
                ),

            "cost":
                str(row["Accommodation cost"])
        },


        # ------------------------------------
        # TRANSPORTATION
        # ------------------------------------

        "transportation": {

            "type":
                str(row["Transportation type"]),

            "cost":
                str(row["Transportation cost"])
        }
    }


    return context