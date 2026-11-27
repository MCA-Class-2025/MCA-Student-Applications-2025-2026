
import os
import pandas as pd

from config import ORIGINAL_DATA, FUSED_DATA_DIR


def main():
    original = pd.read_excel(ORIGINAL_DATA)

    fused_path = os.path.join(
        FUSED_DATA_DIR, "fused_food_dataset.csv"
    )

    if not os.path.exists(fused_path):
        raise FileNotFoundError(
            "Fused dataset not found."
        )

    fused = pd.read_csv(fused_path)

    print("=" * 50)
    print("FOOD DATA FUSION VALIDATION")
    print("=" * 50)

    print("\nOriginal rows:", len(original))
    print("Fused rows:", len(fused))
    print("Original columns:", len(original.columns))
    print("Fused columns:", len(fused.columns))

    if len(original) == len(fused):
        print("\nPASS: Original row count preserved.")
    else:
        print("\nFAIL: Row count changed.")

    if "food_id" in original.columns and "food_id" in fused.columns:
        if fused["food_id"].equals(original["food_id"]):
            print("PASS: Food IDs preserved.")
        else:
            print("FAIL: Food IDs changed.")

    print("\nDuplicate rows:", fused.duplicated().sum())

    print("\nAPI MATCH COVERAGE")

    for prefix in ["usda_", "spoonacular_", "themealdb_"]:
        columns = [
            col for col in fused.columns
            if col.startswith(prefix)
        ]

        if not columns:
            print(prefix, "No columns found.")
            continue

        available = fused[columns].notna().any(axis=1).sum()

        print(
            f"{prefix}: {available} / {len(fused)} "
            "food records have matched data"
        )

    print("\nMissing values in fused dataset:")
    print(fused.isna().sum().to_string())

    report_path = os.path.join(
        FUSED_DATA_DIR, "fusion_report.txt"
    )

    with open(report_path, "w", encoding="utf-8") as file:
        file.write("FOOD DATA FUSION REPORT\n")
        file.write(f"Original records: {len(original)}\n")
        file.write(f"Fused records: {len(fused)}\n")
        file.write(f"Fused columns: {len(fused.columns)}\n")
        file.write(
            f"Duplicate rows: {fused.duplicated().sum()}\n"
        )

    print("\nReport saved:", report_path)


if __name__ == "__main__":
    main()
