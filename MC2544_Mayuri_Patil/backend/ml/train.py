"""Train and compare the five cardiovascular-risk classifiers."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import joblib
import pandas as pd
from sklearn.calibration import CalibratedClassifierCV
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.neighbors import KNeighborsClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import LinearSVC
from sklearn.tree import DecisionTreeClassifier

if __package__:
    from .features import FEATURE_COLUMNS, TARGET_COLUMN, build_feature_frame
else:
    from features import FEATURE_COLUMNS, TARGET_COLUMN, build_feature_frame

MODEL_PATH = Path(__file__).with_name("model.joblib")
METRICS_PATH = Path(__file__).with_name("model_metrics.json")


def prepare_dataset(dataset_path: Path) -> pd.DataFrame:
    """Load and validate the source records used by all model candidates."""
    data = pd.read_csv(dataset_path, delimiter=";")

    # The model needs all clinical inputs and the cardio target label to train.
    required_columns = set(FEATURE_COLUMNS + [TARGET_COLUMN])
    missing_columns = required_columns.difference(data.columns)
    if missing_columns:
        raise ValueError(f"Dataset is missing required columns: {sorted(missing_columns)}")

    # Keep complete records only, then convert age from days to years.
    prepared = data[FEATURE_COLUMNS + [TARGET_COLUMN]].dropna().copy()
    prepared["age"] = prepared["age"] / 365.25

    # Exclude impossible clinical measurements before the models learn from them.
    valid_measurements = (
        prepared["height"].between(120, 220)
        & prepared["weight"].between(30, 250)
        & prepared["ap_hi"].between(70, 250)
        & prepared["ap_lo"].between(40, 200)
        & (prepared["ap_hi"] > prepared["ap_lo"])
    )
    return prepared.loc[valid_measurements]


def build_models() -> dict[str, object]:
    """Return the five classifiers evaluated on the same train/test split."""
    return {
        # A simple and interpretable baseline for binary classification.
        "Logistic Regression": Pipeline(
            [
                ("scaler", StandardScaler()),
                (
                    "classifier",
                    LogisticRegression(
                        class_weight="balanced",
                        max_iter=1000,
                        random_state=42,
                    ),
                ),
            ]
        ),
        # Learns if-then style decision rules from patient data.
        "Decision Tree": DecisionTreeClassifier(
            class_weight="balanced",
            max_depth=8,
            min_samples_leaf=25,
            random_state=42,
        ),
        # Predicts risk using the closest similar patient records.
        "K-Nearest Neighbors": Pipeline(
            [
                ("scaler", StandardScaler()),
                ("classifier", KNeighborsClassifier(n_neighbors=25, weights="distance")),
            ]
        ),
        # Finds a boundary between low-risk and high-risk records.
        # Calibration converts SVM scores into probabilities for the UI.
        "Linear SVM": Pipeline(
            [
                ("scaler", StandardScaler()),
                (
                    "classifier",
                    CalibratedClassifierCV(
                        LinearSVC(class_weight="balanced", random_state=42),
                        cv=3,
                        method="sigmoid",
                    ),
                ),
            ]
        ),
        # Combines many decision trees to improve stability.
        "Random Forest": RandomForestClassifier(
            n_estimators=300,
            random_state=42,
            class_weight="balanced",
            n_jobs=-1,
        ),
    }

def evaluate_model(model: object, x_test: pd.DataFrame, y_test: pd.Series) -> dict[str, float]:
    """Calculate the same held-out binary-classification metrics for one model."""
    # Test records were not used during fitting, making evaluation fair.
    predictions = model.predict(x_test)
    probabilities = model.predict_proba(x_test)[:, 1]

    # Accuracy is overall correctness. Precision, recall, and F1 evaluate
    # positive-risk predictions. ROC-AUC evaluates probability ranking.
    return {
        "accuracy": round(float(accuracy_score(y_test, predictions)), 4),
        "precision": round(float(precision_score(y_test, predictions, zero_division=0)), 4),
        "recall": round(float(recall_score(y_test, predictions, zero_division=0)), 4),
        "f1": round(float(f1_score(y_test, predictions, zero_division=0)), 4),
        "roc_auc": round(float(roc_auc_score(y_test, probabilities)), 4),
    }


def train(dataset_path: Path) -> dict[str, object]:
    """Train all classifiers, save their comparison bundle, and return it."""
    dataset = prepare_dataset(dataset_path)

    # Add derived features such as BMI and pulse pressure for every model.
    fused_features = build_feature_frame(dataset)

    # Keep 20% unseen data for evaluation; stratification preserves the
    # low-risk/high-risk balance in both the training and test datasets.
    x_train, x_test, y_train, y_test = train_test_split(
        fused_features,
        dataset[TARGET_COLUMN],
        test_size=0.2,
        random_state=42,
        stratify=dataset[TARGET_COLUMN],
    )

    models = build_models()
    metrics: dict[str, dict[str, float]] = {}
    for name, model in models.items():
        # Each algorithm is trained and tested on the same split for comparison.
        model.fit(x_train, y_train)
        metrics[name] = evaluate_model(model, x_test, y_test)
        print(
            f"{name}: accuracy={metrics[name]['accuracy']:.3f}, "
            f"f1={metrics[name]['f1']:.3f}, roc_auc={metrics[name]['roc_auc']:.3f}"
        )

    # ROC-AUC is the main selection metric; F1 and model name break ties.
    selected_model_name = max(
        metrics,
        key=lambda name: (
            metrics[name]["roc_auc"],
            metrics[name]["f1"],
            name == "Random Forest",
        ),
    )
    artifact: dict[str, object] = {
        "artifact_version": 2,
        "feature_columns": list(fused_features.columns),
        "models": models,
        "metrics": metrics,
        "selected_model_name": selected_model_name,
    }

    # joblib stores fitted models for predictions. JSON stores only the
    # evaluation results for reporting in the API or UI.
    joblib.dump(artifact, MODEL_PATH)
    METRICS_PATH.write_text(
        json.dumps(
            {
                "selected_model_name": selected_model_name,
                "metrics": metrics,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"Training records: {len(x_train)}")
    print(f"Selected model by ROC-AUC: {selected_model_name}")
    return artifact


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Train and compare CardioCare AI's five classification models."
    )
    parser.add_argument(
        "dataset",
        type=Path,
        help="Semicolon-delimited cardiovascular disease CSV.",
    )

    arguments = parser.parse_args()
    train(arguments.dataset)
