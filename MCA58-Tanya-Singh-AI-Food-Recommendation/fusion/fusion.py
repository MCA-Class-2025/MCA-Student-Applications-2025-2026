
import os
import pandas as pd

from config import ORIGINAL_DATA, API_DATA_DIR, FUSED_DATA_DIR


def main():
    os.makedirs(FUSED_DATA_DIR, exist_ok=True)

    original = pd.read_excel(ORIGINAL_DATA)

    matched_path = os.path.join(
        API_DATA_DIR,
        "matched_food_data.csv"
    )

    if not os.path.exists(matched_path):
        raise FileNotFoundError(
            "Matched data not found. First run: "
            "python -m fusion.match_records"
        )

    matched = pd.read_csv(matched_path)

    # Verify original rows and food IDs remain unchanged
    if len(original) != len(matched):
        raise ValueError(
            f"Row count mismatch: original={len(original)}, "
            f"matched={len(matched)}"
        )

    if "food_id" in original.columns:
        if "food_id" not in matched.columns:
            raise ValueError("food_id is missing from matched data.")

        if not original["food_id"].equals(matched["food_id"]):
            raise ValueError("Food IDs changed during matching.")

    # Save final fused food dataset
    fused_path = os.path.join(
        FUSED_DATA_DIR,
        "fused_food_dataset.csv"
    )

    matched.to_csv(
        fused_path,
        index=False,
        encoding="utf-8-sig"
    )

    # Save weather separately
    weather_path = os.path.join(
        API_DATA_DIR,
        "weather_data.csv"
    )

    if os.path.exists(weather_path):
        weather = pd.read_csv(weather_path)

        weather_output = os.path.join(
            FUSED_DATA_DIR,
            "fused_weather_data.csv"
        )

        weather.to_csv(
            weather_output,
            index=False,
            encoding="utf-8-sig"
        )

        print("Weather data saved:", weather_output)
    else:
        print("Weather data file not found. Skipping weather.")

    print("\n========== DATA FUSION COMPLETED ==========")
    print("Original records:", len(original))
    print("Fused records:", len(matched))
    print("Original columns:", len(original.columns))
    print("Fused columns:", len(matched.columns))
    print("Fused dataset:", fused_path)


if __name__ == "__main__":
    main()
