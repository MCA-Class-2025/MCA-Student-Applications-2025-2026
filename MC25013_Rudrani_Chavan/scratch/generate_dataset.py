# -*- coding: utf-8 -*-
import csv
import json
import os
import sqlite3
import sys
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, os.path.abspath("."))
from fastapi.testclient import TestClient
from backend.main import app

def generate_csv_text():
    db_path = os.path.abspath("data/nutrimate.db")

    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("SELECT name, ingredients FROM meals WHERE source_type='curated' ORDER BY id ASC LIMIT 50")
    curated = c.fetchall()
    c.execute("SELECT name, ingredients FROM meals WHERE source_type!='curated' ORDER BY id ASC LIMIT 50")
    others = c.fetchall()
    conn.close()

    food_items = curated + others

    client = TestClient(app)

    columns = [
        "food_name", "api_name", "status", "status_code", "serving_size",
        "calories", "protein", "carbohydrates", "fat", "fiber", "vitamins",
        "minerals", "ingredients", "health_benefits", "consume_in_moderation",
        "diet_type", "diet_veg", "diet_egg", "diet_nv", "detected_allergens",
        "allergen_count", "warning_level", "explanation", "safe_for_vegetarian",
        "safe_for_eggetarian", "safe_for_vegan", "target_goal", "substitutions",
        "substitution_count", "summary", "confidence_score", "source_type",
        "raw_response_json"
    ]

    def process_item(item):
        name, raw_ings = item
        try:
            ings = json.loads(raw_ings) if raw_ings else []
        except Exception:
            ings = []

        item_recs = []
        s_count = 0
        f_count = 0

        # 1. Nutrition Analysis API
        r1 = client.post("/api/nutrition/analyze", json={"food_name": name, "ingredients": ings})
        if r1.status_code == 200:
            d1 = r1.json()
            s_count += 1
            item_recs.append({
                "food_name": name, "api_name": "Nutrition Analysis API",
                "status": "success", "status_code": 200,
                "serving_size": d1.get("serving_size", ""), "calories": str(d1.get("calories", "")),
                "protein": str(d1.get("protein", "")), "carbohydrates": str(d1.get("carbohydrates", "")),
                "fat": str(d1.get("fat", "")), "fiber": str(d1.get("fiber", "")),
                "vitamins": str(d1.get("vitamins", "")), "minerals": str(d1.get("minerals", "")),
                "ingredients": json.dumps(d1.get("ingredients", [])), "health_benefits": str(d1.get("health_benefits", "")),
                "consume_in_moderation": str(d1.get("consume_in_moderation", "")), "diet_type": str(d1.get("diet_type", "")),
                "confidence_score": str(d1.get("confidence_score", "")), "source_type": str(d1.get("source_type", "")),
                "raw_response_json": json.dumps(d1, ensure_ascii=False)
            })
        else:
            f_count += 1
            item_recs.append({"food_name": name, "api_name": "Nutrition Analysis API", "status": "failed", "status_code": r1.status_code, "raw_response_json": r1.text})

        # 2. Nutrition Database API
        r2 = client.get(f"/api/foods/{name}")
        if r2.status_code == 200:
            d2 = r2.json()
            s_count += 1
            item_recs.append({
                "food_name": name, "api_name": "Nutrition Database API",
                "status": "success", "status_code": 200,
                "calories": str(d2.get("calories", "")), "protein": str(d2.get("protein", "")),
                "carbohydrates": str(d2.get("carbohydrates", "")), "fat": str(d2.get("fat", "")),
                "fiber": str(d2.get("fiber", "")), "vitamins": json.dumps(d2.get("vitamins", [])),
                "minerals": json.dumps(d2.get("minerals", [])), "ingredients": json.dumps(d2.get("ingredients", [])),
                "health_benefits": str(d2.get("health_benefits", "")), "diet_veg": str(d2.get("diet_veg", "")),
                "diet_egg": str(d2.get("diet_egg", "")), "diet_nv": str(d2.get("diet_nv", "")),
                "source_type": str(d2.get("source_type", "")),
                "raw_response_json": json.dumps(d2, ensure_ascii=False)
            })
        else:
            f_count += 1
            item_recs.append({"food_name": name, "api_name": "Nutrition Database API", "status": "failed", "status_code": r2.status_code, "raw_response_json": r2.text})

        # 3. Allergen Detection API
        r3 = client.post("/api/foods/allergens", json={"food_name": name, "ingredients": ings})
        if r3.status_code == 200:
            d3 = r3.json()
            s_count += 1
            item_recs.append({
                "food_name": name, "api_name": "Allergen Detection API",
                "status": "success", "status_code": 200,
                "detected_allergens": json.dumps(d3.get("detected_allergens", [])),
                "allergen_count": str(d3.get("allergen_count", 0)), "warning_level": str(d3.get("warning_level", "")),
                "explanation": str(d3.get("explanation", "")), "safe_for_vegetarian": str(d3.get("safe_for_vegetarian", "")),
                "safe_for_eggetarian": str(d3.get("safe_for_eggetarian", "")), "safe_for_vegan": str(d3.get("safe_for_vegan", "")),
                "confidence_score": str(d3.get("confidence_score", "")),
                "raw_response_json": json.dumps(d3, ensure_ascii=False)
            })
        else:
            f_count += 1
            item_recs.append({"food_name": name, "api_name": "Allergen Detection API", "status": "failed", "status_code": r3.status_code, "raw_response_json": r3.text})

        # 4. Healthy Substitution API
        r4 = client.post("/api/foods/substitutions", json={"food_name": name, "ingredients": ings, "goal": "weight_loss"})
        if r4.status_code == 200:
            d4 = r4.json()
            s_count += 1
            item_recs.append({
                "food_name": name, "api_name": "Healthy Substitution API",
                "status": "success", "status_code": 200,
                "target_goal": str(d4.get("target_goal", "")), "substitutions": json.dumps(d4.get("substitutions", [])),
                "substitution_count": str(d4.get("substitution_count", 0)), "summary": str(d4.get("summary", "")),
                "confidence_score": str(d4.get("confidence_score", "")),
                "raw_response_json": json.dumps(d4, ensure_ascii=False)
            })
        else:
            f_count += 1
            item_recs.append({"food_name": name, "api_name": "Healthy Substitution API", "status": "failed", "status_code": r4.status_code, "raw_response_json": r4.text})

        return item_recs

    with ThreadPoolExecutor(max_workers=10) as executor:
        results = list(executor.map(process_item, food_items))

    records = []
    for item_recs in results:
        records.extend(item_recs)

    import io
    s = io.StringIO()
    writer = csv.DictWriter(s, fieldnames=columns)
    writer.writeheader()
    for r in records:
        writer.writerow({col: r.get(col, "") for col in columns})

    return s.getvalue()

if __name__ == "__main__":
    csv_text = generate_csv_text()
    out_path = os.path.abspath("data/datasets/nutrimate_api_records.csv")
    with open(out_path, "w", encoding="utf-8", newline="") as f:
        f.write(csv_text)
    print(f"Dataset generated. Length: {len(csv_text)} bytes")
