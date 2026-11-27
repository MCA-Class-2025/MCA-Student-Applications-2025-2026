from pathlib import Path
import pandas as pd


# ============================================================
# CITY COMPARISON - REAL-TIME AIR QUALITY
# ============================================================

INPUT_FILE = Path("live_data/live_predictions.csv")
OUTPUT_DIR = Path("live_data")
OUTPUT_DIR.mkdir(exist_ok=True)

OUTPUT_FILE = OUTPUT_DIR / "city_comparison.csv"


print("=" * 90)
print("REAL-TIME AIR QUALITY - CITY COMPARISON")
print("=" * 90)


# ------------------------------------------------------------
# 1. CHECK INPUT
# ------------------------------------------------------------

if not INPUT_FILE.exists():

    print("\nERROR: Live prediction file not found:")
    print(INPUT_FILE)

    print("\nRun this first:")
    print("python live_prediction.py")

    raise SystemExit(1)


# ------------------------------------------------------------
# 2. LOAD DATA
# ------------------------------------------------------------

df = pd.read_csv(
    INPUT_FILE,
    low_memory=False
)

print("\nCities available:", len(df))


# ------------------------------------------------------------
# 3. NUMERIC CONVERSION
# ------------------------------------------------------------

numeric_columns = [
    "Current_PM25",
    "Predicted_PM25_Next_1Hour",
    "Expected_Change",
    "Temperature",
    "Humidity",
    "Pressure",
    "WindSpeed",
    "WindDirection",
    "Rain1h"
]

for col in numeric_columns:

    if col in df.columns:

        df[col] = pd.to_numeric(
            df[col],
            errors="coerce"
        )


# ------------------------------------------------------------
# 4. RANK CITIES BY CURRENT PM2.5
# ------------------------------------------------------------

current_ranking = df.sort_values(
    "Current_PM25",
    ascending=False
).reset_index(drop=True)

current_ranking[
    "Current_Rank"
] = current_ranking.index + 1


# ------------------------------------------------------------
# 5. RANK CITIES BY PREDICTED PM2.5
# ------------------------------------------------------------

prediction_ranking = df.sort_values(
    "Predicted_PM25_Next_1Hour",
    ascending=False
).reset_index(drop=True)

prediction_ranking[
    "Predicted_Rank"
] = prediction_ranking.index + 1


# ------------------------------------------------------------
# 6. RANK BY EXPECTED CHANGE
# ------------------------------------------------------------

increase_ranking = df.sort_values(
    "Expected_Change",
    ascending=False
).reset_index(drop=True)


# ------------------------------------------------------------
# 7. CREATE COMPARISON TABLE
# ------------------------------------------------------------

comparison = df.copy()

comparison = comparison.merge(
    current_ranking[
        [
            "City",
            "Current_Rank"
        ]
    ],
    on="City",
    how="left"
)

comparison = comparison.merge(
    prediction_ranking[
        [
            "City",
            "Predicted_Rank"
        ]
    ],
    on="City",
    how="left"
)


comparison = comparison.sort_values(
    "Current_Rank"
).reset_index(drop=True)


# ------------------------------------------------------------
# 8. SAVE COMPARISON
# ------------------------------------------------------------

comparison.to_csv(
    OUTPUT_FILE,
    index=False
)


# ============================================================
# 9. DISPLAY OVERALL COMPARISON
# ============================================================

print("\n" + "=" * 90)
print("CITY AIR QUALITY COMPARISON")
print("=" * 90)


display_columns = [
    "Current_Rank",
    "City",
    "Current_PM25",
    "Predicted_PM25_Next_1Hour",
    "Expected_Change",
    "Expected_Direction",
    "Predicted_Category"
]

display_columns = [
    col
    for col in display_columns
    if col in comparison.columns
]


print(
    comparison[
        display_columns
    ].to_string(index=False)
)


# ============================================================
# 10. MOST POLLUTED CITY
# ============================================================

worst_current = df.loc[
    df["Current_PM25"].idxmax()
]

worst_prediction = df.loc[
    df["Predicted_PM25_Next_1Hour"].idxmax()
]


# ============================================================
# 11. CLEANEST CITY
# ============================================================

best_current = df.loc[
    df["Current_PM25"].idxmin()
]

best_prediction = df.loc[
    df["Predicted_PM25_Next_1Hour"].idxmin()
]


# ============================================================
# 12. LARGEST INCREASE / DECREASE
# ============================================================

largest_increase = df.loc[
    df["Expected_Change"].idxmax()
]

largest_decrease = df.loc[
    df["Expected_Change"].idxmin()
]


# ============================================================
# 13. SUMMARY
# ============================================================

print("\n" + "=" * 90)
print("COMPARISON SUMMARY")
print("=" * 90)

print(
    f"\nMost polluted currently:"
    f" {worst_current['City']}"
    f" ({worst_current['Current_PM25']:.2f} µg/m³)"
)

print(
    f"Lowest current PM2.5:"
    f" {best_current['City']}"
    f" ({best_current['Current_PM25']:.2f} µg/m³)"
)

print(
    f"\nHighest predicted PM2.5:"
    f" {worst_prediction['City']}"
    f" ({worst_prediction['Predicted_PM25_Next_1Hour']:.2f} µg/m³)"
)

print(
    f"Lowest predicted PM2.5:"
    f" {best_prediction['City']}"
    f" ({best_prediction['Predicted_PM25_Next_1Hour']:.2f} µg/m³)"
)

print(
    f"\nLargest expected increase:"
    f" {largest_increase['City']}"
    f" (+{largest_increase['Expected_Change']:.2f} µg/m³)"
)

print(
    f"Largest expected decrease:"
    f" {largest_decrease['City']}"
    f" ({largest_decrease['Expected_Change']:.2f} µg/m³)"
)


# ============================================================
# 14. IMPROVING / WORSENING CITIES
# ============================================================

increasing = comparison[
    comparison["Expected_Direction"] == "Increase"
]

decreasing = comparison[
    comparison["Expected_Direction"] == "Decrease"
]

stable = comparison[
    comparison["Expected_Direction"] == "Stable"
]


print("\n" + "=" * 90)
print("CITY TREND COMPARISON")
print("=" * 90)


print(
    "\nCities expected to worsen:",
    len(increasing)
)

if len(increasing) > 0:

    print(
        increasing[
            [
                "City",
                "Current_PM25",
                "Predicted_PM25_Next_1Hour",
                "Expected_Change"
            ]
        ].to_string(index=False)
    )


print(
    "\nCities expected to improve:",
    len(decreasing)
)

if len(decreasing) > 0:

    print(
        decreasing[
            [
                "City",
                "Current_PM25",
                "Predicted_PM25_Next_1Hour",
                "Expected_Change"
            ]
        ].to_string(index=False)
    )


print(
    "\nStable cities:",
    len(stable)
)


# ============================================================
# 15. CATEGORY DISTRIBUTION
# ============================================================

if "Predicted_Category" in comparison.columns:

    print("\n" + "=" * 90)
    print("PREDICTED POLLUTION CATEGORY DISTRIBUTION")
    print("=" * 90)

    print(
        comparison[
            "Predicted_Category"
        ].value_counts().to_string()
    )


# ============================================================
# 16. SAVE COMPLETE RESULT
# ============================================================

print("\n" + "=" * 90)
print("CITY COMPARISON COMPLETE")
print("=" * 90)

print("\nSaved:")
print(OUTPUT_FILE)

print("\n" + "=" * 90)