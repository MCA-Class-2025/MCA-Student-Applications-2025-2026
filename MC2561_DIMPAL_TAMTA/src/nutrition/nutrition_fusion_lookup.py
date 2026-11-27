# nutrition/nutrition_fusion_lookup.py
#
# Cascading nutrition lookup:
#     food name -> local CSV -> USDA (cached) -> Global Fusion Dataset (Gemini/Pixabay/OFF) -> Spoonacular -> give up

from nutrition.nutrition_db import get_nutrition
from fusion.usda_client import get_usda_food_cached
from nutrition.global_fusion_lookup import get_global_fusion_data
from utils.api_helpers import get_spoonacular_nutrition


def _usda_to_display(usda_data):
    mapping = {
        "usda_calories": "Energy (kcal)", "usda_protein": "Protein (g)",
        "usda_fat": "Fat (g)", "usda_carbohydrates": "Carbohydrates (g)",
        "usda_fiber": "Dietary Fiber (g)", "usda_calcium": "Calcium (mg)",
        "usda_iron": "Iron (mg)", "usda_sodium": "Sodium (mg)", "usda_sugar": "Sugar (g)",
    }
    out = {}
    for k, display in mapping.items():
        if k in usda_data and usda_data[k] is not None:
            out[display] = usda_data[k]
    return out


def _spoonacular_to_display(sp_data):
    mapping = {"calories": "Energy (kcal)", "protein": "Protein (g)", "fat": "Fat (g)", "carbs": "Carbohydrates (g)"}
    out = {}
    for k, display in mapping.items():
        v = sp_data.get(k)
        if v not in (None, "N/A"):
            out[display] = v
    return out


# The exact 10 nutrient columns you want shown for the global fusion source
GLOBAL_FUSION_NUTRIENT_DISPLAY_MAP = {
    "calories": "Calories (kcal)",
    "protein": "Protein (g)",
    "carbohydrate": "Carbohydrates (g)",
    "fat": "Fat (g)",
    "fiber": "Fiber (g)",
    "usda_calcium_mg": "Calcium (mg)",
    "usda_iron_mg": "Iron (mg)",
    "usda_potassium_mg": "Potassium (mg)",
    "usda_sodium_mg": "Sodium (mg)",
    "usda_vitamin_c_mg": "Vitamin C (mg)",
}


def _global_fusion_to_display(row):
    out = {}
    for k, display in GLOBAL_FUSION_NUTRIENT_DISPLAY_MAP.items():
        v = row.get(k)
        if v is not None:
            out[display] = v
    return out


def get_nutrition_with_fallback(food_name, format_local_fn=None):
    """
    Returns (display_dict, source, raw_data) where source is one of:
    'local', 'usda', 'global_fusion', 'spoonacular', 'none'.
    """
    # 1. Local CSV
    local_data = get_nutrition(food_name)
    if local_data:
        display = format_local_fn(local_data) if format_local_fn else local_data
        if display:
            return display, "local", local_data

    # 2. USDA
    usda_data, status = get_usda_food_cached(food_name, sleep_between_calls=0)
    if status == "matched" and usda_data:
        display = _usda_to_display(usda_data)
        if display:
            return display, "usda", usda_data

    # 3. Global Fusion Dataset (Gemini origin/production, Pixabay image, translations)
    global_row = get_global_fusion_data(food_name)
    if global_row:
        display = _global_fusion_to_display(global_row)
        if display:
            return display, "global_fusion", global_row

    # 4. Spoonacular
    sp_data = get_spoonacular_nutrition(food_name)
    if sp_data:
        display = _spoonacular_to_display(sp_data)
        if display:
            return display, "spoonacular", sp_data

    return {}, "none", {}


SOURCE_LABELS = {
    "local": "📗 Local Indian Food Database",
    "usda": "🇺🇸 USDA FoodData Central (live API)",
    "global_fusion": "🌍 Global Fusion Dataset (USDA + Gemini + Open Food Facts)",
    "spoonacular": "🥄 Spoonacular (live API)",
    "none": "❌ No source had data for this food",
}