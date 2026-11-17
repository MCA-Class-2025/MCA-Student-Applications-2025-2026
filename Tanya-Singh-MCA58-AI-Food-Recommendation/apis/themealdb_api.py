import requests

BASE_URL = (
    "https://www.themealdb.com/api/json/v1/1"
)


def search_meals(food_name):

    url = (
        f"{BASE_URL}/search.php"
    )

    params = {
        "s": food_name
    }

    try:

        response = requests.get(
            url,
            params=params,
            timeout=15
        )

        if response.status_code != 200:

            return {
                "success": False,
                "error": (
                    f"TheMealDB Error: "
                    f"{response.status_code}"
                )
            }

        data = response.json()

        meals = data.get(
            "meals"
        )

        if not meals:

            return {
                "success": False,
                "error": (
                    f"No meal found for "
                    f"{food_name}"
                )
            }

        results = []

        for meal in meals[:5]:

            results.append(
                extract_meal(
                    meal
                )
            )

        return {
            "success": True,
            "meals": results
        }

    except Exception as e:

        return {
            "success": False,
            "error": str(e)
        }


def extract_meal(meal):

    ingredients = []

    for i in range(1, 21):

        ingredient = meal.get(
            f"strIngredient{i}"
        )

        measure = meal.get(
            f"strMeasure{i}"
        )

        if ingredient:

            ingredients.append(
                {
                    "ingredient": ingredient,
                    "measure": measure
                }
            )

    return {

        "id": meal.get(
            "idMeal"
        ),

        "name": meal.get(
            "strMeal"
        ),

        "category": meal.get(
            "strCategory"
        ),

        "area": meal.get(
            "strArea"
        ),

        "instructions": meal.get(
            "strInstructions"
        ),

        "thumbnail": meal.get(
            "strMealThumb"
        ),

        "youtube": meal.get(
            "strYoutube"
        ),

        "ingredients": ingredients
    }


if __name__ == "__main__":

    print("=" * 60)
    print("THEMEALDB API TEST")
    print("=" * 60)

    result = search_meals(
        "Chicken"
    )

    if result["success"]:

        print(
            f"\nFound {len(result['meals'])} meals."
        )

        for meal in result["meals"]:

            print("\nMeal:")
            print(
                meal["name"]
            )

            print(
                "Category:",
                meal["category"]
            )

            print(
                "Area:",
                meal["area"]
            )

            print(
                "Ingredients:",
                meal["ingredients"][:5]
            )

    else:

        print(
            "ERROR:",
            result["error"]
        )