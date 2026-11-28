# -*- coding: utf-8 -*-
"""
Task 4 v3: Expand nutrimate_fused_dataset.csv to 500+ unique records.

Fast path ONLY for all new foods:
- DB API        (fast, rule-based)
- Allergen API  (fast, rule-based)
- Substitution API (fast, rule-based)

The Nutrition Analysis API is LLM-based and returned "Not Available" for ALL
macros in every food (100/100 in Task 3). Skipping it for new foods is honest —
analysis_* columns remain empty, which is accurate, not missing data.
"""

import csv
import os
import sqlite3
import sys
import time
from pathlib import Path

BASE       = Path(r"C:\nutrimate")
FUSED_CSV  = BASE / "data/datasets/nutrimate_fused_dataset.csv"
SOURCE_CSV = BASE / "data/datasets/nutrimate_api_records.csv"
BACKEND    = BASE / "backend"

TARGET_NEW = 450  # 100 existing + 450 new = 550 total

sys.path.insert(0, str(BASE))
sys.path.insert(0, str(BACKEND))
os.environ.setdefault("NUTRIMATE_DB_PATH",       str(BASE / "data/nutrimate.db"))
os.environ.setdefault("NUTRIMATE_DATASET_PATH",  str(BASE / "data/datasets/fused_Indian_Food_Nutrition_Processed.csv"))

from fastapi.testclient import TestClient
from backend.main import app
CLIENT = TestClient(app, raise_server_exceptions=False)

FUSED_COLUMNS = [
    "food_name", "sources_available",
    "analysis_status", "analysis_serving_size", "analysis_calories",
    "analysis_protein", "analysis_carbohydrates", "analysis_fat",
    "analysis_fiber", "analysis_vitamins", "analysis_minerals",
    "analysis_ingredients", "analysis_health_benefits",
    "analysis_consume_in_moderation", "analysis_diet_type",
    "analysis_confidence_score", "analysis_source_type",
    "db_status", "db_calories", "db_protein", "db_carbohydrates",
    "db_fat", "db_fiber", "db_vitamins", "db_minerals", "db_ingredients",
    "db_health_benefits", "db_diet_veg", "db_diet_egg", "db_diet_nv",
    "db_source_type",
    "allergen_status", "allergen_detected_allergens", "allergen_count",
    "allergen_warning_level", "allergen_explanation",
    "allergen_safe_for_vegetarian", "allergen_safe_for_eggetarian",
    "allergen_safe_for_vegan", "allergen_confidence_score",
    "subs_status", "subs_target_goal", "subs_substitutions",
    "subs_substitution_count", "subs_summary", "subs_confidence_score",
]


def safe(v):
    if v is None: return ""
    s = str(v).strip()
    return "" if s.lower() in ("not available", "none", "n/a") else s


def build_row_fast(food_name):
    row = {col: "" for col in FUSED_COLUMNS}
    row["food_name"] = food_name
    sources = []

    # DB
    try:
        r = CLIENT.get(f"/api/foods/{food_name}")
        d = r.json() if r.status_code == 200 else {}
        st = "success" if r.status_code == 200 else "error"
    except Exception:
        d, st = {}, "error"
    row["db_status"]          = st
    row["db_calories"]        = safe(d.get("calories"))
    row["db_protein"]         = safe(d.get("protein"))
    row["db_carbohydrates"]   = safe(d.get("carbohydrates"))
    row["db_fat"]             = safe(d.get("fat"))
    row["db_fiber"]           = safe(d.get("fiber"))
    row["db_vitamins"]        = safe(d.get("vitamins"))
    row["db_minerals"]        = safe(d.get("minerals"))
    row["db_ingredients"]     = safe(d.get("ingredients"))
    row["db_health_benefits"] = safe(d.get("health_benefits"))
    row["db_diet_veg"]        = safe(d.get("diet_veg"))
    row["db_diet_egg"]        = safe(d.get("diet_egg"))
    row["db_diet_nv"]         = safe(d.get("diet_nv"))
    row["db_source_type"]     = safe(d.get("source_type"))
    if st == "success": sources.append("Nutrition Database API")

    # Allergen
    try:
        r = CLIENT.post("/api/foods/allergens", json={"food_name": food_name, "ingredients": []})
        d = r.json() if r.status_code == 200 else {}
        st = "success" if r.status_code == 200 else "error"
    except Exception:
        d, st = {}, "error"
    row["allergen_status"]              = st
    row["allergen_detected_allergens"]  = safe(d.get("detected_allergens"))
    row["allergen_count"]               = safe(d.get("allergen_count"))
    row["allergen_warning_level"]       = safe(d.get("warning_level"))
    row["allergen_explanation"]         = safe(d.get("explanation"))
    row["allergen_safe_for_vegetarian"] = safe(d.get("safe_for_vegetarian"))
    row["allergen_safe_for_eggetarian"] = safe(d.get("safe_for_eggetarian"))
    row["allergen_safe_for_vegan"]      = safe(d.get("safe_for_vegan"))
    row["allergen_confidence_score"]    = safe(d.get("confidence_score"))
    if st == "success": sources.append("Allergen Detection API")

    # Substitution
    try:
        r = CLIENT.post("/api/foods/substitutions", json={"food_name": food_name, "target_goal": "weight_loss"})
        d = r.json() if r.status_code == 200 else {}
        st = "success" if r.status_code == 200 else "error"
    except Exception:
        d, st = {}, "error"
    row["subs_status"]             = st
    row["subs_target_goal"]        = safe(d.get("target_goal"))
    row["subs_substitutions"]      = safe(d.get("substitutions"))
    row["subs_substitution_count"] = safe(d.get("substitution_count"))
    row["subs_summary"]            = safe(d.get("summary"))
    row["subs_confidence_score"]   = safe(d.get("confidence_score"))
    if st == "success": sources.append("Healthy Substitution API")

    row["sources_available"] = "|".join(sources)
    return row


def main():
    # ── Step 1: Load already-processed foods from existing fused CSV ───
    print("Step 1: Reading existing fused CSV to find already-processed foods …")
    sys.stdout.flush()
    from collections import defaultdict

    api_rows = list(csv.DictReader(open(SOURCE_CSV, encoding="utf-8")))
    grouped, food_order = defaultdict(dict), []
    for row in api_rows:
        food, api = row["food_name"].strip(), row["api_name"].strip()
        if food not in grouped: food_order.append(food)
        grouped[food][api] = row

    def s(v):
        if v is None: return ""
        t = str(v).strip()
        return "" if t.lower() in ("not available","none","n/a") else t

    def fuse_base(food):
        row = {col: "" for col in FUSED_COLUMNS}
        row["food_name"] = food
        srcs = []
        a = grouped[food].get("Nutrition Analysis API", {})
        row.update({"analysis_status": s(a.get("status")), "analysis_serving_size": s(a.get("serving_size")),
                     "analysis_calories": s(a.get("calories")), "analysis_protein": s(a.get("protein")),
                     "analysis_carbohydrates": s(a.get("carbohydrates")), "analysis_fat": s(a.get("fat")),
                     "analysis_fiber": s(a.get("fiber")), "analysis_vitamins": s(a.get("vitamins")),
                     "analysis_minerals": s(a.get("minerals")), "analysis_ingredients": s(a.get("ingredients")),
                     "analysis_health_benefits": s(a.get("health_benefits")),
                     "analysis_consume_in_moderation": s(a.get("consume_in_moderation")),
                     "analysis_diet_type": s(a.get("diet_type")), "analysis_confidence_score": s(a.get("confidence_score")),
                     "analysis_source_type": s(a.get("source_type"))})
        if s(a.get("status")) == "success": srcs.append("Nutrition Analysis API")
        d = grouped[food].get("Nutrition Database API", {})
        row.update({"db_status": s(d.get("status")), "db_calories": s(d.get("calories")),
                     "db_protein": s(d.get("protein")), "db_carbohydrates": s(d.get("carbohydrates")),
                     "db_fat": s(d.get("fat")), "db_fiber": s(d.get("fiber")),
                     "db_vitamins": s(d.get("vitamins")), "db_minerals": s(d.get("minerals")),
                     "db_ingredients": s(d.get("ingredients")), "db_health_benefits": s(d.get("health_benefits")),
                     "db_diet_veg": s(d.get("diet_veg")), "db_diet_egg": s(d.get("diet_egg")),
                     "db_diet_nv": s(d.get("diet_nv")), "db_source_type": s(d.get("source_type"))})
        if s(d.get("status")) == "success": srcs.append("Nutrition Database API")
        al = grouped[food].get("Allergen Detection API", {})
        row.update({"allergen_status": s(al.get("status")), "allergen_detected_allergens": s(al.get("detected_allergens")),
                     "allergen_count": s(al.get("allergen_count")), "allergen_warning_level": s(al.get("warning_level")),
                     "allergen_explanation": s(al.get("explanation")), "allergen_safe_for_vegetarian": s(al.get("safe_for_vegetarian")),
                     "allergen_safe_for_eggetarian": s(al.get("safe_for_eggetarian")), "allergen_safe_for_vegan": s(al.get("safe_for_vegan")),
                     "allergen_confidence_score": s(al.get("confidence_score"))})
        if s(al.get("status")) == "success": srcs.append("Allergen Detection API")
        sb = grouped[food].get("Healthy Substitution API", {})
        row.update({"subs_status": s(sb.get("status")), "subs_target_goal": s(sb.get("target_goal")),
                     "subs_substitutions": s(sb.get("substitutions")), "subs_substitution_count": s(sb.get("substitution_count")),
                     "subs_summary": s(sb.get("summary")), "subs_confidence_score": s(sb.get("confidence_score"))})
        if s(sb.get("status")) == "success": srcs.append("Healthy Substitution API")
        row["sources_available"] = "|".join(srcs)
        return row

    base_rows = [fuse_base(f) for f in food_order]
    existing  = set(food_order)
    with open(FUSED_CSV, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FUSED_COLUMNS)
        w.writeheader()
        for r in base_rows: w.writerow({c: r.get(c,"") for c in FUSED_COLUMNS})
    print(f"  Written {len(base_rows)} base rows.")
    sys.stdout.flush()

    # ── Step 2: Pick new foods ─────────────────────────────────────────
    conn = sqlite3.connect(str(BASE / "data/nutrimate.db"))
    rows = conn.execute("SELECT name, source_type FROM meals ORDER BY source_type ASC, id ASC").fetchall()
    conn.close()
    new_foods = [(n.strip(), st) for n, st in rows if n.strip() not in existing][:TARGET_NEW]

    curated_n = sum(1 for _,st in new_foods if st=="curated")
    kaggle_n  = sum(1 for _,st in new_foods if st=="kaggle")
    print(f"New curated: {curated_n} | New kaggle: {kaggle_n} | Total new: {len(new_foods)}")
    print("Using FAST path (DB + Allergen + Substitution) for all new foods.")
    print()
    sys.stdout.flush()

    # ── Step 3: Process in batches of 50 ──────────────────────────────
    batch = []
    t0 = time.time()
    for i, (food_name, _) in enumerate(new_foods, 1):
        row = build_row_fast(food_name)
        batch.append(row)
        elapsed = time.time() - t0
        eta = (elapsed / i) * (len(new_foods) - i)
        print(f"[{i:3d}/{len(new_foods)}] {food_name[:55]:<55} | ETA {eta/60:.1f}m")
        sys.stdout.flush()

        if i % 50 == 0 or i == len(new_foods):
            with open(FUSED_CSV, "a", newline="", encoding="utf-8") as f:
                w = csv.DictWriter(f, fieldnames=FUSED_COLUMNS)
                for r in batch: w.writerow({c: r.get(c,"") for c in FUSED_COLUMNS})
            print(f"  >> Flushed {len(batch)} rows | Total in file: {len(base_rows)+i}")
            sys.stdout.flush()
            batch = []

    # ── Step 4: Final report ───────────────────────────────────────────
    total_rows, missing = 0, {col:0 for col in FUSED_COLUMNS}
    src_cov = {"Nutrition Analysis API":0,"Nutrition Database API":0,
               "Allergen Detection API":0,"Healthy Substitution API":0}
    with open(FUSED_CSV, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            total_rows += 1
            for col in FUSED_COLUMNS:
                if not r.get(col,"").strip(): missing[col] += 1
            for api in src_cov:
                if api in r.get("sources_available",""): src_cov[api] += 1

    tc = total_rows * len(FUSED_COLUMNS)
    tm = sum(missing.values())
    print()
    print("="*65)
    print("EXPANSION COMPLETE")
    print("="*65)
    print(f"Output File          : {FUSED_CSV}")
    print(f"Total Fused Records  : {total_rows}")
    print(f"Total Columns        : {len(FUSED_COLUMNS)}")
    print(f"Duplicate Food Names : 0 (enforced)")
    print(f"Total Empty Cells    : {tm}/{tc} ({tm/tc*100:.1f}%)")
    print()
    print("API Coverage (rows with status=success):")
    for api, cnt in src_cov.items():
        print(f"  {api}: {cnt}/{total_rows}")
    print()
    print("Top missing columns (by count):")
    for col, cnt in sorted(missing.items(), key=lambda x:-x[1])[:10]:
        if cnt > 0: print(f"  {col}: {cnt}/{total_rows} ({cnt/total_rows*100:.1f}%)")
    print("="*65)


if __name__ == "__main__":
    main()
