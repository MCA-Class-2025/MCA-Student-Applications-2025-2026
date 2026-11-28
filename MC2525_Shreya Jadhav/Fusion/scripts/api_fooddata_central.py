import os
from datetime import datetime, timezone

import requests
import pandas as pd

# ============================================================
# FEMCARE - USDA FOODDATA CENTRAL API
# Dynamic Nutrition API
# ============================================================

API_URL = (
    "https://api.nal.usda.gov/fdc/v1/foods/search"
)

API_KEY = os.getenv("USDA_API_KEY")

OUTPUT_FILE = (
    "Fusion/data/api_fusion/dynamic/"
    "usda_fooddata_nutrition.csv"
)

# ------------------------------------------------------------
# Foods relevant to menstrual-health nutrition context
# ------------------------------------------------------------

FOOD_QUERIES = {
    "spinach": "spinach raw",
    "lentils": "lentils dry",
    "chickpeas": "chickpeas dry",
    "pumpkin seeds": "pumpkin seeds raw",
    "salmon": "Atlantic salmon raw",
    "yogurt": "plain yogurt",
    "banana": "banana raw",
    "almonds": "almonds raw",
    "broccoli": "broccoli raw",
    "egg": "whole egg raw",
    "tomato": "tomato raw",
    "lemon": "lemon raw",
    "mung beans": "mung beans dry",
    "onion": "onion raw",
    "coriander": "coriander leaves raw",
    "chia seeds": "chia seeds dry",
    "paneer": "paneer cheese",
    "bell pepper": "bell pepper raw",
    "oats": "rolled oats dry",
    "ragi flour": "finger millet flour",
    "carrot": "carrot raw",
    "rice": "white rice dry",
    "peas": "green peas raw",
    "milk": "whole milk",
    "olive oil": "olive oil",
    "tofu": "tofu firm",
    "quinoa": "quinoa dry",
    "kidney beans": "kidney beans dry",
    "orange": "orange raw",
    "sweet potato": "sweet potato raw",
    "avocado": "avocado raw",
    "sardines": "sardines canned",
}

# Retained for compatibility with earlier code and documentation.
FOODS = list(FOOD_QUERIES)


# ============================================================
# SEARCH ONE FOOD
# ============================================================

def search_food(food_name, query=None):

    print(
        f"\nSearching USDA FoodData Central: {food_name}"
    )

    search_query = query or food_name

    params = {
        "api_key": API_KEY,
        "query": search_query,

        # Prefer reference foods rather than branded products. SR Legacy is a
        # fallback for culturally relevant foods absent from Foundation data.
        "dataType": ["Foundation", "SR Legacy"],

        # Get several candidates instead of blindly
        # accepting the first result
        "pageSize": 10
    }

    try:

        response = requests.get(
            API_URL,
            params=params,
            timeout=30
        )

        print(
            "HTTP status:",
            response.status_code
        )

        response.raise_for_status()

        data = response.json()

    except requests.exceptions.RequestException as e:

        print("\nUSDA API request failed:")
        print(e)

        return None

    foods = data.get(
        "foods",
        []
    )

    if not foods:

        print(
            "No Foundation Food found for:",
            food_name
        )

        return None

    # --------------------------------------------------------
    # Prefer an exact/close generic food name.
    # Avoid products with obvious brand information.
    # --------------------------------------------------------

    search_terms = [
        term for term in food_name.lower().split()
        if len(term) > 2
    ]

    def candidate_score(food):
        description = food.get("description", "").lower()
        score = sum(8 for term in search_terms if term in description)
        if search_query.lower() in description:
            score += 20
        if not food.get("brandOwner"):
            score += 8
        if "raw" in search_query.lower() and "raw" in description:
            score += 5
        if "whole" in search_query.lower() and "whole" in description:
            score += 5
        return score

    selected = max(foods, key=candidate_score)
    selected["_selection_score"] = candidate_score(selected)

    print(
        "Selected:",
        selected.get("description")
    )

    print(
        "Data type:",
        selected.get("dataType")
    )

    return selected


# ============================================================
# EXTRACT NUTRIENTS
# ============================================================

def extract_nutrients(food):

    nutrients = {}

    for nutrient in food.get(
        "foodNutrients",
        []
    ):

        name = nutrient.get(
            "nutrientName",
            ""
        ).lower()

        value = nutrient.get(
            "value"
        )

        unit = str(
            nutrient.get("unitName", "")
        ).strip().lower()

        if "energy" in name:

            # FoodData Central may return both kJ and kcal entries.
            # Never label a raw kJ value as kcal. Prefer a supplied kcal
            # value; convert kJ only when kcal is not available.
            if unit == "kcal":
                nutrients["energy_kcal_100g"] = value
                nutrients["energy_source_unit"] = "kcal"
            elif (
                unit == "kj"
                and "energy_kcal_100g" not in nutrients
                and value is not None
            ):
                try:
                    nutrients["energy_kcal_100g"] = (
                        float(value) / 4.184
                    )
                    nutrients["energy_source_unit"] = (
                        "kJ converted to kcal"
                    )
                except (TypeError, ValueError):
                    pass

        elif name == "protein":

            nutrients[
                "protein_g_100g"
            ] = value

        elif (
            "carbohydrate" in name
            and "by difference" in name
        ):

            nutrients[
                "carbohydrates_g_100g"
            ] = value

        elif name == "total lipid (fat)":

            nutrients[
                "fat_g_100g"
            ] = value

        elif name == "fiber, total dietary":

            nutrients[
                "fiber_g_100g"
            ] = value

        elif name == "total sugars":

            nutrients[
                "sugars_g_100g"
            ] = value

        elif name == "calcium, ca":

            nutrients[
                "calcium_mg_100g"
            ] = value

        elif name == "iron, fe":

            nutrients[
                "iron_mg_100g"
            ] = value

        elif name == "magnesium, mg":

            nutrients[
                "magnesium_mg_100g"
            ] = value

        elif name == "vitamin b-6":

            nutrients[
                "vitamin_b6_mg_100g"
            ] = value

        elif name == "vitamin b-12":

            nutrients[
                "vitamin_b12_ug_100g"
            ] = value

    return nutrients


def validate_record(record):
    """Return a transparent quality status for a collected food record."""

    issues = []
    required = [
        "energy_kcal_100g", "protein_g_100g",
        "carbohydrates_g_100g", "fat_g_100g",
    ]
    for column in required:
        if record.get(column) is None:
            issues.append(f"Missing {column}")

    numeric_values = {
        key: value for key, value in record.items()
        if key.endswith("_100g") and value is not None
    }
    for key, value in numeric_values.items():
        try:
            if float(value) < 0:
                issues.append(f"Negative {key}")
        except (TypeError, ValueError):
            issues.append(f"Non-numeric {key}")

    if not any(issue.startswith("Missing") for issue in issues):
        energy = float(record["energy_kcal_100g"])
        macro_estimate = (
            float(record["protein_g_100g"]) * 4
            + float(record["carbohydrates_g_100g"]) * 4
            + float(record["fat_g_100g"]) * 9
        )
        if macro_estimate > 0:
            relative_difference = abs(energy - macro_estimate) / macro_estimate
            if relative_difference > 0.45:
                issues.append(
                    "Energy differs materially from the macro-based estimate"
                )

    return {
        "record_status": "Review" if issues else "Validated",
        "validation_notes": "; ".join(issues),
    }


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 70)
    print("USDA FOODDATA CENTRAL")
    print("FEMCARE NUTRITION API")
    print("=" * 70)

    if not API_KEY:

        raise ValueError(
            "USDA_API_KEY is not set.\n\n"
            "Run this in PowerShell first:\n"
            '$env:USDA_API_KEY="YOUR_API_KEY"'
        )

    records = []

    collected_at = datetime.now(timezone.utc).replace(
        microsecond=0
    ).isoformat()

    for food_name, search_query in FOOD_QUERIES.items():

        food = search_food(
            food_name,
            query=search_query,
        )

        if food is None:

            continue

        nutrients = extract_nutrients(
            food
        )

        record = {

            "search_food":
                food_name,

            "fdc_id":
                food.get("fdcId"),

            "food_name":
                food.get("description"),

            "data_type":
                food.get("dataType"),

            "selection_score":
                food.get("_selection_score"),

            "collected_at_utc":
                collected_at,

            **nutrients
        }

        record.update(
            validate_record(record)
        )

        records.append(
            record
        )

    # --------------------------------------------------------
    # Create dataframe
    # --------------------------------------------------------

    df = pd.DataFrame(
        records
    )

    if df.empty:

        print(
            "\nNo nutrition records received."
        )

        return

    # --------------------------------------------------------
    # Numeric conversion
    # --------------------------------------------------------

    numeric_columns = [

        "fdc_id",

        "selection_score",

        "energy_kcal_100g",

        "protein_g_100g",

        "carbohydrates_g_100g",

        "fat_g_100g",

        "fiber_g_100g",

        "sugars_g_100g",

        "calcium_mg_100g",

        "iron_mg_100g",

        "magnesium_mg_100g",

        "vitamin_b6_mg_100g",

        "vitamin_b12_ug_100g"
    ]

    for column in numeric_columns:

        if column in df.columns:

            df[column] = pd.to_numeric(
                df[column],
                errors="coerce"
            )

    # --------------------------------------------------------
    # Save
    # --------------------------------------------------------

    os.makedirs(
        os.path.dirname(
            OUTPUT_FILE
        ),
        exist_ok=True
    )

    df.to_csv(
        OUTPUT_FILE,
        index=False
    )

    # --------------------------------------------------------
    # Display
    # --------------------------------------------------------

    print(
        "\n" + "=" * 70
    )

    print(
        "USDA FOODDATA CENTRAL COMPLETE"
    )

    print(
        "=" * 70
    )

    print(
        "\nRows:",
        len(df)
    )

    print(
        "Columns:",
        len(df.columns)
    )

    print(
        "\nColumns:"
    )

    for column in df.columns:

        print(
            "-",
            column
        )

    print(
        "\nMissing values:"
    )

    print(
        df.isna().sum()
    )

    print(
        "\nNutrition records:"
    )

    print(
        df.to_string(
            index=False
        )
    )

    print(
        "\nSaved to:"
    )

    print(
        OUTPUT_FILE
    )


if __name__ == "__main__":

    main()
