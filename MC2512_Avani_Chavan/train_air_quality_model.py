from pathlib import Path
import pandas as pd
import numpy as np

from sklearn.ensemble import RandomForestRegressor, HistGradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.dummy import DummyRegressor
import joblib


# ============================================================
# AIR QUALITY - MULTI-CITY MODEL TRAINING
# ============================================================
# Input:
#   features/multi_city_hourly_features.csv
#
# Dataset:
#   2025 hourly air-quality data
#   9 usable cities
#
# Train/Test split:
#   Chronological 80% -> Training
#   Chronological 20% -> Testing
#
# Target:
#   PM2.5 at the next 1-hour timestamp
# ============================================================


INPUT_FILE = Path(
    "features/multi_city_hourly_features.csv"
)

MODEL_DIR = Path("models")
MODEL_DIR.mkdir(exist_ok=True)

RF_FILE = MODEL_DIR / "random_forest_pm25.pkl"
GB_FILE = MODEL_DIR / "gradient_boosting_pm25.pkl"


# ------------------------------------------------------------
# 1. LOAD DATA
# ------------------------------------------------------------

if not INPUT_FILE.exists():
    print("ERROR: Feature dataset not found:")
    print(INPUT_FILE)
    print("\nRun feature_engineering.py first.")
    raise SystemExit

df = pd.read_csv(
    INPUT_FILE,
    low_memory=False
)

print("=" * 90)
print("MULTI-CITY HOURLY AIR QUALITY - MODEL TRAINING")
print("=" * 90)

print("\nTotal records:", len(df))


# ------------------------------------------------------------
# 2. TIMESTAMP
# ------------------------------------------------------------

df["Timestamp"] = pd.to_datetime(
    df["Timestamp"],
    errors="coerce",
    utc=True
)

df = df.dropna(
    subset=["Timestamp"]
).copy()

# Keep each city's observations in chronological order.
df = df.sort_values(
    ["City", "Timestamp"]
).reset_index(drop=True)

print("\nCities in dataset:")
print(sorted(df["City"].astype(str).unique().tolist()))


# ------------------------------------------------------------
# 3. TARGET
# ------------------------------------------------------------

TARGET = "Target_PM25_Next_1Hour"

if TARGET not in df.columns:
    print("ERROR: Target column not found:")
    print(TARGET)
    raise SystemExit


# ------------------------------------------------------------
# 4. REMOVE NON-FEATURE COLUMNS
# ------------------------------------------------------------

# Timestamp is used for chronological splitting.
# It is not passed directly to the ML models.

EXCLUDE_COLUMNS = [
    "Timestamp",
    TARGET
]

feature_columns = [
    col
    for col in df.columns
    if col not in EXCLUDE_COLUMNS
]


# ------------------------------------------------------------
# 5. CITY ENCODING
# ------------------------------------------------------------

# Convert City into numeric one-hot columns.

if "City" not in df.columns:
    print("ERROR: City column not found.")
    raise SystemExit

df = pd.get_dummies(
    df,
    columns=["City"],
    dtype=int
)

# Rebuild feature list after one-hot encoding.
feature_columns = [
    col
    for col in df.columns
    if col not in EXCLUDE_COLUMNS
]


# ------------------------------------------------------------
# 6. REMOVE REMAINING MISSING VALUES
# ------------------------------------------------------------

before = len(df)

df = df.dropna(
    subset=feature_columns + [TARGET]
).copy()

print(
    "\nRows removed because of remaining missing values:",
    before - len(df)
)


# ------------------------------------------------------------
# 7. CHRONOLOGICAL TRAIN / TEST SPLIT
# ------------------------------------------------------------
# The complete dataset is from 2025, so a 2024/2025 split
# cannot be used.
#
# We use the first 80% of the chronological observations
# for training and the final 20% for testing.
#
# This avoids using future observations to train the model.

df = df.sort_values(
    ["Timestamp"]
).reset_index(drop=True)

split_index = int(len(df) * 0.80)

train_df = df.iloc[:split_index].copy()
test_df = df.iloc[split_index:].copy()

print("\n" + "=" * 90)
print("CHRONOLOGICAL DATA SPLIT")
print("=" * 90)

print("\nTraining period:")
print(
    train_df["Timestamp"].min(),
    "to",
    train_df["Timestamp"].max()
)

print(
    "Training records:",
    len(train_df)
)

print("\nTesting period:")
print(
    test_df["Timestamp"].min(),
    "to",
    test_df["Timestamp"].max()
)

print(
    "Testing records:",
    len(test_df)
)


# ------------------------------------------------------------
# 8. X / Y
# ------------------------------------------------------------

X_train = train_df[feature_columns]
y_train = train_df[TARGET]

X_test = test_df[feature_columns]
y_test = test_df[TARGET]

print("\nNumber of model features:", len(feature_columns))


# ------------------------------------------------------------
# 9. BASELINE MODEL
# ------------------------------------------------------------
# Baseline predicts the average training PM2.5.
# This gives us a reference point.

print("\n" + "=" * 90)
print("BASELINE MODEL")
print("=" * 90)

baseline = DummyRegressor(
    strategy="mean"
)

baseline.fit(
    X_train,
    y_train
)

baseline_prediction = baseline.predict(
    X_test
)

baseline_mae = mean_absolute_error(
    y_test,
    baseline_prediction
)

baseline_rmse = np.sqrt(
    mean_squared_error(
        y_test,
        baseline_prediction
    )
)

baseline_r2 = r2_score(
    y_test,
    baseline_prediction
)

print(
    f"MAE : {baseline_mae:.4f}"
)

print(
    f"RMSE: {baseline_rmse:.4f}"
)

print(
    f"R²  : {baseline_r2:.4f}"
)


# ------------------------------------------------------------
# 10. RANDOM FOREST
# ------------------------------------------------------------

print("\n" + "=" * 90)
print("RANDOM FOREST TRAINING")
print("=" * 90)

rf_model = RandomForestRegressor(
    n_estimators=250,
    max_depth=25,
    min_samples_leaf=2,
    random_state=42,
    n_jobs=-1
)

print("\nTraining Random Forest...")

rf_model.fit(
    X_train,
    y_train
)

rf_prediction = rf_model.predict(
    X_test
)


# ------------------------------------------------------------
# 11. RANDOM FOREST METRICS
# ------------------------------------------------------------

rf_mae = mean_absolute_error(
    y_test,
    rf_prediction
)

rf_rmse = np.sqrt(
    mean_squared_error(
        y_test,
        rf_prediction
    )
)

rf_r2 = r2_score(
    y_test,
    rf_prediction
)

print("\nRandom Forest Results:")

print(
    f"MAE : {rf_mae:.4f}"
)

print(
    f"RMSE: {rf_rmse:.4f}"
)

print(
    f"R²  : {rf_r2:.4f}"
)


# ------------------------------------------------------------
# 12. HISTOGRAM GRADIENT BOOSTING
# ------------------------------------------------------------

print("\n" + "=" * 90)
print("GRADIENT BOOSTING TRAINING")
print("=" * 90)

gb_model = HistGradientBoostingRegressor(
    max_iter=300,
    learning_rate=0.05,
    max_leaf_nodes=31,
    l2_regularization=1.0,
    random_state=42
)

print("\nTraining Gradient Boosting...")

gb_model.fit(
    X_train,
    y_train
)

gb_prediction = gb_model.predict(
    X_test
)


# ------------------------------------------------------------
# 13. GRADIENT BOOSTING METRICS
# ------------------------------------------------------------

gb_mae = mean_absolute_error(
    y_test,
    gb_prediction
)

gb_rmse = np.sqrt(
    mean_squared_error(
        y_test,
        gb_prediction
    )
)

gb_r2 = r2_score(
    y_test,
    gb_prediction
)

print("\nGradient Boosting Results:")

print(
    f"MAE : {gb_mae:.4f}"
)

print(
    f"RMSE: {gb_rmse:.4f}"
)

print(
    f"R²  : {gb_r2:.4f}"
)


# ------------------------------------------------------------
# 14. MODEL COMPARISON
# ------------------------------------------------------------

results = pd.DataFrame({

    "Model": [
        "Baseline",
        "Random Forest",
        "Gradient Boosting"
    ],

    "MAE": [
        baseline_mae,
        rf_mae,
        gb_mae
    ],

    "RMSE": [
        baseline_rmse,
        rf_rmse,
        gb_rmse
    ],

    "R2": [
        baseline_r2,
        rf_r2,
        gb_r2
    ]

})


print("\n" + "=" * 90)
print("MODEL COMPARISON")
print("=" * 90)

print(
    results
    .round(4)
    .to_string(index=False)
)


# ------------------------------------------------------------
# 15. SELECT BEST MODEL
# ------------------------------------------------------------
# Lower MAE is better.

if rf_mae <= gb_mae:

    best_model = rf_model
    best_name = "Random Forest"

else:

    best_model = gb_model
    best_name = "Gradient Boosting"


print("\nBest model based on MAE:")
print(best_name)


# ------------------------------------------------------------
# 16. SAVE MODELS
# ------------------------------------------------------------

joblib.dump(
    rf_model,
    RF_FILE
)

joblib.dump(
    gb_model,
    GB_FILE
)

# Save feature names so the prediction program can create
# exactly the same input structure later.

feature_info = {
    "feature_columns": feature_columns,
    "target": TARGET,
    "model_type": best_name
}

joblib.dump(
    feature_info,
    MODEL_DIR / "feature_info.pkl"
)


# ------------------------------------------------------------
# 17. FEATURE IMPORTANCE
# ------------------------------------------------------------

print("\n" + "=" * 90)
print("RANDOM FOREST FEATURE IMPORTANCE")
print("=" * 90)

importance = pd.DataFrame({

    "Feature": feature_columns,

    "Importance": rf_model.feature_importances_

})

importance = importance.sort_values(
    "Importance",
    ascending=False
)

print(
    importance.head(20)
    .round(6)
    .to_string(index=False)
)

importance.to_csv(
    MODEL_DIR / "feature_importance.csv",
    index=False
)


# ------------------------------------------------------------
# 18. SAVE TEST PREDICTIONS
# ------------------------------------------------------------

prediction_output = test_df[
    ["Timestamp"]
].copy()

# Recover city from one-hot columns for reporting.
city_columns = [
    c for c in feature_columns
    if c.startswith("City_")
]

if city_columns:

    city_matrix = test_df[city_columns]

    prediction_output["City"] = (
        city_matrix
        .idxmax(axis=1)
        .str.replace(
            "City_",
            "",
            regex=False
        )
        .values
    )

else:

    prediction_output["City"] = "Unknown"


prediction_output["Actual_PM25"] = y_test.values

prediction_output["RandomForest_Prediction"] = (
    rf_prediction
)

prediction_output["GradientBoosting_Prediction"] = (
    gb_prediction
)

prediction_output.to_csv(
    MODEL_DIR / "test_predictions.csv",
    index=False
)


# ------------------------------------------------------------
# 19. FINAL SUMMARY
# ------------------------------------------------------------

print("\n" + "=" * 90)
print("MODEL TRAINING COMPLETE")
print("=" * 90)

print("\nTraining records:", len(train_df))
print("Testing records :", len(test_df))

print("\nBaseline:")
print(
    f"MAE={baseline_mae:.4f}, "
    f"RMSE={baseline_rmse:.4f}, "
    f"R²={baseline_r2:.4f}"
)

print("\nRandom Forest:")
print(
    f"MAE={rf_mae:.4f}, "
    f"RMSE={rf_rmse:.4f}, "
    f"R²={rf_r2:.4f}"
)

print("\nGradient Boosting:")
print(
    f"MAE={gb_mae:.4f}, "
    f"RMSE={gb_rmse:.4f}, "
    f"R²={gb_r2:.4f}"
)

print("\nSelected model:", best_name)

print("\nSaved files:")

print("-", RF_FILE)
print("-", GB_FILE)
print("-", MODEL_DIR / "feature_info.pkl")
print("-", MODEL_DIR / "feature_importance.csv")
print("-", MODEL_DIR / "test_predictions.csv")

print("\n" + "=" * 90)