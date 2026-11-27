
import os
import re
import pandas as pd

from config import ORIGINAL_DATA, API_DATA_DIR


def normalize_name(value):
    if pd.isna(value):
        return ""

    value = str(value).lower().strip()
    value = re.sub(r"[^a-z0-9\s]", " ", value)
    value = re.sub(r"\s+", " ", value)

    return value


def attach_food_id(original_df, api_df, prefix):
    """
    Match API results to original food names using query_food.
    Preserves every original row and its food_id.
    """

    if api_df.empty:
        return original_df.copy()

    if "query_food" in api_df.columns:
        match_column = "query_food"
    elif "food_name" in api_df.columns:
        match_column = "food_name"
    else:
        print(f"No usable food name column for {prefix}")
        return original_df.copy()

    api_df = api_df.copy()
    api_df["_match_key"] = api_df[match_column].apply(normalize_name)

    # Keep one API result for each searched food
    api_df = api_df.drop_duplicates(
        subset=["_match_key"],
        keep="first"
    )

    api_lookup = api_df.set_index("_match_key").to_dict("index")

    result = original_df.copy()

    api_columns = [
        col for col in api_df.columns
        if col != "_match_key"
    ]

    for col in api_columns:
        result[f"{prefix}_{col}"] = None

    for index, food in result["food_name"].items():
        key = normalize_name(food)
        record = api_lookup.get(key)

        if record:
            for col in api_columns:
                result.at[index, f"{prefix}_{col}"] = record.get(col)

    matched = result[
        [f"{prefix}_{col}" for col in api_columns]
    ].notna().any(axis=1).sum()

    print(f"{prefix}: matched {matched} of {len(result)} rows")

    return result


def main():
    original = pd.read_excel(ORIGINAL_DATA)

    if "food_name" not in original.columns:
        raise ValueError("Original Excel must contain food_name.")

    result = original.copy()

    api_files = [
        ("usda_data.csv", "usda"),
        ("spoonacular_data.csv", "spoonacular"),
        ("themealdb_data.csv", "themealdb"),
    ]

    for filename, prefix in api_files:
        path = os.path.join(API_DATA_DIR, filename)

        if not os.path.exists(path):
            print(f"Skipping missing file: {filename}")
            continue

        api_df = pd.read_csv(path)

        if api_df.empty:
            print(f"Skipping empty file: {filename}")
            continue

        result = attach_food_id(result, api_df, prefix)

    output_path = os.path.join(
        API_DATA_DIR,
        "matched_food_data.csv"
    )

    result.to_csv(
        output_path,
        index=False,
        encoding="utf-8-sig"
    )

    print("\nMATCHING COMPLETED")
    print("Original rows:", len(original))
    print("Matched rows:", len(result))
    print("Total columns:", len(result.columns))
    print("Saved:", output_path)


if __name__ == "__main__":
    main()
