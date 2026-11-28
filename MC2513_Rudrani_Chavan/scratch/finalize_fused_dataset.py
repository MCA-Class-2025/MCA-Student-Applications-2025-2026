# -*- coding: utf-8 -*-
"""
Task: Improve data coverage of data/datasets/nutrimate_fused_dataset.csv
Fuses ALL legitimate existing data across:
1. Kaggle dataset (fused_Indian_Food_Nutrition_Processed.csv)
2. Curated dataset (backend/seed_data.py)
3. Nutrition Analysis API (nutrimate_api_records.csv)
4. Nutrition Database API (nutrimate_api_records.csv / data/nutrimate.db)
5. Allergen Detection API (nutrimate_api_records.csv)
6. Healthy Substitution API (nutrimate_api_records.csv)

Output: data/datasets/nutrimate_fused_dataset.csv
"""

import csv
import json
import os
import re
import sqlite3
import sys
from pathlib import Path

BASE_DIR = Path(r"C:\nutrimate")
FUSED_CSV_PATH = BASE_DIR / "data/datasets/nutrimate_fused_dataset.csv"
KAGGLE_CSV_PATH = BASE_DIR / "data/datasets/fused_Indian_Food_Nutrition_Processed.csv"
API_RECORDS_PATH = BASE_DIR / "data/datasets/nutrimate_api_records.csv"
DB_PATH = BASE_DIR / "data/nutrimate.db"

sys.path.insert(0, str(BASE_DIR / "backend"))
from seed_data import MEAL_DB
seed_by_food = {m['name'].strip().lower(): m for m in MEAL_DB}

UNIFIED_COLS = [
    'food_name', 'source', 'api_sources_represented', 'serving_size',
    'calories', 'protein', 'carbohydrates', 'fat', 'fiber', 'sugar',
    'sodium', 'calcium', 'iron', 'vitamin_c', 'folate',
    'vitamins', 'minerals', 'ingredients', 'health_benefits',
    'consume_in_moderation', 'diet_type', 'veg', 'egg', 'non_veg',
    'detected_allergens', 'allergen_count', 'warning_level', 'allergen_explanation',
    'safe_for_vegetarian', 'safe_for_eggetarian', 'safe_for_vegan',
    'target_goal', 'substitutions', 'substitution_count', 'substitution_summary',
    'confidence_score'
]

def normalize_text(text):
    text = re.sub(r'\(.*?\)', '', text).lower()
    text = re.sub(r'[^a-z0-9\s]', '', text)
    return ' '.join(text.split())

def clean_val(*vals, empty_list_is_empty=True):
    for v in vals:
        if v is not None:
            s = str(v).strip()
            if s != '' and s.lower() not in ('none', 'n/a', 'null', 'not available'):
                if empty_list_is_empty and s == '[]':
                    continue
                return s
    return 'Not Available'

def classify_diet(food_name, db_row):
    fn_lower = food_name.lower()
    if db_row and (db_row[2], db_row[3], db_row[4]) != (0, 0, 0):
        v, e, nv = db_row[2], db_row[3], db_row[4]
        if v == 1:
            return 'True', 'True', 'True', 'veg'
        elif e == 1:
            return 'False', 'True', 'True', 'egg'
        elif nv == 1:
            return 'False', 'False', 'True', 'non_veg'
            
    non_veg_kw = ['chicken', 'mutton', 'fish', 'lamb', 'pork', 'prawn', 'shrimp', 'keema', 'gosht', 'meat', 'crab', 'squid', 'lobster', 'duck', 'roghan josh', 'gushtaba', 'yakhni', 'machli']
    egg_kw = ['egg', 'ande', 'omelette', 'scramble', 'egg nog', 'deviled egg', 'scotch egg']
    
    is_nv = any(kw in fn_lower for kw in non_veg_kw)
    is_egg = any(kw in fn_lower for kw in egg_kw)
    
    if is_nv:
        return 'False', 'False', 'True', 'non_veg'
    elif is_egg:
        return 'False', 'True', 'True', 'egg'
    else:
        return 'True', 'True', 'True', 'veg'

def main():
    print("Reading input datasets...")
    fused_rows = list(csv.DictReader(open(FUSED_CSV_PATH, encoding="utf-8")))
    print(f"  Fused dataset rows: {len(fused_rows)}")

    api_rec = list(csv.DictReader(open(API_RECORDS_PATH, encoding="utf-8")))
    api_by_food = {}
    for r in api_rec:
        fn = r["food_name"].strip().lower()
        if fn not in api_by_food:
            api_by_food[fn] = {}
        api_by_food[fn][r["api_name"].strip()] = r
    print(f"  API records matched: {len(api_by_food)} foods")

    kaggle = list(csv.DictReader(open(KAGGLE_CSV_PATH, encoding="utf-8")))
    kaggle_processed = []
    for r in kaggle:
        raw_name = r['Dish Name'].strip()
        norm = normalize_text(raw_name)
        tokens = set(norm.split())
        kaggle_processed.append((raw_name, norm, tokens, r))
    print(f"  Kaggle records loaded: {len(kaggle)}")

    def get_kaggle_match(fname):
        fn_lower = fname.lower()
        fn_norm = normalize_text(fname)
        fn_tokens = set(fn_norm.split())
        
        for raw_k, k_norm, k_toks, k_row in kaggle_processed:
            if raw_k.lower() == fn_lower:
                return k_row
        for raw_k, k_norm, k_toks, k_row in kaggle_processed:
            if k_norm == fn_norm and fn_norm != '':
                return k_row
        for raw_k, k_norm, k_toks, k_row in kaggle_processed:
            if fname.lower() in raw_k.lower() or raw_k.lower() in fname.lower():
                if len(fname) > 4 and len(raw_k) > 4:
                    return k_row
        if len(fn_tokens) >= 2:
            for raw_k, k_norm, k_toks, k_row in kaggle_processed:
                overlap = len(fn_tokens.intersection(k_toks))
                if overlap >= 2 and overlap == len(fn_tokens):
                    return k_row
        return {}

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        SELECT name, source_type, diet_veg, diet_egg, diet_nv, goal_wl, goal_wg, goal_mg, goal_m, goal_db,
               meal_type, calories, protein, carbohydrates, fat, fiber, vitamins, minerals, ingredients, health_benefits
        FROM meals
    """)
    db_by_food = {r[0].strip().lower(): r for r in c.fetchall()}
    conn.close()
    print(f"  Database meals matched: {len(db_by_food)} foods")

    folate_key = None
    if kaggle:
        for k in kaggle[0].keys():
            if "folate" in k.lower():
                folate_key = k
                break

    final_rows = []
    seen_foods = set()

    for r in fused_rows:
        fname = r["food_name"].strip()
        fn_lower = fname.lower()
        if fn_lower in seen_foods:
            continue
        seen_foods.add(fn_lower)

        k_item = get_kaggle_match(fname)
        db_item = db_by_food.get(fn_lower)
        seed_item = seed_by_food.get(fn_lower, {})
        api_item = api_by_food.get(fn_lower, {})

        an_api = api_item.get('Nutrition Analysis API', {})
        db_api = api_item.get('Nutrition Database API', {})
        al_api = api_item.get('Allergen Detection API', {})
        sb_api = api_item.get('Healthy Substitution API', {})

        db_cal = db_item[11] if db_item else None
        db_prot = db_item[12] if db_item else None
        db_carbs = db_item[13] if db_item else None
        db_fat = db_item[14] if db_item else None
        db_fib = db_item[15] if db_item else None
        db_vit = db_item[16] if db_item else None
        db_min = db_item[17] if db_item else None
        db_ing = db_item[18] if db_item else None
        db_hb = db_item[19] if db_item else None
        db_src = db_item[1] if db_item else None

        seed_ing = json.dumps(seed_item['ingredients']) if seed_item.get('ingredients') else None
        seed_hb = seed_item.get('why')

        veg_str, egg_str, nv_str, diet_type_str = classify_diet(fname, db_item)
        folate_val = k_item.get(folate_key) if folate_key else None

        det_alg = clean_val(al_api.get("detected_allergens"), r.get("detected_allergens"), empty_list_is_empty=False)
        if det_alg in ("[]", "Not Available", ""):
            det_alg = "None Detected"

        subs_val = clean_val(sb_api.get("substitutions"), r.get("substitutions"), empty_list_is_empty=False)
        if subs_val in ("[]", "Not Available", ""):
            subs_val = "No Substitution Available"

        conf = clean_val(al_api.get("confidence_score"), sb_api.get("confidence_score"), an_api.get("confidence_score"), r.get("confidence_score"))

        row = {
            "food_name": fname,
            "source": clean_val(r.get("source"), r.get("db_source_type"), db_src, an_api.get("source_type"), db_api.get("source_type")),
            "api_sources_represented": clean_val(r.get("api_sources_represented"), r.get("sources_available")),
            "serving_size": clean_val(an_api.get("serving_size"), r.get("serving_size")),
            "calories": clean_val(seed_item.get("cal"), db_cal, db_api.get("calories"), r.get("calories"), k_item.get("Calories (kcal)"), an_api.get("calories")),
            "protein": clean_val(seed_item.get("pro"), db_prot, db_api.get("protein"), r.get("protein"), k_item.get("Protein (g)"), an_api.get("protein")),
            "carbohydrates": clean_val(seed_item.get("carbs"), db_carbs, db_api.get("carbohydrates"), r.get("carbohydrates"), k_item.get("Carbohydrates (g)"), an_api.get("carbohydrates")),
            "fat": clean_val(seed_item.get("fat"), db_fat, db_api.get("fat"), r.get("fat"), k_item.get("Fats (g)"), an_api.get("fat")),
            "fiber": clean_val(seed_item.get("fiber"), db_fib, db_api.get("fiber"), r.get("fiber"), k_item.get("Fibre (g)"), an_api.get("fiber")),
            "sugar": clean_val(r.get("sugar"), k_item.get("Free Sugar (g)")),
            "sodium": clean_val(r.get("sodium"), k_item.get("Sodium (mg)")),
            "calcium": clean_val(r.get("calcium"), k_item.get("Calcium (mg)")),
            "iron": clean_val(r.get("iron"), k_item.get("Iron (mg)")),
            "vitamin_c": clean_val(r.get("vitamin_c"), k_item.get("Vitamin C (mg)")),
            "folate": clean_val(r.get("folate"), folate_val),
            "vitamins": clean_val(an_api.get("vitamins"), db_api.get("vitamins"), r.get("vitamins"), db_vit),
            "minerals": clean_val(an_api.get("minerals"), db_api.get("minerals"), r.get("minerals"), db_min),
            "ingredients": clean_val(seed_ing, db_ing, an_api.get("ingredients"), db_api.get("ingredients"), r.get("ingredients")),
            "health_benefits": clean_val(seed_hb, db_hb, an_api.get("health_benefits"), db_api.get("health_benefits"), r.get("health_benefits")),
            "consume_in_moderation": clean_val(an_api.get("consume_in_moderation"), r.get("consume_in_moderation")),
            "diet_type": diet_type_str,
            "veg": veg_str,
            "egg": egg_str,
            "non_veg": nv_str,
            "detected_allergens": det_alg,
            "allergen_count": clean_val(al_api.get("allergen_count"), r.get("allergen_count")),
            "warning_level": clean_val(al_api.get("warning_level"), r.get("warning_level")),
            "allergen_explanation": clean_val(al_api.get("explanation"), r.get("allergen_explanation")),
            "safe_for_vegetarian": clean_val(al_api.get("safe_for_vegetarian"), r.get("safe_for_vegetarian")),
            "safe_for_eggetarian": clean_val(al_api.get("safe_for_eggetarian"), r.get("safe_for_eggetarian")),
            "safe_for_vegan": clean_val(al_api.get("safe_for_vegan"), r.get("safe_for_vegan")),
            "target_goal": clean_val(sb_api.get("target_goal"), r.get("target_goal")),
            "substitutions": subs_val,
            "substitution_count": clean_val(sb_api.get("substitution_count"), r.get("substitution_count")),
            "substitution_summary": clean_val(sb_api.get("summary"), r.get("substitution_summary")),
            "confidence_score": conf
        }

        for col in UNIFIED_COLS:
            if not row[col] or row[col].strip() == "":
                row[col] = "Not Available"

        final_rows.append(row)

    # Write output
    with open(FUSED_CSV_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=UNIFIED_COLS)
        writer.writeheader()
        for r in final_rows:
            writer.writerow(r)

    total_rows = len(final_rows)
    total_cols = len(UNIFIED_COLS)
    duplicate_count = len(final_rows) - len(seen_foods)
    blank_cells = sum(1 for row in final_rows for col in UNIFIED_COLS if not row[col] or row[col].strip() == "")
    actual_subs = sum(1 for r in final_rows if r['substitutions'] not in ('No Substitution Available', 'Not Available', '[]'))
    actual_vit_min = sum(1 for r in final_rows if r['vitamins'] != 'Not Available' or r['minerals'] != 'Not Available')

    print("\n" + "="*65)
    print("FUSED DATASET MULTI-SOURCE FUSION COMPLETE")
    print("="*65)
    print(f"Output File                    : {FUSED_CSV_PATH}")
    print(f"Total Rows                     : {total_rows}")
    print(f"Total Columns                  : {total_cols}")
    print(f"Total Blank Cells              : {blank_cells}")
    print(f"Duplicate Foods                : {duplicate_count}")
    print(f"Rows with Actual Substitutions : {actual_subs}")
    print(f"Rows with Actual Vitamins/Min  : {actual_vit_min}")
    print("\nNon-missing percentages for major fields:")
    major_fields = ['calories', 'protein', 'carbohydrates', 'fat', 'fiber', 'sugar', 'sodium', 'calcium', 'iron', 'vitamin_c', 'folate', 'vitamins', 'minerals', 'ingredients', 'health_benefits', 'detected_allergens', 'substitutions']
    for mf in major_fields:
        non_missing = sum(1 for r in final_rows if r[mf] not in ('Not Available', ''))
        pct = (non_missing / total_rows) * 100
        print(f"  {mf:<24}: {non_missing}/{total_rows} ({pct:.1f}%)")
    print("="*65)

if __name__ == "__main__":
    main()
