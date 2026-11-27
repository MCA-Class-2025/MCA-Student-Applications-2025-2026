
import os
import re
import pandas as pd

from config import API_DATA_DIR


FILES = [
    "usda_data.csv",
    "spoonacular_data.csv",
    "themealdb_data.csv"
]


def normalize_name(value):
    if pd.isna(value):
        return ""

    value = str(value).lower().strip()
    value = re.sub(r"[^a-z0-9\s]", " ", value)
    value = re.sub(r"\s+", " ", value)

    return value


def clean_file(filename):
    path = os.path.join(API_DATA_DIR, filename)

    if not os.path.exists(path):
        print("File not found:", filename)
        return

    df = pd.read_csv(path)

    if df.empty:
        print("No records:", filename)
        return

    df = df.dropna(how="all")

    if "food_name" in df.columns:
        df["food_name"] = df["food_name"].fillna("").astype(str).str.strip()
        df["normalized_name"] = df["food_name"].apply(normalize_name)

    if "query_food" in df.columns:
        df["query_food"] = df["query_food"].fillna("").astype(str).str.strip()
        df["normalized_query"] = df["query_food"].apply(normalize_name)

    df = df.drop_duplicates()

    # Keep the first result for each API query and API record
    if "recipe_id" in df.columns:
        df = df.drop_duplicates(subset=["recipe_id"])

    if "meal_id" in df.columns:
        df = df.drop_duplicates(subset=["meal_id"])

    if "fdc_id" in df.columns:
        df = df.drop_duplicates(subset=["fdc_id"])

    df.to_csv(path, index=False, encoding="utf-8-sig")

    print(f"Cleaned {filename}: {len(df)} records")


def main():
    for filename in FILES:
        clean_file(filename)

    print("\nAPI DATA CLEANING COMPLETED.")


if __name__ == "__main__":
    main()
