from pathlib import Path
import pandas as pd
import joblib


# ============================================================
# AIR QUALITY - NEXT 15-MINUTE PREDICTION
# ============================================================
# Uses the already trained Random Forest model.
#
# This script is a VALIDATION/PREDICTION layer:
# it takes the latest available feature record for Mumbai
# and Pune from the prepared dataset and predicts PM2.5
# for the next 15 minutes.
#
# It does NOT create fake sensor data.
# ============================================================


FEATURE_FILE = Path(
    "features/air_quality_features.csv"
)

MODEL_FILE = Path(
    "models/random_forest_pm25.pkl"
)

FEATURE_INFO_FILE = Path(
    "models/feature_info.pkl"
)


# ------------------------------------------------------------
# 1. CHECK FILES
# ------------------------------------------------------------

for file in [
    FEATURE_FILE,
    MODEL_FILE,
    FEATURE_INFO_FILE
]:

    if not file.exists():

        print("ERROR: Required file not found:")
        print(file)

        raise SystemExit


# ------------------------------------------------------------
# 2. LOAD MODEL AND DATA
# ------------------------------------------------------------

print("=" * 90)
print("AIR QUALITY - NEXT 15-MINUTE PREDICTION")
print("=" * 90)

df = pd.read_csv(
    FEATURE_FILE,
    low_memory=False
)

model = joblib.load(
    MODEL_FILE
)

feature_info = joblib.load(
    FEATURE_INFO_FILE
)

model_features = feature_info["feature_columns"]


# ------------------------------------------------------------
# 3. CONVERT TIMESTAMP
# ------------------------------------------------------------

df["Timestamp"] = pd.to_datetime(
    df["Timestamp"],
    errors="coerce",
    utc=True
)

df = df.dropna(
    subset=["Timestamp"]
).copy()


# ------------------------------------------------------------
# 4. CITY ENCODING
# ------------------------------------------------------------
# The training script converted City into:
#
# City_Mumbai
# City_Pune
#
# We recreate exactly the same columns.

df = pd.get_dummies(
    df,
    columns=["City"],
    dtype=int
)


# ------------------------------------------------------------
# 5. MAKE SURE ALL MODEL FEATURES EXIST
# ------------------------------------------------------------

for col in model_features:

    if col not in df.columns:

        df[col] = 0


# Keep exactly the feature order used during training.

X = df[
    model_features
]


# ------------------------------------------------------------
# 6. PREDICT FOR LATEST RECORD OF EACH CITY
# ------------------------------------------------------------

city_columns = [
    col
    for col in model_features
    if col.startswith("City_")
]


# Find the city represented by each row.

if not city_columns:

    print(
        "ERROR: City encoding columns were not found."
    )

    raise SystemExit


df["_City"] = (
    df[city_columns]
    .idxmax(axis=1)
    .str.replace(
        "City_",
        "",
        regex=False
    )
)


print("\nAvailable cities:")

for city in sorted(
    df["_City"].unique()
):

    print("-", city)


# ------------------------------------------------------------
# 7. PREDICT EACH CITY
# ------------------------------------------------------------

print("\n" + "=" * 90)
print("LATEST PREDICTIONS")
print("=" * 90)


for city in sorted(
    df["_City"].unique()
):

    city_df = df[
        df["_City"] == city
    ].copy()

    city_df = city_df.sort_values(
        "Timestamp"
    )

    latest = city_df.iloc[-1]

    latest_features = pd.DataFrame(
        [latest[model_features].values],
        columns=model_features
    )

    prediction = model.predict(
        latest_features
    )[0]


    # --------------------------------------------------------
    # Current PM2.5
    # --------------------------------------------------------

    current_pm25 = latest.get(
        "PM25_Lag_1",
        None
    )

    if pd.notna(current_pm25):

        change = (
            prediction -
            float(current_pm25)
        )

    else:

        change = None


    # --------------------------------------------------------
    # Air-quality interpretation
    # --------------------------------------------------------

    if prediction <= 30:

        category = "Good"

    elif prediction <= 60:

        category = "Satisfactory"

    elif prediction <= 90:

        category = "Moderate"

    elif prediction <= 120:

        category = "Poor"

    elif prediction <= 250:

        category = "Very Poor"

    else:

        category = "Severe"


    print("\n" + "-" * 70)

    print(
        "City:",
        city
    )

    print(
        "Latest timestamp:",
        latest["Timestamp"]
    )

    if current_pm25 is not None:

        print(
            f"Latest PM2.5: {float(current_pm25):.2f} µg/m³"
        )

    print(
        f"Predicted PM2.5 after 15 minutes: "
        f"{prediction:.2f} µg/m³"
    )

    if change is not None:

        if change > 0:

            direction = "increase"

        elif change < 0:

            direction = "decrease"

        else:

            direction = "no change"

        print(
            f"Expected change: {abs(change):.2f} µg/m³ "
            f"({direction})"
        )

    print(
        "Predicted category:",
        category
    )


print("\n" + "=" * 90)
print("PREDICTION COMPLETE")
print("=" * 90)