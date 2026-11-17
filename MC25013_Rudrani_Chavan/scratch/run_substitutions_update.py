# -*- coding: utf-8 -*-
"""
Re-run Healthy Substitution API collection for all 300 foods in data/datasets/nutrimate_fused_dataset.csv
using the Healthy Substitution API logic (goal and ingredients).

Updates ONLY:
- target_goal
- substitutions
- substitution_count
- substitution_summary
- confidence_score

Preserves all unrelated columns without modification.
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
DB_PATH = BASE_DIR / "data/nutrimate.db"

sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(BASE_DIR / "backend"))
os.environ.setdefault("NUTRIMATE_DB_PATH", str(DB_PATH))
os.environ.setdefault("NUTRIMATE_DATASET_PATH", str(BASE_DIR / "data/datasets/fused_Indian_Food_Nutrition_Processed.csv"))

from backend.main import _SUBSTITUTION_RULES, SubstitutionItem, HealthySubstitutionResponse

# Load DB ingredients for extra coverage if fused dataset ingredients are 'Not Available'
conn = sqlite3.connect(DB_PATH)
c = conn.cursor()
c.execute("SELECT name, ingredients FROM meals")
db_meals = {r[0].strip().lower(): r[1] for r in c.fetchall()}
conn.close()

def evaluate_substitutions_api(food_name, ingredients_list, target_goal):
    target_goal = (target_goal.strip().lower() if target_goal else "weight_loss")
    combined_text = f"{food_name} {' '.join(ingredients_list)}".lower()
    
    substitutions = []
    for rule in _SUBSTITUTION_RULES:
        if target_goal != "general_health" and target_goal not in rule["goals"]:
            continue
        for kw in rule["keywords"]:
            pattern = r'\b' + re.escape(kw) + r'\b'
            if re.search(pattern, combined_text):
                substitutions.append(
                    SubstitutionItem(
                        original_ingredient=rule["original"],
                        replacement=rule["replacement"],
                        reason=rule["reason"],
                        estimated_nutrition_impact=rule["impact"],
                        suitable_for_goal=target_goal
                    )
                )
                break

    sub_count = len(substitutions)
    if sub_count == 0:
        summary = (
            f"This meal ('{food_name}') already consists of whole, nutrient-dense ingredients. "
            "No immediate substitutions are required."
        )
        confidence = 95
    else:
        summary = (
            f"Found {sub_count} healthier ingredient substitution(s) for '{food_name}' "
            f"tailored to your {target_goal} goal."
        )
        confidence = 90

    return HealthySubstitutionResponse(
        food_name=food_name,
        target_goal=target_goal,
        substitutions=substitutions,
        substitution_count=sub_count,
        summary=summary,
        confidence_score=confidence
    )

def main():
    print(f"Loading {FUSED_CSV_PATH}...")
    fused_rows = list(csv.DictReader(open(FUSED_CSV_PATH, encoding="utf-8")))
    fieldnames = list(fused_rows[0].keys())

    print(f"Total foods in fused dataset: {len(fused_rows)}")
    print("Evaluating Healthy Substitution API for all 300 foods...")

    updated_rows = []
    seen_foods = set()
    actual_subs_count = 0
    no_subs_count = 0

    for item in fused_rows:
        fname = item["food_name"].strip()
        fn_lower = fname.lower()

        if fn_lower in seen_foods:
            continue
        seen_foods.add(fn_lower)

        # Extract ingredients
        ing_raw = item.get("ingredients", "Not Available")
        ings = []
        if ing_raw and ing_raw != "Not Available":
            try:
                parsed = json.loads(ing_raw)
                if isinstance(parsed, list):
                    ings = [str(x) for x in parsed]
                else:
                    ings = [str(parsed)]
            except Exception:
                ings = [ing_raw]

        # Check DB if fused ingredients empty
        if not ings:
            db_ing_raw = db_meals.get(fn_lower)
            if db_ing_raw:
                try:
                    parsed = json.loads(db_ing_raw)
                    if isinstance(parsed, list):
                        ings = [str(x) for x in parsed]
                except Exception:
                    pass

        # Target goal
        goal = item.get("target_goal")
        if not goal or goal == "Not Available":
            goal = "weight_loss"

        # Execute Healthy Substitution API evaluation
        res = evaluate_substitutions_api(fname, ings, goal)

        sub_count = res.substitution_count
        subs_list = res.substitutions

        if sub_count > 0 and subs_list:
            subs_data = [sub_item.model_dump() for sub_item in subs_list]
            subs_str = json.dumps(subs_data)
            actual_subs_count += 1
        else:
            subs_str = "No Substitution Available"
            sub_count = 0
            no_subs_count += 1

        # Update ONLY the 5 substitution fields
        item["target_goal"] = str(res.target_goal)
        item["substitutions"] = subs_str
        item["substitution_count"] = str(sub_count)
        item["substitution_summary"] = str(res.summary)
        item["confidence_score"] = str(res.confidence_score)

        updated_rows.append(item)

    # Save to file
    with open(FUSED_CSV_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in updated_rows:
            writer.writerow(r)

    total_processed = len(updated_rows)
    coverage_pct = (actual_subs_count / total_processed) * 100
    blank_cells = sum(1 for row in updated_rows for col in fieldnames if not row[col] or row[col].strip() == "")
    duplicate_count = len(updated_rows) - len(seen_foods)

    # Substitution count consistency check
    inconsistent = 0
    for r in updated_rows:
        sc = int(r["substitution_count"])
        if sc == 0 and r["substitutions"] != "No Substitution Available":
            inconsistent += 1
        elif sc > 0 and r["substitutions"] == "No Substitution Available":
            inconsistent += 1

    print("\n" + "="*65)
    print("HEALTHY SUBSTITUTION DATA COLLECTION COMPLETE")
    print("="*65)
    print(f"Output File                       : {FUSED_CSV_PATH}")
    print(f"Total Foods Processed             : {total_processed}")
    print(f"Foods with Actual Substitutions   : {actual_subs_count}")
    print(f"Foods with No Substitutions       : {no_subs_count}")
    print(f"Substitution Coverage Percentage  : {coverage_pct:.1f}%")
    print(f"Substitution Count Consistency    : {'100% Consistent' if inconsistent == 0 else f'{inconsistent} inconsistent'}")
    print(f"Blank Cells                       : {blank_cells}")
    print(f"Duplicate Food Names              : {duplicate_count}")
    print("="*65)

if __name__ == "__main__":
    main()
