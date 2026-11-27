
import os
import pandas as pd

from config import ORIGINAL_DATA, FUSED_DATA_DIR


def main():

    original_df = pd.read_excel(
        ORIGINAL_DATA,
        engine="openpyxl"
    )

    fused_path = os.path.join(
        FUSED_DATA_DIR,
        "fused_food_dataset.csv"
    )

    if not os.path.exists(fused_path):
        print("Fused dataset not found!")
        print("Run fusion/fusion.py first.")
        return

    fused_df = pd.read_csv(fused_path)

    print("\n========== FUSION VALIDATION ==========")

    print("\nOriginal records:", len(original_df))
    print("Fused records:", len(fused_df))

    print("\nOriginal attributes:", len(original_df.columns))
    print("Fused attributes:", len(fused_df.columns))

    print("\nOriginal duplicate rows:", original_df.duplicated().sum())
    print("Fused duplicate rows:", fused_df.duplicated().sum())

    print(
        "\nOriginal duplicate food IDs:",
        original_df["food_id"].duplicated().sum()
    )

    print(
        "Fused duplicate food IDs:",
        fused_df["food_id"].duplicated().sum()
    )

    print("\n========== API MATCH VALIDATION ==========")

    api_columns = {
        "USDA": "fdc_id",
        "Spoonacular": "spoonacular_id",
        "TheMealDB": "themealdb_id"
    }

    for source, column in api_columns.items():

        if column in fused_df.columns:

            matched = fused_df[column].notna().sum()
            unmatched = fused_df[column].isna().sum()

            print(f"\n{source}")
            print("Matched records:", matched)
            print("Unmatched records:", unmatched)

        else:
            print(f"\n{source}: API data not merged.")

    print("\n========== MISSING VALUE SUMMARY ==========")

    print(
        fused_df.isnull()
        .sum()
        .sort_values(ascending=False)
    )

    print("\n========== RECORD PRESERVATION ==========")

    if len(fused_df) == len(original_df):
        print("SUCCESS: All original records were preserved.")
    else:
        print("WARNING: Original record count changed.")

    if fused_df["food_id"].duplicated().sum() == 0:
        print("SUCCESS: No duplicate food IDs.")
    else:
        print("WARNING: Duplicate food IDs detected.")

    print("\nValidation completed!")


if __name__ == "__main__":
    main()
