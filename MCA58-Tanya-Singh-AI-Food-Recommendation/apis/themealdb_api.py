
import requests
import pandas as pd
from config import THEMEALDB_API_KEY, API_DATA_DIR


def collect_themealdb_data(food_names):
    results = []

    base_url = (
        f"https://www.themealdb.com/api/json/v1/"
        f"{THEMEALDB_API_KEY}/search.php"
    )

    for food in food_names:
        try:
            response = requests.get(
                base_url,
                params={"s": food},
                timeout=30
            )
            response.raise_for_status()

            meals = response.json().get("meals") or []

            if meals:
                meal = meals[0]

                ingredients = []
                for i in range(1, 21):
                    ingredient = meal.get(f"strIngredient{i}")
                    measure = meal.get(f"strMeasure{i}")

                    if ingredient and ingredient.strip():
                        ingredients.append(
                            f"{measure or ''} {ingredient}".strip()
                        )

                results.append({
                    "food_name": food,
                    "themealdb_id": meal.get("idMeal"),
                    "themealdb_title": meal.get("strMeal"),
                    "themealdb_category": meal.get("strCategory"),
                    "themealdb_area": meal.get("strArea"),
                    "themealdb_instructions": meal.get(
                        "strInstructions"
                    ),
                    "themealdb_ingredients": "; ".join(ingredients),
                    "themealdb_image": meal.get("strMealThumb")
                })

            print("TheMealDB searched:", food)

        except requests.RequestException as error:
            print("TheMealDB error for", food, ":", error)

    df = pd.DataFrame(results)

    df.to_csv(
        f"{API_DATA_DIR}/themealdb_data.csv",
        index=False
    )

    print("\nTheMealDB records collected:", len(df))
    return df
