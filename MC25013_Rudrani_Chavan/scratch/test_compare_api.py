"""
Automated test suite for Task 8: NutriMate Food Comparison API (POST /api/foods/compare)
Tests:
1. Poha vs Upma -> 200 OK
2. Paneer Tikka vs Chicken Tikka -> 200 OK
3. Near-equal nutrition values (Egg Curry vs Egg Curry) -> 200 OK with "Equal"
4. Non-existent food -> HTTP 404 Not Found
5. Empty food name -> HTTP 422 Unprocessable Entity
6. Goal-aware calorie evaluation (weight_gain vs weight_loss)
7. OpenAPI spec check -> All 6 endpoints registered
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
print("TASK 8: FOOD COMPARISON API TEST SUITE")
print("="*60)

# ── 1. Poha vs Upma Comparison ─────────────────────────────────────────
try:
    payload = {
        "food_1": "Poha",
        "food_2": "Upma",
        "goal": "weight_loss"
    }
    resp = requests.post(f"{BASE_URL}/api/foods/compare", json=payload, timeout=30)
    print(f"Test 1 status: {resp.status_code}")
    if resp.status_code == 200:
        data = resp.json()
        print(f"Response 1:\n{json.dumps(data, indent=2)}")
        if "food_1" in data and "food_2" in data and "better_for_goal" in data:
            log_test("1. Poha vs Upma", True, f"Comparing '{data['food_1']['name']}' vs '{data['food_2']['name']}'. Recommended: '{data['better_for_goal']}'")
        else:
            log_test("1. Poha vs Upma", False, f"Unexpected response format: {data}")
            all_passed = False
    else:
        log_test("1. Poha vs Upma", False, f"HTTP {resp.status_code}: {resp.text}")
        all_passed = False
except Exception as e:
    log_test("1. Poha vs Upma", False, str(e))
    all_passed = False

# ── 2. Paneer Tikka vs Chicken Tikka Comparison ───────────────────────
try:
    payload = {
        "food_1": "Paneer Tikka",
        "food_2": "Chicken Tikka",
        "goal": "muscle_gain"
    }
    resp = requests.post(f"{BASE_URL}/api/foods/compare", json=payload, timeout=30)
    print(f"Test 2 status: {resp.status_code}")
    if resp.status_code == 200:
        data = resp.json()
        print(f"Response 2:\n{json.dumps(data, indent=2)}")
        if "better_for_protein" in data and "nutrition_comparison" in data:
            log_test("2. Paneer Tikka vs Chicken Tikka", True, f"Better for protein: '{data['better_for_protein']}', Protein diff: {data['nutrition_comparison']['protein_diff']}g")
        else:
            log_test("2. Paneer Tikka vs Chicken Tikka", False, f"Unexpected response format: {data}")
            all_passed = False
    else:
        log_test("2. Paneer Tikka vs Chicken Tikka", False, f"HTTP {resp.status_code}: {resp.text}")
        all_passed = False
except Exception as e:
    log_test("2. Paneer Tikka vs Chicken Tikka", False, str(e))
    all_passed = False

# ── 3. Near-Equal Nutrition Values Test ───────────────────────────────
try:
    payload = {
        "food_1": "Egg Curry",
        "food_2": "Egg Curry",
        "goal": "maintenance"
    }
    resp = requests.post(f"{BASE_URL}/api/foods/compare", json=payload, timeout=30)
    print(f"Test 3 status: {resp.status_code}")
    if resp.status_code == 200:
        data = resp.json()
        print(f"Response 3:\n{json.dumps(data, indent=2)}")
        if data.get("better_for_calories") == "Equal" and data.get("better_for_protein") == "Equal":
            log_test("3. Near-Equal Values", True, f"Handled equal metrics correctly: calories={data['better_for_calories']}, protein={data['better_for_protein']}")
        else:
            log_test("3. Near-Equal Values", False, f"Unexpected response: {data}")
            all_passed = False
    else:
        log_test("3. Near-Equal Values", False, f"HTTP {resp.status_code}: {resp.text}")
        all_passed = False
except Exception as e:
    log_test("3. Near-Equal Values", False, str(e))
    all_passed = False

# ── 4. Non-Existent Food Test (HTTP 404) ──────────────────────────────
try:
    payload = {
        "food_1": "Paneer Tikka",
        "food_2": "NonExistentAlienDish9999",
        "goal": "weight_loss"
    }
    resp = requests.post(f"{BASE_URL}/api/foods/compare", json=payload, timeout=10)
    print(f"Test 4 status: {resp.status_code}")
    if resp.status_code == 404:
        log_test("4. Non-Existent Food", True, f"Correctly returned HTTP 404: {resp.json().get('detail')}")
    else:
        log_test("4. Non-Existent Food", False, f"Expected 404, got HTTP {resp.status_code}: {resp.text}")
        all_passed = False
except Exception as e:
    log_test("4. Non-Existent Food", False, str(e))
    all_passed = False

# ── 5. Empty Food Name Validation Test (HTTP 422) ─────────────────────
try:
    payload = {
        "food_1": "",
        "food_2": "Poha"
    }
    resp = requests.post(f"{BASE_URL}/api/foods/compare", json=payload, timeout=10)
    print(f"Test 5 status: {resp.status_code}")
    if resp.status_code == 422:
        log_test("5. Empty Food Name Validation", True, "Correctly returned HTTP 422 for empty food_1")
    else:
        log_test("5. Empty Food Name Validation", False, f"Expected 422, got HTTP {resp.status_code}: {resp.text}")
        all_passed = False
except Exception as e:
    log_test("5. Empty Food Name Validation", False, str(e))
    all_passed = False

# ── 6. Goal-Aware Calorie Comparison Check ────────────────────────────
try:
    # Under weight_loss -> lower calories is better
    p_wl = {"food_1": "Poha", "food_2": "Vegetable Biryani", "goal": "weight_loss"}
    r_wl = requests.post(f"{BASE_URL}/api/foods/compare", json=p_wl, timeout=10).json()

    # Under weight_gain -> higher calories is better
    p_wg = {"food_1": "Poha", "food_2": "Vegetable Biryani", "goal": "weight_gain"}
    r_wg = requests.post(f"{BASE_URL}/api/foods/compare", json=p_wg, timeout=10).json()

    if r_wl.get("better_for_calories") != r_wg.get("better_for_calories"):
        log_test("6. Goal-Aware Calorie Logic", True, f"WL calorie winner: '{r_wl.get('better_for_calories')}', WG calorie winner: '{r_wg.get('better_for_calories')}'")
    else:
        log_test("6. Goal-Aware Calorie Logic", False, f"Goal aware logic did not change winner: {r_wl.get('better_for_calories')}")
        all_passed = False
except Exception as e:
    log_test("6. Goal-Aware Calorie Logic", False, str(e))
    all_passed = False

# ── 7. OpenAPI Specifications Check for All 6 Endpoints ───────────────
try:
    resp = requests.get(f"{BASE_URL}/openapi.json", timeout=10)
    if resp.status_code == 200:
        paths = list(resp.json().get("paths", {}).keys())
        expected_endpoints = [
            "/api/nutrition/analyze",
            "/api/foods",
            "/api/foods/{food_name}",
            "/api/foods/recognize",
            "/api/foods/allergens",
            "/api/foods/substitutions",
            "/api/foods/compare"
        ]
        missing = [ep for ep in expected_endpoints if ep not in paths]
        if not missing:
            log_test("7. OpenAPI Documentation", True, f"All 6 API modules (7 endpoint routes) registered cleanly: {paths}")
        else:
            log_test("7. OpenAPI Documentation", False, f"Missing endpoints in OpenAPI docs: {missing}")
            all_passed = False
    else:
        log_test("7. OpenAPI Documentation", False, f"HTTP {resp.status_code}")
        all_passed = False
except Exception as e:
    log_test("7. OpenAPI Documentation", False, str(e))
    all_passed = False

print("="*60)
print("TASK 8 SUITE RESULT:", "ALL TESTS PASSED" if all_passed else "SOME TESTS FAILED")
print("="*60)

sys.exit(0 if all_passed else 1)
