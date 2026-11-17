"""
Test script for POST /api/nutrition/analyze endpoint.
Tests three valid dishes + one invalid input.
"""
import requests
import json
import sys

BASE_URL = "http://127.0.0.1:8000"

# ── Valid test cases ──────────────────────────────────────────────
valid_tests = [
    {
        "food_name": "Paneer Tikka",
        "serving_size": "1 plate"
    },
    {
        "food_name": "Poha",
        "ingredients": ["Flattened Rice", "Onion", "Peanuts", "Mustard Seeds", "Curry Leaves", "Turmeric"],
        "serving_size": "1 bowl"
    },
    {
        "food_name": "Dal Khichdi",
        "recipe_text": "A comforting one-pot dish made with rice, moong dal, ghee, cumin, turmeric, and vegetables.",
        "serving_size": "1 plate"
    },
]

# ── Invalid test cases ───────────────────────────────────────────
invalid_tests = [
    {
        "label": "Empty food_name (should 422)",
        "payload": {"food_name": ""},
        "expected_status": 422,
    },
    {
        "label": "Missing food_name field (should 422)",
        "payload": {},
        "expected_status": 422,
    },
]

REQUIRED_FIELDS = [
    "food_name", "serving_size", "calories", "protein", "carbohydrates",
    "fat", "fiber", "vitamins", "minerals", "ingredients",
    "health_benefits", "consume_in_moderation", "diet_type",
    "confidence_score", "source_type"
]

all_passed = True

# ── Run valid tests ──────────────────────────────────────────────
for i, payload in enumerate(valid_tests, 1):
    dish = payload["food_name"]
    print(f"\n{'='*60}")
    print(f"TEST {i}: {dish}")
    print(f"{'='*60}")
    print(f"Request: {json.dumps(payload, indent=2)}")

    try:
        resp = requests.post(f"{BASE_URL}/api/nutrition/analyze", json=payload, timeout=180)
        print(f"HTTP Status: {resp.status_code}")

        if resp.status_code == 200:
            data = resp.json()
            print(f"Response:\n{json.dumps(data, indent=2)}")

            missing = [f for f in REQUIRED_FIELDS if f not in data]
            if missing:
                print(f"  FAIL: Missing fields: {missing}")
                all_passed = False
            else:
                print(f"  PASS: All {len(REQUIRED_FIELDS)} required fields present")

            if data.get("diet_type") not in ("veg", "egg", "nv"):
                print(f"  FAIL: diet_type '{data.get('diet_type')}' invalid")
                all_passed = False
            else:
                print(f"  PASS: diet_type = '{data['diet_type']}'")

            if not isinstance(data.get("confidence_score"), int):
                print(f"  FAIL: confidence_score not int")
                all_passed = False
            else:
                print(f"  PASS: confidence_score = {data['confidence_score']}")

            if data.get("source_type") != "api_analysis":
                print(f"  FAIL: source_type != 'api_analysis'")
                all_passed = False
            else:
                print(f"  PASS: source_type = 'api_analysis'")

            if not isinstance(data.get("ingredients"), list):
                print(f"  FAIL: ingredients is not a list")
                all_passed = False
            else:
                print(f"  PASS: ingredients is list ({len(data['ingredients'])} items)")
        else:
            print(f"  FAIL: Expected 200, got {resp.status_code}")
            print(f"  Body: {resp.text}")
            all_passed = False
    except Exception as e:
        print(f"  FAIL: {e}")
        all_passed = False

# ── Run invalid tests ────────────────────────────────────────────
for j, tc in enumerate(invalid_tests, len(valid_tests) + 1):
    print(f"\n{'='*60}")
    print(f"TEST {j}: {tc['label']}")
    print(f"{'='*60}")
    print(f"Request: {json.dumps(tc['payload'], indent=2)}")

    try:
        resp = requests.post(f"{BASE_URL}/api/nutrition/analyze", json=tc["payload"], timeout=30)
        print(f"HTTP Status: {resp.status_code}")

        if resp.status_code == tc["expected_status"]:
            print(f"  PASS: Got expected status {tc['expected_status']}")
            print(f"  Detail: {resp.json().get('detail', resp.text)}")
        else:
            print(f"  FAIL: Expected {tc['expected_status']}, got {resp.status_code}")
            print(f"  Body: {resp.text}")
            all_passed = False
    except Exception as e:
        print(f"  FAIL: {e}")
        all_passed = False

# ── Summary ──────────────────────────────────────────────────────
print(f"\n{'='*60}")
print("ALL TESTS PASSED" if all_passed else "SOME TESTS FAILED")
print(f"{'='*60}")
sys.exit(0 if all_passed else 1)
