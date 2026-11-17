import os
import requests
from dotenv import load_dotenv

load_dotenv()

USDA_API_KEY = os.getenv("USDA_API_KEY")

BASE_URL = "https://api.nal.usda.gov/fdc/v1/foods/search"


def search_food_nutrition(food_name):

    if not USDA_API_KEY:

        return {
            "success": False,
            "error": "USDA_API_KEY is missing from .env"
        }

    params = {
        "api_key": USDA_API_KEY,
        "query": food_name,
        "pageSize": 5
    }

    try:

        response = requests.get(
            BASE_URL,
            params=params,
            timeout=15
        )

        if response.status_code != 200:

            return {
                "success": False,
                "error": (
                    f"USDA API Error: "
                    f"{response.status_code}"
                )
            }

        data = response.json()

        foods = data.get("foods", [])

        if not foods:

            return {
                "success": False,
                "error": f"No USDA food found for {food_name}"
            }

        results = []

        for food in foods[:5]:

            nutrients = {}

            for nutrient in food.get(
                "foodNutrients",
                []
            ):

                name = nutrient.get(
                    "nutrientName",
                    ""
                )

                value = nutrient.get(
                    "value",
                    0
                )

                unit = nutrient.get(
                    "unitName",
                    ""
                )

                if name in [
                    "Energy",
                    "Protein",
                    "Total lipid (fat)",
                    "Carbohydrate, by difference",
                    "Fiber, total dietary"
                ]:

                    nutrients[name] = {
                        "value": value,
                        "unit": unit
                    }

            results.append(
                {
                    "food_name": food.get(
                        "description",
                        ""
                    ),
                    "fdc_id": food.get(
                        "fdcId"
                    ),
                    "nutrition": nutrients
                }
            )

        return {
            "success": True,
            "results": results
        }

    except Exception as e:

        return {
            "success": False,
            "error": str(e)
        }


if __name__ == "__main__":

    print("=" * 60)
    print("USDA FOODDATA CENTRAL API TEST")
    print("=" * 60)

    result = search_food_nutrition(
        "chicken"
    )

    if result["success"]:

        for food in result["results"]:

            print("\nFood:")
            print(food["food_name"])

            print(
                "FDC ID:",
                food["fdc_id"]
            )

            print(
                "Nutrition:",
                food["nutrition"]
            )

    else:

        print(
            "ERROR:",
            result["error"]
        )