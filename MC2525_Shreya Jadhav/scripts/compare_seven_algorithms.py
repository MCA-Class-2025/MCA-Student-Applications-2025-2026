"""Reproducible, leakage-aware comparison of seven models on the fused CSV.

Run from the repository root: python scripts/compare_seven_algorithms.py
This is an academic retrospective analysis, not a clinical prediction tool.
"""

from __future__ import annotations

import json
from pathlib import Path
from time import perf_counter

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    mean_absolute_error,
    mean_squared_error,
    precision_score,
    r2_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import GroupShuffleSplit
from sklearn.naive_bayes import GaussianNB
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, PolynomialFeatures, StandardScaler
from sklearn.tree import DecisionTreeClassifier


ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "data/api_fusion/final/femcare_final_cleaned.csv"
OUTPUT = ROOT / "report/algorithm_comparison"
RANDOM_STATE = 42
SINGLE_FEATURE = "stress_score_baseline"

# Only background, state-level, and historical date-linked context. No pain-derived
# fields, other same-cycle outcomes, IDs, or flags calculated from the target.
NUMERIC_FEATURES = [
    "age", "bmi", "sleep_hours", "caffeine_intake", "water_intake_liters",
    "birth_control_use", "pcos_diagnosed", "stress_score_baseline",
    "census_median_household_income", "cdc_obesity_prevalence",
    "cdc_physical_inactivity_prevalence", "cdc_smoking_prevalence",
    "cdc_depression_prevalence", "temperature_mean", "humidity_mean",
    "precipitation", "wind_speed_mean",
]
CATEGORICAL_FEATURES = [
    "diet_quality", "exercise_frequency", "alcohol_consumption", "smoking_status",
]
FEATURES = NUMERIC_FEATURES + CATEGORICAL_FEATURES


def full_preprocessor() -> ColumnTransformer:
    return ColumnTransformer(
        [
            ("numeric", Pipeline([
                ("impute", SimpleImputer(strategy="median")),
                ("scale", StandardScaler()),
            ]), NUMERIC_FEATURES),
            ("category", Pipeline([
                ("impute", SimpleImputer(strategy="most_frequent")),
                ("encode", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
            ]), CATEGORICAL_FEATURES),
        ],
        sparse_threshold=0,
    )


def single_preprocessor(polynomial: bool = False) -> Pipeline:
    steps = [("impute", SimpleImputer(strategy="median"))]
    if polynomial:
        steps.append(("degree_2", PolynomialFeatures(degree=2, include_bias=False)))
    steps.append(("scale", StandardScaler()))
    return Pipeline(steps)


def plot_scores(scores: pd.DataFrame) -> None:
    specs = [
        ("classification", "f1", "F1 score", "classification_f1.png"),
        ("regression", "mae", "Mean absolute error (pain-score points; lower is better)", "regression_mae.png"),
    ]
    for task, metric, label, filename in specs:
        frame = scores.loc[scores.task == task]
        fig, ax = plt.subplots(figsize=(8, 4.2))
        bars = ax.barh(frame.algorithm, frame[metric], color="#397db7" if task == "classification" else "#d43b93")
        ax.invert_yaxis()
        ax.set_xlabel(label)
        ax.bar_label(bars, fmt="%.3f", padding=4)
        ax.spines[["top", "right"]].set_visible(False)
        fig.tight_layout()
        fig.savefig(OUTPUT / filename, dpi=180)
        plt.close(fig)


def main() -> None:
    if not INPUT.exists():
        raise FileNotFoundError(INPUT)
    data = pd.read_csv(INPUT)
    required = set(FEATURES + ["user_id", "pain_level"])
    missing = required - set(data.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")
    if data["pain_level"].isna().any():
        raise ValueError("Target pain_level contains missing values")
    if not data["pain_level"].between(0, 10).all():
        raise ValueError("Expected pain_level on the 0–10 scale")

    X = data[FEATURES]
    y_reg = data["pain_level"].astype(float)
    y_cls = (y_reg >= 7).astype(int)
    train_idx, test_idx = next(GroupShuffleSplit(
        n_splits=1, test_size=0.20, random_state=RANDOM_STATE,
    ).split(X, y_cls, groups=data["user_id"]))
    train_users = set(data.iloc[train_idx]["user_id"])
    test_users = set(data.iloc[test_idx]["user_id"])
    assert not train_users.intersection(test_users)
    assert len(test_idx) > 0 and y_cls.iloc[test_idx].nunique() == 2

    classifiers = [
        ("Naive Bayes", GaussianNB()),
        ("Random Forest", RandomForestClassifier(
            n_estimators=150, min_samples_leaf=5, random_state=RANDOM_STATE, n_jobs=-1,
        )),
        ("Decision Tree", DecisionTreeClassifier(
            min_samples_leaf=20, random_state=RANDOM_STATE,
        )),
        ("Logistic Regression", LogisticRegression(max_iter=2000, random_state=RANDOM_STATE)),
    ]
    rows = []
    for name, estimator in classifiers:
        model = Pipeline([("prepare", full_preprocessor()), ("model", estimator)])
        start = perf_counter()
        model.fit(X.iloc[train_idx], y_cls.iloc[train_idx])
        prediction = model.predict(X.iloc[test_idx])
        probability = model.predict_proba(X.iloc[test_idx])[:, 1]
        rows.append({
            "task": "classification", "algorithm": name,
            "accuracy": accuracy_score(y_cls.iloc[test_idx], prediction),
            "precision": precision_score(y_cls.iloc[test_idx], prediction, zero_division=0),
            "recall": recall_score(y_cls.iloc[test_idx], prediction, zero_division=0),
            "f1": f1_score(y_cls.iloc[test_idx], prediction, zero_division=0),
            "roc_auc": roc_auc_score(y_cls.iloc[test_idx], probability),
            "mae": np.nan, "rmse": np.nan, "r2": np.nan,
            "fit_and_predict_seconds": round(perf_counter() - start, 3),
        })
        print(f"{name}: F1={rows[-1]['f1']:.3f}")

    regressors = [
        ("Simple Linear Regression", [SINGLE_FEATURE], single_preprocessor(), LinearRegression()),
        ("Multiple Linear Regression", FEATURES, full_preprocessor(), LinearRegression()),
        ("Polynomial Regression (degree 2)", [SINGLE_FEATURE], single_preprocessor(True), LinearRegression()),
    ]
    for name, columns, prep, estimator in regressors:
        model = Pipeline([("prepare", prep), ("model", estimator)])
        start = perf_counter()
        model.fit(data.iloc[train_idx][columns], y_reg.iloc[train_idx])
        prediction = model.predict(data.iloc[test_idx][columns])
        rows.append({
            "task": "regression", "algorithm": name,
            "accuracy": np.nan, "precision": np.nan, "recall": np.nan,
            "f1": np.nan, "roc_auc": np.nan,
            "mae": mean_absolute_error(y_reg.iloc[test_idx], prediction),
            "rmse": np.sqrt(mean_squared_error(y_reg.iloc[test_idx], prediction)),
            "r2": r2_score(y_reg.iloc[test_idx], prediction),
            "fit_and_predict_seconds": round(perf_counter() - start, 3),
        })
        print(f"{name}: MAE={rows[-1]['mae']:.3f}")

    OUTPUT.mkdir(parents=True, exist_ok=True)
    scores = pd.DataFrame(rows)
    scores.to_csv(OUTPUT / "seven_algorithm_scores.csv", index=False, float_format="%.5f")
    metadata = {
        "source": str(INPUT.relative_to(ROOT)).replace("\\", "/"),
        "rows": len(data), "columns": len(data.columns),
        "classification_target": "high_pain = 1 if pain_level >= 7 else 0",
        "regression_target": "pain_level (observed range 1–10; permitted scale 0–10)",
        "train_rows": len(train_idx), "test_rows": len(test_idx),
        "train_users": len(train_users), "test_users": len(test_users),
        "train_high_pain_rate": round(float(y_cls.iloc[train_idx].mean()), 5),
        "test_high_pain_rate": round(float(y_cls.iloc[test_idx].mean()), 5),
        "split": "80/20 GroupShuffleSplit by user_id; random_state=42",
        "all_feature_columns": FEATURES,
        "single_and_polynomial_feature": SINGLE_FEATURE,
        "polynomial_degree": 2,
        "excluded_examples": {
            "identifiers": ["user_id", "cycle_number", "state", "state_fips", "state_abbr"],
            "target_or_same_cycle_outcomes": [
                "pain_level", "flow_level", "pms_symptoms", "mood_score",
                "stress_score_cycle", "sleep_hours_cycle", "energy_level",
                "concentration_score", "work_hours_lost", "overall_health_score",
            ],
            "redundant_or_not_selected": [
                "census_total_population", "census_female_population",
                "cdc_total_population", "latitude", "longitude",
            ],
        },
        "interpretation": (
            "Retrospective academic comparison only. State-level Census and CDC values "
            "repeat across people and cannot establish individual or causal effects. "
            "Weather represents a state-capital location and historical date, not a "
            "personal measurement or a forecast. The data and models are not clinically validated."
        ),
    }
    (OUTPUT / "comparison_metadata.json").write_text(
        json.dumps(metadata, indent=2), encoding="utf-8",
    )
    plot_scores(scores)
    print(f"Saved results to {OUTPUT}")


if __name__ == "__main__":
    main()
