
import os
import pandas as pd

from config import (
    ORIGINAL_DATA,
    API_DATA_DIR,
    FUSED_DATA_DIR
)

from fusion.match_records import attach_food_id


def read_api_file(filename):

    path = os.path.join(API_DATA_DIR, filename)

    if not os.path.exists(path):
        print("API file not found:", filename)
        return pd.DataFrame()

    try:
        return pd.read_csv(path)
    except pd.errors.EmptyDataError:
        print("API file is empty:", filename)
        return pd.DataFrame()


def main():

    print("\n========== FOOD DATA FUSION ==========")

    # Load original dataset
    original_df = pd.read_excel(
        ORIGINAL_DATA,
        engine="openpyxl"
    )

    fused_df = original_df.copy()

    print("Original dataset:", original_df.shape)

    api_files = {
        "USDA": "usda_data.csv",
        "Spoonacular": "spoonacular_data.csv",
        "TheMealDB": "themealdb_data.csv"
    }

    for source, filename in api_files.items():

        print(f"\nProcessing {source} data...")

        api_df = read_api_file(filename)

        if api_df.empty:
            print("Skipping", source)
            continue

        matched_df = attach_food_id(
            api_df,
            original_df,
            source
        )

        if matched_df.empty:
            print("No matching records for", source)
            continue

        # Remove search name to avoid duplicate food_name columns
        if "food_name" in matched_df.columns:
            matched_df = matched_df.drop(
                columns=["food_name"]
            )

        # Check that each food_id occurs only once per API
        if matched_df["food_id"].duplicated().any():
            raise ValueError(
                f"Duplicate food_id found in {source} data. "
                "Resolve duplicates before merging."
            )

        # Left join preserves every original food record
        fused_df = fused_df.merge(
            matched_df,
            on="food_id",
            how="left",
            validate="many_to_one"
        )

        print(source, "merged successfully.")

    # Save fused dataset
    csv_path = os.path.join(
        FUSED_DATA_DIR,
        "fused_food_dataset.csv"
    )

    excel_path = os.path.join(
        FUSED_DATA_DIR,
        "fused_food_dataset.xlsx"
    )

    fused_df.to_csv(csv_path, index=False)
    fused_df.to_excel(excel_path, index=False)

    print("\n========== FUSION COMPLETED ==========")
    print("Original shape:", original_df.shape)
    print("Fused shape:", fused_df.shape)
    print("CSV saved:", csv_path)
    print("Excel saved:", excel_path)

    print("\nFused dataset preview:")
    print(fused_df.head())


if __name__ == "__main__":
    main()
