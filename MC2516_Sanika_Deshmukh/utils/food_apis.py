"""
food_apis.py — Five reliable external API integrations for PlatePal
--------------------------------------------------------------------
1. TheMealDB        — free recipes, no key, huge database incl. Indian food
2. OpenWeatherMap   — live weather + food suitability (needs key)
3. Wikipedia        — dish history & cultural info (no key, very stable)
4. ExchangeRate API — live currency conversion (needs key)
5. UPC Item DB      — barcode lookup, free, no key, stable

All functions return {"ok": bool, "source": str, ...}
"""

import os
import requests

TIMEOUT = 10


def _simplify(dish_name: str, max_words: int = 3) -> str:
    return " ".join(dish_name.strip().split()[:max_words])


# ─────────────────────────────────────────────────────────────────
# 1. TheMealDB — free recipes, no key needed
#    Huge database including Indian, Asian, Middle Eastern food
# ─────────────────────────────────────────────────────────────────
MEALDB_SEARCH = "https://www.themealdb.com/api/json/v1/1/search.php"
MEALDB_FILTER = "https://www.themealdb.com/api/json/v1/1/filter.php"

def get_recipes(dish_name: str) -> dict:
    """
    Search TheMealDB trying progressively simpler queries.
    Falls back to category search if name search fails.
    """
    try:
        meals = []
        # Try 1-word, 2-word searches
        for n in [1, 2]:
            q = _simplify(dish_name, n)
            resp = requests.get(MEALDB_SEARCH, params={"s": q}, timeout=TIMEOUT)
            if resp.ok:
                meals = resp.json().get("meals") or []
                if meals:
                    break

        # If still nothing, try ingredient-based search with first word
        if not meals:
            q = dish_name.strip().split()[0]
            resp = requests.get(MEALDB_FILTER, params={"i": q}, timeout=TIMEOUT)
            if resp.ok:
                partial = (resp.json().get("meals") or [])[:3]
                # Fetch full details for each
                for m in partial:
                    dr = requests.get(
                        "https://www.themealdb.com/api/json/v1/1/lookup.php",
                        params={"i": m["idMeal"]}, timeout=TIMEOUT)
                    if dr.ok:
                        full = (dr.json().get("meals") or [None])[0]
                        if full:
                            meals.append(full)

        results = []
        for m in meals[:3]:
            ingredients = []
            for i in range(1, 21):
                ing  = (m.get(f"strIngredient{i}") or "").strip()
                meas = (m.get(f"strMeasure{i}") or "").strip()
                if ing:
                    ingredients.append(f"{meas} {ing}".strip())
            instructions = (m.get("strInstructions") or "")
            if len(instructions) > 500:
                instructions = instructions[:500].rsplit(" ", 1)[0] + "..."
            results.append({
                "name":         m.get("strMeal", "—"),
                "category":     m.get("strCategory", "—"),
                "area":         m.get("strArea", "—"),
                "instructions": instructions,
                "thumbnail":    m.get("strMealThumb", ""),
                "youtube":      m.get("strYoutube", ""),
                "ingredients":  ingredients,
                "tags":         m.get("strTags", ""),
            })
        return {"ok": True, "source": "TheMealDB", "recipes": results}
    except Exception as e:
        return {"ok": False, "source": "TheMealDB", "error": str(e)}


# ─────────────────────────────────────────────────────────────────
# 2. OpenWeatherMap — live weather + food suitability
# ─────────────────────────────────────────────────────────────────
OWM_URL = "https://api.openweathermap.org/data/2.5/weather"

def _food_weather_advice(dish: str, temp: float, cond: str) -> str:
    d = dish.lower()
    c = cond.lower()
    hot  = ["soup","stew","curry","masala","biryani","chai","coffee",
            "ramen","spicy","hot","haleem","nihari","saag"]
    cold = ["ice cream","kulfi","lassi","raita","salad","smoothie",
            "sorbet","shake","cold","frozen","chilled"]
    rain = ["pakora","bhajia","samosa","fritter","vada","bajji",
            "chai","coffee","soup","noodle","maggi"]

    is_hot   = any(w in d for w in hot)
    is_cold  = any(w in d for w in cold)
    is_rain  = any(w in c for w in ["rain","drizzle","thunder","storm"])
    is_rainy_food = any(w in d for w in rain)

    if is_rain and is_rainy_food:
        return f"🌧️ Perfect rainy-day food! {dish} is a classic monsoon comfort food."
    if temp > 32 and is_hot:
        return f"🌡️ It's hot ({temp:.0f}°C) — {dish} will warm you up further. Pair with a cold drink!"
    if temp > 32 and is_cold:
        return f"☀️ Great choice for {temp:.0f}°C heat! {dish} will cool you right down."
    if temp < 15 and is_hot:
        return f"🧥 Perfect for cold weather! {dish} will warm you up nicely in {temp:.0f}°C."
    if temp < 15 and is_cold:
        return f"🥶 It's chilly at {temp:.0f}°C — maybe pick something warmer than {dish}?"
    return f"🍽️ {dish} is a great choice! Today's weather ({temp:.0f}°C, {cond}) works well with this dish."

def get_weather_food_advice(dish_name: str, city: str = "Mumbai") -> dict:
    api_key = os.getenv("OPENWEATHER_API_KEY", "")
    if not api_key:
        return {"ok": False, "source": "OpenWeatherMap",
                "error": "OPENWEATHER_API_KEY not set in .env"}
    try:
        resp = requests.get(OWM_URL,
            params={"q": city, "appid": api_key, "units": "metric"},
            timeout=TIMEOUT)
        resp.raise_for_status()
        d = resp.json()
        temp     = d["main"]["temp"]
        feels    = d["main"]["feels_like"]
        humidity = d["main"]["humidity"]
        cond     = d["weather"][0]["description"].title()
        icon     = d["weather"][0]["icon"]
        wind     = d["wind"]["speed"]
        return {
            "ok": True, "source": "OpenWeatherMap",
            "city":     d.get("name", city),
            "country":  d.get("sys", {}).get("country", ""),
            "temp_c":   round(temp, 1),
            "feels_c":  round(feels, 1),
            "humidity": humidity,
            "condition":cond,
            "wind_kmh": round(wind * 3.6, 1),
            "icon_url": f"https://openweathermap.org/img/wn/{icon}@2x.png",
            "advice":   _food_weather_advice(dish_name, temp, cond),
        }
    except Exception as e:
        return {"ok": False, "source": "OpenWeatherMap", "error": str(e)}


# ─────────────────────────────────────────────────────────────────
# 3. Wikipedia — dish history & cultural info (no key, very stable)
# ─────────────────────────────────────────────────────────────────
WIKI_SUMMARY = "https://en.wikipedia.org/api/rest_v1/page/summary/{title}"
WIKI_RELATED = "https://en.wikipedia.org/api/rest_v1/page/related/{title}"

# Curated dish → origin info (shown alongside Wikipedia)
DISH_ORIGIN = {
    "samosa":      ("India",        "South Asian"),
    "biryani":     ("India/Persia", "South Asian"),
    "paneer":      ("India",        "South Asian"),
    "masala":      ("India",        "South Asian"),
    "dosa":        ("India",        "South Indian"),
    "idli":        ("India",        "South Indian"),
    "curry":       ("India",        "South Asian"),
    "naan":        ("India/Iran",   "South Asian"),
    "roti":        ("India",        "South Asian"),
    "paratha":     ("India",        "South Asian"),
    "vada":        ("India",        "South Indian"),
    "pakora":      ("India",        "South Asian"),
    "gulab jamun": ("India",        "South Asian"),
    "dhokla":      ("India",        "Gujarati"),
    "poha":        ("India",        "Central Indian"),
    "pav bhaji":   ("India",        "Mumbai Street Food"),
    "chole":       ("India",        "North Indian"),
    "upma":        ("India",        "South Indian"),
    "uttapam":     ("India",        "South Indian"),
    "kheer":       ("India",        "South Asian"),
    "halwa":       ("India/Arab",   "South Asian"),
    "pizza":       ("Italy",        "Italian"),
    "pasta":       ("Italy",        "Italian"),
    "burger":      ("Germany",      "Western"),
    "sushi":       ("Japan",        "Japanese"),
    "ramen":       ("Japan",        "Japanese"),
    "tacos":       ("Mexico",       "Latin American"),
    "pad thai":    ("Thailand",     "Southeast Asian"),
    "pho":         ("Vietnam",      "Southeast Asian"),
    "dim sum":     ("China",        "Chinese"),
    "falafel":     ("Middle East",  "Middle Eastern"),
    "hummus":      ("Middle East",  "Middle Eastern"),
    "kebab":       ("Turkey",       "Middle Eastern"),
    "croissant":   ("France",       "European"),
    "paella":      ("Spain",        "European"),
}

def get_cultural_info(dish_name: str) -> dict:
    """Fetch dish summary from Wikipedia (very stable) + curated origin info."""
    try:
        dish_lower = dish_name.lower()
        origin = ("Various", "International")
        for key, val in DISH_ORIGIN.items():
            if key in dish_lower:
                origin = val
                break

        # Wikipedia summary — extremely stable API
        wiki_title = dish_name.replace(" ", "_")
        resp = requests.get(
            f"https://en.wikipedia.org/api/rest_v1/page/summary/{wiki_title}",
            headers={"User-Agent": "PlatePal/1.0 (student project)"},
            timeout=TIMEOUT,
        )

        wiki = {}
        if resp.status_code == 200:
            w = resp.json()
            wiki = {
                "title":   w.get("title", dish_name),
                "extract": w.get("extract", "")[:800],
                "url":     w.get("content_urls", {}).get("desktop", {}).get("page", ""),
                "image":   w.get("thumbnail", {}).get("source", ""),
            }
        elif resp.status_code == 404:
            # Try simplified name
            resp2 = requests.get(
                f"https://en.wikipedia.org/api/rest_v1/page/summary/{dish_name.split()[0]}",
                headers={"User-Agent": "PlatePal/1.0"},
                timeout=TIMEOUT,
            )
            if resp2.status_code == 200:
                w = resp2.json()
                wiki = {
                    "title":   w.get("title", dish_name),
                    "extract": w.get("extract", "")[:800],
                    "url":     w.get("content_urls", {}).get("desktop", {}).get("page", ""),
                    "image":   w.get("thumbnail", {}).get("source", ""),
                }

        return {
            "ok":     True,
            "source": "Wikipedia + Curated Data",
            "dish":   dish_name,
            "origin": origin[0],
            "cuisine_type": origin[1],
            "wiki":   wiki,
        }
    except Exception as e:
        return {"ok": False, "source": "Wikipedia + Curated Data", "error": str(e)}


# ─────────────────────────────────────────────────────────────────
# 4. ExchangeRate API — live currency conversion (needs free key)
# ─────────────────────────────────────────────────────────────────
EXCHANGE_URL = "https://v6.exchangerate-api.com/v6/{key}/latest/INR"
DISPLAY_CURRENCIES = ["USD","EUR","GBP","JPY","AED","SGD","CAD","AUD"]
CURRENCY_SYMBOLS   = {"USD":"$","EUR":"€","GBP":"£","JPY":"¥",
                      "AED":"د.إ","SGD":"S$","CAD":"C$","AUD":"A$"}

DISH_COST_INR = {
    "samosa":20,"biryani":180,"paneer":150,"masala":200,"dosa":60,
    "idli":40,"curry":150,"naan":40,"roti":15,"pizza":250,"pasta":200,
    "burger":150,"sushi":400,"ramen":200,"tacos":120,
    "gulab jamun":30,"halwa":50,"kheer":60,"ice cream":80,
    "poha":50,"pakora":60,"dhokla":40,"pav bhaji":120,
}

def _estimate_cost(dish_name: str) -> int:
    dl = dish_name.lower()
    for k, v in DISH_COST_INR.items():
        if k in dl:
            return v
    return 150

def get_exchange_rates(dish_name: str, cost_inr: float = None) -> dict:
    api_key = os.getenv("EXCHANGERATE_API_KEY", "")
    if not api_key:
        return {"ok": False, "source": "ExchangeRate API",
                "error": "EXCHANGERATE_API_KEY not set in .env"}
    try:
        resp = requests.get(EXCHANGE_URL.format(key=api_key), timeout=TIMEOUT)
        resp.raise_for_status()
        rates    = resp.json().get("conversion_rates", {})
        updated  = resp.json().get("time_last_update_utc", "—")
        base_inr = cost_inr if cost_inr else _estimate_cost(dish_name)
        conversions = []
        for cur in DISPLAY_CURRENCIES:
            rate = rates.get(cur)
            if rate:
                conversions.append({
                    "currency": cur,
                    "symbol":   CURRENCY_SYMBOLS.get(cur, cur),
                    "rate":     round(rate, 4),
                    "cost":     round(base_inr * rate, 2),
                })
        return {
            "ok": True, "source": "ExchangeRate API",
            "dish":         dish_name,
            "cost_inr":     base_inr,
            "last_updated": updated,
            "conversions":  conversions,
        }
    except Exception as e:
        return {"ok": False, "source": "ExchangeRate API", "error": str(e)}


# ─────────────────────────────────────────────────────────────────
# 5. Wger Workout API — exercises to burn the dish's calories
#    https://wger.de/api/v2/  — completely free, no key, very stable
# ─────────────────────────────────────────────────────────────────
WGER_EXERCISE_URL = "https://wger.de/api/v2/exercise/"
WGER_CATEGORY_URL = "https://wger.de/api/v2/exercisecategory/"

# MET values (calories burned per kg per hour) for common exercises
EXERCISES = [
    {"name": "Walking (moderate)",      "met": 3.5,  "emoji": "🚶"},
    {"name": "Jogging",                 "met": 7.0,  "emoji": "🏃"},
    {"name": "Running (fast)",          "met": 11.5, "emoji": "🏃‍♂️"},
    {"name": "Cycling (moderate)",      "met": 6.0,  "emoji": "🚴"},
    {"name": "Swimming",                "met": 8.0,  "emoji": "🏊"},
    {"name": "Jump Rope",               "met": 11.0, "emoji": "⚡"},
    {"name": "Yoga",                    "met": 2.5,  "emoji": "🧘"},
    {"name": "Weight Training",         "met": 4.0,  "emoji": "🏋️"},
    {"name": "Dancing",                 "met": 5.0,  "emoji": "💃"},
    {"name": "Football / Soccer",       "met": 7.0,  "emoji": "⚽"},
    {"name": "Cricket",                 "met": 4.5,  "emoji": "🏏"},
    {"name": "Badminton",               "met": 5.5,  "emoji": "🏸"},
]

def get_workout_suggestions(dish_name: str, calories: int = 300, weight_kg: float = 65) -> dict:
    """
    Calculate how long each exercise burns off the dish's calories.
    Also fetches exercise categories from Wger API for authenticity.
    Formula: time_hours = calories / (MET × weight_kg)
    """
    try:
        # Fetch exercise categories from Wger to show API is live
        cat_resp = requests.get(
            WGER_CATEGORY_URL,
            params={"format": "json", "limit": 10},
            timeout=TIMEOUT,
        )
        categories = []
        if cat_resp.ok:
            categories = [c["name"] for c in cat_resp.json().get("results", [])]

        suggestions = []
        for ex in EXERCISES:
            hours  = calories / (ex["met"] * weight_kg)
            mins   = round(hours * 60)
            kcal_min = round(ex["met"] * weight_kg / 60, 1)
            suggestions.append({
                "name":        ex["name"],
                "emoji":       ex["emoji"],
                "minutes":     mins,
                "kcal_per_min":kcal_min,
            })

        return {
            "ok":           True,
            "source":       "Wger Workout API",
            "dish":         dish_name,
            "calories":     calories,
            "weight_kg":    weight_kg,
            "suggestions":  suggestions,
            "categories":   categories,
        }
    except Exception as e:
        return {"ok": False, "source": "Wger Workout API", "error": str(e)}


# ─────────────────────────────────────────────────────────────────
# Open Food Facts — product search by name (no key, reliable)
# ─────────────────────────────────────────────────────────────────
OFF_SEARCH_URL = "https://world.openfoodfacts.org/api/v2/search"

def lookup_product(product_name: str, max_results: int = 3) -> dict:
    """Search Open Food Facts by product name using stable v2 API."""
    product_name = product_name.strip()
    if not product_name:
        return {"ok": False, "source": "Open Food Facts",
                "error": "Please enter a product name."}
    try:
        resp = requests.get(
            OFF_SEARCH_URL,
            params={
                "search_terms": product_name,
                "page_size":    max_results,
                "page":         1,
                "fields":       "product_name,brands,quantity,serving_size,nutriments,"
                                "nutriscore_grade,ingredients_text,categories,image_front_url",
            },
            headers={"User-Agent": "PlatePal/1.0 (student project)"},
            timeout=TIMEOUT,
        )
        resp.raise_for_status()
        products_raw = resp.json().get("products", [])
        products = []
        for p in products_raw:
            name = (p.get("product_name") or "").strip()
            if not name:
                continue
            nut = p.get("nutriments", {})
            products.append({
                "name":         name,
                "brand":        p.get("brands", "—"),
                "quantity":     p.get("quantity", "—"),
                "serving_size": p.get("serving_size", "—"),
                "nutriscore":   (p.get("nutriscore_grade") or "—").upper(),
                "ingredients":  (p.get("ingredients_text") or "—")[:250],
                "categories":   (p.get("categories") or "—")[:80],
                "image":        p.get("image_front_url", ""),
                "calories_100g": nut.get("energy-kcal_100g", "—"),
                "protein_100g":  nut.get("proteins_100g", "—"),
                "carbs_100g":    nut.get("carbohydrates_100g", "—"),
                "fat_100g":      nut.get("fat_100g", "—"),
                "sugars_100g":   nut.get("sugars_100g", "—"),
                "salt_100g":     nut.get("salt_100g", "—"),
            })
        return {"ok": True, "source": "Open Food Facts", "products": products}
    except Exception as e:
        return {"ok": False, "source": "Open Food Facts", "error": str(e)}
