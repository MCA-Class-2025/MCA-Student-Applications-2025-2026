import json
from pathlib import Path

import pandas as pd


# =============================================================================
# PATHS
# =============================================================================

RECIPE_PATH = Path("Fusion/data/nutrition/recipes.json")

USDA_PATH = Path(
    "Fusion/data/api_fusion/dynamic/usda_fooddata_nutrition.csv"
)


# =============================================================================
# RECIPES
# =============================================================================

def load_recipes():
    """Load the local FemCare recipe database."""

    if not RECIPE_PATH.exists():
        return []

    try:
        with open(RECIPE_PATH, "r", encoding="utf-8") as file:
            return json.load(file)
    except Exception:
        return []


def filter_recipes(
    recipes,
    nutrition_focus="All",
    diet="All",
    meal_type="All",
    cycle_phase="All",
    max_prep_time=None,
    excluded_allergens=None,
    search_text="",
):
    """Filter recipes using only explicit recipe metadata."""

    excluded_allergens = {
        str(value).casefold()
        for value in (excluded_allergens or [])
    }
    search_text = str(search_text).strip().casefold()

    filtered = []
    for recipe in recipes:
        if (
            nutrition_focus != "All"
            and nutrition_focus not in recipe.get("nutrition_focus", [])
        ):
            continue
        if diet != "All" and recipe.get("diet") != diet:
            continue
        if meal_type != "All" and recipe.get("meal_type") != meal_type:
            continue
        if (
            cycle_phase != "All"
            and cycle_phase not in recipe.get("cycle_phases", [])
        ):
            continue
        if (
            max_prep_time is not None
            and (
                float(recipe.get("prep_time", 0))
                + float(recipe.get("cook_time", 0))
            ) > float(max_prep_time)
        ):
            continue
        recipe_allergens = {
            str(value).casefold()
            for value in recipe.get("allergens", [])
        }
        if excluded_allergens.intersection(recipe_allergens):
            continue
        if search_text:
            ingredient_names = [
                item.get("name", "") if isinstance(item, dict) else str(item)
                for item in recipe.get("ingredients_detailed", recipe.get("ingredients", []))
            ]
            searchable = " ".join([
                recipe.get("name", ""),
                *ingredient_names,
                *recipe.get("nutrition_focus", []),
            ]).casefold()
            if search_text not in searchable:
                continue
        filtered.append(recipe)

    return filtered


# =============================================================================
# USDA FOODDATA CENTRAL
# =============================================================================

def load_usda_foods():
    """
    Load the locally stored USDA FoodData Central nutrition dataset.
    """

    if not USDA_PATH.exists():
        return pd.DataFrame()

    try:
        data = pd.read_csv(USDA_PATH)
        data = _normalize_legacy_energy(data)
        return assess_usda_records(data)
    except Exception:
        return pd.DataFrame()


def _normalize_legacy_energy(df):
    """Correct legacy rows where a kJ value was stored as kcal.

    Older exports did not save the USDA energy unit. A correction is applied
    only when converting the value from kJ to kcal makes it substantially
    closer to the independent energy estimate from protein, carbohydrate and
    fat. The raw CSV remains unchanged and the correction is disclosed in a
    quality-note column.
    """

    required = {
        "energy_kcal_100g",
        "protein_g_100g",
        "carbohydrates_g_100g",
        "fat_g_100g",
    }

    result = df.copy()
    result["energy_quality_note"] = ""

    if not required.issubset(result.columns):
        return result

    energy = pd.to_numeric(
        result["energy_kcal_100g"], errors="coerce"
    )
    macro_energy = (
        pd.to_numeric(result["protein_g_100g"], errors="coerce") * 4
        + pd.to_numeric(
            result["carbohydrates_g_100g"], errors="coerce"
        ) * 4
        + pd.to_numeric(result["fat_g_100g"], errors="coerce") * 9
    )
    converted = energy / 4.184

    raw_difference = (energy - macro_energy).abs()
    converted_difference = (converted - macro_energy).abs()
    looks_like_kj = (
        energy.notna()
        & macro_energy.gt(0)
        & energy.gt(macro_energy * 2.5)
        & converted_difference.lt(raw_difference * 0.35)
    )

    result.loc[looks_like_kj, "energy_kcal_100g"] = (
        converted.loc[looks_like_kj].round(2)
    )
    result.loc[looks_like_kj, "energy_quality_note"] = (
        "Legacy USDA kJ value converted to kcal. Refresh the USDA export "
        "to store the original unit explicitly."
    )

    return result


def assess_usda_records(df):
    """Add record-level validation without replacing missing nutrients with zero."""

    result = df.copy()
    required = [
        "energy_kcal_100g", "protein_g_100g",
        "carbohydrates_g_100g", "fat_g_100g",
    ]

    statuses = []
    notes = []
    for _, row in result.iterrows():
        issues = []
        for column in required:
            if column not in result.columns or pd.isna(row.get(column)):
                issues.append(f"Missing {column}")

        if not issues:
            energy = float(row["energy_kcal_100g"])
            macro_estimate = (
                float(row["protein_g_100g"]) * 4
                + float(row["carbohydrates_g_100g"]) * 4
                + float(row["fat_g_100g"]) * 9
            )
            if macro_estimate > 0:
                difference = abs(energy - macro_estimate) / macro_estimate
                if difference > 0.45:
                    issues.append(
                        "Energy differs materially from the macro-based estimate"
                    )

        statuses.append("Review" if issues else "Validated")
        notes.append("; ".join(issues))

    result["record_status"] = statuses
    result["validation_notes"] = notes
    return result


def format_recipe_ingredient(ingredient):
    """Return an ingredient quantity suitable for recipe cards."""

    if not isinstance(ingredient, dict):
        return str(ingredient)
    return str(ingredient.get("display") or ingredient.get("name") or "Ingredient")


def calculate_recipe_nutrition(recipe, foods):
    """Calculate per-serving nutrition only when ingredient coverage is sufficient."""

    ingredients = recipe.get("ingredients_detailed", [])
    servings = max(float(recipe.get("servings", 1)), 1)
    nutrient_columns = [
        "energy_kcal_100g", "protein_g_100g", "carbohydrates_g_100g",
        "fat_g_100g", "fiber_g_100g", "iron_mg_100g",
        "calcium_mg_100g", "magnesium_mg_100g",
        "vitamin_b6_mg_100g", "vitamin_b12_ug_100g",
    ]

    if not ingredients or foods.empty or "search_food" not in foods.columns:
        return {"complete": False, "coverage_percent": 0.0, "values": {}}

    lookup = (
        foods.drop_duplicates("search_food")
        .set_index("search_food", drop=False)
    )
    totals = {column: 0.0 for column in nutrient_columns}
    unavailable = set()
    total_mass = 0.0
    matched_mass = 0.0

    for ingredient in ingredients:
        grams = float(ingredient.get("grams", 0) or 0)
        total_mass += grams
        key = ingredient.get("usda_key")
        if not key or key not in lookup.index or grams <= 0:
            continue

        record = lookup.loc[key]
        matched_mass += grams
        for column in nutrient_columns:
            if column not in foods.columns or pd.isna(record.get(column)):
                unavailable.add(column)
                continue
            totals[column] += float(record[column]) * grams / 100

    coverage = 100 * matched_mass / total_mass if total_mass else 0.0
    complete = coverage >= 99.9
    values = {}
    if complete:
        for column, total in totals.items():
            values[column] = (
                None if column in unavailable else total / servings
            )

    return {
        "complete": complete,
        "coverage_percent": round(coverage, 1),
        "values": values,
    }


def get_usda_food_names(df):
    """
    Return unique food names from the USDA dataset.
    """

    if df.empty or "food_name" not in df.columns:
        return []

    return sorted(
        df["food_name"]
        .dropna()
        .astype(str)
        .unique()
        .tolist()
    )


def get_food_record(df, food_name):
    """
    Return the selected food record.
    """

    if df.empty or "food_name" not in df.columns:
        return None

    matches = df[
        df["food_name"].astype(str) == str(food_name)
    ]

    if matches.empty:
        return None

    return matches.iloc[0]


def format_nutrient(value, unit):
    """
    Format nutrient values safely.
    Missing values are displayed as 'Not available'
    instead of being converted to zero.
    """

    if pd.isna(value):
        return "Not available"

    try:
        return f"{float(value):.2f} {unit}"
    except (ValueError, TypeError):
        return "Not available"
