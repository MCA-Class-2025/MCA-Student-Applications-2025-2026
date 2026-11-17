import os
import requests
from dotenv import load_dotenv

load_dotenv()

SPOONACULAR_API_KEY = os.getenv(
    "SPOONACULAR_API_KEY"
)

BASE_URL = (
    "https://api.spoonacular.com/recipes/complexSearch"
)


def search_recipes(
    query,
    diet=None,
    cuisine=None,
    number=5
):

    if not SPOONACULAR_API_KEY:

        return {
            "success": False,
            "error": (
                "SPOONACULAR_API_KEY "
                "is missing from .env"
            )
        }

    params = {

        "apiKey": SPOONACULAR_API_KEY,

        "query": query,

        "number": number,

        "addRecipeInformation": True,

        "fillIngredients": True
    }

    if diet:

        params["diet"] = diet

    if cuisine:

        params["cuisine"] = cuisine

    try:

        response = requests.get(
            BASE_URL,
            params=params,
            timeout=20
        )

        if response.status_code != 200:

            return {
                "success": False,
                "error": (
                    f"Spoonacular API Error: "
                    f"{response.status_code}"
                )
            }

        data = response.json()

        recipes = []

        for recipe in data.get(
            "results",
            []
        ):

            ingredients = []

            for ingredient in recipe.get(
                "extendedIngredients",
                []
            ):

                ingredients.append(
                    ingredient.get(
                        "original",
                        ""
                    )
                )

            recipes.append(
                {
                    "id": recipe.get(
                        "id"
                    ),

                    "title": recipe.get(
                        "title",
                        ""
                    ),

                    "ready_in_minutes": recipe.get(
                        "readyInMinutes"
                    ),

                    "servings": recipe.get(
                        "servings"
                    ),

                    "vegetarian": recipe.get(
                        "vegetarian"
                    ),

                    "vegan": recipe.get(
                        "vegan"
                    ),

                    "health_score": recipe.get(
                        "healthScore"
                    ),

                    "ingredients": ingredients,

                    "source_url": recipe.get(
                        "sourceUrl"
                    )
                }
            )

        return {
            "success": True,
            "recipes": recipes
        }

    except Exception as e:

        return {
            "success": False,
            "error": str(e)
        }


if __name__ == "__main__":

    print("=" * 60)
    print("SPOONACULAR API TEST")
    print("=" * 60)

    result = search_recipes(
        query="Indian vegetarian dinner",
        number=5
    )

    if result["success"]:

        print(
            f"\nFound {len(result['recipes'])} recipes."
        )

        for recipe in result["recipes"]:

            print("\nRecipe:")
            print(
                recipe["title"]
            )

            print(
                "Cooking time:",
                recipe["ready_in_minutes"]
            )

            print(
                "Ingredients:",
                recipe["ingredients"][:5]
            )

    else:

        print(
            "ERROR:",
            result["error"]
        )