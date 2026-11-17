# -*- coding: utf-8 -*-
"""
Generate 5 Confusion Matrix Visualization PNGs for the Classification Models.
Uses existing saved model artifacts from scratch/*.pkl.
"""

import os
import pickle
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import confusion_matrix

BASE_DIR = Path(r"C:\nutrimate")
DATASET_PATH = BASE_DIR / "data/datasets/nutrimate_fused_dataset.csv"
SCRATCH_DIR = BASE_DIR / "scratch"

# Load Dataset & Split
df = pd.read_csv(DATASET_PATH)
feature_cols = ['calories', 'protein', 'carbohydrates', 'fat', 'fiber']
target_col = 'diet_type'

for col in feature_cols:
    df[col] = pd.to_numeric(df[col], errors='coerce')

clean_df = df.dropna(subset=feature_cols + [target_col]).copy()

le = LabelEncoder()
clean_df['target_encoded'] = le.fit_transform(clean_df[target_col])
classes = list(le.classes_)  # ['egg', 'non_veg', 'veg']

X = clean_df[feature_cols].values
y = clean_df['target_encoded'].values

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.20, stratify=y, random_state=42
)

models_info = [
    {
        "name": "Naive Bayes",
        "pkl_name": "naive_bayes_model.pkl",
        "png_name": "naive_bayes_confusion_matrix.png",
        "title": "Naive Bayes Classifier - Confusion Matrix",
        "expected_cm": np.array([[0, 3, 2], [0, 2, 4], [1, 0, 48]]),
        "needs_scaling": True
    },
    {
        "name": "Support Vector Machine (SVM)",
        "pkl_name": "svm_model.pkl",
        "png_name": "svm_confusion_matrix.png",
        "title": "Support Vector Machine (SVM) - Confusion Matrix",
        "expected_cm": np.array([[1, 0, 4], [2, 1, 3], [0, 0, 49]]),
        "needs_scaling": True
    },
    {
        "name": "Decision Tree",
        "pkl_name": "decision_tree_model.pkl",
        "png_name": "decision_tree_confusion_matrix.png",
        "title": "Decision Tree Classifier - Confusion Matrix",
        "expected_cm": np.array([[2, 0, 3], [2, 2, 2], [2, 2, 45]]),
        "needs_scaling": False
    },
    {
        "name": "Random Forest",
        "pkl_name": "random_forest_model.pkl",
        "png_name": "random_forest_confusion_matrix.png",
        "title": "Random Forest Classifier - Confusion Matrix",
        "expected_cm": np.array([[2, 0, 3], [3, 1, 2], [1, 0, 48]]),
        "needs_scaling": False
    },
    {
        "name": "Logistic Regression",
        "pkl_name": "logistic_regression_model.pkl",
        "png_name": "logistic_regression_confusion_matrix.png",
        "title": "Logistic Regression - Confusion Matrix",
        "expected_cm": np.array([[1, 0, 4], [1, 3, 2], [0, 0, 49]]),
        "needs_scaling": True
    }
]

print("=" * 60)
print("GENERATING CLASSIFICATION CONFUSION MATRIX PLOTS")
print("=" * 60)

all_matched = True

for m_info in models_info:
    pkl_path = SCRATCH_DIR / m_info["pkl_name"]
    png_path = SCRATCH_DIR / m_info["png_name"]
    
    with open(pkl_path, "rb") as f:
        artifact = pickle.load(f)
    
    model = artifact["model"]
    scaler = artifact.get("scaler")
    
    if scaler and m_info["needs_scaling"]:
        X_eval = scaler.transform(X_test)
    else:
        X_eval = X_test

    y_pred = model.predict(X_eval)
    cm = confusion_matrix(y_test, y_pred)
    
    # Verify exact match
    match_status = np.array_equal(cm, m_info["expected_cm"])
    if not match_status:
        all_matched = False
    
    # Plot Heatmap
    plt.figure(figsize=(7, 5.5))
    sns.heatmap(
        cm,
        annot=True,
        fmt="d",
        cmap="Blues",
        xticklabels=classes,
        yticklabels=classes,
        cbar=True,
        linewidths=1,
        linecolor="gray",
        annot_kws={"size": 14, "weight": "bold"}
    )
    
    plt.title(m_info["title"], fontsize=12, fontweight="bold", pad=12)
    plt.xlabel("Predicted Class", fontsize=10, fontweight="bold", labelpad=8)
    plt.ylabel("Actual Class", fontsize=10, fontweight="bold", labelpad=8)
    plt.tight_layout()
    
    plt.savefig(png_path, dpi=300)
    plt.close()
    
    print(f"\nModel: {m_info['name']}")
    print(f"  - Saved Plot : {png_path}")
    print(f"  - Exact Match: {'YES (Matched)' if match_status else 'NO (Mismatch)'}")
    print("  - Matrix Output:")
    print(cm)

print("\n" + "=" * 60)
print(f"ALL PLOTS GENERATED. MATCH VERIFICATION: {'SUCCESS (100% Match)' if all_matched else 'FAILED'}")
print("=" * 60)
