from pathlib import Path
import pickle
import requests
import pandas as pd
import numpy as np

from config import OPENWEATHER_API_KEY


# ============================================================
# OPENWEATHER + ML AIR QUALITY COMPARISON
# ============================================================

MODEL_FILE = Path("models/random_forest_pm25.pkl")
FEATURE_INFO_FILE = Path("models/feature_info.pkl")
FEATURE_FILE = Path("features/multi_city_hourly_features.csv")

OPENWEATHER_FILE = Path("live_data/openweather_current.csv")

OUTPUT_DIR = Path("live_data")
OUTPUT_DIR.mkdir(exist_ok=True)

OUTPUT_FILE = OUTPUT_DIR / "openweather_ml_comparison.csv"

OPENWEATHER_URL = (
    "https://api.openweathermap.org/data/2.5/weather"
)


# ============================================================
# CITIES
# ============================================================

CITIES = {
    "Ahmedabad": {
        "lat": 23.0225,
        "lon": 72.5714
    },
    "Bengaluru": {
        "lat": 12.9716,
        "lon": 77.5946
    },
    "Chennai": {
        "lat": 13.0827,
        "lon": 80.2707
    },
    "Delhi": {
        "lat": 28.6139,
        "lon": 77.2090
    },
    "Hyderabad": {
        "lat": 17.3850,
        "lon": 78.4867
    },
    "Jaipur": {
        "lat": 26.9124,
        "lon": 75.7873
    },
    "Kolkata": {
        "lat": 22.5726,
        "lon": 88.3639
    },
    "Nagpur": {
        "lat": 21.1458,
        "lon": 79.0882
    },
    "Nashik": {
        "lat": 19.9975,
        "lon": 73.7898
    }
}


# ============================================================
# HEADER
# ============================================================

print("=" * 90)
print("OPENWEATHER + ML AIR QUALITY COMPARISON")
print("=" * 90)


# ============================================================
# 1. CHECK FILES
# ============================================================

required_files = [
    MODEL_FILE,
    FEATURE_INFO_FILE,
    FEATURE_FILE
]

for file in required_files:

    if not file.exists():

        print("\nERROR: Required file not found:")
        print(file)

        raise SystemExit(1)


# ============================================================
# 2. CHECK API KEY
# ============================================================

if not OPENWEATHER_API_KEY:

    print("\nERROR: OpenWeather API key is missing.")

    raise SystemExit(1)

if OPENWEATHER_API_KEY == "YOUR_OPENWEATHER_API_KEY":

    print("\nERROR: Replace the API key in config.py")

    raise SystemExit(1)


# ============================================================
# 3. LOAD MODEL
# ============================================================

print("\nLoading Random Forest model...")

# joblib is preferred for sklearn models.
try:

    import joblib

    model = joblib.load(
        MODEL_FILE
    )

except Exception:

    with open(
        MODEL_FILE,
        "rb"
    ) as f:

        model = pickle.load(f)


print(
    "Model type:",
    type(model)
)


if not hasattr(model, "predict"):

    print(
        "\nERROR: Loaded object is not a trained model."
    )

    print(
        "Object type:",
        type(model)
    )

    raise SystemExit(1)


# ============================================================
# 4. LOAD FEATURE INFORMATION
# ============================================================

print("\nLoading feature information...")

with open(
    FEATURE_INFO_FILE,
    "rb"
) as f:

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

    print(
        "\nERROR: Could not determine model feature names."
    )

    raise SystemExit(1)


feature_names = list(
    feature_names
)


print(
    "Number of model features:",
    len(feature_names)
)


# ============================================================
# 5. LOAD HISTORICAL FEATURE DATA
# ============================================================

print("\nLoading feature data:")

print(
    FEATURE_FILE
)

df = pd.read_csv(
    FEATURE_FILE,
    low_memory=False
)


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
).reset_index(
    drop=True
)


print(
    "Rows available:",
    len(df)
)


# ============================================================
# 6. CITY ONE-HOT ENCODING
# ============================================================

for city in CITIES:

    column = f"City_{city}"

    df[column] = (
        df["City"]
        .eq(city)
        .astype(int)
    )


# ============================================================
# 7. SELECT LATEST RECORD FOR EACH CITY
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
    "\nLatest historical records available:",
    len(latest)
)


# ============================================================
# 8. BUILD MODEL INPUT
# ============================================================

missing_features = [
    column
    for column in feature_names
    if column not in latest.columns
]


if missing_features:

    print(
        "\nERROR: Required model features are missing:"
    )

    for column in missing_features:

        print(
            "-",
            column
        )

    raise SystemExit(1)


X = latest[
    feature_names
].copy()


# ============================================================
# 9. CONVERT NUMERIC FEATURES
# ============================================================

for column in X.columns:

    X[column] = pd.to_numeric(
        X[column],
        errors="coerce"
    )


valid_mask = X.notna().all(
    axis=1
)


print(
    "\nComplete ML rows:",
    valid_mask.sum()
)


if not valid_mask.any():

    print(
        "\nERROR: No complete rows available for prediction."
    )

    raise SystemExit(1)


# ============================================================
# 10. GENERATE ML PREDICTION
# ============================================================

print(
    "\nGenerating ML predictions..."
)


latest["Predicted_PM25_Next_1Hour"] = np.nan


latest.loc[
    valid_mask,
    "Predicted_PM25_Next_1Hour"
] = model.predict(
    X.loc[valid_mask]
)


# ============================================================
# 11. CURRENT PM2.5
# ============================================================

if "PM25_Lag_1H" in latest.columns:

    latest["Current_PM25"] = (
        latest["PM25_Lag_1H"]
    )

else:

    latest["Current_PM25"] = np.nan


# ============================================================
# 12. EXPECTED CHANGE
# ============================================================

latest["Expected_Change"] = (
    latest["Predicted_PM25_Next_1Hour"]
    - latest["Current_PM25"]
)


# ============================================================
# 13. DIRECTION
# ============================================================

def direction(value):

    if pd.isna(value):

        return "Unknown"

    if value > 0.5:

        return "Increase"

    if value < -0.5:

        return "Decrease"

    return "Stable"


latest["Expected_Direction"] = (
    latest["Expected_Change"]
    .apply(direction)
)


# ============================================================
# 14. PM2.5 CATEGORY
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


latest["Predicted_Category"] = (
    latest[
        "Predicted_PM25_Next_1Hour"
    ]
    .apply(category)
)


# ============================================================
# 15. FETCH CURRENT OPENWEATHER DATA
# ============================================================

print(
    "\nFetching current OpenWeather data..."
)


weather_records = []


for city, location in CITIES.items():

    print(
        f"\nOpenWeather: {city}"
    )

    params = {

        "lat": location["lat"],

        "lon": location["lon"],

        "appid": OPENWEATHER_API_KEY,

        "units": "metric"
    }


    try:

        response = requests.get(
            OPENWEATHER_URL,
            params=params,
            timeout=15
        )


        if response.status_code != 200:

            print(
                "ERROR:",
                response.status_code
            )

            try:

                error_data = response.json()

                print(
                    "Message:",
                    error_data.get(
                        "message",
                        "Unknown error"
                    )
                )

            except Exception:

                pass

            continue


        data = response.json()


        weather = data.get(
            "weather",
            [{}]
        )[0]


        main = data.get(
            "main",
            {}
        )


        wind = data.get(
            "wind",
            {}
        )


        clouds = data.get(
            "clouds",
            {}
        )


        rain = data.get(
            "rain",
            {}
        )


        record = {

            "City": city,

            "OpenWeather_Temperature_C":
                main.get("temp"),

            "OpenWeather_Humidity_pct":
                main.get("humidity"),

            "OpenWeather_Pressure_hPa":
                main.get("pressure"),

            "OpenWeather_WindSpeed_ms":
                wind.get("speed"),

            "OpenWeather_WindDirection_deg":
                wind.get("deg"),

            "OpenWeather_Clouds_pct":
                clouds.get("all"),

            "OpenWeather_Rain_1h_mm":
                rain.get("1h", 0),

            "OpenWeather_Weather":
                weather.get("main"),

            "OpenWeather_Description":
                weather.get("description")
        }


        weather_records.append(
            record
        )


        print(
            "Status: SUCCESS"
        )


    except requests.exceptions.RequestException as e:

        print(
            "ERROR:",
            e
        )


# ============================================================
# 16. CREATE WEATHER DATAFRAME
# ============================================================

weather_df = pd.DataFrame(
    weather_records
)


if weather_df.empty:

    print(
        "\nERROR: No OpenWeather data received."
    )

    raise SystemExit(1)


# ============================================================
# 17. MERGE ML + OPENWEATHER
# ============================================================

comparison = latest.merge(
    weather_df,
    on="City",
    how="left"
)


# ============================================================
# 18. CREATE COMPARISON INSIGHT
# ============================================================

def create_insight(row):

    predicted = row[
        "Predicted_PM25_Next_1Hour"
    ]

    current = row[
        "Current_PM25"
    ]

    humidity = row[
        "OpenWeather_Humidity_pct"
    ]

    wind = row[
        "OpenWeather_WindSpeed_ms"
    ]


    if pd.isna(predicted):

        return "Prediction unavailable"


    if predicted <= 30:

        quality = "Good"

    elif predicted <= 60:

        quality = "Satisfactory"

    elif predicted <= 90:

        quality = "Moderate"

    elif predicted <= 120:

        quality = "Poor"

    elif predicted <= 250:

        quality = "Very Poor"

    else:

        quality = "Severe"


    direction_value = (
        row["Expected_Direction"]
    )


    if pd.notna(current):

        change_text = (
            f"{direction_value} by "
            f"{abs(row['Expected_Change']):.2f} µg/m³"
        )

    else:

        change_text = direction_value


    weather_text = []


    if pd.notna(humidity):

        weather_text.append(
            f"humidity {humidity:.0f}%"
        )


    if pd.notna(wind):

        weather_text.append(
            f"wind {wind:.1f} m/s"
        )


    if weather_text:

        weather_part = (
            " | "
            + ", ".join(weather_text)
        )

    else:

        weather_part = ""


    return (
        f"{quality}; "
        f"{change_text}"
        f"{weather_part}"
    )


comparison["Comparison_Insight"] = (
    comparison.apply(
        create_insight,
        axis=1
    )
)


# ============================================================
# 19. FINAL OUTPUT
# ============================================================

output_columns = [

    "City",

    "Timestamp",

    "Current_PM25",

    "Predicted_PM25_Next_1Hour",

    "Expected_Change",

    "Expected_Direction",

    "Predicted_Category",

    "OpenWeather_Temperature_C",

    "OpenWeather_Humidity_pct",

    "OpenWeather_Pressure_hPa",

    "OpenWeather_WindSpeed_ms",

    "OpenWeather_WindDirection_deg",

    "OpenWeather_Clouds_pct",

    "OpenWeather_Rain_1h_mm",

    "OpenWeather_Weather",

    "OpenWeather_Description",

    "Comparison_Insight"
]


output = comparison[
    [
        column
        for column in output_columns
        if column in comparison.columns
    ]
].copy()


# ============================================================
# 20. SAVE
# ============================================================

output.to_csv(
    OUTPUT_FILE,
    index=False
)


# ============================================================
# 21. DISPLAY RESULTS
# ============================================================

print(
    "\n" + "=" * 90
)

print(
    "OPENWEATHER + ML COMPARISON RESULTS"
)

print(
    "=" * 90
)


display_columns = [

    "City",

    "Current_PM25",

    "Predicted_PM25_Next_1Hour",

    "Expected_Change",

    "Expected_Direction",

    "Predicted_Category",

    "OpenWeather_Temperature_C",

    "OpenWeather_Humidity_pct",

    "OpenWeather_WindSpeed_ms",

    "OpenWeather_Weather"
]


print(
    "\n"
)


print(
    output[
        [
            column
            for column in display_columns
            if column in output.columns
        ]
    ].to_string(
        index=False
    )
)


# ============================================================
# 22. SUMMARY
# ============================================================

print(
    "\n" + "=" * 90
)

print(
    "SUMMARY"
)

print(
    "=" * 90
)


print(
    "\nCities compared:",
    len(output)
)


print(
    "\nPredicted PM2.5 categories:"
)


print(
    output[
        "Predicted_Category"
    ]
    .value_counts()
    .to_string()
)


print(
    "\nExpected direction:"
)


print(
    output[
        "Expected_Direction"
    ]
    .value_counts()
    .to_string()
)


print(
    "\nSaved:"
)

print(
    OUTPUT_FILE
)


print(
    "\n" + "=" * 90
)

print(
    "OPENWEATHER + ML COMPARISON COMPLETE"
)

print(
    "=" * 90
)