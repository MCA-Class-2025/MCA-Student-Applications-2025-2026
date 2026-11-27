# fusion/usda_client.py – USDA FoodData Central client with caching + manual mapping
import os, re, json, time, requests
from dotenv import load_dotenv

load_dotenv()
USDA_API_KEY = os.getenv("USDA_API_KEY")

CACHE_DIR = "data/fusion/usda_cache"
CACHE_FILE = os.path.join(CACHE_DIR, "usda_cache.json")

# Manual mapping for Indian foods to USDA common names
MANUAL_USDA_MAP = {
    "bajra": "millet",
    "jowar": "sorghum",
    "ragi": "finger millet",
    "maize": "corn",
    "tur dal": "pigeon peas",
    "moong dal": "mung beans",
    "urad dal": "black gram",
    "chana dal": "chickpeas",
    "masoor dal": "red lentils",
    "paneer": "cheese, paneer",
    "ghee": "ghee",
    "coconut": "coconut, meat",
    "groundnut": "peanuts",
    "sugarcane": "sugarcane",
    "jaggery": "jaggery",
    "mustard oil": "mustard oil",
    "sunflower oil": "sunflower oil",
    "soya": "soybeans",
    "ragi": "finger millet",
    "bajra": "pearl millet",
    "jowar": "sorghum",
    "maize": "corn",
    "wheat": "wheat",
    "rice": "rice",
    "pulses": "pulses",
}

NUTRIENT_MAP = {
    ("Energy", "KCAL"): "usda_calories",
    ("Protein", "G"): "usda_protein",
    ("Total lipid (fat)", "G"): "usda_fat",
    ("Carbohydrate, by difference", "G"): "usda_carbohydrates",
    ("Fiber, total dietary", "G"): "usda_fiber",
    ("Sodium, Na", "MG"): "usda_sodium",
    ("Calcium, Ca", "MG"): "usda_calcium",
    ("Iron, Fe", "MG"): "usda_iron",
    ("Sugars, total including NLEA", "G"): "usda_sugar",
}

def normalize_food_name(name):
    return re.sub(r"\s+", " ", str(name).strip().lower())

def _load_cache():
    os.makedirs(CACHE_DIR, exist_ok=True)
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r") as f:
                return json.load(f)
        except:
            return {}
    return {}

def _save_cache(cache):
    os.makedirs(CACHE_DIR, exist_ok=True)
    with open(CACHE_FILE, "w") as f:
        json.dump(cache, f)

def _parse_nutrients(food_detail_json):
    """
    Extract nutrient fields from the USDA response.
    - Maps known nutrients to canonical usda_* names via NUTRIENT_MAP
      (e.g. ("Energy","KCAL") -> "usda_calories") so the rest of the
      pipeline (fusion.py) can find them.
    - ALSO keeps every raw nutrient under its original "Name (UNIT)" key,
      so Step 0's "raw USDA data" preview shows the FULL nutrient panel,
      not just the ~9 mapped ones.
    """
    result = {}
    for n in food_detail_json.get("foodNutrients", []):
        name = n.get("nutrientName", "")
        unit = n.get("unitName", "")
        amount = n.get("amount")
        if amount is None:
            continue
        mapped_key = NUTRIENT_MAP.get((name, unit))
        if mapped_key:
            result[mapped_key] = amount
        raw_key = f"{name} ({unit})" if unit else name
        result[raw_key] = amount
    result["usda_food_name"] = food_detail_json.get("description", "")
    result["usda_fdc_id"] = food_detail_json.get("fdcId")
    return result


def fetch_usda_food(query, api_key=None, session=None, timeout=10):
    api_key = api_key or USDA_API_KEY
    if not api_key:
        return {}, "error"
    sess = session or requests
    try:
        search_resp = sess.get(
            "https://api.nal.usda.gov/fdc/v1/foods/search",
            params={
                "query": query,
                "api_key": api_key,
                "pageSize": 5,
                # Foundation / SR Legacy entries have full nutrient panels.
                # Branded Food entries (the default top match) often have
                # only a handful of nutrients on the label -- that was
                # silently starving Step 0's "raw data" preview.
                "dataType": "Foundation,SR Legacy",
            },
            timeout=timeout,
        )
        if search_resp.status_code != 200:
            return {}, "error"
        foods = search_resp.json().get("foods", [])
        if not foods:
            # Fall back to ANY data type if Foundation/SR Legacy has no match
            search_resp = sess.get(
                "https://api.nal.usda.gov/fdc/v1/foods/search",
                params={"query": query, "api_key": api_key, "pageSize": 1},
                timeout=timeout,
            )
            if search_resp.status_code != 200:
                return {}, "error"
            foods = search_resp.json().get("foods", [])
            if not foods:
                return {}, "no_match"
        fdc_id = foods[0].get("fdcId")
        detail_resp = sess.get(
            f"https://api.nal.usda.gov/fdc/v1/food/{fdc_id}",
            params={"api_key": api_key, "format": "full"},
            timeout=timeout,
        )
        if detail_resp.status_code != 200:
            return {}, "error"
        data = _parse_nutrients(detail_resp.json())
        if not any(k.startswith("usda_") and k not in ("usda_food_name", "usda_fdc_id") for k in data):
            return data, "taxonomy_only"
        return data, "matched"
    except requests.RequestException:
        return {}, "error"

def fetch_usda_food(query, api_key=None, session=None, timeout=10):
    api_key = api_key or USDA_API_KEY
    if not api_key:
        return {}, "error"
    sess = session or requests
    try:
        search_resp = sess.get(
            "https://api.nal.usda.gov/fdc/v1/foods/search",
            params={"query": query, "api_key": api_key, "pageSize": 1},
            timeout=timeout,
        )
        if search_resp.status_code != 200:
            return {}, "error"
        foods = search_resp.json().get("foods", [])
        if not foods:
            return {}, "no_match"
        fdc_id = foods[0].get("fdcId")
        detail_resp = sess.get(
            f"https://api.nal.usda.gov/fdc/v1/food/{fdc_id}",
            params={"api_key": api_key},
            timeout=timeout,
        )
        if detail_resp.status_code != 200:
            return {}, "error"
        data = _parse_nutrients(detail_resp.json())
        if not any(k.startswith("usda_") and k not in ("usda_food_name", "usda_fdc_id") for k in data):
            return data, "taxonomy_only"
        return data, "matched"
    except requests.RequestException:
        return {}, "error"

def get_usda_food_cached(query, api_key=None, session=None, sleep_between_calls=1.0):
    cache = _load_cache()
    key = normalize_food_name(query)
    if key in cache:
        return cache[key]["data"], cache[key]["status"]

    # Try mapped name first
    mapped_query = MANUAL_USDA_MAP.get(key, query)
    data, status = fetch_usda_food(mapped_query, api_key=api_key, session=session)

    # If no match with mapped name, try the original name
    if status in ("no_match", "taxonomy_only") and mapped_query != query:
        data2, status2 = fetch_usda_food(query, api_key=api_key, session=session)
        if status2 == "matched":
            data, status = data2, status2

    if status == "error":
        if sleep_between_calls:
            time.sleep(sleep_between_calls)
        return data, status

    cache[key] = {"data": data, "status": status}
    _save_cache(cache)
    if sleep_between_calls:
        time.sleep(sleep_between_calls)
    return data, status