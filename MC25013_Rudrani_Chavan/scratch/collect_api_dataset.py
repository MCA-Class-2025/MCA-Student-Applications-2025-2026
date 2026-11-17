# -*- coding: utf-8 -*-
"""
Script to collect actual API responses from NutriMate's 4 core APIs
for 100 food items from the SQLite database and write to
data/datasets/nutrimate_api_records.csv
"""

import csv
import json
import os
import sqlite3
import sys

# Ensure root is in path
sys.path.insert(0, os.path.abspath("."))

from fastapi.testclient import TestClient
from backend.main import app

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "data", "nutrimate.db")
OUTPUT_CSV = os.path.join(BASE_DIR, "data", "datasets", "nutrimate_api_records.csv")

def collect_api_data():
    if not os.path.exists(DB_PATH):
        print(f"[ERROR] Database not found at {DB_PATH}")
        sys.exit(1)

    # 1. Fetch 100 distinct food names from database (mix of curated and kaggle)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Select 50 curated first, then fill up to 100 with kaggle entries
    c.execute("SELECT name FROM meals WHERE source_type='curated' ORDER BY id ASC LIMIT 50")
    curated_names = [row[0] for row in c.fetchall()]
    
    remaining_needed = 100 - len(curated_names)
    c.execute(f"SELECT name FROM meals WHERE source_type!='curated' ORDER BY id ASC LIMIT {remaining_needed}")
    other_names = [row[0] for row in c.fetchall()]
    
    food_names = curated_names + other_names
    conn.close()

    print(f"Loaded {len(food_names)} food names from database ({len(curated_names)} curated, {len(other_names)} kaggle/api).")

    # 2. Setup FastAPI TestClient
    client = TestClient(app)

    # 3. CSV Column Definitions
    columns = [
        "food_name",
        "api_name",
        "status",
        "status_code",
        "serving_size",
        "calories",
        "protein",
        "carbohydrates",
        "fat",
        "fiber",
        "vitamins",
        "minerals",
        "ingredients",
        "health_benefits",
        "consume_in_moderation",
        "diet_type",
        "diet_veg",
        "diet_egg",
        "diet_nv",
        "detected_allergens",
        "allergen_count",
        "warning_level",
        "explanation",
        "safe_for_vegetarian",
        "safe_for_eggetarian",
        "safe_for_vegan",
        "target_goal",
        "substitutions",
        "substitution_count",
        "summary",
        "confidence_score",
        "source_type",
        "raw_response_json"
    ]

    records = []
    success_count = 0
    fail_count = 0

    print("Beginning API response collection across 4 endpoints...")

    for idx, name in enumerate(food_names, 1):
        print(f"[{idx:03d}/100] Processing food: '{name}'")

        # ── API 1: Nutrition Analysis ──────────────────────────────────
        try:
            r1 = client.post("/api/nutrition/analyze", json={"food_name": name})
            if r1.status_code == 200:
                data1 = r1.json()
                success_count += 1
                records.append({
                    "food_name": name,
                    "api_name": "Nutrition Analysis API",
                    "status": "success",
                    "status_code": 200,
                    "serving_size": data1.get("serving_size", ""),
                    "calories": data1.get("calories", ""),
                    "protein": data1.get("protein", ""),
                    "carbohydrates": data1.get("carbohydrates", ""),
                    "fat": data1.get("fat", ""),
                    "fiber": data1.get("fiber", ""),
                    "vitamins": data1.get("vitamins", ""),
                    "minerals": data1.get("minerals", ""),
                    "ingredients": json.dumps(data1.get("ingredients", [])),
                    "health_benefits": data1.get("health_benefits", ""),
                    "consume_in_moderation": data1.get("consume_in_moderation", ""),
                    "diet_type": data1.get("diet_type", ""),
                    "confidence_score": data1.get("confidence_score", ""),
                    "source_type": data1.get("source_type", ""),
                    "raw_response_json": json.dumps(data1, ensure_ascii=False)
                })
            else:
                fail_count += 1
                records.append({
                    "food_name": name,
                    "api_name": "Nutrition Analysis API",
                    "status": "failed",
                    "status_code": r1.status_code,
                    "raw_response_json": r1.text
                })
        except Exception as e:
            fail_count += 1
            records.append({
                "food_name": name,
                "api_name": "Nutrition Analysis API",
                "status": "failed",
                "status_code": 500,
                "raw_response_json": str(e)
            })

        # ── API 2: Nutrition Database ──────────────────────────────────
        try:
            r2 = client.get(f"/api/foods/{name}")
            if r2.status_code == 200:
                data2 = r2.json()
                success_count += 1
                records.append({
                    "food_name": name,
                    "api_name": "Nutrition Database API",
                    "status": "success",
                    "status_code": 200,
                    "calories": data2.get("calories", ""),
                    "protein": data2.get("protein", ""),
                    "carbohydrates": data2.get("carbohydrates", ""),
                    "fat": data2.get("fat", ""),
                    "fiber": data2.get("fiber", ""),
                    "vitamins": json.dumps(data2.get("vitamins", [])),
                    "minerals": json.dumps(data2.get("minerals", [])),
                    "ingredients": json.dumps(data2.get("ingredients", [])),
                    "health_benefits": data2.get("health_benefits", ""),
                    "diet_veg": data2.get("diet_veg", ""),
                    "diet_egg": data2.get("diet_egg", ""),
                    "diet_nv": data2.get("diet_nv", ""),
                    "source_type": data2.get("source_type", ""),
                    "raw_response_json": json.dumps(data2, ensure_ascii=False)
                })
            else:
                fail_count += 1
                records.append({
                    "food_name": name,
                    "api_name": "Nutrition Database API",
                    "status": "failed",
                    "status_code": r2.status_code,
                    "raw_response_json": r2.text
                })
        except Exception as e:
            fail_count += 1
            records.append({
                "food_name": name,
                "api_name": "Nutrition Database API",
                "status": "failed",
                "status_code": 500,
                "raw_response_json": str(e)
            })

        # ── API 3: Allergen Detection ──────────────────────────────────
        try:
            r3 = client.post("/api/foods/allergens", json={"food_name": name})
            if r3.status_code == 200:
                data3 = r3.json()
                success_count += 1
                records.append({
                    "food_name": name,
                    "api_name": "Allergen Detection API",
                    "status": "success",
                    "status_code": 200,
                    "detected_allergens": json.dumps(data3.get("detected_allergens", [])),
                    "allergen_count": data3.get("allergen_count", 0),
                    "warning_level": data3.get("warning_level", ""),
                    "explanation": data3.get("explanation", ""),
                    "safe_for_vegetarian": data3.get("safe_for_vegetarian", ""),
                    "safe_for_eggetarian": data3.get("safe_for_eggetarian", ""),
                    "safe_for_vegan": data3.get("safe_for_vegan", ""),
                    "confidence_score": data3.get("confidence_score", ""),
                    "raw_response_json": json.dumps(data3, ensure_ascii=False)
                })
            else:
                fail_count += 1
                records.append({
                    "food_name": name,
                    "api_name": "Allergen Detection API",
                    "status": "failed",
                    "status_code": r3.status_code,
                    "raw_response_json": r3.text
                })
        except Exception as e:
            fail_count += 1
            records.append({
                "food_name": name,
                "api_name": "Allergen Detection API",
                "status": "failed",
                "status_code": 500,
                "raw_response_json": str(e)
            })

        # ── API 4: Healthy Substitution ────────────────────────────────
        try:
            r4 = client.post("/api/foods/substitutions", json={"food_name": name, "goal": "weight_loss"})
            if r4.status_code == 200:
                data4 = r4.json()
                success_count += 1
                records.append({
                    "food_name": name,
                    "api_name": "Healthy Substitution API",
                    "status": "success",
                    "status_code": 200,
                    "target_goal": data4.get("target_goal", ""),
                    "substitutions": json.dumps(data4.get("substitutions", [])),
                    "substitution_count": data4.get("substitution_count", 0),
                    "summary": data4.get("summary", ""),
                    "confidence_score": data4.get("confidence_score", ""),
                    "raw_response_json": json.dumps(data4, ensure_ascii=False)
                })
            else:
                fail_count += 1
                records.append({
                    "food_name": name,
                    "api_name": "Healthy Substitution API",
                    "status": "failed",
                    "status_code": r4.status_code,
                    "raw_response_json": r4.text
                })
        except Exception as e:
            fail_count += 1
            records.append({
                "food_name": name,
                "api_name": "Healthy Substitution API",
                "status": "failed",
                "status_code": 500,
                "raw_response_json": str(e)
            })

    # 4. Write output to CSV
    os.makedirs(os.path.dirname(OUTPUT_CSV), exist_ok=True)
    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        for row in records:
            # Ensure all keys in columns are present in row
            full_row = {col: row.get(col, "") for col in columns}
            writer.writerow(full_row)

    print("\n" + "="*60)
    print("API DATASET COLLECTION COMPLETE")
    print("="*60)
    print(f"Output File      : {OUTPUT_CSV}")
    print(f"Total Records    : {len(records)}")
    print(f"Total Columns    : {len(columns)}")
    print(f"Successful Calls : {success_count}")
    print(f"Failed Calls     : {fail_count}")
    print("="*60)

if __name__ == "__main__":
    collect_api_data()
