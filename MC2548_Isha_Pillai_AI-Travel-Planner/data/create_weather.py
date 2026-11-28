import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import pandas as pd
from services.weather_service import get_weather

# Read original travel dataset
input_file = "data/Travel details dataset.csv"
df = pd.read_csv(input_file, sep="\t")
weather_records = []
for _, row in df.iterrows():
    trip_id = row["Trip ID"]
    destination = str(row["Destination"]).strip()

    # Take city name before comma
    city = destination.split(",")[0].strip()
    print(f"Getting weather for Trip {trip_id}: {city}")
    data = get_weather(city)
    if data is None:
        print(f"Skipping Trip {trip_id} - weather data unavailable")
        continue

    # Check required fields
    if (
        "main" not in data
        or "weather" not in data
        or not data["weather"]
        or "wind" not in data
    ):
        print(f"Skipping Trip {trip_id} - incomplete weather data")
        continue
    record = {
        "Weather_ID": f"W{trip_id:03d}",
        "Trip_ID": trip_id,
        "Destination": destination,
        "Temperature_C": data["main"]["temp"],
        "Feels_Like_C": data["main"]["feels_like"],
        "Humidity": data["main"]["humidity"],
        "Weather_Condition": data["weather"][0]["description"],
        "Wind_Speed": data["wind"]["speed"]
    }
    weather_records.append(record)
# Create clean DataFrame
weather_df = pd.DataFrame(weather_records)
# Remove duplicate Trip_ID records
weather_df = weather_df.drop_duplicates(
    subset=["Trip_ID"],
    keep="first"
)
# Remove rows containing empty/null values
weather_df = weather_df.dropna()

# Save clean weather data
output_file = "data/weather.csv"
weather_df.to_csv(
    output_file,
    index=False
)

print("\n--------------------------------")
print("Clean weather.csv created!")
print("--------------------------------")
print("Number of records:", len(weather_df))
print("\nColumns:")
print(list(weather_df.columns))
print("\nWeather Data:")
print(weather_df.to_string(index=False))