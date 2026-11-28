
import math
import json
from pathlib import Path

import pandas as pd
import numpy as np
import joblib

from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler, PolynomialFeatures
from sklearn.naive_bayes import GaussianNB
from sklearn.svm import SVC
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression, LinearRegression
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    mean_absolute_error,
    mean_squared_error,
    r2_score
)

# -------------------------------------------------
# 1. Load fused weather dataset
# -------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = PROJECT_ROOT / "dataset" / "processed" / "fused_weather_data.csv"
OUTPUT_DIR = PROJECT_ROOT / "ml_algorithm" / "results" / "metrics"
MODELS_DIR = PROJECT_ROOT / "ml_algorithm" / "results" / "models"

if not DATA_PATH.exists():
    raise FileNotFoundError(
        f"Fused weather dataset not found: {DATA_PATH}"
    )

df = pd.read_csv(DATA_PATH)
df.columns = df.columns.str.strip()

print("Dataset shape:", df.shape)
print("Available columns:", df.columns.tolist())
if len(df) < 4:
    raise ValueError(
        "At least 4 records are required to train and evaluate "
        "the regression models."
    )

# -------------------------------------------------
# 2. Select features and targets
# -------------------------------------------------
classification_target = "current_condition"
regression_target = "current_temperature_celsius"

classification_features = [
    "current_temperature_celsius",
    "historical_average_celsius",
    "historical_min_celsius",
    "historical_max_celsius",
    "current_humidity_percent",
    "current_wind_speed_kmh",
    "historical_records_used"
]

regression_features = [
    "historical_average_celsius",
    "historical_min_celsius",
    "historical_max_celsius",
    "current_humidity_percent",
    "current_wind_speed_kmh",
    "historical_records_used"
]

required = set(
    classification_features
    + regression_features
    + [classification_target, regression_target]
)

missing = required - set(df.columns)

if missing:
    raise ValueError(f"Missing dataset columns: {sorted(missing)}.")

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
MODELS_DIR.mkdir(parents=True, exist_ok=True)

# Convert selected fields to numeric
numeric_columns = set(classification_features + regression_features + [regression_target])
for col in numeric_columns:
    df[col] = pd.to_numeric(df[col], errors="coerce")

# -------------------------------------------------
# 3. Classification dataset
# -------------------------------------------------
classification_df = df[
    classification_features + [classification_target]
].dropna(subset=[classification_target]).copy()

X_cls = classification_df[classification_features]
y_cls = classification_df[classification_target]

# Keep classes with enough records to occur in both training and test sets.
counts = y_cls.value_counts()
valid_classes = counts[counts >= 2].index

classification_df = classification_df[classification_df[classification_target].isin(valid_classes)]

X_cls = classification_df[classification_features]
y_cls = classification_df[classification_target]

if y_cls.nunique() < 2:
    raise ValueError(
        "Classification requires at least two current_condition classes "
        "with at least 2 records each."
    )

classification_test_size = max(
    math.ceil(len(classification_df) * 0.2),
    y_cls.nunique()
)
if len(classification_df) - classification_test_size < y_cls.nunique():
    raise ValueError(
        "Not enough records to place every current_condition class "
        "in both the training and test sets."
    )

X_train_cls, X_test_cls, y_train_cls, y_test_cls = (
    train_test_split(
        X_cls,
        y_cls,
        test_size=classification_test_size,
        random_state=42,
        stratify=y_cls
    )
)
print(
    f"Classification split: {len(X_train_cls)} train / "
    f"{len(X_test_cls)} test records"
)

classification_models = {
    "Naive Bayes": GaussianNB(),
    "SVM": make_pipeline(
        SimpleImputer(strategy="median"),
        StandardScaler(),
        SVC()
    ),
    "Decision Tree": DecisionTreeClassifier(
        random_state=42,
        class_weight="balanced"
    ),
    "Random Forest": RandomForestClassifier(
        n_estimators=100,
        random_state=42,
        n_jobs=-1,
        class_weight="balanced"
    ),
    "Logistic Regression": make_pipeline(
        SimpleImputer(strategy="median"),
        StandardScaler(),
        LogisticRegression(
            max_iter=2000,
            class_weight="balanced"
        )
    )
}

classification_results = []

for name, model in classification_models.items():
    # Impute missing feature values for every model
    if name in ["Naive Bayes", "Decision Tree", "Random Forest"]:
        model = make_pipeline(
            SimpleImputer(strategy="median"),
            model
        )

    model.fit(X_train_cls, y_train_cls)
    predictions = model.predict(X_test_cls)

    classification_results.append({
        "Algorithm": name,
        "Accuracy": accuracy_score(y_test_cls, predictions),
        "Precision_weighted": precision_score(
            y_test_cls, predictions,
            average="weighted", zero_division=0
        ),
        "Recall_weighted": recall_score(
            y_test_cls, predictions,
            average="weighted", zero_division=0
        ),
        "F1_weighted": f1_score(
            y_test_cls, predictions,
            average="weighted", zero_division=0
        )
    })

    filename = (
        name.lower().replace(" ", "_")
        .replace("-", "_") + ".joblib"
    )
    joblib.dump(model, MODELS_DIR / filename)
    print(f"Trained: {name}")

# -------------------------------------------------
# 4. Regression dataset
# -------------------------------------------------
regression_df = df[
    regression_features + [regression_target]
].dropna(subset=[regression_target])

X_reg = regression_df[regression_features]
y_reg = regression_df[regression_target]
if len(regression_df) < 4:
    raise ValueError(
        f"Only {len(regression_df)} usable regression records remain; "
        "at least 4 are required."
    )

regression_test_size = max(2, math.ceil(len(regression_df) * 0.2))
X_train_reg, X_test_reg, y_train_reg, y_test_reg = (
    train_test_split(
        X_reg,
        y_reg,
        test_size=regression_test_size,
        random_state=42
    )
)
print(
    f"Regression split: {len(X_train_reg)} train / "
    f"{len(X_test_reg)} test records"
)

regression_results = []

def evaluate_regression(name, model, X_train, X_test):
    model.fit(X_train, y_train_reg)
    predictions = model.predict(X_test)

    regression_results.append({
        "Algorithm": name,
        "MAE": mean_absolute_error(y_test_reg, predictions),
        "RMSE": np.sqrt(mean_squared_error(y_test_reg, predictions)),
        "R2": r2_score(y_test_reg, predictions)
    })

    filename = (
        name.lower().replace(" ", "_")
        .replace("-", "_") + ".joblib"
    )
    joblib.dump(model, MODELS_DIR / filename)
    print(f"Trained: {name}")

# 6. Regression Analysis (Simple Linear Regression)
simple_features = ["historical_average_celsius"]
simple_model = make_pipeline(
    SimpleImputer(strategy="median"),
    LinearRegression()
)

evaluate_regression(
    "Regression Analysis (Simple Linear Regression)",
    simple_model,
    X_train_reg[simple_features],
    X_test_reg[simple_features]
)

# 7. Multiple Linear Regression
multiple_model = make_pipeline(
    SimpleImputer(strategy="median"),
    LinearRegression()
)

evaluate_regression(
    "Multiple Linear Regression",
    multiple_model,
    X_train_reg,
    X_test_reg
)

# 8. Polynomial Regression (degree 2)
polynomial_model = make_pipeline(
    SimpleImputer(strategy="median"),
    PolynomialFeatures(degree=2, include_bias=False),
    StandardScaler(),
    LinearRegression()
)

evaluate_regression(
    "Polynomial Regression",
    polynomial_model,
    X_train_reg[simple_features],
    X_test_reg[simple_features]
)

# -------------------------------------------------
# 5. Save results
# -------------------------------------------------
classification_results_df = pd.DataFrame(classification_results)
regression_results_df = pd.DataFrame(regression_results)

classification_results_df.to_csv(
    OUTPUT_DIR / "classification_results.csv",
    index=False
)

regression_results_df.to_csv(
    OUTPUT_DIR / "regression_results.csv",
    index=False
)

print("\nCLASSIFICATION RESULTS")
print(classification_results_df.to_string(index=False))

print("\nREGRESSION RESULTS")
print(regression_results_df.to_string(index=False))

print("\nAll model results saved in ml_algorithm/results.")

metadata = {
    "dataset_rows": len(df),
    "classification_rows": len(classification_df),
    "regression_rows": len(regression_df),
    "classification_algorithms": list(classification_models),
    "regression_algorithms": [
        "Regression Analysis (Simple Linear Regression)",
        "Multiple Linear Regression",
        "Polynomial Regression"
    ]
}

(OUTPUT_DIR / "model_metadata.json").write_text(
    json.dumps(metadata, indent=2),
    encoding="utf-8"
)
print(f"Model metadata saved to {OUTPUT_DIR / 'model_metadata.json'}")