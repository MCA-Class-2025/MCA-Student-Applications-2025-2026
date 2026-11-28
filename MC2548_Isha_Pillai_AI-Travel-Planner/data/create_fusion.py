import pandas as pd


# ==================================================
# 1. LOAD DATASETS
# ==================================================

print("\nLoading datasets...")

travel = pd.read_csv("data/clean_travel_data.csv")
weather = pd.read_csv("data/weather.csv")
exchange = pd.read_csv("data/exchange_rates.csv")
images = pd.read_csv("data/images.csv")
flights = pd.read_csv("data/flights.csv")
places = pd.read_csv("data/places.csv")


print("Travel records:", len(travel))
print("Weather records:", len(weather))
print("Exchange records:", len(exchange))
print("Image records:", len(images))
print("Flight records:", len(flights))
print("Place records:", len(places))


# ==================================================
# 2. VALID TRIPS
# ==================================================

valid_trip_ids = travel["Trip ID"].astype(int)


weather = weather[
    weather["Trip_ID"].isin(valid_trip_ids)
].copy()

exchange = exchange[
    exchange["Trip_ID"].isin(valid_trip_ids)
].copy()

images = images[
    images["Trip_ID"].isin(valid_trip_ids)
].copy()

flights = flights[
    flights["Trip_ID"].isin(valid_trip_ids)
].copy()

places = places[
    places["Trip_ID"].isin(valid_trip_ids)
].copy()


# ==================================================
# 3. PREPARE WEATHER
# ==================================================

weather = weather[
    [
        "Trip_ID",
        "Temperature_C",
        "Feels_Like_C",
        "Humidity",
        "Weather_Condition",
        "Wind_Speed"
    ]
].drop_duplicates(
    subset=["Trip_ID"],
    keep="first"
)

weather = weather.rename(
    columns={
        "Temperature_C": "Weather_Temperature_C",
        "Feels_Like_C": "Weather_Feels_Like_C",
        "Humidity": "Weather_Humidity",
        "Weather_Condition": "Weather_Condition",
        "Wind_Speed": "Weather_Wind_Speed"
    }
)


# ==================================================
# 4. PREPARE EXCHANGE RATE
# ==================================================

exchange = exchange[
    [
        "Trip_ID",
        "From_Currency",
        "To_Currency",
        "Amount_INR",
        "Exchange_Rate",
        "Converted_Amount"
    ]
].drop_duplicates(
    subset=["Trip_ID"],
    keep="first"
)

exchange = exchange.rename(
    columns={
        "From_Currency": "Currency_From",
        "To_Currency": "Currency_To",
        "Amount_INR": "Currency_Amount_INR",
        "Exchange_Rate": "Currency_Exchange_Rate",
        "Converted_Amount": "Currency_Converted_Amount"
    }
)


# ==================================================
# 5. PREPARE IMAGES
# ==================================================

images = images[
    [
        "Trip_ID",
        "Photo_ID",
        "Photographer",
        "Image_URL",
        "Pexels_URL"
    ]
].drop_duplicates(
    subset=["Trip_ID"],
    keep="first"
)

images = images.rename(
    columns={
        "Photo_ID": "Pexels_Photo_ID",
        "Photographer": "Pexels_Photographer",
        "Image_URL": "Pexels_Image_URL",
        "Pexels_URL": "Pexels_Page_URL"
    }
)


# ==================================================
# 6. PREPARE FLIGHTS
# ==================================================

flights = flights[
    [
        "Trip_ID",
        "Flight_Date",
        "Flight_Status",
        "Departure_IATA",
        "Arrival_IATA",
        "Departure_Time",
        "Arrival_Time",
        "Airline",
        "Airline_IATA",
        "Flight_Number",
        "Flight_IATA"
    ]
].drop_duplicates(
    subset=["Trip_ID"],
    keep="first"
)

flights = flights.rename(
    columns={
        "Departure_IATA": "Flight_Departure_IATA",
        "Arrival_IATA": "Flight_Arrival_IATA",
        "Departure_Time": "Flight_Departure_Time",
        "Arrival_Time": "Flight_Arrival_Time",
        "Airline": "Flight_Airline",
        "Airline_IATA": "Flight_Airline_IATA"
    }
)


# ==================================================
# 7. PREPARE GEOAPIFY PLACES
# ==================================================

print("\nPreparing Geoapify places...")

# Remove incomplete places
places = places.dropna(
    subset=[
        "Place_Name",
        "Category",
        "Address",
        "Latitude",
        "Longitude"
    ]
).copy()


# Create a readable list of places for each Trip_ID
places_summary = (
    places.groupby("Trip_ID")
    .agg(
        Place_Count=("Place_ID", "count"),
        Places_List=(
            "Place_Name",
            lambda x: " | ".join(
                x.astype(str).drop_duplicates()
            )
        )
    )
    .reset_index()
)


# ==================================================
# 8. MERGE WEATHER
# ==================================================

print("Merging Weather data...")

fusion = travel.merge(
    weather,
    left_on="Trip ID",
    right_on="Trip_ID",
    how="left"
)

fusion = fusion.drop(
    columns=["Trip_ID"]
)


# ==================================================
# 9. MERGE EXCHANGE RATE
# ==================================================

print("Merging Exchange Rate data...")

fusion = fusion.merge(
    exchange,
    left_on="Trip ID",
    right_on="Trip_ID",
    how="left"
)

fusion = fusion.drop(
    columns=["Trip_ID"]
)


# ==================================================
# 10. MERGE IMAGES
# ==================================================

print("Merging Pexels data...")

fusion = fusion.merge(
    images,
    left_on="Trip ID",
    right_on="Trip_ID",
    how="left"
)

fusion = fusion.drop(
    columns=["Trip_ID"]
)


# ==================================================
# 11. MERGE FLIGHTS
# ==================================================

print("Merging Aviationstack data...")

fusion = fusion.merge(
    flights,
    left_on="Trip ID",
    right_on="Trip_ID",
    how="left"
)

fusion = fusion.drop(
    columns=["Trip_ID"]
)


# ==================================================
# 12. MERGE PLACES SUMMARY
# ==================================================

print("Merging Geoapify places summary...")

fusion = fusion.merge(
    places_summary,
    left_on="Trip ID",
    right_on="Trip_ID",
    how="left"
)

fusion = fusion.drop(
    columns=["Trip_ID"]
)


# ==================================================
# 13. HANDLE MISSING FLIGHT DATA
# ==================================================

flight_columns = [
    "Flight_Date",
    "Flight_Status",
    "Flight_Departure_IATA",
    "Flight_Arrival_IATA",
    "Flight_Departure_Time",
    "Flight_Arrival_Time",
    "Flight_Airline",
    "Flight_Airline_IATA",
    "Flight_Number",
    "Flight_IATA"
]

for column in flight_columns:
    fusion[column] = fusion[column].fillna(
        "Not Available"
    )


# ==================================================
# 14. HANDLE MISSING PLACE DATA
# ==================================================

fusion["Place_Count"] = fusion[
    "Place_Count"
].fillna(0).astype(int)

fusion["Places_List"] = fusion[
    "Places_List"
].fillna("Not Available")


# ==================================================
# 15. ADD SOURCE INFORMATION
# ==================================================

fusion["Weather_Source"] = "OpenWeather"

fusion["Exchange_Rate_Source"] = "ExchangeRate API"

fusion["Image_Source"] = "Pexels"

fusion["Flight_Source"] = "Aviationstack"

fusion["Places_Source"] = "Geoapify"


# ==================================================
# 16. FINAL CHECK
# ==================================================

print("\n------------------------------------------")
print("FINAL FUSION CHECK")
print("------------------------------------------")

print(
    "Clean travel trips:",
    len(travel)
)

print(
    "Fusion records:",
    len(fusion)
)

print(
    "Duplicate Trip IDs:",
    fusion["Trip ID"].duplicated().sum()
)


print("\nMissing values:")

print(
    fusion.isnull().sum()
)


# ==================================================
# 17. SAVE FINAL FUSION DATASET
# ==================================================

output_file = "data/final_fusion.csv"

fusion.to_csv(
    output_file,
    index=False,
    encoding="utf-8-sig"
)


print("\n------------------------------------------")
print("FINAL FUSION DATASET CREATED!")
print("------------------------------------------")

print(
    "File:",
    output_file
)

print(
    "Records:",
    len(fusion)
)

print(
    "Columns:",
    len(fusion.columns)
)


# ==================================================
# 18. SAMPLE
# ==================================================

print("\nFirst 5 records:")

print(
    fusion.head().to_string(
        index=False
    )
)