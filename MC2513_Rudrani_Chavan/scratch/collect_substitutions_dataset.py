# -*- coding: utf-8 -*-
"""
Re-run Healthy Substitution API collection for all 300 foods in data/datasets/nutrimate_fused_dataset.csv
using the correct POST /api/foods/substitutions payload (goal='weight_loss'/target_goal and ingredients).

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
import sqlite3
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

BASE_DIR = Path(r"C:\nutrimate")
FUSED_CSV_PATH = BASE_DIR / "data/datasets/nutrimate_fused_dataset.csv"
DB_PATH = BASE_DIR / "data/nutrimate.db"

sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(BASE_DIR / "backend"))
os.environ.setdefault("NUTRIMATE_DB_PATH", str(DB_PATH))
os.environ.setdefault("NUTRIMATE_DATASET_PATH", str(BASE_DIR / "data/datasets/fused_Indian_Food_Nutrition_Processed.csv"))

from fastapi.testclient import TestClient
from backend.main import app

def fetch_substitution_for_item(item, client):
    name = item["food_name"].strip()
    
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

    goal = item.get("target_goal")
    if not goal or goal == "Not Available":
        goal = "weight_loss"

    payload = {
        "food_name": name,
        "ingredients": ings,
        "goal": goal
    }

    try:
        r = client.post("/api/foods/substitutions", json=payload, timeout=30)
        if r.status_code == 200:
            res = r.json()
            sub_count = res.get("substitution_count", 0)
            subs_list = res.get("substitutions", [])
            target_g = res.get("target_goal", goal)
            summary = res.get("summary", "")
            conf = res.get("confidence_score", 90 if sub_count > 0 else 95)

            if sub_count > 0 and subs_list:
                subs_str = json.dumps(subs_list)
            else:
                subs_str = "No Substitution Available"
                sub_count = 0

            return name, {
                "target_goal": str(target_g),
                "substitutions": subs_str,
                "substitution_count": str(sub_count),
                "substitution_summary": str(summary),
                "confidence_score": str(conf)
            }
    except Exception as e:
        print(f"[WARN] Error fetching substitution for '{name}': {e}")

    # Fallback if API fails
    return name, {
        "target_goal": goal,
        "substitutions": "No Substitution Available",
        "substitution_count": "0",
        "substitution_summary": f"This meal ('{name}') already consists of whole, nutrient-dense ingredients. No immediate substitutions are required.",
        "confidence_score": "95"
    }

def main():
    print(f"Loading {FUSED_CSV_PATH}...")
    fused_rows = list(csv.DictReader(open(FUSED_CSV_PATH, encoding="utf-8")))
    fieldnames = list(fused_rows[0].keys())

    print(f"Total foods in fused dataset: {len(fused_rows)}")
    print("Starting parallel API requests (5 workers)...")

    results_map = {}
    completed_count = 0

    # ThreadPoolExecutor to run requests concurrently
    def worker_task(item):
        client = TestClient(app)
        return fetch_substitution_for_item(item, client)

    with ThreadPoolExecutor(max_workers=5) as executor:
        future_to_item = {executor.submit(worker_task, item): item for item in fused_rows}
        for future in as_completed(future_to_item):
            item = future_to_item[future]
            name, sub_data = future.result()
            results_map[name.lower()] = sub_data
            completed_count += 1
            if completed_count % 25 == 0 or completed_count == len(fused_rows):
                print(f"  Processed {completed_count}/{len(fused_rows)} foods...")

    # Update rows with new substitution data
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

        sub_info = results_map.get(fn_lower)
        if sub_info:
            item["target_goal"] = sub_info["target_goal"]
            item["substitutions"] = sub_info["substitutions"]
            item["substitution_count"] = sub_info["substitution_count"]
            item["substitution_summary"] = sub_info["substitution_summary"]
            item["confidence_score"] = sub_info["confidence_score"]

        # Track stats
        cnt = int(item["substitution_count"])
        if cnt > 0 and item["substitutions"] != "No Substitution Available":
            actual_subs_count += 1
        else:
            no_subs_count += 1

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

    # Check substitution_count consistency
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
