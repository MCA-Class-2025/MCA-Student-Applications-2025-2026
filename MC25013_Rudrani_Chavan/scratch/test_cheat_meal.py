# -*- coding: utf-8 -*-
"""Task 11: Cheat Meal Impact API -- test script."""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
import json
import requests

BASE = "http://127.0.0.1:8000"

def post(path, body):
    r = requests.post(f"{BASE}{path}", json=body, timeout=120)
    return r.status_code, r.json()

def check(label, code, data, expected_code=200):
    status = "PASS" if code == expected_code else f"FAIL(HTTP {code})"
    print(f"[{status}] {label}")
    return code == expected_code

print("=" * 65)
print("TASK 11 — CHEAT MEAL IMPACT API TESTS")
print("=" * 65)

# -- TEST 1: Burger — LLM estimation, weight_loss goal -----------------
print("\nTEST 1: Burger (no calories supplied -> LLM estimate, weight_loss)")
code, data = post("/api/foods/cheat-meal-impact", {
    "food_name": "Burger",
    "goal": "weight_loss",
})
if check("Burger LLM estimate", code, data):
    print(f"    estimated_calories     : {data['estimated_calories']}")
    print(f"    calorie_budget_used_%  : {data['calorie_budget_used_pct']}")
    print(f"    remaining_cal_budget   : {data['remaining_calorie_budget']}")
    print(f"    fat_budget_used_%      : {data['fat_budget_used_pct']}")
    print(f"    impact_level           : {data['impact_level']}")
    print(f"    calorie_source         : {data['calorie_source']}")
    print(f"    alternatives           : {len(data['alternatives'])}")
    rec = data['recommendation'][:120]
    print(f"    recommendation[:120]   : {rec}")
else:
    print(f"    error: {data}")

# -- TEST 2: Pizza — user-supplied values, diabetic_friendly goal -------
print("\nTEST 2: Pizza (user-supplied 680 kcal, 8g sugar, 28g fat, diabetic_friendly)")
code, data = post("/api/foods/cheat-meal-impact", {
    "food_name": "Pizza",
    "calories": 680.0,
    "sugar_g": 8.0,
    "fat_g": 28.0,
    "daily_calorie_target": 1800.0,
    "goal": "diabetic_friendly",
})
if check("Pizza user-supplied", code, data):
    print(f"    estimated_calories     : {data['estimated_calories']}")
    print(f"    calorie_budget_used_%  : {data['calorie_budget_used_pct']}")
    print(f"    sugar_budget_used_%    : {data['sugar_budget_used_pct']}")
    print(f"    fat_budget_used_%      : {data['fat_budget_used_pct']}")
    print(f"    impact_level           : {data['impact_level']}")
    print(f"    calorie_source         : {data['calorie_source']}")
    if data["alternatives"]:
        print(f"    alternative[0]         : {data['alternatives'][0]['replacement'][:70]}")
else:
    print(f"    error: {data}")

# -- TEST 3: Cold drink — high sugar, no fat, no goal ------------------
print("\nTEST 3: Cold drink (140 kcal, 39g sugar — expected impact elevation)")
code, data = post("/api/foods/cheat-meal-impact", {
    "food_name": "Cold drink",
    "calories": 140.0,
    "sugar_g": 39.0,
    "fat_g": 0.0,
    "daily_calorie_target": 2000.0,
    "daily_sugar_target": 50.0,
})
if check("Cold drink high sugar", code, data):
    print(f"    estimated_calories     : {data['estimated_calories']}")
    print(f"    calorie_budget_used_%  : {data['calorie_budget_used_pct']}")
    print(f"    sugar_budget_used_%    : {data['sugar_budget_used_pct']}")
    print(f"    fat_budget_used_%      : {data['fat_budget_used_pct']}")
    print(f"    impact_level           : {data['impact_level']}")
    print(f"    calorie_source         : {data['calorie_source']}")
    assert data["calorie_budget_used_pct"] == 7.0, "Expected 7.0% calorie budget"
    assert data["sugar_budget_used_pct"] == 78.0, f"Expected 78.0% sugar budget, got {data['sugar_budget_used_pct']}"
    assert data["impact_level"] == "Moderate", f"Expected Moderate, got {data['impact_level']}"
    print("    ASSERTION: impact_level elevated from Low -> Moderate due to sugar%: PASS")
else:
    print(f"    error: {data}")

# -- TEST 4: Missing / invalid values ----------------------------------
print("\nTEST 4a: Empty food_name (expected 422)")
r = requests.post(f"{BASE}/api/foods/cheat-meal-impact", json={"food_name": ""}, timeout=10)
check("Empty food_name -> 422", r.status_code, r.json(), expected_code=422)
print(f"    detail: {r.json().get('detail', r.text)[:80]}")

print("\nTEST 4b: Missing food_name field (expected 422)")
r = requests.post(f"{BASE}/api/foods/cheat-meal-impact", json={}, timeout=10)
check("Missing food_name -> 422", r.status_code, r.json(), expected_code=422)
print(f"    detail: {str(r.json())[:80]}")

print("\nTEST 4c: Negative calories (expected 422)")
r = requests.post(f"{BASE}/api/foods/cheat-meal-impact", json={"food_name": "test", "calories": -50}, timeout=10)
check("Negative calories -> 422", r.status_code, r.json(), expected_code=422)
print(f"    detail: {str(r.json())[:80]}")

# -- EXISTING API SMOKE TESTS ------------------------------------------
print("\n" + "=" * 65)
print("SMOKE TEST: Existing APIs")
print("=" * 65)

r = requests.get(f"{BASE}/api/foods", timeout=10)
check("GET /api/foods", r.status_code, r.json())

r = requests.post(f"{BASE}/api/foods/allergens", json={"food_name": "Paneer Tikka"}, timeout=60)
check("POST /api/foods/allergens", r.status_code, r.json())

r = requests.post(f"{BASE}/api/foods/substitutions", json={"food_name": "Butter Chicken", "goal": "weight_loss"}, timeout=60)
check("POST /api/foods/substitutions", r.status_code, r.json())

r = requests.post(f"{BASE}/api/foods/compare", json={"food_1": "Poha", "food_2": "Upma"}, timeout=60)
check("POST /api/foods/compare", r.status_code, r.json())

# -- CHECK /docs CONTAINS ENDPOINT ------------------------------------
print("\n" + "=" * 65)
print("VERIFY /docs contains cheat-meal-impact")
print("=" * 65)
r = requests.get(f"{BASE}/openapi.json", timeout=10)
openapi = r.json()
paths = list(openapi.get("paths", {}).keys())
has_cheat = any("cheat-meal-impact" in p for p in paths)
print(f"    /docs paths: {[p for p in paths if 'cheat' in p]}")
check("cheat-meal-impact in /docs", 200 if has_cheat else 404, {}, expected_code=200)

print("\n" + "=" * 65)
print("ALL TESTS COMPLETE")
print("=" * 65)
