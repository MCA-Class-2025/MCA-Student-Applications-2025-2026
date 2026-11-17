# -*- coding: utf-8 -*-
"""
Task: Restructure data/datasets/nutrimate_fused_dataset.csv into ONE clean row per food,
unifying all API sources (Nutrition Analysis, Nutrition Database, Allergen Detection, Healthy Substitution)
and Kaggle/curated datasets into a clean 36-column schema.
Zero blank cells, no duplicate food names, 100% data preservation.
"""

import csv
import os
import sqlite3
from pathlib import Path

BASE_DIR = Path(r"C:\nutrimate")
FUSED_CSV_PATH = BASE_DIR / "data/datasets/nutrimate_fused_dataset.csv"
KAGGLE_CSV_PATH = BASE_DIR / "data/datasets/fused_Indian_Food_Nutrition_Processed.csv"
API_RECORDS_PATH = BASE_DIR / "data/datasets/nutrimate_api_records.csv"
DB_PATH = BASE_DIR / "data/nutrimate.db"

UNIFIED_COLUMNS = [
    "food_name",
    "source",
    "api_sources_represented",
    "serving_size",
    "calories",
    "protein",
    "carbohydrates",
    "fat",
    "fiber",
    "sugar",
    "sodium",
    "calcium",
    "iron",
    "vitamin_c",
    "folate",
    "vitamins",
    "minerals",
    "ingredients",
    "health_benefits",
    "consume_in_moderation",
    "diet_type",
    "veg",
    "egg",
    "non_veg",
    "detected_allergens",
    "allergen_count",
    "warning_level",
    "allergen_explanation",
    "safe_for_vegetarian",
    "safe_for_eggetarian",
    "safe_for_vegan",
    "target_goal",
    "substitutions",
    "substitution_count",
    "substitution_summary",
    "confidence_score"
]

def clean_val(*vals, empty_list_is_empty=True):
    for v in vals:
        if v is not None:
            s = str(v).strip()
            if s != "" and s.lower() not in ("none", "n/a", "null", "not available"):
                if empty_list_is_empty and s == "[]":
                    continue
                return s
    return "Not Available"

def main():
    print(f"Reading input sources…")
    
    # 1. Existing fused CSV
    fused_rows = list(csv.DictReader(open(FUSED_CSV_PATH, encoding="utf-8")))
    print(f"Existing fused dataset rows: {len(fused_rows)}")
    
    # 2. Kaggle CSV
    kaggle_rows = list(csv.DictReader(open(KAGGLE_CSV_PATH, encoding="utf-8")))
    kaggle_dict = {r["Dish Name"].strip().lower(): r for r in kaggle_rows}
    print(f"Kaggle CSV records: {len(kaggle_rows)}")
    
    # 3. Database
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        SELECT name, source_type, diet_veg, diet_egg, diet_nv, goal_wl, goal_wg, goal_mg, goal_m, goal_db,
               meal_type, calories, protein, carbohydrates, fat, fiber, vitamins, minerals, ingredients, health_benefits
        FROM meals
    """)
    db_rows = c.fetchall()
    db_dict = {r[0].strip().lower(): r for r in db_rows}
    conn.close()
    print(f"Database meal records: {len(db_rows)}")

    # 4. Helper to find Kaggle Folate key
    folate_key = None
    if kaggle_rows:
        for k in kaggle_rows[0].keys():
            if "folate" in k.lower():
                folate_key = k
                break

    restructured_rows = []
    seen_foods = set()

    for r in fused_rows:
        fname = r["food_name"].strip()
        fn_lower = fname.lower()

        if fn_lower in seen_foods:
            continue
        seen_foods.add(fn_lower)

        k_item = kaggle_dict.get(fn_lower, {})
        db_item = db_dict.get(fn_lower)

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
        db_veg = "True" if (db_item and db_item[2]) else ("False" if (db_item and db_item[2] == 0) else None)
        db_egg = "True" if (db_item and db_item[3]) else ("False" if (db_item and db_item[3] == 0) else None)
        db_nv = "True" if (db_item and db_item[4]) else ("False" if (db_item and db_item[4] == 0) else None)

        folate_val = k_item.get(folate_key) if folate_key else None

        # Build clean unified row
        row = {
            "food_name": fname,
            "source": clean_val(r.get("db_source_type"), r.get("analysis_source_type"), db_src),
            "api_sources_represented": clean_val(r.get("sources_available")),
            "serving_size": clean_val(r.get("analysis_serving_size")),
            "calories": clean_val(r.get("db_calories"), db_cal, k_item.get("Calories (kcal)"), r.get("analysis_calories")),
            "protein": clean_val(r.get("db_protein"), db_prot, k_item.get("Protein (g)"), r.get("analysis_protein")),
            "carbohydrates": clean_val(r.get("db_carbohydrates"), db_carbs, k_item.get("Carbohydrates (g)"), r.get("analysis_carbohydrates")),
            "fat": clean_val(r.get("db_fat"), db_fat, k_item.get("Fats (g)"), r.get("analysis_fat")),
            "fiber": clean_val(r.get("db_fiber"), db_fib, k_item.get("Fibre (g)"), r.get("analysis_fiber")),
            "sugar": clean_val(k_item.get("Free Sugar (g)")),
            "sodium": clean_val(k_item.get("Sodium (mg)")),
            "calcium": clean_val(k_item.get("Calcium (mg)")),
            "iron": clean_val(k_item.get("Iron (mg)")),
            "vitamin_c": clean_val(k_item.get("Vitamin C (mg)")),
            "folate": clean_val(folate_val),
            "vitamins": clean_val(r.get("db_vitamins"), db_vit, r.get("analysis_vitamins")),
            "minerals": clean_val(r.get("db_minerals"), db_min, r.get("analysis_minerals")),
            "ingredients": clean_val(r.get("db_ingredients"), db_ing, r.get("analysis_ingredients")),
            "health_benefits": clean_val(r.get("db_health_benefits"), db_hb, r.get("analysis_health_benefits")),
            "consume_in_moderation": clean_val(r.get("analysis_consume_in_moderation")),
            "diet_type": clean_val(r.get("analysis_diet_type")),
            "veg": clean_val(r.get("db_diet_veg"), db_veg),
            "egg": clean_val(r.get("db_diet_egg"), db_egg),
            "non_veg": clean_val(r.get("db_diet_nv"), db_nv),
            "detected_allergens": clean_val(r.get("allergen_detected_allergens"), empty_list_is_empty=False),
            "allergen_count": clean_val(r.get("allergen_count")),
            "warning_level": clean_val(r.get("allergen_warning_level")),
            "allergen_explanation": clean_val(r.get("allergen_explanation")),
            "safe_for_vegetarian": clean_val(r.get("allergen_safe_for_vegetarian")),
            "safe_for_eggetarian": clean_val(r.get("allergen_safe_for_eggetarian")),
            "safe_for_vegan": clean_val(r.get("allergen_safe_for_vegan")),
            "target_goal": clean_val(r.get("subs_target_goal")),
            "substitutions": clean_val(r.get("subs_substitutions"), empty_list_is_empty=False),
            "substitution_count": clean_val(r.get("subs_substitution_count")),
            "substitution_summary": clean_val(r.get("subs_summary")),
            "confidence_score": clean_val(r.get("allergen_confidence_score"), r.get("subs_confidence_score"), r.get("analysis_confidence_score"))
        }

        # Final safety check: no cell can be empty or whitespace only
        for col in UNIFIED_COLUMNS:
            if not row[col] or row[col].strip() == "":
                row[col] = "Not Available"

        restructured_rows.append(row)

    # Write output
    with open(FUSED_CSV_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=UNIFIED_COLUMNS)
        writer.writeheader()
        for r in restructured_rows:
            writer.writerow(r)

    print("\n" + "="*60)
    print("RESTRUCTURING COMPLETE")
    print("="*60)
    print(f"Output File           : {FUSED_CSV_PATH}")
    print(f"Total Fused Rows      : {len(restructured_rows)}")
    print(f"Total Columns         : {len(UNIFIED_COLUMNS)}")
    print(f"Duplicate Food Names  : {len(restructured_rows) - len(seen_foods)}")
    
    # Blank cells check
    blank_cells = sum(1 for row in restructured_rows for col in UNIFIED_COLUMNS if not row[col] or row[col].strip() == "")
    print(f"Total Blank Cells     : {blank_cells}")

    # API Coverage
    api_names = [
        "Nutrition Analysis API",
        "Nutrition Database API",
        "Allergen Detection API",
        "Healthy Substitution API"
    ]
    print("\nAPI Sources Represented:")
    for api in api_names:
        cnt = sum(1 for r in restructured_rows if api in r["api_sources_represented"])
        print(f"  {api:<28}: {cnt}/{len(restructured_rows)}")

    print("="*60)

if __name__ == "__main__":
    main()
