from pathlib import Path
import pandas as pd
import numpy as np


# ============================================================
# MULTI-CITY HOURLY AIR QUALITY - FEATURE ENGINEERING
# ============================================================

INPUT_FILE = Path(
    "live_data/city_historical_processed.csv"
)

OUTPUT_DIR = Path("features")
OUTPUT_DIR.mkdir(exist_ok=True)

OUTPUT_FILE = OUTPUT_DIR / "multi_city_hourly_features.csv"


print("=" * 90)
print("MULTI-CITY HOURLY AIR QUALITY - FEATURE ENGINEERING")
print("=" * 90)


# ------------------------------------------------------------
# 1. CHECK INPUT
# ------------------------------------------------------------

if not INPUT_FILE.exists():

    print("\nERROR: Combined city dataset not found:")
    print(INPUT_FILE)

    print("\nRun:")
    print("python process_city_datasets.py")

    raise SystemExit


# ------------------------------------------------------------
# 2. LOAD DATA
# ------------------------------------------------------------

df = pd.read_csv(
    INPUT_FILE,
    low_memory=False
)

print("\nInput rows:", len(df))
print("Input columns:", len(df.columns))


# ------------------------------------------------------------
# 3. CLEAN COLUMN NAMES
# ------------------------------------------------------------

df.columns = (
    df.columns
    .astype(str)
    .str.strip()
)


# ------------------------------------------------------------
# 4. TIMESTAMP
# ------------------------------------------------------------

df["Timestamp"] = pd.to_datetime(
    df["Timestamp"],
    errors="coerce"
)

df = df.dropna(
    subset=["Timestamp"]
).copy()


# ------------------------------------------------------------
# 5. CITY CLEANING
# ------------------------------------------------------------

df["City"] = (
    df["City"]
    .astype(str)
    .str.strip()
)

print("\nCities in input:")

print(
    sorted(
        df["City"]
        .dropna()
        .unique()
        .tolist()
    )
)


# ------------------------------------------------------------
# 6. PM2.5 COLUMN
# ------------------------------------------------------------

PM25 = "PM2.5 (µg/m³)"

if PM25 not in df.columns:

    print("\nERROR: PM2.5 column not found.")
    raise SystemExit


# ------------------------------------------------------------
# 7. SHOW PM2.5 AVAILABILITY
# ------------------------------------------------------------

print("\nPM2.5 availability by city:")

pm25_counts = (
    df.groupby("City")[PM25]
    .apply(lambda s: s.notna().sum())
    .sort_values(ascending=False)
)

print(pm25_counts.to_string())


# ------------------------------------------------------------
# 8. EXCLUDE CITIES WITHOUT PM2.5
# ------------------------------------------------------------

valid_cities = (
    pm25_counts[pm25_counts > 0]
    .index
    .tolist()
)

df = df[
    df["City"].isin(valid_cities)
].copy()

print("\nCities retained:")

print(
    sorted(
        df["City"].unique().tolist()
    )
)

print("\nCities excluded:")

all_cities = set(pm25_counts.index)
excluded = sorted(all_cities - set(valid_cities))

if excluded:
    for city in excluded:
        print("-", city)
else:
    print("None")


# ------------------------------------------------------------
# 9. SORT
# ------------------------------------------------------------

df = df.sort_values(
    ["City", "Timestamp"]
).reset_index(drop=True)


# ------------------------------------------------------------
# 10. TIME FEATURES
# ------------------------------------------------------------

df["Hour"] = df["Timestamp"].dt.hour

df["DayOfWeek"] = (
    df["Timestamp"].dt.dayofweek
)

df["DayOfMonth"] = (
    df["Timestamp"].dt.day
)

df["Month"] = (
    df["Timestamp"].dt.month
)

df["IsWeekend"] = (
    df["DayOfWeek"] >= 5
).astype(int)


# ------------------------------------------------------------
# 11. CYCLIC TIME FEATURES
# ------------------------------------------------------------

df["HourSin"] = np.sin(
    2 * np.pi * df["Hour"] / 24
)

df["HourCos"] = np.cos(
    2 * np.pi * df["Hour"] / 24
)

df["MonthSin"] = np.sin(
    2 * np.pi * df["Month"] / 12
)

df["MonthCos"] = np.cos(
    2 * np.pi * df["Month"] / 12
)


# ------------------------------------------------------------
# 12. ENVIRONMENTAL FEATURES
# ------------------------------------------------------------

numeric_features = [

    "PM10 (µg/m³)",
    "NO2 (µg/m³)",
    "NH3 (µg/m³)",
    "SO2 (µg/m³)",
    "CO (mg/m³)",
    "Ozone (µg/m³)",

    "AT (°C)",
    "RH (%)",
    "WS (m/s)",
    "WD (deg)"

]

numeric_features = [

    c for c in numeric_features
    if c in df.columns

]


# ------------------------------------------------------------
# 13. CONVERT NUMERIC VALUES
# ------------------------------------------------------------

for col in numeric_features + [PM25]:

    df[col] = pd.to_numeric(
        df[col],
        errors="coerce"
    )


# ------------------------------------------------------------
# 14. IMPUTE ENVIRONMENTAL FEATURES
# ------------------------------------------------------------
# Environmental inputs can have missing observations.
#
# First:
#   interpolate within each city
#
# Then:
#   fill any remaining values using the overall median.
#
# PM2.5 is NOT included here.
# PM2.5 remains a real observation because it is the target.


print("\nImputing environmental features...")

for col in numeric_features:

    missing_before = df[col].isna().sum()

    df[col] = (
        df.groupby("City")[col]
        .transform(
            lambda s:
            s.interpolate(
                method="linear",
                limit_direction="both"
            )
        )
    )

    remaining_missing = df[col].isna().sum()

    if remaining_missing > 0:

        median_value = df[col].median()

        if pd.notna(median_value):

            df[col] = df[col].fillna(
                median_value
            )

    missing_after = df[col].isna().sum()

    print(
        f"{col}: "
        f"{missing_before} missing -> "
        f"{missing_after} remaining"
    )


# ------------------------------------------------------------
# 15. PM2.5 HISTORY
# ------------------------------------------------------------
# PM2.5 history is used to create lag and rolling features.
#
# Missing historical PM2.5 values are interpolated only for
# constructing historical input features.
#
# The actual target is NEVER filled.


df["PM25_History"] = (
    df.groupby("City")[PM25]
    .transform(
        lambda s:
        s.interpolate(
            method="linear",
            limit_direction="both"
        )
    )
)


# ------------------------------------------------------------
# 16. LAG FEATURES
# ------------------------------------------------------------

for lag in [1, 3, 6, 24, 168]:

    df[f"PM25_Lag_{lag}H"] = (

        df.groupby("City")["PM25_History"]
        .shift(lag)

    )


# ------------------------------------------------------------
# 17. ROLLING FEATURES
# ------------------------------------------------------------

df["PM25_RollingMean_3H"] = (

    df.groupby("City")["PM25_History"]
    .transform(
        lambda s:
        s.shift(1)
        .rolling(
            window=3,
            min_periods=2
        )
        .mean()
    )

)


df["PM25_RollingMean_6H"] = (

    df.groupby("City")["PM25_History"]
    .transform(
        lambda s:
        s.shift(1)
        .rolling(
            window=6,
            min_periods=3
        )
        .mean()
    )

)


df["PM25_RollingMean_24H"] = (

    df.groupby("City")["PM25_History"]
    .transform(
        lambda s:
        s.shift(1)
        .rolling(
            window=24,
            min_periods=12
        )
        .mean()
    )

)


df["PM25_RollingStd_6H"] = (

    df.groupby("City")["PM25_History"]
    .transform(
        lambda s:
        s.shift(1)
        .rolling(
            window=6,
            min_periods=3
        )
        .std()
    )

)


# ------------------------------------------------------------
# 18. TARGET
# ------------------------------------------------------------
# Source data is hourly.
#
# shift(-1) = PM2.5 at the next hour.


df["Target_PM25_Next_1Hour"] = (

    df.groupby("City")[PM25]
    .shift(-1)

)


# ------------------------------------------------------------
# 19. TARGET MUST BE REAL
# ------------------------------------------------------------

before = len(df)

df = df.dropna(
    subset=[
        "Target_PM25_Next_1Hour"
    ]
).copy()


print(
    "\nRows removed because next-hour PM2.5 was missing:",
    before - len(df)
)


# ------------------------------------------------------------
# 20. REMOVE TEMPORARY HISTORY
# ------------------------------------------------------------

df = df.drop(
    columns=[
        "PM25_History"
    ],
    errors="ignore"
)


# ------------------------------------------------------------
# 21. FINAL FEATURES
# ------------------------------------------------------------

feature_columns = [

    "City",

    "Hour",
    "DayOfWeek",
    "DayOfMonth",
    "Month",
    "IsWeekend",

    "HourSin",
    "HourCos",
    "MonthSin",
    "MonthCos",

    "PM10 (µg/m³)",
    "NO2 (µg/m³)",
    "NH3 (µg/m³)",
    "SO2 (µg/m³)",
    "CO (mg/m³)",
    "Ozone (µg/m³)",

    "AT (°C)",
    "RH (%)",
    "WS (m/s)",
    "WD (deg)",

    "PM25_Lag_1H",
    "PM25_Lag_3H",
    "PM25_Lag_6H",
    "PM25_Lag_24H",
    "PM25_Lag_168H",

    "PM25_RollingMean_3H",
    "PM25_RollingMean_6H",
    "PM25_RollingMean_24H",
    "PM25_RollingStd_6H",

    "Target_PM25_Next_1Hour"

]


feature_columns = [

    c for c in feature_columns
    if c in df.columns

]


features = df[
    ["Timestamp"] + feature_columns
].copy()


# ------------------------------------------------------------
# 22. REMOVE ROWS WITH MISSING ML INPUTS
# ------------------------------------------------------------

required_ml_inputs = [

    c for c in feature_columns

    if c != "City"
    and c != "Target_PM25_Next_1Hour"

]


before = len(features)

features = features.dropna(
    subset=required_ml_inputs
).copy()


print(
    "\nRows removed because required ML inputs were missing:",
    before - len(features)
)


# ------------------------------------------------------------
# 23. FINAL SORT
# ------------------------------------------------------------

features = features.sort_values(
    ["City", "Timestamp"]
).reset_index(drop=True)


# ------------------------------------------------------------
# 24. SAVE
# ------------------------------------------------------------

features.to_csv(
    OUTPUT_FILE,
    index=False
)


# ------------------------------------------------------------
# 25. SUMMARY
# ------------------------------------------------------------

print("\n" + "=" * 90)
print("FEATURE ENGINEERING COMPLETE")
print("=" * 90)

print(
    "\nFinal rows:",
    len(features)
)

print(
    "Final columns:",
    len(features.columns)
)


print("\nCities:")

print(
    features["City"]
    .value_counts()
    .to_string()
)


print("\nDate range:")

print(
    features["Timestamp"].min(),
    "to",
    features["Timestamp"].max()
)


print("\nTarget:")
print("Target_PM25_Next_1Hour")


print("\nFeature columns:")

for col in features.columns:

    print("-", col)


print("\nSaved:")
print(OUTPUT_FILE)

print("=" * 90)