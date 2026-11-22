import requests
import pandas as pd
from config import SPOONACULAR_API_KEY, API_DATA_DIR

def collect_spoonacular_data(food_names):
    results = []

    if not SPOONACULAR_API_KEY:
        print("Spoonacular API key missing!")
        return pd.DataFrame()

    url = "https://api.spoonacular.com/recipes/complexSearch"

    for food in food_names:
        try:
            response = requests.get(
                url,
                params={
                    "apiKey": SPOONACULAR_API_KEY,
                    "query": food,
                    "number": 1,
                    "addRecipeInformation": True
                },
                timeout=30
            )

            response.raise_for_status()
            data = response.json()

            for item in data.get("results", []):
                results.append({
                    "food_name": food,
                    "spoonacular_id": item.get("id"),
                    "spoonacular_title": item.get("title"),
                    "spoonacular_ready_minutes": item.get("readyInMinutes"),
                    "spoonacular_servings": item.get("servings"),
                    "spoonacular_image": item.get("image")
                })

            print("Spoonacular collected:", food)

        except requests.RequestException as e:
            print("Spoonacular error:", food, e)

    df = pd.DataFrame(results)

    df.to_csv(
        f"{API_DATA_DIR}/spoonacular_data.csv",
        index=False
    )

    return df