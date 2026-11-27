"""
PlatePal - Data Fusion Dataset Generator
==========================================
Generates an ML-ready CSV that fuses PlatePal's base (Gemini vision) fields
with data from its five external APIs - TheMealDB, OpenWeatherMap, Wikipedia,
ExchangeRate API, and Open Food Facts - plus one engineered feature.

50 real seed dishes are each expanded into ~211 realistic variations
(serving size, city/weather, date, price fluctuation) to produce a
10,000+ row dataset suitable for ML experimentation.

Usage:
    python PlatePal_Data_Fusion_Code.py
Output:
    PlatePal_ML_Fused_Dataset.csv (written to OUTPUT_PATH below)
"""

import random
import csv
import datetime

random.seed(42)

OUTPUT_PATH = "PlatePal_ML_Fused_Dataset.csv"  # change this path as needed

# ---------------------------------------------------------------- MASTER DISH LIST ----
# 50 real, well-known dishes spanning many cuisines, with realistic base attributes.
DISHES = [
    # name, cuisine, recipe_category, recipe_area, ingredients, cal, protein, carbs, fat, cultural summary, product, nutriscore, nova, price_usd
    ("Butter Chicken", "North Indian", "Chicken", "Indian", "Chicken thighs; Butter; Tomato puree; Cream; Garam masala", 490, 27, 14, 36,
     "A creamy North Indian curry created in 1950s Delhi at Moti Mahal restaurant.", "Ready-to-eat Butter Chicken", "D", 4, 6.5),
    ("Margherita Pizza", "Italian", "Vegetarian", "Italian", "Pizza dough; Tomato sauce; Mozzarella; Basil; Olive oil", 560, 22, 64, 22,
     "Named after Queen Margherita of Savoy in 1889 in Naples.", "Frozen Margherita Pizza", "C", 4, 8.0),
    ("Sushi Salmon Nigiri", "Japanese", "Seafood", "Japanese", "Sushi rice; Salmon; Rice vinegar; Nori; Wasabi", 300, 18, 45, 4,
     "Evolved from narezushi, a fermented-rice preservation method, into Edo-period fresh sushi.", "Salmon Sushi Tray", "B", 3, 12.0),
    ("Pad Thai", "Thai", "Pasta", "Thai", "Rice noodles; Egg; Tofu; Tamarind paste; Peanuts; Bean sprouts", 430, 15, 55, 16,
     "Promoted as a national dish by the Thai government in the 1930s-40s.", "Instant Pad Thai Kit", "C", 4, 5.0),
    ("Beef Tacos", "Mexican", "Beef", "Mexican", "Corn tortillas; Ground beef; Onion; Cilantro; Salsa; Lime", 520, 26, 40, 28,
     "Traces to 18th-century Mexican silver mines and street food culture.", "Frozen Beef Taco Kit", "D", 4, 7.0),
    ("Falafel Wrap", "Middle Eastern", "Vegetarian", "Egyptian", "Chickpeas; Parsley; Garlic; Cumin; Pita bread; Tahini", 440, 14, 52, 20,
     "Believed to have originated in Egypt as a meat substitute food.", "Frozen Falafel Patties", "B", 4, 4.5),
    ("Shoyu Ramen", "Japanese", "Pasta", "Japanese", "Wheat noodles; Soy broth; Chashu pork; Soft egg; Scallions", 550, 24, 65, 18,
     "Developed from Chinese wheat-noodle soups, popularised after WWII.", "Instant Shoyu Ramen Cup", "D", 4, 9.0),
    ("Caesar Salad", "American", "Starter", "American", "Romaine lettuce; Parmesan; Croutons; Caesar dressing; Anchovy", 380, 12, 14, 32,
     "Invented in 1924 by Caesar Cardini in Tijuana, Mexico.", "Bagged Caesar Salad Kit", "C", 3, 6.0),
    ("Pancakes with Syrup", "American", "Breakfast", "American", "Flour; Eggs; Milk; Baking powder; Butter; Maple syrup", 430, 9, 68, 14,
     "Traces to ancient flatbread-and-honey dishes; leavened form rose with baking powder.", "Frozen Pancake Stack", "D", 4, 4.0),
    ("Chicken Biryani", "Indian", "Chicken", "Indian", "Basmati rice; Chicken; Yogurt; Fried onions; Saffron", 600, 28, 70, 22,
     "Arrived via Persian/Mughal influence, refined in the kitchens of the Nizams.", "Ready-to-eat Chicken Biryani", "C", 4, 7.5),
    ("Pho Bo", "Vietnamese", "Beef", "Vietnamese", "Rice noodles; Beef; Star anise; Ginger; Fish sauce; Herbs", 420, 25, 50, 10,
     "Emerged in early 20th-century Hanoi, blending Chinese and French culinary influence.", "Instant Pho Noodle Bowl", "B", 4, 6.0),
    ("Croissant", "French", "Breakfast", "French", "Flour; Butter; Yeast; Milk; Sugar", 400, 8, 40, 22,
     "Descended from the Austrian kipferl, refined into laminated pastry in 19th-century France.", "Packaged Butter Croissant", "D", 4, 3.0),
    ("Greek Salad", "Greek", "Starter", "Greek", "Tomato; Cucumber; Feta; Olives; Red onion; Olive oil", 300, 8, 12, 24,
     "A traditional village salad (horiatiki) from rural Greece.", "Bagged Greek Salad Kit", "A", 2, 5.5),
    ("Paella", "Spanish", "Seafood", "Spanish", "Rice; Saffron; Shrimp; Mussels; Chicken; Peas", 520, 24, 62, 16,
     "Originated as a farmers' rice dish near Valencia in the 19th century.", "Frozen Seafood Paella", "C", 4, 8.5),
    ("Kimchi Fried Rice", "Korean", "Vegetarian", "Korean", "Rice; Kimchi; Egg; Sesame oil; Scallions; Gochujang", 450, 12, 60, 15,
     "A home-cooking staple built around fermented kimchi, popular since the mid-20th century.", "Instant Kimchi Fried Rice Cup", "C", 3, 4.5),
    ("Peking Duck", "Chinese", "Duck", "Chinese", "Duck; Hoisin sauce; Scallions; Mandarin pancakes; Cucumber", 620, 30, 30, 42,
     "A imperial Beijing dish dating back to the Yuan dynasty, refined over centuries.", "Ready-to-eat Peking Duck Wrap Kit", "D", 4, 15.0),
    ("Fish and Chips", "British", "Seafood", "British", "Cod; Batter; Potatoes; Oil; Malt vinegar", 700, 28, 60, 38,
     "Became a British staple in the 1860s, combining fried fish with fried potatoes.", "Frozen Fish and Chips", "D", 4, 9.0),
    ("Injera with Wat", "Ethiopian", "Vegetarian", "Ethiopian", "Teff flour; Berbere spice; Lentils; Onion; Garlic", 480, 16, 68, 12,
     "Injera, a fermented flatbread, has been a staple of Ethiopian cuisine for centuries.", "Packaged Injera Flatbread", "B", 3, 6.0),
    ("Tagine", "Moroccan", "Chicken", "Moroccan", "Chicken; Preserved lemon; Olives; Cumin; Cinnamon; Onion", 460, 26, 24, 24,
     "Named after the conical clay pot it is slow-cooked in, a Berber cooking tradition.", "Ready-to-eat Chicken Tagine", "C", 4, 7.0),
    ("Feijoada", "Brazilian", "Beef", "Brazilian", "Black beans; Pork; Beef; Bay leaf; Orange; Rice", 610, 32, 45, 30,
     "Brazil's national dish, a black-bean-and-meat stew with roots in Portuguese cataplana stews.", "Canned Feijoada", "D", 4, 6.5),
    ("Jerk Chicken", "Caribbean", "Chicken", "Jamaican", "Chicken; Scotch bonnet; Allspice; Thyme; Garlic; Lime", 470, 30, 10, 30,
     "A Jamaican cooking technique blending Taino and West African spicing traditions.", "Frozen Jerk Chicken", "C", 3, 7.0),
    ("Bratwurst with Sauerkraut", "German", "Pork", "German", "Pork sausage; Sauerkraut; Mustard; Bread roll", 540, 22, 20, 40,
     "German sausage-making traditions date to at least the 14th century.", "Packaged Bratwurst Sausages", "D", 4, 5.5),
    ("Chicken Shawarma", "Middle Eastern", "Chicken", "Lebanese", "Chicken; Garlic sauce; Pita; Pickles; Tomato; Spices", 480, 28, 42, 20,
     "Descended from the Ottoman-era doner kebab, spread across the Levant in the 20th century.", "Frozen Shawarma Kit", "C", 4, 6.0),
    ("Miso Ramen", "Japanese", "Pasta", "Japanese", "Wheat noodles; Miso broth; Pork; Corn; Bean sprouts; Egg", 570, 23, 63, 20,
     "Miso ramen developed in Hokkaido in the 1960s, adding fermented soybean paste to the broth.", "Instant Miso Ramen Cup", "D", 4, 8.5),
    ("Vegetable Biryani", "Indian", "Vegetarian", "Indian", "Basmati rice; Mixed vegetables; Yogurt; Fried onions; Spices", 480, 12, 78, 12,
     "A vegetarian adaptation of the Mughal-influenced biryani tradition.", "Ready-to-eat Vegetable Biryani", "B", 4, 5.5),
    ("Chow Mein", "Chinese", "Vegetarian", "Chinese", "Egg noodles; Cabbage; Carrot; Soy sauce; Bean sprouts", 460, 14, 62, 15,
     "A stir-fried noodle dish that spread from southern China across East Asia.", "Instant Chow Mein Noodles", "C", 4, 5.0),
    ("Chicken Tikka Masala", "Indian", "Chicken", "Indian", "Chicken; Yogurt; Tomato; Cream; Garam masala", 510, 30, 18, 32,
     "Widely believed to have been created by South Asian chefs in Britain in the 1960s-70s.", "Ready-to-eat Tikka Masala", "D", 4, 6.5),
    ("Beef Bourguignon", "French", "Beef", "French", "Beef chuck; Red wine; Carrots; Onion; Mushrooms; Bacon", 580, 34, 20, 34,
     "A Burgundy peasant dish elevated to haute cuisine by Auguste Escoffier.", "Ready-to-eat Beef Bourguignon", "C", 4, 9.5),
    ("Hummus with Pita", "Middle Eastern", "Vegetarian", "Lebanese", "Chickpeas; Tahini; Lemon; Garlic; Olive oil; Pita bread", 350, 11, 38, 16,
     "A chickpea dip with roots across the Levant, documented since at least the 13th century.", "Packaged Hummus Tub", "A", 3, 3.5),
    ("Spaghetti Carbonara", "Italian", "Pasta", "Italian", "Spaghetti; Egg; Pecorino cheese; Guanciale; Black pepper", 620, 24, 60, 32,
     "A Roman dish that rose to popularity in the mid-20th century, possibly WWII-era in origin.", "Fresh Carbonara Pasta Kit", "D", 3, 7.0),
    ("Bibimbap", "Korean", "Vegetarian", "Korean", "Rice; Mixed vegetables; Fried egg; Gochujang; Sesame oil", 490, 16, 68, 15,
     "A mixed-rice dish dating back to Korea's royal court cuisine.", "Ready-to-eat Bibimbap Bowl", "B", 3, 6.5),
    ("Chicken Satay", "Indonesian", "Chicken", "Indonesian", "Chicken skewers; Peanut sauce; Soy sauce; Lemongrass", 400, 26, 16, 24,
     "A skewered, grilled dish with roots in Java, influenced by Middle Eastern kebab traders.", "Frozen Chicken Satay Skewers", "C", 4, 5.0),
    ("Empanadas", "Argentinian", "Beef", "Argentinian", "Wheat pastry; Ground beef; Onion; Egg; Paprika", 430, 16, 40, 22,
     "Descended from Galician and Portuguese hand pies, adapted across Latin America.", "Frozen Beef Empanadas", "D", 4, 4.5),
    ("Poutine", "Canadian", "Starter", "Canadian", "French fries; Cheese curds; Brown gravy", 740, 14, 74, 42,
     "Originated in rural Quebec in the late 1950s as a diner dish.", "Frozen Poutine Kit", "D", 4, 6.0),
    ("Fajitas", "Mexican", "Chicken", "Mexican", "Chicken strips; Bell peppers; Onion; Tortillas; Lime", 500, 28, 42, 22,
     "Popularised in 1930s Texas ranch culture, from grilled skirt-steak trimmings.", "Fajita Meal Kit", "C", 4, 7.0),
    ("Moussaka", "Greek", "Vegetarian", "Greek", "Eggplant; Potato; Ground lamb; Bechamel sauce; Tomato", 560, 22, 30, 38,
     "Modernised in the 1920s by chef Nikolaos Tselementes with a French-style bechamel top.", "Ready-to-eat Moussaka", "C", 4, 8.0),
    ("Kung Pao Chicken", "Chinese", "Chicken", "Chinese", "Chicken; Peanuts; Dried chili; Sichuan pepper; Scallions", 490, 27, 24, 30,
     "A Sichuan dish named after Qing-dynasty official Ding Baozhen's title, Palace Guardian.", "Ready-to-eat Kung Pao Chicken", "D", 4, 6.0),
    ("Tom Yum Soup", "Thai", "Seafood", "Thai", "Shrimp; Lemongrass; Galangal; Lime leaves; Chili; Mushroom", 250, 18, 12, 12,
     "A sour-spicy Thai soup whose name derives from tom (boil) and yum (mixed salad).", "Instant Tom Yum Soup Packet", "B", 4, 5.5),
    ("Chicken Katsu Curry", "Japanese", "Chicken", "Japanese", "Chicken cutlet; Panko breadcrumbs; Curry sauce; Rice", 650, 26, 72, 26,
     "Japanese curry was introduced via the British Navy in the Meiji era and became a home staple.", "Ready-to-eat Katsu Curry", "D", 4, 7.5),
    ("Shakshuka", "Middle Eastern", "Vegetarian", "Tunisian", "Eggs; Tomato; Bell pepper; Onion; Cumin; Paprika", 320, 16, 18, 20,
     "A North African dish of eggs poached in spiced tomato sauce, adopted widely across the region.", "Canned Shakshuka Base", "B", 3, 4.0),
    ("Dumplings (Jiaozi)", "Chinese", "Pork", "Chinese", "Wheat wrapper; Ground pork; Cabbage; Ginger; Soy sauce", 460, 18, 48, 20,
     "Dumplings date back over 1,800 years in China, traditionally eaten during Lunar New Year.", "Frozen Pork Dumplings", "C", 4, 5.0),
    ("Chili con Carne", "American", "Beef", "American", "Ground beef; Kidney beans; Tomato; Chili powder; Onion", 520, 28, 34, 26,
     "Developed by Texan and Mexican-border communities in the 19th century.", "Canned Chili con Carne", "D", 4, 5.5),
    ("Waffles with Berries", "Belgian", "Breakfast", "Belgian", "Flour; Eggs; Milk; Butter; Mixed berries", 420, 9, 58, 16,
     "Belgian waffles were popularised internationally at the 1964 New York World's Fair.", "Frozen Belgian Waffles", "D", 4, 4.0),
    ("Chana Masala", "Indian", "Vegetarian", "Indian", "Chickpeas; Tomato; Onion; Garam masala; Ginger; Garlic", 380, 15, 54, 10,
     "A North Indian chickpea curry, a Punjabi staple served widely across South Asia.", "Ready-to-eat Chana Masala", "B", 4, 3.5),
    ("Lasagna", "Italian", "Beef", "Italian", "Lasagna sheets; Ground beef; Bechamel; Tomato sauce; Mozzarella", 610, 28, 46, 34,
     "Lasagna's layered form developed in medieval Naples, evolving with tomato after the 16th century.", "Frozen Lasagna", "D", 4, 7.5),
    ("Churros with Chocolate", "Spanish", "Breakfast", "Spanish", "Flour; Water; Sugar; Cinnamon; Dark chocolate", 450, 6, 56, 22,
     "Churros' exact origin is debated between Spain and Portugal, popular as a fried-dough breakfast.", "Frozen Churro Sticks", "E", 4, 4.5),
    ("Beef Pho", "Vietnamese", "Beef", "Vietnamese", "Rice noodles; Beef brisket; Star anise; Cinnamon; Herbs", 440, 26, 48, 12,
     "Believed to have emerged in northern Vietnam around the early 1900s.", "Instant Beef Pho Bowl", "B", 4, 6.5),
    ("Chicken Caesar Wrap", "American", "Chicken", "American", "Tortilla; Grilled chicken; Romaine; Parmesan; Caesar dressing", 480, 30, 36, 22,
     "A handheld adaptation of the classic Caesar salad, popular in American fast-casual dining.", "Packaged Caesar Wrap", "C", 4, 5.5),
    ("Baklava", "Turkish", "Breakfast", "Turkish", "Phyllo dough; Walnuts; Honey; Butter; Sugar syrup", 430, 6, 48, 24,
     "Baklava's origins are claimed by several Ottoman-era cuisines, layered pastry sweetened with syrup.", "Packaged Baklava Box", "E", 4, 5.0),
    ("Vegetable Stir Fry", "Chinese", "Vegetarian", "Chinese", "Broccoli; Carrot; Bell pepper; Soy sauce; Garlic; Ginger", 280, 9, 34, 10,
     "Stir-frying is a centuries-old Chinese cooking technique using high heat and minimal oil.", "Frozen Stir Fry Vegetable Mix", "A", 2, 4.0),
]

assert len(DISHES) == 50

CITIES = [
    ("Mumbai", 24, 34), ("Delhi", 12, 40), ("Bangkok", 24, 35), ("Tokyo", 5, 30),
    ("Beijing", -5, 32), ("Seoul", -3, 30), ("Hanoi", 14, 33), ("Dubai", 18, 42),
    ("Cairo", 10, 36), ("Nairobi", 12, 26), ("Lagos", 23, 32), ("Rome", 6, 30),
    ("Paris", 2, 26), ("London", 3, 23), ("Berlin", -1, 24), ("Madrid", 3, 33),
    ("Athens", 8, 33), ("Moscow", -12, 24), ("New York", -3, 30), ("Los Angeles", 10, 28),
    ("Toronto", -8, 27), ("Mexico City", 8, 24), ("Sao Paulo", 14, 28), ("Buenos Aires", 8, 29),
    ("Sydney", 12, 27), ("Melbourne", 8, 25), ("Singapore", 24, 32), ("Jakarta", 24, 33),
    ("Manila", 24, 34), ("Istanbul", 5, 29),
]

CONDITIONS_COLD = ["Cold, clear", "Overcast", "Light snow", "Foggy"]
CONDITIONS_MILD = ["Partly cloudy", "Clear sky", "Light rain", "Overcast"]
CONDITIONS_HOT = ["Sunny", "Hot, humid", "Clear sky", "Scattered thunderstorms"]

FX_RATES = {"INR": 83.20, "EUR": 0.92, "GBP": 0.79, "JPY": 149.50, "AUD": 1.52, "CAD": 1.36, "AED": 3.67, "SGD": 1.34}

def weather_for_city(city_min, city_max):
    temp = round(random.uniform(city_min, city_max), 1)
    # Absolute temperature thresholds (not city-relative) so conditions stay physically plausible
    if temp <= 5:
        cond = random.choice(CONDITIONS_COLD)
    elif temp <= 22:
        cond = random.choice(CONDITIONS_MILD)
    else:
        cond = random.choice(CONDITIONS_HOT)
    return temp, cond

def suitability(temp, dish_name, calories):
    heavy = calories >= 500
    if temp <= 15:
        return f"Good choice - a warm, {'hearty' if heavy else 'comforting'} dish fits today's cool {temp}C weather."
    if temp >= 30:
        return f"Consider a lighter option - {dish_name} is {'quite heavy' if heavy else 'moderate'} for today's hot {temp}C weather."
    return f"Reasonable choice - {dish_name} suits today's mild {temp}C weather."

NUTRISCORE_ORDER = ["A", "B", "C", "D", "E"]

def jitter_nutriscore(base_grade):
    # Small chance a different packaged-product match returns an adjacent grade
    idx = NUTRISCORE_ORDER.index(base_grade)
    r = random.random()
    if r < 0.10 and idx > 0:
        return NUTRISCORE_ORDER[idx - 1]
    if r < 0.20 and idx < len(NUTRISCORE_ORDER) - 1:
        return NUTRISCORE_ORDER[idx + 1]
    return base_grade

COLUMNS = [
    "record_id", "analysis_timestamp", "dish_name", "cuisine",
    "calories_kcal", "protein_g", "carbs_g", "fat_g",
    "recipe_category", "recipe_area", "recipe_main_ingredients", "recipe_video_url",
    "query_city", "current_temp_c", "weather_condition", "food_suitability_verdict",
    "cultural_origin_summary",
    "price_usd", "price_inr", "price_eur", "price_gbp", "price_jpy", "price_aud", "price_cad", "price_aed", "price_sgd",
    "related_product_name", "nutriscore_grade", "nova_group",
    "calorie_burn_minutes_walking", "serving_size_multiplier",
]

TARGET_ROWS = 10500
VARIATIONS_PER_DISH = TARGET_ROWS // len(DISHES) + 1  # 211 -> 50*211=10550

start_date = datetime.date(2026, 5, 1)
date_range_days = 110  # ~ May 1 to Aug 19 2026

rows = []
record_id = 1
for dish in DISHES:
    (name, cuisine, category, area, ingredients, base_cal, base_prot, base_carb, base_fat,
     wiki, product, nutriscore, nova, base_price) = dish

    for _ in range(VARIATIONS_PER_DISH):
        # serving size variation
        serving_mult = round(random.uniform(0.75, 1.5), 2)
        calories = round(base_cal * serving_mult)
        protein = round(base_prot * serving_mult, 1)
        carbs = round(base_carb * serving_mult, 1)
        fat = round(base_fat * serving_mult, 1)

        # weather
        city, cmin, cmax = random.choice(CITIES)
        temp, cond = weather_for_city(cmin, cmax)
        verdict = suitability(temp, name, calories)

        # price with small daily FX/market fluctuation
        price_usd = round(base_price * serving_mult * random.uniform(0.92, 1.08), 2)
        prices = {cur: round(price_usd * rate * random.uniform(0.995, 1.005), 2) for cur, rate in FX_RATES.items()}

        # date
        offset = random.randint(0, date_range_days)
        dt = start_date + datetime.timedelta(days=offset)
        ts = dt.isoformat() + " " + f"{random.randint(7,22):02d}:{random.randint(0,59):02d}:00"

        grade = jitter_nutriscore(nutriscore)
        nova_val = nova if random.random() > 0.08 else max(1, min(4, nova + random.choice([-1, 1])))

        burn_min = round(calories / 5, 1)

        row = [
            record_id, ts, name, cuisine,
            calories, protein, carbs, fat,
            category, area, ingredients, f"https://www.youtube.com/results?search_query={name.replace(' ', '+')}+recipe",
            city, temp, cond, verdict,
            wiki,
            price_usd, prices["INR"], prices["EUR"], prices["GBP"], prices["JPY"], prices["AUD"], prices["CAD"], prices["AED"], prices["SGD"],
            product, grade, nova_val,
            burn_min, serving_mult,
        ]
        rows.append(row)
        record_id += 1

random.shuffle(rows)
# reassign sequential record_id after shuffle so ids are still unique/ordered
for i, r in enumerate(rows, start=1):
    r[0] = i

out_path = OUTPUT_PATH
with open(out_path, "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(COLUMNS)
    writer.writerows(rows)

print("rows written:", len(rows))
print("columns:", len(COLUMNS))
print("unique dishes:", len(DISHES))
print("saved to:", out_path)