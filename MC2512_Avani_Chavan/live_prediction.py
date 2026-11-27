from pathlib import Path
import joblib
import pickle
import pandas as pd
import numpy as np


# ============================================================
# MULTI-CITY AIR QUALITY - LIVE 1-HOUR PREDICTION
# 11 CITIES
# CPCB / STATE PCB HISTORICAL DATA + OPENWEATHER LIVE DATA
# ============================================================

FEATURE_FILE = Path("features/multi_city_hourly_features.csv")
MODEL_FILE = Path("models/random_forest_pm25.pkl")
FEATURE_INFO_FILE = Path("models/feature_info.pkl")
WEATHER_FILE = Path("live_data/openweather_current.csv")

OUTPUT_DIR = Path("live_data")
OUTPUT_DIR.mkdir(exist_ok=True)

OUTPUT_FILE = OUTPUT_DIR / "live_predictions.csv"


print("=" * 90)
print("MULTI-CITY AIR QUALITY - LIVE 1-HOUR PREDICTION")
print("11 CITIES - HISTORICAL DATA + OPENWEATHER LIVE DATA")
print("=" * 90)


# ============================================================
# 1. CHECK REQUIRED FILES
# ============================================================

required_files = [
    FEATURE_FILE,
    MODEL_FILE,
    FEATURE_INFO_FILE,
    WEATHER_FILE
]

for file in required_files:

    if not file.exists():

        print("\nERROR: Required file not found:")
        print(file)

        raise SystemExit(1)


# ============================================================
# 2. LOAD RANDOM FOREST MODEL
# ============================================================

print("\nLoading Random Forest model...")

try:

    model = joblib.load(MODEL_FILE)

except Exception:

    with open(MODEL_FILE, "rb") as f:
        model = pickle.load(f)


print("Model type:", type(model))


if not hasattr(model, "predict"):

    print("\nERROR: The loaded file is not a trained model.")
    print("Loaded object type:", type(model))

    print("\nPlease run:")
    print("python train_air_quality_model.py")

    raise SystemExit(1)


# ============================================================
# 3. LOAD FEATURE INFORMATION
# ============================================================

print("\nLoading feature information...")

try:

    feature_info = joblib.load(FEATURE_INFO_FILE)

except Exception:

    with open(FEATURE_INFO_FILE, "rb") as f:
        feature_info = pickle.load(f)


if isinstance(feature_info, dict):

    feature_names = (
        feature_info.get("feature_columns")
        or feature_info.get("features")
        or feature_info.get("model_features")
    )

else:

    feature_names = feature_info


if feature_names is None:

    print("\nERROR: Could not determine model feature names.")

    raise SystemExit(1)


feature_names = list(feature_names)

print("Number of model features:", len(feature_names))


# ============================================================
# 4. LOAD HISTORICAL FEATURE DATA
# ============================================================

print("\nLoading historical feature data:")
print(FEATURE_FILE)

df = pd.read_csv(
    FEATURE_FILE,
    low_memory=False
)

print("Historical rows:", len(df))


df["Timestamp"] = pd.to_datetime(
    df["Timestamp"],
    errors="coerce",
    utc=True
)


df["City"] = (
    df["City"]
    .astype(str)
    .str.strip()
)


df = df.dropna(
    subset=[
        "Timestamp",
        "City"
    ]
)


df = df.sort_values(
    [
        "City",
        "Timestamp"
    ]
).reset_index(drop=True)


# ============================================================
# 5. LOAD OPENWEATHER DATA
# ============================================================

print("\nLoading OpenWeather live data:")
print(WEATHER_FILE)

weather = pd.read_csv(
    WEATHER_FILE,
    low_memory=False
)

print("OpenWeather records:", len(weather))


print("\nOpenWeather columns:")

for col in weather.columns:

    print("-", col)


# ============================================================
# 6. NORMALIZE OPENWEATHER COLUMN NAMES
# ============================================================

weather = weather.rename(
    columns={

        "Temperature (°C)": "Temperature",
        "Temperature (Â°C)": "Temperature",

        "Humidity (%)": "Humidity",

        "Pressure (hPa)": "Pressure",

        "Wind_Speed (m/s)": "WindSpeed",

        "Wind_Direction (deg)": "WindDirection",

        "Rain_1h (mm)": "Rain1h"
    }
)


# ============================================================
# 7. DISPLAY WEATHER DATA
# ============================================================

display_columns = [

    "City",
    "Temperature",
    "Humidity",
    "Pressure",
    "WindSpeed",
    "WindDirection",
    "Rain1h",
    "Weather"
]


display_columns = [
    c
    for c in display_columns
    if c in weather.columns
]


print("\nOpenWeather data:")

print(
    weather[
        display_columns
    ].to_string(index=False)
)


# ============================================================
# 8. CREATE 11-CITY ONE-HOT FEATURES
# ============================================================

city_columns = [

    "City_Ahmedabad",
    "City_Bengaluru",
    "City_Chennai",
    "City_Delhi",
    "City_Hyderabad",
    "City_Jaipur",
    "City_Kolkata",
    "City_Mumbai",
    "City_Nagpur",
    "City_Nashik",
    "City_Pune"
]


for col in city_columns:

    city_name = col.replace(
        "City_",
        ""
    )

    df[col] = (
        df["City"]
        .eq(city_name)
        .astype(int)
    )


# ============================================================
# 9. GET LATEST HISTORICAL RECORD PER CITY
# ============================================================

latest = (

    df.sort_values(
        [
            "City",
            "Timestamp"
        ]
    )

    .groupby(
        "City",
        as_index=False
    )

    .tail(1)

    .copy()
)


print(
    "\nLatest historical records:",
    len(latest)
)


# ============================================================
# 10. MERGE LIVE WEATHER
# ============================================================

latest = latest.merge(
    weather,
    on="City",
    how="left"
)


# ============================================================
# 11. USE LIVE WEATHER VALUES
# ============================================================

if "Temperature" in latest.columns:

    latest["AT (°C)"] = latest[
        "Temperature"
    ]


if "Humidity" in latest.columns:

    latest["RH (%)"] = latest[
        "Humidity"
    ]


if "WindSpeed" in latest.columns:

    latest["WS (m/s)"] = latest[
        "WindSpeed"
    ]


if "WindDirection" in latest.columns:

    latest["WD (deg)"] = latest[
        "WindDirection"
    ]


# ============================================================
# 12. CHECK MODEL FEATURES
# ============================================================

missing_features = [

    col

    for col in feature_names

    if col not in latest.columns
]


if missing_features:

    print("\nERROR: Required model features are missing:")

    for col in missing_features:

        print("-", col)

    print("\nModel expects:")

    for col in feature_names:

        print("-", col)

    raise SystemExit(1)


# ============================================================
# 13. BUILD MODEL INPUT
# ============================================================

X = latest[
    feature_names
].copy()


# Convert everything to numeric

for col in X.columns:

    X[col] = pd.to_numeric(
        X[col],
        errors="coerce"
    )


# ============================================================
# 14. HANDLE MISSING MODEL INPUTS
# ============================================================

valid_mask = X.notna().all(
    axis=1
)


print(
    "\nComplete rows available for prediction:",
    valid_mask.sum()
)


if not valid_mask.any():

    print(
        "\nERROR: No complete rows available for prediction."
    )

    raise SystemExit(1)


# ============================================================
# 15. GENERATE PREDICTIONS
# ============================================================

print("\nGenerating predictions...")


latest["Predicted_PM25_Next_1Hour"] = np.nan


predictions = model.predict(
    X.loc[valid_mask]
)


latest.loc[
    valid_mask,
    "Predicted_PM25_Next_1Hour"
] = predictions


# ============================================================
# 16. CURRENT PM2.5
# ============================================================

if "PM25_Lag_1H" in latest.columns:

    latest["Current_PM25"] = latest[
        "PM25_Lag_1H"
    ]

else:

    latest["Current_PM25"] = np.nan


# ============================================================
# 17. EXPECTED CHANGE
# ============================================================

latest["Expected_Change"] = (

    latest["Predicted_PM25_Next_1Hour"]

    - latest["Current_PM25"]
)


# ============================================================
# 18. DIRECTION
# ============================================================

def direction(value):

    if pd.isna(value):

        return "Unknown"

    if value > 0.5:

        return "Increase"

    if value < -0.5:

        return "Decrease"

    return "Stable"


latest[
    "Expected_Direction"
] = latest[
    "Expected_Change"
].apply(direction)


# ============================================================
# 19. PM2.5 CATEGORY
# ============================================================

def category(value):

    if pd.isna(value):

        return "Unknown"

    if value <= 30:

        return "Good"

    if value <= 60:

        return "Satisfactory"

    if value <= 90:

        return "Moderate"

    if value <= 120:

        return "Poor"

    if value <= 250:

        return "Very Poor"

    return "Severe"


latest[
    "Predicted_Category"
] = latest[
    "Predicted_PM25_Next_1Hour"
].apply(category)


# ============================================================
# 20. OUTPUT
# ============================================================

output_columns = [

    "City",

    "Timestamp",

    "Current_PM25",

    "Predicted_PM25_Next_1Hour",

    "Expected_Change",

    "Expected_Direction",

    "Predicted_Category",

    "Temperature",

    "Humidity",

    "Pressure",

    "WindSpeed",

    "WindDirection",

    "Rain1h",

    "Weather"
]


output_columns = [

    col

    for col in output_columns

    if col in latest.columns
]


output = latest[
    output_columns
].copy()


# ============================================================
# 21. SORT CITIES
# ============================================================

city_order = [

    "Ahmedabad",
    "Bengaluru",
    "Chennai",
    "Delhi",
    "Hyderabad",
    "Jaipur",
    "Kolkata",
    "Mumbai",
    "Nagpur",
    "Nashik",
    "Pune"
]


output["City"] = pd.Categorical(
    output["City"],
    categories=city_order,
    ordered=True
)


output = output.sort_values(
    "City"
).reset_index(
    drop=True
)


# ============================================================
# 22. SAVE
# ============================================================

output.to_csv(
    OUTPUT_FILE,
    index=False
)


# ============================================================
# 23. DISPLAY RESULTS
# ============================================================

print("\n" + "=" * 90)
print("LIVE 1-HOUR PREDICTIONS")
print("=" * 90)


print(
    "\nCities predicted:",
    len(output)
)


print("\nPredictions:")

print(
    output.to_string(
        index=False
    )
)


print("\nSaved:")
print(OUTPUT_FILE)


print("\n" + "=" * 90)
print("LIVE PREDICTION COMPLETE")
print("=" * 90)