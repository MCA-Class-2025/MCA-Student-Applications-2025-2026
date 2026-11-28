# -*- coding: utf-8 -*-
"""Collect API response dataset synchronously into data/datasets/nutrimate_api_records.csv"""
import csv
import json
import os
import sqlite3
import sys

from fastapi.testclient import TestClient
sys.path.insert(0, os.path.abspath("."))
from backend.main import app

OUT_PATH = os.path.abspath("data/datasets/nutrimate_api_records.csv")
DB_PATH = os.path.abspath("data/nutrimate.db")

print("Target CSV path:", OUT_PATH)

conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

c.execute("SELECT name FROM meals WHERE source_type='curated' ORDER BY id ASC LIMIT 50")
curated_names = [row[0] for row in c.fetchall()]

c.execute("SELECT name FROM meals WHERE source_type!='curated' ORDER BY id ASC LIMIT 50")
other_names = [row[0] for row in c.fetchall()]

food_names = curated_names + other_names
conn.close()

print(f"Selected {len(food_names)} food names from DB.")

client = TestClient(app)

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
succ = 0
fail = 0

for idx, name in enumerate(food_names, 1):
    # 1. Nutrition Analysis
    try:
        r1 = client.post("/api/nutrition/analyze", json={"food_name": name})
        if r1.status_code == 200:
            d1 = r1.json()
            succ += 1
            records.append({
                "food_name": name,
                "api_name": "Nutrition Analysis API",
                "status": "success",
                "status_code": 200,
                "serving_size": d1.get("serving_size", ""),
                "calories": d1.get("calories", ""),
                "protein": d1.get("protein", ""),
                "carbohydrates": d1.get("carbohydrates", ""),
                "fat": d1.get("fat", ""),
                "fiber": d1.get("fiber", ""),
                "vitamins": d1.get("vitamins", ""),
                "minerals": d1.get("minerals", ""),
                "ingredients": json.dumps(d1.get("ingredients", [])),
                "health_benefits": d1.get("health_benefits", ""),
                "consume_in_moderation": d1.get("consume_in_moderation", ""),
                "diet_type": d1.get("diet_type", ""),
                "confidence_score": d1.get("confidence_score", ""),
                "source_type": d1.get("source_type", ""),
                "raw_response_json": json.dumps(d1, ensure_ascii=False)
            })
        else:
            fail += 1
            records.append({
                "food_name": name,
                "api_name": "Nutrition Analysis API",
                "status": "failed",
                "status_code": r1.status_code,
                "raw_response_json": r1.text
            })
    except Exception as e:
        fail += 1
        records.append({
            "food_name": name,
            "api_name": "Nutrition Analysis API",
            "status": "failed",
            "status_code": 500,
            "raw_response_json": str(e)
        })

    # 2. Nutrition Database
    try:
        r2 = client.get(f"/api/foods/{name}")
        if r2.status_code == 200:
            d2 = r2.json()
            succ += 1
            records.append({
                "food_name": name,
                "api_name": "Nutrition Database API",
                "status": "success",
                "status_code": 200,
                "calories": d2.get("calories", ""),
                "protein": d2.get("protein", ""),
                "carbohydrates": d2.get("carbohydrates", ""),
                "fat": d2.get("fat", ""),
                "fiber": d2.get("fiber", ""),
                "vitamins": json.dumps(d2.get("vitamins", [])),
                "minerals": json.dumps(d2.get("minerals", [])),
                "ingredients": json.dumps(d2.get("ingredients", [])),
                "health_benefits": d2.get("health_benefits", ""),
                "diet_veg": d2.get("diet_veg", ""),
                "diet_egg": d2.get("diet_egg", ""),
                "diet_nv": d2.get("diet_nv", ""),
                "source_type": d2.get("source_type", ""),
                "raw_response_json": json.dumps(d2, ensure_ascii=False)
            })
        else:
            fail += 1
            records.append({
                "food_name": name,
                "api_name": "Nutrition Database API",
                "status": "failed",
                "status_code": r2.status_code,
                "raw_response_json": r2.text
            })
    except Exception as e:
        fail += 1
        records.append({
            "food_name": name,
            "api_name": "Nutrition Database API",
            "status": "failed",
            "status_code": 500,
            "raw_response_json": str(e)
        })

    # 3. Allergen Detection
    try:
        r3 = client.post("/api/foods/allergens", json={"food_name": name})
        if r3.status_code == 200:
            d3 = r3.json()
            succ += 1
            records.append({
                "food_name": name,
                "api_name": "Allergen Detection API",
                "status": "success",
                "status_code": 200,
                "detected_allergens": json.dumps(d3.get("detected_allergens", [])),
                "allergen_count": d3.get("allergen_count", 0),
                "warning_level": d3.get("warning_level", ""),
                "explanation": d3.get("explanation", ""),
                "safe_for_vegetarian": d3.get("safe_for_vegetarian", ""),
                "safe_for_eggetarian": d3.get("safe_for_eggetarian", ""),
                "safe_for_vegan": d3.get("safe_for_vegan", ""),
                "confidence_score": d3.get("confidence_score", ""),
                "raw_response_json": json.dumps(d3, ensure_ascii=False)
            })
        else:
            fail += 1
            records.append({
                "food_name": name,
                "api_name": "Allergen Detection API",
                "status": "failed",
                "status_code": r3.status_code,
                "raw_response_json": r3.text
            })
    except Exception as e:
        fail += 1
        records.append({
            "food_name": name,
            "api_name": "Allergen Detection API",
            "status": "failed",
            "status_code": 500,
            "raw_response_json": str(e)
        })

    # 4. Healthy Substitution
    try:
        r4 = client.post("/api/foods/substitutions", json={"food_name": name, "goal": "weight_loss"})
        if r4.status_code == 200:
            d4 = r4.json()
            succ += 1
            records.append({
                "food_name": name,
                "api_name": "Healthy Substitution API",
                "status": "success",
                "status_code": 200,
                "target_goal": d4.get("target_goal", ""),
                "substitutions": json.dumps(d4.get("substitutions", [])),
                "substitution_count": d4.get("substitution_count", 0),
                "summary": d4.get("summary", ""),
                "confidence_score": d4.get("confidence_score", ""),
                "raw_response_json": json.dumps(d4, ensure_ascii=False)
            })
        else:
            fail += 1
            records.append({
                "food_name": name,
                "api_name": "Healthy Substitution API",
                "status": "failed",
                "status_code": r4.status_code,
                "raw_response_json": r4.text
            })
    except Exception as e:
        fail += 1
        records.append({
            "food_name": name,
            "api_name": "Healthy Substitution API",
            "status": "failed",
            "status_code": 500,
            "raw_response_json": str(e)
        })

os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
with open(OUT_PATH, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=columns)
    writer.writeheader()
    for r in records:
        writer.writerow({col: r.get(col, "") for col in columns})

print("="*60)
print(f"WRITTEN TO CSV: {OUT_PATH}")
print(f"Total Records    : {len(records)}")
print(f"Total Columns    : {len(columns)}")
print(f"Successful Calls : {succ}")
print(f"Failed Calls     : {fail}")
print("="*60)
