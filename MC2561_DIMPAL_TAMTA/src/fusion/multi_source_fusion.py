# fusion/multi_source_fusion.py
"""
Multi-source data fusion for NutriCare AI.

Produces TWO separate datasets (they have different shapes and shouldn't be merged
into one table):

1. nutricare_unified_food_dataset.csv
   -> one row per food item, columns from Local DB + USDA + Spoonacular,
      plus engineered difference/density/ratio features.

2. nutricare_facility_dataset.csv
   -> one row per real-world place (hospital, clinic, food bank) pulled from
      OpenStreetMap via Overpass, for a given search location.

Drop this file in fusion/multi_source_fusion.py. It re-uses your existing
lookup functions rather than reimplementing them:
    - nutrition.nutrition_db.get_nutrition
    - nutrition.nutrition_fusion_lookup.get_nutrition_with_fallback
    - utils.api_helpers.get_spoonacular_nutrition

Adjust the FIELD MAP dictionaries below if your USDA / Spoonacular return
dicts use different key names than assumed here.
"""

import os
import time
import requests
import pandas as pd

from nutrition.nutrition_db import get_nutrition
from nutrition.nutrition_fusion_lookup import get_nutrition_with_fallback
from utils.api_helpers import get_spoonacular_nutrition
# FIX: use the project's shared logger (utils.utils.get_logger) instead of a
# bare logging.getLogger(...) with no handler attached -- otherwise progress
# messages never show up in the terminal like your other modules do.
from utils.utils import get_logger

logger = get_logger("multi_source_fusion")

# --------------------------------------------------------------------------
# 1. NUTRITION FUSION: Local + USDA + Spoonacular
# --------------------------------------------------------------------------

# Map of "canonical name" -> possible local-DB column names.
# Adjust these to match your indian_food_database.csv columns exactly.
LOCAL_FIELD_MAP = {
    "calories": "energy_kcal",
    "protein": "protein_g",
    "fat": "fat_g",
    "carbohydrates": "carb_g",
    "fiber": "fibre_g",
}

# Map of "canonical name" -> key returned inside get_nutrition_with_fallback's
# raw USDA dict (source == "usda"). Adjust to your actual USDA parser output.
USDA_FIELD_MAP = {
    "calories": "calories",
    "protein": "protein",
    "fat": "fat",
    "carbohydrates": "carbohydrates",
    "fiber": "fiber",
}

# Map of "canonical name" -> key returned by get_spoonacular_nutrition.
# Adjust to your actual Spoonacular parser output.
SPOONACULAR_FIELD_MAP = {
    "calories": "calories",
    "protein": "protein",
    "fat": "fat",
    "carbohydrates": "carbohydrates",
    "fiber": "fiber",
}

CANONICAL_NUTRIENTS = ["calories", "protein", "fat", "carbohydrates", "fiber"]


def _safe_float(val):
    try:
        return float(val)
    except (TypeError, ValueError):
        return None


def _extract(d, field_map):
    """Pull canonical nutrient values out of a raw dict using a field map."""
    out = {}
    if not d:
        return out
    for canon, key in field_map.items():
        if key in d:
            out[canon] = _safe_float(d[key])
    return out


def fuse_one_food(food_name):
    """
    Look up a single food across all three sources and return one merged row
    (dict) with local_*, usda_*, spoon_* columns plus engineered features.
    """
    row = {"food_name": food_name}

    # --- Local ---
    local_raw = get_nutrition(food_name)
    local_vals = _extract(local_raw, LOCAL_FIELD_MAP)
    for k, v in local_vals.items():
        row[f"local_{k}"] = v

    # --- USDA (via your existing fallback cascade) ---
    # get_nutrition_with_fallback already tries local -> USDA -> Spoonacular
    # and returns (clean_data, source, raw_data). We call it once and use
    # the raw dict only when source == "usda" so we don't double count local.
    usda_vals = {}
    try:
        _, source, raw_data = get_nutrition_with_fallback(food_name)
        if source == "usda":
            usda_vals = _extract(raw_data, USDA_FIELD_MAP)
    except Exception as e:
        logger.warning("USDA lookup failed for %s: %s", food_name, e)
    for k, v in usda_vals.items():
        row[f"usda_{k}"] = v

    # --- Spoonacular (direct call, independent of the fallback cascade) ---
    spoon_vals = {}
    try:
        spoon_raw = get_spoonacular_nutrition(food_name)
        spoon_vals = _extract(spoon_raw, SPOONACULAR_FIELD_MAP)
    except Exception as e:
        logger.warning("Spoonacular lookup failed for %s: %s", food_name, e)
    for k, v in spoon_vals.items():
        row[f"spoon_{k}"] = v

    # --- Engineered features ---
    for nutrient in CANONICAL_NUTRIENTS:
        l = row.get(f"local_{nutrient}")
        u = row.get(f"usda_{nutrient}")
        s = row.get(f"spoon_{nutrient}")

        if l is not None and u is not None:
            row[f"{nutrient}_local_usda_difference"] = round(l - u, 3)
        if l is not None and s is not None:
            row[f"{nutrient}_local_spoon_difference"] = round(l - s, 3)

    # Protein/fiber density relative to calories, when available
    cal = row.get("local_calories") or row.get("usda_calories") or row.get("spoon_calories")
    protein = row.get("local_protein") or row.get("usda_protein") or row.get("spoon_protein")
    fiber = row.get("local_fiber") or row.get("usda_fiber") or row.get("spoon_fiber")
    fat = row.get("local_fat") or row.get("usda_fat") or row.get("spoon_fat")

    if cal and cal > 0:
        if protein is not None:
            row["protein_density"] = round(protein / cal * 100, 4)
        if fiber is not None:
            row["fiber_density"] = round(fiber / cal * 100, 4)
    if protein and protein > 0 and fat is not None:
        row["fat_protein_ratio"] = round(fat / protein, 4)

    return row


def build_full_unified_dataset(local_csv, output_csv, limit=500, delay=0.3):
    """
    Iterate over the local food database and fuse each item across
    Local + USDA + Spoonacular. Writes a CSV and returns the DataFrame.

    `delay` adds a small pause between API calls to be polite to
    USDA / Spoonacular rate limits.
    """
    df_local = pd.read_csv(local_csv, encoding="latin-1")
    food_names = df_local["food_name"].dropna().unique().tolist()[:limit]

    rows = []
    for i, name in enumerate(food_names):
        rows.append(fuse_one_food(name))
        if delay:
            time.sleep(delay)
        if (i + 1) % 25 == 0:
            logger.info("Fused %d/%d foods", i + 1, len(food_names))

    df_out = pd.DataFrame(rows)
    os.makedirs(os.path.dirname(output_csv), exist_ok=True)
    df_out.to_csv(output_csv, index=False)
    logger.info("Saved unified nutrition dataset: %s (%d rows)", output_csv, len(df_out))
    return df_out


# --------------------------------------------------------------------------
# 2. FACILITY FUSION: OpenStreetMap (Overpass + Nominatim)
# --------------------------------------------------------------------------

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
OVERPASS_URL = "https://overpass-api.de/api/interpreter"
OSM_HEADERS = {
    "User-Agent": "NutriCare AI (contact: tamtadimpal654@gmail.com)"
}


def geocode_location(location, timeout=10):
    params = {"q": location, "format": "json", "limit": 1}
    resp = requests.get(NOMINATIM_URL, params=params, headers=OSM_HEADERS, timeout=timeout)
    resp.raise_for_status()
    data = resp.json()
    if not data:
        raise ValueError(f"Could not geocode location: {location}")
    return float(data[0]["lat"]), float(data[0]["lon"])


def _overpass_query(lat, lon, search_type, radius_m=5000):
    if search_type == "Cancer Centers":
        return f"""
        [out:json];
        (
          node["healthcare"="hospital"](around:{radius_m},{lat},{lon});
          node["healthcare"="clinic"](around:{radius_m},{lat},{lon});
          node["amenity"="hospital"](around:{radius_m},{lat},{lon});
          node["amenity"="clinic"](around:{radius_m},{lat},{lon});
        );
        out body;
        """
    else:
        return f"""
        [out:json];
        (
          node["amenity"="food_bank"](around:{radius_m},{lat},{lon});
          node["amenity"="community_kitchen"](around:{radius_m},{lat},{lon});
          node["social_facility"="food_bank"](around:{radius_m},{lat},{lon});
        );
        out body;
        """


def fetch_facilities(location, search_type="Cancer Centers", radius_m=5000, timeout=30):
    """
    Geocode `location`, query Overpass for nearby facilities, and return a
    list of dicts: name, lat, lon, street, city, type, source_query.
    Uses POST (not GET) to avoid Overpass rejecting long/encoded GET queries.
    """
    lat, lon = geocode_location(location)
    query = _overpass_query(lat, lon, search_type, radius_m)

    resp = requests.post(OVERPASS_URL, data={"data": query}, headers=OSM_HEADERS, timeout=timeout)
    resp.raise_for_status()
    elements = resp.json().get("elements", [])

    rows = []
    for el in elements:
        el_lat, el_lon = el.get("lat"), el.get("lon")
        if el_lat is None or el_lon is None:
            continue
        tags = el.get("tags", {})
        rows.append({
            "name": tags.get("name", "Unnamed"),
            "lat": el_lat,
            "lon": el_lon,
            "street": tags.get("addr:street", ""),
            "city": tags.get("addr:city", ""),
            "type": search_type,
            "healthcare_tag": tags.get("healthcare", "") or tags.get("amenity", ""),
            "search_location": location,
        })
    return rows


def build_facility_dataset(locations, search_types=("Cancer Centers", "Food/Nutrition Assistance"),
                            output_csv="data/fusion/nutricare_facility_dataset.csv", delay=1.0):
    """
    Build a facility dataset across one or more locations and search types.
    `locations` can be a single string or a list of strings.
    Nominatim/Overpass rate-limit aggressively, so `delay` (seconds) is
    applied between requests -- keep it >= 1s for Nominatim's usage policy.
    """
    if isinstance(locations, str):
        locations = [locations]

    all_rows = []
    for loc in locations:
        for stype in search_types:
            try:
                rows = fetch_facilities(loc, stype)
                all_rows.extend(rows)
                logger.info("Fetched %d %s facilities near %s", len(rows), stype, loc)
            except Exception as e:
                logger.warning("Facility fetch failed for %s / %s: %s", loc, stype, e)
            time.sleep(delay)

    df_out = pd.DataFrame(all_rows).drop_duplicates(subset=["name", "lat", "lon"])
    os.makedirs(os.path.dirname(output_csv), exist_ok=True)
    df_out.to_csv(output_csv, index=False)
    logger.info("Saved facility dataset: %s (%d rows)", output_csv, len(df_out))
    return df_out