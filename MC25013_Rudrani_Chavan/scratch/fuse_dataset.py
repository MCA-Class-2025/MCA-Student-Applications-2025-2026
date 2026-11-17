# -*- coding: utf-8 -*-
"""
Task 3: Create NutriMate Fused Dataset
Pivots nutrimate_api_records.csv (4 rows per food) into ONE row per food.
Each source API gets prefixed columns so data origin is always traceable.
Output: data/datasets/nutrimate_fused_dataset.csv
"""

import csv
import json
import os
import sys
from collections import defaultdict

INPUT_CSV  = os.path.abspath("data/datasets/nutrimate_api_records.csv")
OUTPUT_CSV = os.path.abspath("data/datasets/nutrimate_fused_dataset.csv")

# ── Column definitions with source prefixes ────────────────────────────
FUSED_COLUMNS = [
    # Identity
    "food_name",
    "sources_available",

    # ── Nutrition Analysis API columns ────────────────────────────────
    "analysis_status",
    "analysis_serving_size",
    "analysis_calories",
    "analysis_protein",
    "analysis_carbohydrates",
    "analysis_fat",
    "analysis_fiber",
    "analysis_vitamins",
    "analysis_minerals",
    "analysis_ingredients",
    "analysis_health_benefits",
    "analysis_consume_in_moderation",
    "analysis_diet_type",
    "analysis_confidence_score",
    "analysis_source_type",

    # ── Nutrition Database API columns ─────────────────────────────────
    "db_status",
    "db_calories",
    "db_protein",
    "db_carbohydrates",
    "db_fat",
    "db_fiber",
    "db_vitamins",
    "db_minerals",
    "db_ingredients",
    "db_health_benefits",
    "db_diet_veg",
    "db_diet_egg",
    "db_diet_nv",
    "db_source_type",

    # ── Allergen Detection API columns ─────────────────────────────────
    "allergen_status",
    "allergen_detected_allergens",
    "allergen_count",
    "allergen_warning_level",
    "allergen_explanation",
    "allergen_safe_for_vegetarian",
    "allergen_safe_for_eggetarian",
    "allergen_safe_for_vegan",
    "allergen_confidence_score",

    # ── Healthy Substitution API columns ───────────────────────────────
    "subs_status",
    "subs_target_goal",
    "subs_substitutions",
    "subs_substitution_count",
    "subs_summary",
    "subs_confidence_score",
]


def safe(v):
    """Return value or empty string — never invent data."""
    if v is None:
        return ""
    s = str(v).strip()
    # Treat placeholder strings as empty (not invented data)
    if s.lower() in ("not available", "none", "n/a"):
        return ""
    return s


def fuse_records(rows_by_api):
    """Merge 4 API rows for a single food into one fused dict."""
    row = {}

    # ── Nutrition Analysis API ────────────────────────────────────────
    a = rows_by_api.get("Nutrition Analysis API", {})
    row["analysis_status"]                 = safe(a.get("status"))
    row["analysis_serving_size"]           = safe(a.get("serving_size"))
    row["analysis_calories"]               = safe(a.get("calories"))
    row["analysis_protein"]                = safe(a.get("protein"))
    row["analysis_carbohydrates"]          = safe(a.get("carbohydrates"))
    row["analysis_fat"]                    = safe(a.get("fat"))
    row["analysis_fiber"]                  = safe(a.get("fiber"))
    row["analysis_vitamins"]               = safe(a.get("vitamins"))
    row["analysis_minerals"]               = safe(a.get("minerals"))
    row["analysis_ingredients"]            = safe(a.get("ingredients"))
    row["analysis_health_benefits"]        = safe(a.get("health_benefits"))
    row["analysis_consume_in_moderation"]  = safe(a.get("consume_in_moderation"))
    row["analysis_diet_type"]              = safe(a.get("diet_type"))
    row["analysis_confidence_score"]       = safe(a.get("confidence_score"))
    row["analysis_source_type"]            = safe(a.get("source_type"))

    # ── Nutrition Database API ─────────────────────────────────────────
    d = rows_by_api.get("Nutrition Database API", {})
    row["db_status"]           = safe(d.get("status"))
    row["db_calories"]         = safe(d.get("calories"))
    row["db_protein"]          = safe(d.get("protein"))
    row["db_carbohydrates"]    = safe(d.get("carbohydrates"))
    row["db_fat"]              = safe(d.get("fat"))
    row["db_fiber"]            = safe(d.get("fiber"))
    row["db_vitamins"]         = safe(d.get("vitamins"))
    row["db_minerals"]         = safe(d.get("minerals"))
    row["db_ingredients"]      = safe(d.get("ingredients"))
    row["db_health_benefits"]  = safe(d.get("health_benefits"))
    row["db_diet_veg"]         = safe(d.get("diet_veg"))
    row["db_diet_egg"]         = safe(d.get("diet_egg"))
    row["db_diet_nv"]          = safe(d.get("diet_nv"))
    row["db_source_type"]      = safe(d.get("source_type"))

    # ── Allergen Detection API ─────────────────────────────────────────
    al = rows_by_api.get("Allergen Detection API", {})
    row["allergen_status"]               = safe(al.get("status"))
    row["allergen_detected_allergens"]   = safe(al.get("detected_allergens"))
    row["allergen_count"]                = safe(al.get("allergen_count"))
    row["allergen_warning_level"]        = safe(al.get("warning_level"))
    row["allergen_explanation"]          = safe(al.get("explanation"))
    row["allergen_safe_for_vegetarian"]  = safe(al.get("safe_for_vegetarian"))
    row["allergen_safe_for_eggetarian"]  = safe(al.get("safe_for_eggetarian"))
    row["allergen_safe_for_vegan"]       = safe(al.get("safe_for_vegan"))
    row["allergen_confidence_score"]     = safe(al.get("confidence_score"))

    # ── Healthy Substitution API ───────────────────────────────────────
    sb = rows_by_api.get("Healthy Substitution API", {})
    row["subs_status"]              = safe(sb.get("status"))
    row["subs_target_goal"]         = safe(sb.get("target_goal"))
    row["subs_substitutions"]       = safe(sb.get("substitutions"))
    row["subs_substitution_count"]  = safe(sb.get("substitution_count"))
    row["subs_summary"]             = safe(sb.get("summary"))
    row["subs_confidence_score"]    = safe(sb.get("confidence_score"))

    # sources_available: which APIs returned status=success
    sources = [
        api for api in [
            "Nutrition Analysis API",
            "Nutrition Database API",
            "Allergen Detection API",
            "Healthy Substitution API"
        ]
        if rows_by_api.get(api, {}).get("status") == "success"
    ]
    row["sources_available"] = "|".join(sources)

    return row


def main():
    if not os.path.exists(INPUT_CSV):
        print(f"[ERROR] Input CSV not found: {INPUT_CSV}")
        sys.exit(1)

    # 1. Load all rows from input CSV
    all_rows = []
    with open(INPUT_CSV, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            all_rows.append(r)

    print(f"Loaded {len(all_rows)} rows from {INPUT_CSV}")

    # 2. Group by food_name → then by api_name
    grouped = defaultdict(dict)
    food_order = []  # preserve insertion order of food names
    for row in all_rows:
        food = row["food_name"].strip()
        api  = row["api_name"].strip()
        if food not in grouped:
            food_order.append(food)
        grouped[food][api] = row

    print(f"Unique food names: {len(food_order)}")

    # 3. Check for duplicate food names
    seen = set()
    duplicates = []
    for food in food_order:
        if food in seen:
            duplicates.append(food)
        seen.add(food)
    if duplicates:
        print(f"[WARN] Duplicate food names found: {duplicates}")
    else:
        print("No duplicate food names.")

    # 4. Fuse all records
    fused_rows = []
    for food in food_order:
        rows_by_api = grouped[food]
        row = fuse_records(rows_by_api)
        row["food_name"] = food
        fused_rows.append(row)

    # 5. Analyse missing values
    print("\nMissing value analysis (empty fields per column):")
    missing_counts = {col: 0 for col in FUSED_COLUMNS}
    for row in fused_rows:
        for col in FUSED_COLUMNS:
            if not row.get(col, "").strip():
                missing_counts[col] += 1

    for col, cnt in missing_counts.items():
        if cnt > 0:
            pct = (cnt / len(fused_rows)) * 100
            print(f"  {col}: {cnt}/{len(fused_rows)} missing ({pct:.1f}%)")

    # 6. Write output CSV
    os.makedirs(os.path.dirname(OUTPUT_CSV), exist_ok=True)
    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FUSED_COLUMNS)
        writer.writeheader()
        for row in fused_rows:
            writer.writerow({col: row.get(col, "") for col in FUSED_COLUMNS})

    # 7. Final report
    print("\n" + "="*60)
    print("FUSED DATASET CREATION COMPLETE")
    print("="*60)
    print(f"Output File           : {OUTPUT_CSV}")
    print(f"Total Fused Records   : {len(fused_rows)}")
    print(f"Total Columns         : {len(FUSED_COLUMNS)}")
    print(f"Duplicate Food Names  : {len(duplicates)}")

    # Sources breakdown
    api_labels = [
        "Nutrition Analysis API",
        "Nutrition Database API",
        "Allergen Detection API",
        "Healthy Substitution API"
    ]
    print("\nAPI Sources Represented (rows with status=success):")
    for api in api_labels:
        count = sum(1 for r in fused_rows if api in r.get("sources_available", ""))
        print(f"  {api}: {count}/{len(fused_rows)}")

    total_missing = sum(missing_counts.values())
    total_cells = len(fused_rows) * len(FUSED_COLUMNS)
    print(f"\nTotal Empty Cells     : {total_missing} / {total_cells} ({(total_missing/total_cells)*100:.1f}%)")
    print("="*60)


if __name__ == "__main__":
    main()
