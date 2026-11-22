from services.defect_service import search_defects


# =========================================================
# TEST WATER LEAK
# =========================================================

results = search_defects(
    defect="Water leak"
)


print("\n===== WATER LEAK DEFECTS =====")

for result in results:

    print("\nWork type:", result["work_type"])
    print("Location:", result["location"])
    print("Element:", result["element"])
    print("Defect:", result["defect"])
    print("Description:", result["example_description"])