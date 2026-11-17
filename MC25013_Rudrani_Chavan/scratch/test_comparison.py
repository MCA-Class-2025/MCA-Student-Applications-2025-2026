# -*- coding: utf-8 -*-
"""Verification script for Food Comparison endpoint."""
import requests
import json

BASE = "http://127.0.0.1:8000"

# List of pairs to test
TEST_PAIRS = [
    # Required ones
    ("Poha with Roasted Peanuts and Sprouts", "Oats Vegetable Upma with Almonds", "weight_loss"),
    ("Vada Pav", "Bhel Puri", "weight_loss"),
    ("Paneer Tikka", "Tandoori Chicken", "muscle_gain"),
    ("Chole Bhature", "Vegetable Pulao", "maintenance"),
    # 10 additional combinations
    ("Misal Pav", "Pav Bhaji", "weight_gain"),
    ("Pani Puri", "Samosa", "diabetic_friendly"),
    ("Aloo Tikki", "Medu Vada", "maintenance"),
    ("Palak Paneer", "Butter Chicken", "muscle_gain"),
    ("Fish Curry", "Egg Curry", "weight_loss"),
    ("Lemon Rice", "Curd Rice", "diabetic_friendly"),
    ("Idiyappam", "Appam", "weight_loss"),
    ("Moong Dal Cheela with Paneer Stuffing", "Besan Chilla with Mint Coriander Chutney", "muscle_gain"),
    ("Oats Vegetable Upma with Almonds", "Bajra Cheela with Low-Fat Curd", "diabetic_friendly"),
    ("Steamed Multigrain Idli with Sambar", "Jowar Dosa with Flaxseed Chutney", "maintenance")
]

print("=" * 70)
print("TESTING FOOD COMPARISON API ENDPOINT WITH 14 COMBINATIONS")
print("=" * 70)

all_passed = True

for idx, (food1, food2, goal) in enumerate(TEST_PAIRS, start=1):
    payload = {
        "food_1": food1,
        "food_2": food2,
        "goal": goal
    }
    try:
        r = requests.post(f"{BASE}/api/foods/compare", json=payload, timeout=30)
        if r.status_code != 200:
            print(f"[FAIL] {idx}. {food1} vs {food2} ({goal}) -> HTTP {r.status_code}")
            print("Response:", r.text)
            all_passed = False
        else:
            data = r.json()
            # Verify keys exist
            assert "food_1" in data, "Missing food_1"
            assert "food_2" in data, "Missing food_2"
            assert "nutrition_comparison" in data, "Missing nutrition_comparison"
            assert "better_for_goal" in data, "Missing better_for_goal"
            comp = data["nutrition_comparison"]
            assert "calories_diff" in comp, "Missing calories_diff"
            assert "protein_diff" in comp, "Missing protein_diff"
            assert "carbs_diff" in comp, "Missing carbs_diff"
            assert "fat_diff" in comp, "Missing fat_diff"
            assert "fiber_diff" in comp, "Missing fiber_diff"
            
            print(f"[PASS] {idx:02d}. {food1} vs {food2} (Goal: {goal})")
            print(f"       Winner: {data['better_for_goal']} | Cal Diff: {comp['calories_diff']} kcal | Pro Diff: {comp['protein_diff']} g")
    except Exception as e:
        print(f"[ERROR] Exception comparing {food1} vs {food2}: {e}")
        all_passed = False

print("\n" + "=" * 70)
if all_passed:
    print("ALL 14 FOOD COMPARISON TESTS PASSED SUCCESSFULLY!")
else:
    print("SOME FOOD COMPARISON TESTS FAILED.")
print("=" * 70)
