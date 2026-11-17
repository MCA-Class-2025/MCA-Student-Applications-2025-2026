import os
import pandas as pd
from dotenv import load_dotenv


load_dotenv()

from apis.gemini_api import generate_food_recommendation
from apis.usda_api import search_food_nutrition
from apis.weather_api import get_weather_category
from apis.spoonacular_api import search_recipes
from apis.themealdb_api import search_meals


DATASET_PATH = os.path.join(
    "data",
    "food_dataset.csv"
)


# ============================================================
# LOAD LOCAL DATASET
# ============================================================

def load_local_dataset():

    try:

        df = pd.read_csv(DATASET_PATH)

        return df

    except Exception as e:

        print(
            "ERROR loading dataset:",
            e
        )

        return pd.DataFrame()


# ============================================================
# SEARCH LOCAL FOOD DATASET
# ============================================================

def search_local_food(
    food_name=None,
    diet=None,
    meal_type=None
):

    df = load_local_dataset()

    if df.empty:

        return []

    result = df.copy()

    # --------------------------------------------------------
    # Search food name
    # --------------------------------------------------------

    if food_name:

        mask = (
            result["food_name"]
            .astype(str)
            .str.lower()
            .str.contains(
                food_name.lower(),
                na=False
            )
        )

        result = result[mask]

    # --------------------------------------------------------
    # Filter diet
    # --------------------------------------------------------

    if diet:

        result = result[
            result["diet"]
            .astype(str)
            .str.lower()
            .str.contains(
                diet.lower(),
                na=False
            )
        ]

    # --------------------------------------------------------
    # Filter meal type
    # --------------------------------------------------------

    if meal_type:

        result = result[
            result["meal_type"]
            .astype(str)
            .str.lower()
            .str.contains(
                meal_type.lower(),
                na=False
            )
        ]

    return result.head(10).to_dict(
        orient="records"
    )


# ============================================================
# GET USDA INFORMATION
# ============================================================

def get_usda_data(food_name):

    try:

        result = search_food_nutrition(
            food_name
        )

        if result.get("success"):

            return result.get(
                "results",
                []
            )

        return []

    except Exception as e:

        print(
            "USDA error:",
            e
        )

        return []


# ============================================================
# GET WEATHER INFORMATION
# ============================================================

def get_weather_data(city):

    try:

        result = get_weather_category(
            city
        )

        if result.get("success"):

            return result.get(
                "data",
                {}
            )

        return {}

    except Exception as e:

        print(
            "Weather error:",
            e
        )

        return {}


# ============================================================
# GET SPOONACULAR RECIPES
# ============================================================

def get_spoonacular_data(
    food_name,
    diet=None
):

    try:

        query = food_name

        if not query:

            query = "Indian food"

        result = search_recipes(
            query=query,
            diet=diet,
            number=5
        )

        if result.get("success"):

            return result.get(
                "recipes",
                []
            )

        return []

    except Exception as e:

        print(
            "Spoonacular error:",
            e
        )

        return []


# ============================================================
# GET THEMEALDB INFORMATION
# ============================================================

def get_themealdb_data(
    food_name
):

    try:

        if not food_name:

            food_name = "Chicken"

        result = search_meals(
            food_name
        )

        if result.get("success"):

            return result.get(
                "meals",
                []
            )

        return []

    except Exception as e:

        print(
            "TheMealDB error:",
            e
        )

        return []


# ============================================================
# FUSION FUNCTION
# ============================================================

def create_fused_data(
    food_name=None,
    city="Mumbai",
    diet=None,
    meal_type=None
):

    print("\n")
    print("=" * 70)
    print("AI FOOD RECOMMENDATION - DATA FUSION")
    print("=" * 70)

    # ========================================================
    # 1. LOCAL DATASET
    # ========================================================

    print("\n[1/5] Searching local dataset...")

    local_data = search_local_food(
        food_name=food_name,
        diet=diet,
        meal_type=meal_type
    )

    print(
        "Local dataset results:",
        len(local_data)
    )

    # ========================================================
    # 2. USDA
    # ========================================================

    print("\n[2/5] Getting USDA nutrition...")

    usda_data = []

    if food_name:

        usda_data = get_usda_data(
            food_name
        )

    print(
        "USDA results:",
        len(usda_data)
    )

    # ========================================================
    # 3. WEATHER
    # ========================================================

    print("\n[3/5] Getting weather...")

    weather_data = get_weather_data(
        city
    )

    if weather_data:

        print(
            "Weather:",
            weather_data.get(
                "weather"
            )
        )

        print(
            "Temperature:",
            weather_data.get(
                "temperature"
            )
        )

        print(
            "Category:",
            weather_data.get(
                "weather_category"
            )
        )

    else:

        print(
            "Weather data unavailable."
        )

    # ========================================================
    # 4. SPOONACULAR
    # ========================================================

    print(
        "\n[4/5] Searching Spoonacular recipes..."
    )

    spoonacular_data = []

    if food_name:

        spoonacular_data = get_spoonacular_data(
            food_name,
            diet=diet
        )

    print(
        "Spoonacular results:",
        len(spoonacular_data)
    )

    # ========================================================
    # 5. THEMEALDB
    # ========================================================

    print(
        "\n[5/5] Searching TheMealDB..."
    )

    themealdb_data = []

    if food_name:

        themealdb_data = get_themealdb_data(
            food_name
        )

    print(
        "TheMealDB results:",
        len(themealdb_data)
    )

    # ========================================================
    # CREATE FUSION OBJECT
    # ========================================================

    fused_data = {

        "user_request": {
            "food_name": food_name,
            "city": city,
            "diet": diet,
            "meal_type": meal_type
        },

        "local_dataset": local_data,

        "usda": usda_data,

        "weather": weather_data,

        "spoonacular": spoonacular_data,

        "themealdb": themealdb_data
    }

    return fused_data


def fusion_to_text(
    fused_data
):

    text = ""

    text += "\n====================================\n"
    text += "USER REQUEST\n"
    text += "====================================\n"

    request = fused_data.get(
        "user_request",
        {}
    )

    text += (
        f"Food: "
        f"{request.get('food_name')}\n"
    )

    text += (
        f"City: "
        f"{request.get('city')}\n"
    )

    text += (
        f"Diet: "
        f"{request.get('diet')}\n"
    )

    text += (
        f"Meal Type: "
        f"{request.get('meal_type')}\n"
    )
    
    text += "\n====================================\n"
    text += "LOCAL FOOD DATASET\n"
    text += "====================================\n"

    for food in fused_data.get(
        "local_dataset",
        []
    ):

        text += (
            f"\nFood: "
            f"{food.get('food_name')}"
        )

        text += (
            f"\nCuisine: "
            f"{food.get('cuisine')}"
        )

        text += (
            f"\nMeal Type: "
            f"{food.get('meal_type')}"
        )

        text += (
            f"\nDiet: "
            f"{food.get('diet')}"
        )

        text += (
            f"\nCalories: "
            f"{food.get('calories')}"
        )

        text += (
            f"\nProtein: "
            f"{food.get('protein')}"
        )

        text += (
            f"\nCarbs: "
            f"{food.get('carbs')}"
        )

        text += (
            f"\nFat: "
            f"{food.get('fat')}"
        )

        text += (
            f"\nFiber: "
            f"{food.get('fiber')}"
        )

        text += (
            f"\nHealth Category: "
            f"{food.get('health_category')}"
        )

        text += (
            f"\nWeather Suitable: "
            f"{food.get('weather_suitable')}"
        )

        text += "\n"

    # ========================================================
    # USDA
    # ========================================================

    text += "\n====================================\n"
    text += "USDA NUTRITION DATA\n"
    text += "====================================\n"

    for food in fused_data.get(
        "usda",
        []
    ):

        text += (
            f"\nFood: "
            f"{food.get('food_name')}"
        )

        text += (
            f"\nFDC ID: "
            f"{food.get('fdc_id')}"
        )

        text += (
            f"\nNutrition: "
            f"{food.get('nutrition')}"
        )

        text += "\n"


    text += "\n====================================\n"
    text += "REAL-TIME WEATHER\n"
    text += "====================================\n"

    weather = fused_data.get(
        "weather",
        {}
    )

    text += (
        f"City: "
        f"{weather.get('city')}\n"
    )

    text += (
        f"Temperature: "
        f"{weather.get('temperature')} °C\n"
    )

    text += (
        f"Feels Like: "
        f"{weather.get('feels_like')} °C\n"
    )

    text += (
        f"Humidity: "
        f"{weather.get('humidity')}%\n"
    )

    text += (
        f"Weather: "
        f"{weather.get('weather')}\n"
    )

    text += (
        f"Description: "
        f"{weather.get('description')}\n"
    )

    text += (
        f"Food Weather Category: "
        f"{weather.get('weather_category')}\n"
    )

    # ========================================================
    # SPOONACULAR
    # ========================================================

    text += "\n====================================\n"
    text += "SPOONACULAR RECIPES\n"
    text += "====================================\n"

    for recipe in fused_data.get(
        "spoonacular",
        []
    ):

        text += (
            f"\nRecipe: "
            f"{recipe.get('title')}"
        )

        text += (
            f"\nReady in: "
            f"{recipe.get('ready_in_minutes')} minutes"
        )

        text += (
            f"\nVegetarian: "
            f"{recipe.get('vegetarian')}"
        )

        text += (
            f"\nVegan: "
            f"{recipe.get('vegan')}"
        )

        text += (
            f"\nHealth Score: "
            f"{recipe.get('health_score')}"
        )

        text += (
            f"\nIngredients: "
            f"{recipe.get('ingredients')}"
        )

        text += "\n"

    # ========================================================
    # THEMEALDB
    # ========================================================

    text += "\n====================================\n"
    text += "THEMEALDB RECIPES\n"
    text += "====================================\n"

    for meal in fused_data.get(
        "themealdb",
        []
    ):

        text += (
            f"\nMeal: "
            f"{meal.get('name')}"
        )

        text += (
            f"\nCategory: "
            f"{meal.get('category')}"
        )

        text += (
            f"\nArea: "
            f"{meal.get('area')}"
        )

        text += (
            f"\nIngredients: "
            f"{meal.get('ingredients')}"
        )

        text += "\n"

    return text


# ============================================================
# GEMINI PROMPT
# ============================================================

def create_gemini_prompt(
    question,
    fused_data
):

    context = fusion_to_text(
        fused_data
    )

    prompt = f"""
You are an intelligent AI Food Recommendation Assistant.

You must recommend food using the provided
retrieved and externally collected information.

USER QUESTION:
{question}

AVAILABLE INFORMATION:
{context}

IMPORTANT RULES:

1. Prefer foods from the user's local dataset
   when they are relevant.

2. Use the Indian food PDF/RAG knowledge base
   when available.

3. Use USDA information for nutrition.

4. Use OpenWeather information for
   weather-aware recommendations.

5. Use Spoonacular and TheMealDB as
   supplementary recipe sources.

6. Do not invent nutrition values.

7. Clearly distinguish between information
   from the local dataset and external sources.

8. Give practical Indian food recommendations.

9. If the user asks for vegetarian food,
   prioritize vegetarian foods.

10. If the user asks for a specific meal,
    respect breakfast/lunch/dinner.

11. Give 2-4 recommendations.

For each recommendation provide:

- Food name
- Why it is recommended
- Calories if available
- Protein if available
- Weather suitability
- Key ingredients
- Short preparation idea

At the end provide a short explanation
of how the recommendation was generated.

Answer in a clear and user-friendly format.
"""

    return prompt


# ============================================================
# COMPLETE FUSION + GEMINI FUNCTION
# ============================================================

def ask_with_fusion(
    question,
    food_name=None,
    city="Mumbai",
    diet=None,
    meal_type=None
):

    fused_data = create_fused_data(
        food_name=food_name,
        city=city,
        diet=diet,
        meal_type=meal_type
    )

    prompt = create_gemini_prompt(
        question,
        fused_data
    )

    print("\n")
    print("=" * 70)
    print("SENDING FUSED DATA TO GEMINI")
    print("=" * 70)

    result = generate_food_recommendation(
        prompt
    )

    return {
        "fusion": fused_data,
        "gemini": result
    }


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    print("\n")
    print("=" * 70)
    print("AI FOOD RECOMMENDATION - FUSION TEST")
    print("=" * 70)

    result = ask_with_fusion(

        question=(
            "What should I eat for dinner "
            "in Mumbai today?"
        ),

        food_name="Dal",

        city="Mumbai",

        diet="Vegetarian",

        meal_type="Dinner"
    )

    print("\n")
    print("=" * 70)
    print("FINAL GEMINI RESULT")
    print("=" * 70)

    if result["gemini"]["success"]:

        print(
            result["gemini"]["answer"]
        )

    else:

        print(
            "Gemini Error:"
        )

        print(
            result["gemini"]["error"]
        )