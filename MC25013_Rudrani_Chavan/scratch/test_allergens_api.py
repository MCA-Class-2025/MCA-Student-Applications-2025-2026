"""
Automated test suite for Task 6: NutriMate Allergen Detection API (POST /api/foods/allergens)
Tests:
1. Paneer Tikka -> Detects 'Milk / Dairy'
2. Egg Bhurji -> Detects 'Egg'
3. Peanut Chikki -> Detects 'Peanuts'
4. Steamed Rice & Apple -> Detects [] (no allergens)
5. Empty food_name -> HTTP 422
6. OpenAPI docs -> HTTP 200
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
print("TASK 6: ALLERGEN DETECTION API TEST SUITE")
print("="*60)

# ── 1. Paneer Tikka Test ───────────────────────────────────────────────
try:
    payload = {
        "food_name": "Paneer Tikka",
        "ingredients": ["Paneer", "Yogurt", "Capsicum", "Tandoori Masala"]
    }
    resp = requests.post(f"{BASE_URL}/api/foods/allergens", json=payload, timeout=30)
    print("Test 1 status:", resp.status_code)
    if resp.status_code == 200:
        data = resp.json()
        print("Response 1:\n", json.dumps(data, indent=2))
        if "Milk / Dairy" in data.get("detected_allergens", []) and data.get("safe_for_vegan") is False:
            log_test("1. Paneer Tikka", True, f"Detected allergens: {data.get('detected_allergens')} (Vegan={data.get('safe_for_vegan')})")
        else:
            log_test("1. Paneer Tikka", False, f"Unexpected response: {data}")
            all_passed = False
    else:
        log_test("1. Paneer Tikka", False, f"HTTP {resp.status_code}: {resp.text}")
        all_passed = False
except Exception as e:
    log_test("1. Paneer Tikka", False, str(e))
    all_passed = False

# ── 2. Egg Bhurji Test ────────────────────────────────────────────────
try:
    payload = {
        "food_name": "Egg Bhurji",
        "ingredients": ["Eggs", "Onion", "Green Chillies", "Butter"]
    }
    resp = requests.post(f"{BASE_URL}/api/foods/allergens", json=payload, timeout=30)
    print("Test 2 status:", resp.status_code)
    if resp.status_code == 200:
        data = resp.json()
        print("Response 2:\n", json.dumps(data, indent=2))
        if "Egg" in data.get("detected_allergens", []) and data.get("safe_for_vegetarian") is False and data.get("safe_for_eggetarian") is True:
            log_test("2. Egg Bhurji", True, f"Detected: {data.get('detected_allergens')} (Veg={data.get('safe_for_vegetarian')}, Eggetarian={data.get('safe_for_eggetarian')})")
        else:
            log_test("2. Egg Bhurji", False, f"Unexpected response: {data}")
            all_passed = False
    else:
        log_test("2. Egg Bhurji", False, f"HTTP {resp.status_code}: {resp.text}")
        all_passed = False
except Exception as e:
    log_test("2. Egg Bhurji", False, str(e))
    all_passed = False

# ── 3. Peanut Chikki Test ─────────────────────────────────────────────
try:
    payload = {
        "food_name": "Peanut Chikki",
        "ingredients": ["Peanuts", "Jaggery"]
    }
    resp = requests.post(f"{BASE_URL}/api/foods/allergens", json=payload, timeout=30)
    print("Test 3 status:", resp.status_code)
    if resp.status_code == 200:
        data = resp.json()
        print("Response 3:\n", json.dumps(data, indent=2))
        if "Peanuts" in data.get("detected_allergens", []) and data.get("safe_for_vegan") is True:
            log_test("3. Peanut Chikki", True, f"Detected: {data.get('detected_allergens')} (Vegan={data.get('safe_for_vegan')})")
        else:
            log_test("3. Peanut Chikki", False, f"Unexpected response: {data}")
            all_passed = False
    else:
        log_test("3. Peanut Chikki", False, f"HTTP {resp.status_code}: {resp.text}")
        all_passed = False
except Exception as e:
    log_test("3. Peanut Chikki", False, str(e))
    all_passed = False

# ── 4. Steamed Rice & Apple (No Allergens) ────────────────────────────
try:
    payload = {
        "food_name": "Steamed Rice with Fresh Apple",
        "ingredients": ["Rice", "Water", "Apple"]
    }
    resp = requests.post(f"{BASE_URL}/api/foods/allergens", json=payload, timeout=30)
    print("Test 4 status:", resp.status_code)
    if resp.status_code == 200:
        data = resp.json()
        print("Response 4:\n", json.dumps(data, indent=2))
        if data.get("allergen_count") == 0 and data.get("warning_level") == "None" and data.get("safe_for_vegan") is True:
            log_test("4. Steamed Rice & Apple", True, f"No allergens detected (Count={data.get('allergen_count')}, Level={data.get('warning_level')})")
        else:
            log_test("4. Steamed Rice & Apple", False, f"Unexpected response: {data}")
            all_passed = False
    else:
        log_test("4. Steamed Rice & Apple", False, f"HTTP {resp.status_code}: {resp.text}")
        all_passed = False
except Exception as e:
    log_test("4. Steamed Rice & Apple", False, str(e))
    all_passed = False

# ── 5. Empty Input Validation Test (HTTP 422) ─────────────────────────
try:
    payload = {
        "food_name": ""
    }
    resp = requests.post(f"{BASE_URL}/api/foods/allergens", json=payload, timeout=10)
    print("Test 5 status:", resp.status_code)
    if resp.status_code == 422:
        log_test("5. Empty Food Name Validation", True, f"Correctly rejected with HTTP 422: {resp.json().get('detail')}")
    else:
        log_test("5. Empty Food Name Validation", False, f"Expected 422, got HTTP {resp.status_code}: {resp.text}")
        all_passed = False
except Exception as e:
    log_test("5. Empty Food Name Validation", False, str(e))
    all_passed = False

# ── 6. OpenAPI Documentation Check ────────────────────────────────────
try:
    resp = requests.get(f"{BASE_URL}/openapi.json", timeout=10)
    if resp.status_code == 200:
        paths = list(resp.json().get("paths", {}).keys())
        if "/api/foods/allergens" in paths:
            log_test("6. OpenAPI Documentation", True, f"/api/foods/allergens present in OpenAPI endpoints: {paths}")
        else:
            log_test("6. OpenAPI Documentation", False, f"Endpoint missing from OpenAPI docs: {paths}")
            all_passed = False
    else:
        log_test("6. OpenAPI Documentation", False, f"HTTP {resp.status_code}: {resp.text}")
        all_passed = False
except Exception as e:
    log_test("6. OpenAPI Documentation", False, str(e))
    all_passed = False

print("="*60)
print("TASK 6 SUITE RESULT:", "ALL TESTS PASSED" if all_passed else "SOME TESTS FAILED")
print("="*60)

sys.exit(0 if all_passed else 1)
