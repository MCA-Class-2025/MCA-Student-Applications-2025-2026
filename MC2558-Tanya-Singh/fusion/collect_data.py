
import os
import time
import requests
import pandas as pd

from config import (
    ORIGINAL_DATA,
    API_DATA_DIR,
    USDA_API_KEY,
    SPOONACULAR_API_KEY,
    OPENWEATHER_API_KEY,
)

BASE_URL = "https://api.spoonacular.com"
USDA_URL = "https://api.nal.usda.gov/fdc/v1"


def get_food_names():
    df = pd.read_excel(ORIGINAL_DATA)

    if "food_name" not in df.columns:
        raise ValueError("food_name column is missing.")

    return df["food_name"].dropna().astype(str).unique().tolist()


def collect_usda(food_names):
    records = []

    if not USDA_API_KEY:
        print("USDA key missing. Skipping USDA.")
        return records

    for food in food_names:
        try:
            response = requests.get(
                f"{USDA_URL}/foods/search",
                params={
                    "query": food,
                    "api_key": USDA_API_KEY,
                    "pageSize": 3
                },
                timeout=20
            )
            response.raise_for_status()

            for item in response.json().get("foods", []):
                nutrients = {}

                for nutrient in item.get("foodNutrients", []):
                    name = nutrient.get("nutrientName", "")
                    value = nutrient.get("value")

                    if name:
                        nutrients[name] = value

                records.append({
                    "query_food": food,
                    "food_name": item.get("description"),
                    "fdc_id": item.get("fdcId"),
                    "data_type": item.get("dataType"),
                    "calories": nutrients.get("Energy"),
                    "protein_g": nutrients.get("Protein"),
                    "carbs_g": nutrients.get("Carbohydrate, by difference"),
                    "fat_g": nutrients.get("Total lipid (fat)"),
                    "fiber_g": nutrients.get("Fiber, total dietary"),
                    "source": "USDA"
                })

            print("USDA:", food)

        except Exception as error:
            print("USDA error:", food, error)

        time.sleep(0.3)

    return records


def collect_spoonacular(food_names):
    records = []

    if not SPOONACULAR_API_KEY:
        print("Spoonacular key missing. Skipping.")
        return records

    for food in food_names:
        try:
            response = requests.get(
                f"{BASE_URL}/recipes/complexSearch",
                params={
                    "apiKey": SPOONACULAR_API_KEY,
                    "query": food,
                    "number": 2,
                    "addRecipeInformation": True,
                    "fillIngredients": True
                },
                timeout=25
            )
            response.raise_for_status()

            for item in response.json().get("results", []):
                ingredients = [
                    ingredient.get("original", "")
                    for ingredient in item.get("extendedIngredients", [])
                ]

                records.append({
                    "query_food": food,
                    "food_name": item.get("title"),
                    "recipe_id": item.get("id"),
                    "ingredients": "; ".join(ingredients),
                    "instructions": item.get("instructions"),
                    "ready_in_minutes": item.get("readyInMinutes"),
                    "servings": item.get("servings"),
                    "source": "Spoonacular"
                })

            print("Spoonacular:", food)

        except Exception as error:
            print("Spoonacular error:", food, error)

        time.sleep(0.5)

    return records


def collect_themealdb(food_names):
    records = []

    for food in food_names:
        try:
            response = requests.get(
                "https://www.themealdb.com/api/json/v1/1/search.php",
                params={"s": food},
                timeout=20
            )
            response.raise_for_status()

            meals = response.json().get("meals") or []

            for meal in meals[:2]:
                ingredients = []

                for number in range(1, 21):
                    ingredient = meal.get(f"strIngredient{number}")
                    measure = meal.get(f"strMeasure{number}")

                    if ingredient and ingredient.strip():
                        ingredients.append(
                            f"{measure or ''} {ingredient}".strip()
                        )

                records.append({
                    "query_food": food,
                    "food_name": meal.get("strMeal"),
                    "meal_id": meal.get("idMeal"),
                    "category": meal.get("strCategory"),
                    "area": meal.get("strArea"),
                    "ingredients": "; ".join(ingredients),
                    "instructions": meal.get("strInstructions"),
                    "image_url": meal.get("strMealThumb"),
                    "source": "TheMealDB"
                })

            print("TheMealDB:", food)

        except Exception as error:
            print("TheMealDB error:", food, error)

        time.sleep(0.2)

    return records


def collect_weather():
    if not OPENWEATHER_API_KEY:
        print("OpenWeather API key missing. Skipping weather.")
        return []

    cities = ["Mumbai", "Delhi", "Bengaluru", "Pune", "Chennai"]
    records = []

    for city in cities:
        try:
            response = requests.get(
                "https://api.openweathermap.org/data/2.5/weather",
                params={
                    "q": city,
                    "appid": OPENWEATHER_API_KEY,
                    "units": "metric"
                },
                timeout=20
            )
            response.raise_for_status()

            data = response.json()
            temperature = data.get("main", {}).get("temp")

            records.append({
                "city": city,
                "temperature_c": temperature,
                "weather_condition": (
                    data.get("weather", [{}])[0].get("description")
                ),
                "humidity": data.get("main", {}).get("humidity"),
                "wind_speed": data.get("wind", {}).get("speed"),
                "weather_timestamp": data.get("dt"),
                "source": "OpenWeatherMap"
            })

            print("Weather:", city)

        except Exception as error:
            print("Weather error:", city, error)

    return records


def save_records(records, filename):
    path = os.path.join(API_DATA_DIR, filename)

    pd.DataFrame(records).to_csv(
        path,
        index=False,
        encoding="utf-8-sig"
    )

    print(f"Saved {len(records)} records: {path}")


def main():
    os.makedirs(API_DATA_DIR, exist_ok=True)

    food_names = get_food_names()
    print("Unique foods:", len(food_names))

    save_records(
        collect_usda(food_names),
        "usda_data.csv"
    )

    save_records(
        collect_spoonacular(food_names),
        "spoonacular_data.csv"
    )

    save_records(
        collect_themealdb(food_names),
        "themealdb_data.csv"
    )

    save_records(
        collect_weather(),
        "weather_data.csv"
    )

    print("\nAPI DATA COLLECTION COMPLETED.")


if __name__ == "__main__":
    main()
