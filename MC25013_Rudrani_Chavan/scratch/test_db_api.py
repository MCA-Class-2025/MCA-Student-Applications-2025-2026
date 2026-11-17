"""
Comprehensive verification script for Task 4: NutriMate Nutrition Database API
Tests:
1. GET /api/foods/Poha (seed record match)
2. POST & GET /api/foods/Paneer Tikka (dynamic record)
3. POST /api/foods (new dynamic record: Vegetable Biryani)
4. GET /api/foods/Vegetable Biryani (retrieve newly saved record)
5. POST /api/foods duplicate insertion (Vegetable Biryani again -> 409 Conflict)
6. GET /api/foods/NonExistentDish9999 (invalid name -> 404 Not Found)
7. GET /api/foods?diet_type=veg&search=Biryani (filtered search)
8. Verify seed records remain intact (>= 81 curated, expanded to 100 with new Indian dishes)
"""

import requests
import json
import sys

BASE_URL = "http://127.0.0.1:8000"
all_passed = True

def log_test(name, passed, msg=""):
    status_str = "PASS" if passed else "FAIL"
    print(f"[{status_str}] {name}: {msg}")

print("="*60)
print("TASK 4: NUTRITION DATABASE API TEST SUITE")
print("="*60)

# ── 1. GET Seed Record: Poha ──────────────────────────────────────────
try:
    resp = requests.get(f"{BASE_URL}/api/foods/Poha", timeout=10)
    if resp.status_code == 200:
        data = resp.json()
        if "Poha" in data.get("name") and data.get("source_type") in ("curated", "kaggle"):
            log_test("1. GET /api/foods/Poha", True, f"Found dish '{data.get('name')}' (Source={data.get('source_type')}, calories={data.get('calories')})")
        else:
            log_test("1. GET /api/foods/Poha", False, f"Unexpected response data: {data}")
            all_passed = False
    else:
        log_test("1. GET /api/foods/Poha", False, f"HTTP {resp.status_code}: {resp.text}")
        all_passed = False
except Exception as e:
    log_test("1. GET /api/foods/Poha", False, str(e))
    all_passed = False

# ── 2. POST & GET Dynamic Record: Paneer Tikka ────────────────────────
paneer_tikka_payload = {
    "name": "Paneer Tikka",
    "source_type": "api_analysis",
    "diet_type": "veg",
    "goals": ["muscle_gain"],
    "meal_type": "Snack",
    "calories": 280.0,
    "protein": 16.0,
    "carbohydrates": 12.0,
    "fat": 18.0,
    "fiber": 3.0,
    "vitamins": ["Vitamin A", "Vitamin C"],
    "minerals": ["Calcium", "Iron"],
    "ingredients": ["Paneer", "Yogurt", "Capsicum", "Onion", "Spices"],
    "health_benefits": "High in protein and calcium."
}

try:
    resp = requests.post(f"{BASE_URL}/api/foods", json=paneer_tikka_payload, timeout=10)
    if resp.status_code in (201, 409):
        resp_get = requests.get(f"{BASE_URL}/api/foods/Paneer%20Tikka", timeout=10)
        if resp_get.status_code == 200:
            data = resp_get.json()
            if "Paneer Tikka" in data.get("name"):
                log_test("2. GET /api/foods/Paneer Tikka", True, f"Retrieved dish '{data.get('name')}' (Source={data.get('source_type')})")
            else:
                log_test("2. GET /api/foods/Paneer Tikka", False, f"Unexpected data: {data}")
                all_passed = False
        else:
            log_test("2. GET /api/foods/Paneer Tikka", False, f"GET returned HTTP {resp_get.status_code}: {resp_get.text}")
            all_passed = False
    else:
        log_test("2. POST /api/foods (Paneer Tikka)", False, f"POST returned HTTP {resp.status_code}: {resp.text}")
        all_passed = False
except Exception as e:
    log_test("2. GET /api/foods/Paneer Tikka", False, str(e))
    all_passed = False

# ── 3. POST New Dynamic Record: Vegetable Biryani ─────────────────────
new_food_payload = {
    "name": "Vegetable Biryani",
    "source_type": "api_analysis",
    "diet_type": "veg",
    "goals": ["weight_loss", "muscle_gain"],
    "meal_type": "Lunch",
    "calories": 380.0,
    "protein": 18.0,
    "carbohydrates": 45.0,
    "fat": 12.0,
    "fiber": 6.0,
    "vitamins": ["Vitamin A", "Vitamin C"],
    "minerals": ["Calcium", "Iron"],
    "ingredients": ["Basmati Rice", "Mixed Vegetables", "Saffron", "Spices"],
    "health_benefits": "High fiber and rich in micronutrients."
}

try:
    resp = requests.post(f"{BASE_URL}/api/foods", json=new_food_payload, timeout=10)
    if resp.status_code == 201:
        data = resp.json()
        if data.get("name") == "Vegetable Biryani" and data.get("source_type") == "api_analysis":
            log_test("3. POST /api/foods (Vegetable Biryani)", True, f"Created new record (ID={data.get('id')})")
        else:
            log_test("3. POST /api/foods (Vegetable Biryani)", False, f"Unexpected response data: {data}")
            all_passed = False
    elif resp.status_code == 409:
        log_test("3. POST /api/foods (Vegetable Biryani)", True, "Record already exists (409 Conflict handled)")
    else:
        log_test("3. POST /api/foods (Vegetable Biryani)", False, f"HTTP {resp.status_code}: {resp.text}")
        all_passed = False
except Exception as e:
    log_test("3. POST /api/foods (Vegetable Biryani)", False, str(e))
    all_passed = False

# ── 4. GET Newly Saved Record: Vegetable Biryani ──────────────────────
try:
    resp = requests.get(f"{BASE_URL}/api/foods/Vegetable%20Biryani", timeout=10)
    if resp.status_code == 200:
        data = resp.json()
        if data.get("name") == "Vegetable Biryani":
            log_test("4. GET /api/foods/Vegetable Biryani", True, f"Retrieved saved record (Ingredients={data.get('ingredients')})")
        else:
            log_test("4. GET /api/foods/Vegetable Biryani", False, f"Unexpected data: {data}")
            all_passed = False
    else:
        log_test("4. GET /api/foods/Vegetable Biryani", False, f"HTTP {resp.status_code}: {resp.text}")
        all_passed = False
except Exception as e:
    log_test("4. GET /api/foods/Vegetable Biryani", False, str(e))
    all_passed = False

# ── 5. POST Duplicate Insertion: Vegetable Biryani -> 409 Conflict ────
try:
    resp = requests.post(f"{BASE_URL}/api/foods", json=new_food_payload, timeout=10)
    if resp.status_code == 409:
        log_test("5. POST Duplicate Insertion", True, f"Correctly rejected duplicate with HTTP 409: {resp.json().get('detail')}")
    else:
        log_test("5. POST Duplicate Insertion", False, f"Expected 409 Conflict, got HTTP {resp.status_code}: {resp.text}")
        all_passed = False
except Exception as e:
    log_test("5. POST Duplicate Insertion", False, str(e))
    all_passed = False

# ── 6. GET Invalid Food Name: NonExistentDish9999 -> 404 Not Found ────
try:
    resp = requests.get(f"{BASE_URL}/api/foods/NonExistentDish9999", timeout=10)
    if resp.status_code == 404:
        log_test("6. GET Invalid Food Name", True, f"Correctly returned HTTP 404: {resp.json().get('detail')}")
    else:
        log_test("6. GET Invalid Food Name", False, f"Expected 404 Not Found, got HTTP {resp.status_code}: {resp.text}")
        all_passed = False
except Exception as e:
    log_test("6. GET Invalid Food Name", False, str(e))
    all_passed = False

# ── 7. GET Filtered Search: diet_type=veg & search=Biryani ────────────
try:
    resp = requests.get(f"{BASE_URL}/api/foods?diet_type=veg&search=Biryani", timeout=10)
    if resp.status_code == 200:
        data = resp.json()
        names = [item["name"] for item in data]
        if "Vegetable Biryani" in names:
            log_test("7. GET Filtered Search", True, f"Found {len(data)} items matching filter: {names}")
        else:
            log_test("7. GET Filtered Search", False, f"Vegetable Biryani not in search results: {names}")
            all_passed = False
    else:
        log_test("7. GET Filtered Search", False, f"HTTP {resp.status_code}: {resp.text}")
        all_passed = False
except Exception as e:
    log_test("7. GET Filtered Search", False, str(e))
    all_passed = False

# ── 8. GET Total Foods Count & Seed Integrity Check ───────────────────
try:
    resp = requests.get(f"{BASE_URL}/api/foods", timeout=10)
    if resp.status_code == 200:
        data = resp.json()
        count = len(data)
        curated_count = sum(1 for x in data if x.get("source_type") == "curated")
        # Expanded from 81 to 100 curated records with new Indian dishes
        if count >= 83 and curated_count >= 81:
            log_test("8. Database Integrity Check", True, f"Total foods: {count}, Curated seed count: {curated_count} intact")
        else:
            log_test("8. Database Integrity Check", False, f"Unexpected counts: Total={count}, Curated={curated_count}")
            all_passed = False
    else:
        log_test("8. Database Integrity Check", False, f"HTTP {resp.status_code}: {resp.text}")
        all_passed = False
except Exception as e:
    log_test("8. Database Integrity Check", False, str(e))
    all_passed = False

print("="*60)
print("TASK 4 SUITE RESULT:", "ALL TESTS PASSED" if all_passed else "SOME TESTS FAILED")
print("="*60)

sys.exit(0 if all_passed else 1)
