
import pandas as pd

from config import ORIGINAL_DATA, API_DATA_DIR

from apis.usda_api import collect_usda_data
from apis.weather_api import collect_weather_data
from apis.spoonacular_api import collect_spoonacular_data
from apis.themealdb_api import collect_themealdb_data


def main():

    print("\n========== STARTING API DATA COLLECTION ==========")

    # Load original Excel dataset
    df = pd.read_excel(ORIGINAL_DATA, engine="openpyxl")

    # Get unique food names
    food_names = (
        df["food_name"]
        .dropna()
        .astype(str)
        .str.strip()
        .drop_duplicates()
        .tolist()
    )

    print("Original records:", len(df))
    print("Unique food names:", len(food_names))

    # API 1: USDA
    print("\n1. Collecting USDA data...")
    usda_df = collect_usda_data(food_names)

    # API 2: OpenWeatherMap
    print("\n2. Collecting weather data...")
    weather_df = collect_weather_data("Mumbai")

    # API 3: Spoonacular
    print("\n3. Collecting Spoonacular data...")
    spoonacular_df = collect_spoonacular_data(food_names)

    # API 4: TheMealDB
    print("\n4. Collecting TheMealDB data...")
    themealdb_df = collect_themealdb_data(food_names)

    print("\n========== COLLECTION SUMMARY ==========")

    print("USDA records:", len(usda_df))
    print("Weather records:", len(weather_df))
    print("Spoonacular records:", len(spoonacular_df))
    print("TheMealDB records:", len(themealdb_df))

    print("\nAPI data saved in:", API_DATA_DIR)


if __name__ == "__main__":
    main()
