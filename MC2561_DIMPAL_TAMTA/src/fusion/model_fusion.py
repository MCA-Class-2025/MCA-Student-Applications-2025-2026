# fusion/model_fusion.py – Feature Fusion + Model Fusion experiment
#
# The experiment: predict a food's category (food_group_nin) from its
# nutrition profile, using two different feature sets, and compare them —
# this is the real, non-fabricated equivalent of your friend's
# "Raw/Data-Level Fusion vs Feature-Level Fusion" comparison.
#
#   Method 1 — Raw/Data-Level Fusion:
#       Uses only the raw merged columns (local_* + usda_*) as features.
#
#   Method 2 — Feature-Level Fusion:
#       Uses the raw columns PLUS the engineered features (differences,
#       densities, ratios) as a single fused feature vector.
#
# If Method 2 outperforms Method 1, that's a genuine, defensible finding:
# "engineering fusion features improved category classification accuracy
# by X%." If it doesn't, that's also a real and reportable result — you
# don't need to pre-decide the outcome.

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score, confusion_matrix,
)

RAW_FEATURE_COLS = [
    "local_calories", "local_protein", "local_fat", "local_carbohydrates",
    "local_fiber", "local_calcium", "local_iron", "local_sodium", "local_sugar",
    "usda_calories", "usda_protein", "usda_fat", "usda_carbohydrates", "usda_fiber",
]

ENGINEERED_FEATURE_COLS = [
    "calories_difference", "protein_difference", "fat_difference",
    "carbohydrates_difference", "fiber_difference",
    "protein_density", "fiber_density", "fat_protein_ratio", "carb_protein_ratio",
]

LABEL_COL = "food_group_nin"
MIN_CLASS_COUNT = 4  # a class needs at least this many rows to be classifiable


def _prepare_xy(df, feature_cols, label_col=LABEL_COL, min_class_count=MIN_CLASS_COUNT):
    cols = [c for c in feature_cols if c in df.columns]
    if label_col not in df.columns or len(cols) < 2:
        return None, None, None, []

    sub = df[[label_col] + cols].copy()
    sub = sub[sub[label_col].notna()]
    counts = sub[label_col].value_counts()
    keep_labels = counts[counts >= min_class_count].index
    sub = sub[sub[label_col].isin(keep_labels)]
    if sub[label_col].nunique() < 2 or len(sub) < 10:
        return None, None, None, []

    X = sub[cols]
    imputer = SimpleImputer(strategy="median")
    X = pd.DataFrame(imputer.fit_transform(X), columns=cols, index=sub.index)

    le = LabelEncoder()
    y = le.fit_transform(sub[label_col])
    return X, y, le, cols


def _train_and_score(X, y, label_encoder, random_state=42):
    stratify = y if len(np.unique(y)) < len(y) else None
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.25, random_state=random_state, stratify=y
    )
    clf = RandomForestClassifier(n_estimators=200, random_state=random_state)
    clf.fit(X_train, y_train)
    y_pred = clf.predict(X_test)

    metrics = {
        "accuracy": accuracy_score(y_test, y_pred) * 100,
        "precision": precision_score(y_test, y_pred, average="weighted", zero_division=0) * 100,
        "recall": recall_score(y_test, y_pred, average="weighted", zero_division=0) * 100,
        "f1": f1_score(y_test, y_pred, average="weighted", zero_division=0) * 100,
    }
    labels_present = sorted(set(y_test) | set(y_pred))
    cm = confusion_matrix(y_test, y_pred, labels=labels_present)
    class_names = [label_encoder.classes_[i] for i in labels_present]
    return metrics, cm, class_names, clf.feature_importances_


def run_fusion_experiments(df):
    """
    Runs both fusion methods on the unified dataset and returns a dict:
    {
      "Raw/Data-Level Fusion": {"metrics": {...}, "cm": array, "class_names": [...], "features": [...]},
      "Feature-Level Fusion":  {"metrics": {...}, "cm": array, "class_names": [...], "features": [...]},
    }
    Methods that can't be trained (e.g. not enough labeled rows) are omitted
    with an explanatory reason rather than silently faked.
    """
    results = {}

    X_raw, y_raw, le_raw, cols_raw = _prepare_xy(df, RAW_FEATURE_COLS)
    if X_raw is not None:
        metrics, cm, class_names, importances = _train_and_score(X_raw, y_raw, le_raw)
        results["Raw/Data-Level Fusion"] = {
            "metrics": metrics, "cm": cm, "class_names": class_names,
            "features": cols_raw, "importances": dict(zip(cols_raw, importances)),
        }
    else:
        results["Raw/Data-Level Fusion"] = {"error": "Not enough labeled rows or usable columns to train."}

    fused_cols = RAW_FEATURE_COLS + ENGINEERED_FEATURE_COLS
    X_feat, y_feat, le_feat, cols_feat = _prepare_xy(df, fused_cols)
    if X_feat is not None:
        metrics, cm, class_names, importances = _train_and_score(X_feat, y_feat, le_feat)
        results["Feature-Level Fusion"] = {
            "metrics": metrics, "cm": cm, "class_names": class_names,
            "features": cols_feat, "importances": dict(zip(cols_feat, importances)),
        }
    else:
        results["Feature-Level Fusion"] = {"error": "Not enough labeled rows or usable columns to train."}

    return results


def plot_confusion_matrix(cm, class_names, title):
    fig, ax = plt.subplots(figsize=(6, 5))
    import seaborn as sns
    sns.heatmap(cm, annot=True, fmt="d", cmap="Blues",
                xticklabels=class_names, yticklabels=class_names, ax=ax)
    ax.set_xlabel("Predicted")
    ax.set_ylabel("Actual")
    ax.set_title(title)
    plt.setp(ax.get_xticklabels(), rotation=30, ha="right")
    plt.tight_layout()
    return fig