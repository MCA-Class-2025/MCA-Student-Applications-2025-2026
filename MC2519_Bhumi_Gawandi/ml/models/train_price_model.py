import warnings
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from sklearn.compose import ColumnTransformer
from sklearn.ensemble import (
    GradientBoostingRegressor,
    RandomForestRegressor
)
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LinearRegression
from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
    r2_score
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder


warnings.filterwarnings("ignore")


# ============================================================
# PATHS
# File location:
# ml/models/train_price_model.py
# ============================================================

ML_ROOT = Path(__file__).resolve().parents[1]

DATASET_DIR = ML_ROOT / "dataset" / "processed"
MODEL_DIR = ML_ROOT / "models" / "saved"
RESULT_DIR = ML_ROOT / "models" / "results"

MODEL_DIR.mkdir(parents=True, exist_ok=True)
RESULT_DIR.mkdir(parents=True, exist_ok=True)


GROCERY_FILE = DATASET_DIR / "grocery_price_history.csv"
ELECTRONICS_FILE = DATASET_DIR / "electronics_price_history.csv"


# ============================================================
# EXACT FEATURES USED BY BOTH TRAINING AND PREDICTION
# ============================================================

NUMERIC_FEATURES = [
    "Price",
    "PreviousPrice",
    "PriceLag2",
    "PriceLag3",
    "RollingMean",
    "RollingMedian",
    "PriceTrend",
    "PriceChange",
    "PriceChangePercent",
    "PriceRatio",
    "Year",
    "Month",
    "Quarter"
]

GROCERY_CATEGORICAL_FEATURES = [
    "Product"
]

ELECTRONICS_CATEGORICAL_FEATURES = [
    "Product",
    "Category",
    "Brand"
]


# ============================================================
# OPTIONAL XGBOOST
# ============================================================

try:
    from xgboost import XGBRegressor
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False


# ============================================================
# HELPERS
# ============================================================

def clean_text(series):
    return (
        series
        .fillna("Unknown")
        .astype(str)
        .str.strip()
    )


def calculate_metrics(y_true, y_pred):
    return {
        "MAE": float(
            mean_absolute_error(
                y_true,
                y_pred
            )
        ),
        "RMSE": float(
            np.sqrt(
                mean_squared_error(
                    y_true,
                    y_pred
                )
            )
        ),
        "R2": float(
            r2_score(
                y_true,
                y_pred
            )
        )
    }


# ============================================================
# LOAD DATA
# ============================================================

def load_dataset(file_path, dataset_type):

    if not file_path.exists():
        raise FileNotFoundError(
            f"Dataset not found:\n{file_path}"
        )

    df = pd.read_csv(file_path)

    if df.empty:
        raise ValueError(
            f"Dataset is empty:\n{file_path}"
        )

    required = [
        "Date",
        "Product",
        "Price"
    ]

    missing = [
        column
        for column in required
        if column not in df.columns
    ]

    if missing:
        raise ValueError(
            f"{dataset_type} dataset is missing columns: "
            f"{missing}"
        )

    df["Date"] = pd.to_datetime(
        df["Date"],
        errors="coerce"
    )

    df["Price"] = pd.to_numeric(
        df["Price"],
        errors="coerce"
    )

    df = df.dropna(
        subset=[
            "Date",
            "Product",
            "Price"
        ]
    ).copy()

    df = df[
        df["Price"] > 0
    ].copy()

    df["Product"] = clean_text(
        df["Product"]
    )

    if dataset_type == "electronics":

        if "Category" not in df.columns:
            df["Category"] = "Electronics"

        if "Brand" not in df.columns:
            df["Brand"] = "Unknown"

        df["Category"] = clean_text(
            df["Category"]
        )

        df["Brand"] = clean_text(
            df["Brand"]
        )

        df["ProductKey"] = (
            df["Product"]
            + " | "
            + df["Brand"]
            + " | "
            + df["Category"]
        )

    else:

        df["ProductKey"] = df["Product"]

    df = (
        df
        .sort_values(
            [
                "ProductKey",
                "Date"
            ]
        )
        .reset_index(drop=True)
    )

    return df


# ============================================================
# FEATURE ENGINEERING
# ============================================================

def create_features(df):

    df = df.copy()

    grouped_price = (
        df.groupby("ProductKey")["Price"]
    )

    # Previous historical price
    df["PreviousPrice"] = (
        grouped_price.shift(1)
    )

    # Two records back
    df["PriceLag2"] = (
        grouped_price.shift(2)
    )

    # Three records back
    df["PriceLag3"] = (
        grouped_price.shift(3)
    )

    # Previous 3 historical records only
    df["RollingMean"] = (
        grouped_price
        .transform(
            lambda x:
            x.shift(1)
            .rolling(
                window=3,
                min_periods=1
            )
            .mean()
        )
    )

    df["RollingMedian"] = (
        grouped_price
        .transform(
            lambda x:
            x.shift(1)
            .rolling(
                window=3,
                min_periods=1
            )
            .median()
        )
    )

    # Price change from previous record
    df["PriceChange"] = (
        df["Price"]
        -
        df["PreviousPrice"]
    )

    # Percentage change
    df["PriceChangePercent"] = np.where(
        df["PreviousPrice"].notna()
        &
        (df["PreviousPrice"] != 0),
        (
            (
                df["Price"]
                -
                df["PreviousPrice"]
            )
            /
            df["PreviousPrice"]
        ) * 100,
        0.0
    )

    # Current / previous ratio
    df["PriceRatio"] = np.where(
        df["PreviousPrice"].notna()
        &
        (df["PreviousPrice"] != 0),
        df["Price"] / df["PreviousPrice"],
        1.0
    )

    # Trend against previous rolling mean
    df["PriceTrend"] = np.where(
        df["RollingMean"].notna()
        &
        (df["RollingMean"] != 0),
        (
            (
                df["Price"]
                -
                df["RollingMean"]
            )
            /
            df["RollingMean"]
        ) * 100,
        0.0
    )

    # Calendar features
    df["Year"] = df["Date"].dt.year
    df["Month"] = df["Date"].dt.month
    df["Quarter"] = df["Date"].dt.quarter

    # Next price
    df["FuturePrice"] = (
        grouped_price.shift(-1)
    )

    # Target = next price / current price
    df["FuturePriceRatio"] = (
        df["FuturePrice"]
        /
        df["Price"]
    )

    df = df.replace(
        [np.inf, -np.inf],
        np.nan
    )

    # Rows without previous history or future target
    df = df.dropna(
        subset=[
            "PreviousPrice",
            "PriceLag2",
            "PriceLag3",
            "RollingMean",
            "RollingMedian",
            "FuturePrice",
            "FuturePriceRatio"
        ]
    ).copy()

    # Protect against corrupt/extreme records
    df = df[
        (df["FuturePriceRatio"] >= 0.10)
        &
        (df["FuturePriceRatio"] <= 10.0)
    ].copy()

    return df


# ============================================================
# BUILD PREPROCESSOR
# ============================================================

def build_preprocessor(
    numeric_features,
    categorical_features
):

    numeric_pipeline = Pipeline(
        steps=[
            (
                "imputer",
                SimpleImputer(
                    strategy="median"
                )
            )
        ]
    )

    categorical_pipeline = Pipeline(
        steps=[
            (
                "imputer",
                SimpleImputer(
                    strategy="most_frequent"
                )
            ),
            (
                "onehot",
                OneHotEncoder(
                    handle_unknown="ignore"
                )
            )
        ]
    )

    return ColumnTransformer(
        transformers=[
            (
                "numeric",
                numeric_pipeline,
                numeric_features
            ),
            (
                "categorical",
                categorical_pipeline,
                categorical_features
            )
        ]
    )


# ============================================================
# MODELS
# ============================================================

def get_models():

    models = {
        "Linear Regression":
            LinearRegression(),

        "Random Forest":
            RandomForestRegressor(
                n_estimators=250,
                max_depth=12,
                min_samples_leaf=2,
                random_state=42,
                n_jobs=-1
            ),

        "Gradient Boosting":
            GradientBoostingRegressor(
                n_estimators=250,
                learning_rate=0.05,
                max_depth=3,
                min_samples_leaf=2,
                random_state=42
            )
    }

    if XGBOOST_AVAILABLE:
        models["XGBoost"] = XGBRegressor(
            n_estimators=300,
            learning_rate=0.05,
            max_depth=5,
            min_child_weight=2,
            subsample=0.8,
            colsample_bytree=0.8,
            objective="reg:squarederror",
            random_state=42,
            n_jobs=-1
        )

    return models


# ============================================================
# TRAIN ONE DATASET
# ============================================================

def train_dataset(
    file_path,
    dataset_type
):

    print("\n" + "=" * 70)
    print(
        f"TRAINING {dataset_type.upper()} PRICE MODEL"
    )
    print("=" * 70)

    df = load_dataset(
        file_path,
        dataset_type
    )

    print(
        "Original records:",
        len(df)
    )

    df = create_features(df)

    print(
        "Records after feature engineering:",
        len(df)
    )

    if len(df) < 10:
        raise ValueError(
            f"Not enough records to train {dataset_type} model."
        )

    if dataset_type == "electronics":
        categorical_features = (
            ELECTRONICS_CATEGORICAL_FEATURES
        )
    else:
        categorical_features = (
            GROCERY_CATEGORICAL_FEATURES
        )

    # Ensure every feature exists
    missing = [
        column
        for column in (
            NUMERIC_FEATURES
            +
            categorical_features
        )
        if column not in df.columns
    ]

    if missing:
        raise ValueError(
            f"Training features are missing: {missing}"
        )

    X = df[
        NUMERIC_FEATURES
        +
        categorical_features
    ].copy()

    # --------------------------------------------------------
    # TARGET
    #
    # Model learns log(next_price / current_price)
    # --------------------------------------------------------

    ratio = pd.to_numeric(
        df["FuturePriceRatio"],
        errors="coerce"
    )

    valid = (
        ratio.notna()
        &
        np.isfinite(ratio)
        &
        (ratio > 0)
    )

    X = X.loc[valid].reset_index(drop=True)
    ratio = ratio.loc[valid].reset_index(drop=True)

    y = np.log(ratio)

    # --------------------------------------------------------
    # Chronological split
    # --------------------------------------------------------

    split_index = int(
        len(X) * 0.80
    )

    if split_index <= 0 or split_index >= len(X):
        raise ValueError(
            "Unable to create train/test split."
        )

    X_train = X.iloc[
        :split_index
    ].copy()

    X_test = X.iloc[
        split_index:
    ].copy()

    y_train = y.iloc[
        :split_index
    ].copy()

    y_test = y.iloc[
        split_index:
    ].copy()

    print(
        "Training records:",
        len(X_train)
    )

    print(
        "Testing records:",
        len(X_test)
    )

    print(
        "Numeric features:",
        NUMERIC_FEATURES
    )

    print(
        "Categorical features:",
        categorical_features
    )

    print(
        "Target: log(FuturePriceRatio)"
    )

    models = get_models()

    results = []
    trained = {}

    for model_name, estimator in models.items():

        print("\n" + "-" * 60)
        print(
            f"Training: {model_name}"
        )
        print("-" * 60)

        preprocessor = build_preprocessor(
            NUMERIC_FEATURES,
            categorical_features
        )

        pipeline = Pipeline(
            steps=[
                (
                    "preprocessor",
                    preprocessor
                ),
                (
                    "model",
                    estimator
                )
            ]
        )

        pipeline.fit(
            X_train,
            y_train
        )

        predicted_log_ratio = (
            pipeline.predict(
                X_test
            )
        )

        predicted_ratio = np.exp(
            predicted_log_ratio
        )

        actual_ratio = np.exp(
            y_test.to_numpy()
        )

        # Safety only for evaluation
        predicted_ratio = np.clip(
            predicted_ratio,
            0.70,
            1.30
        )

        metrics = calculate_metrics(
            actual_ratio,
            predicted_ratio
        )

        print(
            "MAE:",
            round(metrics["MAE"], 6)
        )

        print(
            "RMSE:",
            round(metrics["RMSE"], 6)
        )

        print(
            "R2:",
            round(metrics["R2"], 6)
        )

        results.append(
            {
                "Dataset":
                    dataset_type,

                "Model":
                    model_name,

                "MAE":
                    metrics["MAE"],

                "RMSE":
                    metrics["RMSE"],

                "R2":
                    metrics["R2"]
            }
        )

        trained[
            model_name
        ] = pipeline

    results_df = pd.DataFrame(
        results
    ).sort_values(
        "R2",
        ascending=False
    ).reset_index(
        drop=True
    )

    print("\n" + "=" * 70)
    print(
        f"{dataset_type.upper()} MODEL COMPARISON"
    )
    print("=" * 70)

    print(
        results_df.to_string(
            index=False
        )
    )

    best_model_name = (
        results_df.iloc[0]["Model"]
    )

    best_model = trained[
        best_model_name
    ]

    # --------------------------------------------------------
    # SAVE ONE STANDARD MODEL NAME
    # --------------------------------------------------------

    model_path = (
        MODEL_DIR
        /
        f"{dataset_type}_price_model.pkl"
    )

    # Save model + metadata together
    package = {
        "model": best_model,
        "model_name": best_model_name,
        "dataset_type": dataset_type,
        "numeric_features": NUMERIC_FEATURES,
        "categorical_features": categorical_features,
        "target": "log(FuturePriceRatio)"
    }

    joblib.dump(
        package,
        model_path
    )

    result_path = (
        RESULT_DIR
        /
        f"{dataset_type}_price_model_results.csv"
    )

    results_df.to_csv(
        result_path,
        index=False
    )

    print("\nBest model:")
    print(
        best_model_name
    )

    print("\nSaved model:")
    print(
        model_path
    )

    print("\nSaved results:")
    print(
        result_path
    )

    return (
        best_model,
        best_model_name,
        results_df
    )


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    print("\n")
    print("=" * 70)
    print("AI SMART EXPENSE TRACKER")
    print("FUTURE PRICE PREDICTION TRAINING")
    print("=" * 70)

    print(
        "\nML root:",
        ML_ROOT
    )

    print(
        "Dataset directory:",
        DATASET_DIR
    )

    print(
        "Model directory:",
        MODEL_DIR
    )

    print(
        "\nXGBoost available:",
        XGBOOST_AVAILABLE
    )

    train_dataset(
        GROCERY_FILE,
        "grocery"
    )

    train_dataset(
        ELECTRONICS_FILE,
        "electronics"
    )

    print("\n" + "=" * 70)
    print("PRICE MODEL TRAINING COMPLETED")
    print("=" * 70)
    print(
        "\nCreated:"
    )
    print(
        MODEL_DIR / "grocery_price_model.pkl"
    )
    print(
        MODEL_DIR / "electronics_price_model.pkl"
    )