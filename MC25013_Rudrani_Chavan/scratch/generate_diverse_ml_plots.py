# -*- coding: utf-8 -*-
"""
Generate 8 Diverse, Report-Ready Visualizations for all 8 completed ML algorithms.
Uses existing dataset (data/datasets/nutrimate_fused_dataset.csv) and saved artifacts (scratch/*.pkl).
"""

import os
import pickle
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.decomposition import PCA
from sklearn.tree import plot_tree

BASE_DIR = Path(r"C:\nutrimate")
DATASET_PATH = BASE_DIR / "data/datasets/nutrimate_fused_dataset.csv"
SCRATCH_DIR = BASE_DIR / "scratch"

# Set matplotlib style
plt.style.use('seaborn-v0_8-whitegrid')
plt.rcParams['font.sans-serif'] = 'DejaVu Sans'
plt.rcParams['font.size'] = 10

# Load dataset
df = pd.read_csv(DATASET_PATH)

# Feature and target definitions
clf_features = ['calories', 'protein', 'carbohydrates', 'fat', 'fiber']
clf_target = 'diet_type'

reg_features = ['protein', 'carbohydrates', 'fat', 'fiber']
reg_target = 'calories'

# Clean data
for col in clf_features + [reg_target]:
    df[col] = pd.to_numeric(df[col], errors='coerce')

clean_df = df.dropna(subset=clf_features + [clf_target]).copy()

le = LabelEncoder()
clean_df['target_encoded'] = le.fit_transform(clean_df[clf_target])
classes = list(le.classes_)  # ['egg', 'non_veg', 'veg']

X_clf = clean_df[clf_features].values
y_clf = clean_df['target_encoded'].values

# Stratified Split for Classification (matching original setup)
X_train_clf, X_test_clf, y_train_clf, y_test_clf = train_test_split(
    X_clf, y_clf, test_size=0.20, stratify=y_clf, random_state=42
)

# Train-Test Split for Regression (matching original setup)
X_reg = clean_df[reg_features].values
y_reg = clean_df[reg_target].values

X_train_reg, X_test_reg, y_train_reg, y_test_reg = train_test_split(
    X_reg, y_reg, test_size=0.20, random_state=42
)

print("=" * 60)
print("GENERATING DIVERSE ML VISUALIZATION IMAGES")
print("=" * 60)

# ==============================================================================
# 1. NAIVE BAYES — BOXPLOT OF PROTEIN DISTRIBUTION BY DIET TYPE
# ==============================================================================
print("1. Generating Naive Bayes Feature Distribution Boxplot...")
plt.figure(figsize=(8, 5))
palette = {'egg': '#E9D8A6', 'non_veg': '#E76F51', 'veg': '#588157'}

sns.boxplot(
    data=clean_df,
    x=clf_target,
    y='protein',
    order=classes,
    palette=palette,
    width=0.4,
    fliersize=5
)

plt.title("Naive Bayes: Protein Distribution by Diet Type", fontsize=12, fontweight='bold', pad=12)
plt.xlabel("Diet Type", fontsize=11, fontweight='bold')
plt.ylabel("Protein (g)", fontsize=11, fontweight='bold')
plt.tight_layout()

nb_plot_path = SCRATCH_DIR / "naive_bayes_feature_distribution.png"
plt.savefig(nb_plot_path, dpi=300)
plt.close()
print(f"   Saved: {nb_plot_path}")

# ==============================================================================
# 2. SVM — 2D PCA SCATTER PLOT
# ==============================================================================
print("2. Generating SVM PCA Classification Scatter Plot...")
svm_pkl_path = SCRATCH_DIR / "svm_model.pkl"
with open(svm_pkl_path, "rb") as f:
    svm_artifact = pickle.load(f)

svm_model = svm_artifact["model"]
scaler_svm = svm_artifact["scaler"]

# Standardize test set features
X_test_scaled_svm = scaler_svm.transform(X_test_clf)

# Apply PCA (2 components) on standardized test features
pca = PCA(n_components=2, random_state=42)
X_test_pca = pca.fit_transform(X_test_scaled_svm)

# Also project training support vectors into the 2D PCA space
X_train_scaled_svm = scaler_svm.transform(X_train_clf)
pca_train = PCA(n_components=2, random_state=42)
pca_train.fit(X_train_scaled_svm)

# Transform support vector locations to test PCA space
support_vectors_scaled = svm_model.support_vectors_
support_vectors_pca = pca.transform(support_vectors_scaled)

plt.figure(figsize=(9, 6))

# Plot Test Observations
color_map = {0: '#E9D8A6', 1: '#E76F51', 2: '#588157'}
label_map = {0: 'egg', 1: 'non_veg', 2: 'veg'}

for cls_idx in range(len(classes)):
    mask = (y_test_clf == cls_idx)
    plt.scatter(
        X_test_pca[mask, 0],
        X_test_pca[mask, 1],
        c=color_map[cls_idx],
        label=f'Actual {label_map[cls_idx]}',
        s=70,
        edgecolors='k',
        alpha=0.85
    )

# Highlight Support Vectors in PCA Space
plt.scatter(
    support_vectors_pca[:, 0],
    support_vectors_pca[:, 1],
    s=130,
    facecolors='none',
    edgecolors='navy',
    linewidths=1.2,
    linestyle='--',
    label='SVM Support Vectors (PCA mapped)'
)

plt.title("SVM: PCA Projection of Diet Classification", fontsize=12, fontweight='bold', pad=12)
plt.xlabel("Principal Component 1", fontsize=11, fontweight='bold')
plt.ylabel("Principal Component 2", fontsize=11, fontweight='bold')
plt.legend(fontsize=9, loc='upper right')
plt.tight_layout()

svm_plot_path = SCRATCH_DIR / "svm_pca_classification.png"
plt.savefig(svm_plot_path, dpi=300)
plt.close()
print(f"   Saved: {svm_plot_path}")

# ==============================================================================
# 3. DECISION TREE — TREE STRUCTURE DIAGRAM
# ==============================================================================
print("3. Generating Decision Tree Structure Diagram...")
dt_pkl_path = SCRATCH_DIR / "decision_tree_model.pkl"
with open(dt_pkl_path, "rb") as f:
    dt_artifact = pickle.load(f)

dt_model = dt_artifact["model"]

plt.figure(figsize=(16, 8))
plot_tree(
    dt_model,
    max_depth=3,  # Set display depth to 3 for clean visual presentation
    feature_names=clf_features,
    class_names=classes,
    filled=True,
    rounded=True,
    fontsize=9
)

plt.title("Decision Tree Classifier Structure (Displayed Max Depth = 3)", fontsize=13, fontweight='bold', pad=12)
plt.tight_layout()

dt_plot_path = SCRATCH_DIR / "decision_tree_structure.png"
plt.savefig(dt_plot_path, dpi=300)
plt.close()
print(f"   Saved: {dt_plot_path}")

# ==============================================================================
# 4. RANDOM FOREST — FEATURE IMPORTANCE HORIZONTAL BAR CHART
# ==============================================================================
print("4. Generating Random Forest Feature Importance Bar Chart...")
rf_pkl_path = SCRATCH_DIR / "random_forest_model.pkl"
with open(rf_pkl_path, "rb") as f:
    rf_artifact = pickle.load(f)

feat_imp = rf_artifact["feature_importances"]
sorted_feats = sorted(feat_imp.items(), key=lambda x: x[1], reverse=False)

feat_names = [x[0] for x in sorted_feats]
imp_values = [x[1] for x in sorted_feats]

plt.figure(figsize=(8, 4.5))
bars = plt.barh(feat_names, imp_values, color='#3A5A40', height=0.55)

plt.title("Random Forest: Feature Importance", fontsize=12, fontweight='bold', pad=12)
plt.xlabel("Importance Score", fontsize=11, fontweight='bold')
plt.ylabel("Features", fontsize=11, fontweight='bold')
plt.xlim(0, max(imp_values) * 1.18)

for bar in bars:
    val = bar.get_width()
    plt.text(val + 0.008, bar.get_y() + bar.get_height()/2, f"{val:.4f} ({val*100:.1f}%)", 
             va='center', ha='left', fontsize=9, fontweight='bold')

plt.tight_layout()

rf_plot_path = SCRATCH_DIR / "random_forest_feature_importance.png"
plt.savefig(rf_plot_path, dpi=300)
plt.close()
print(f"   Saved: {rf_plot_path}")

# ==============================================================================
# 5. LOGISTIC REGRESSION — GROUPED COEFFICIENTS BAR CHART
# ==============================================================================
print("5. Generating Logistic Regression Coefficients Bar Chart...")
lr_pkl_path = SCRATCH_DIR / "logistic_regression_model.pkl"
with open(lr_pkl_path, "rb") as f:
    lr_artifact = pickle.load(f)

lr_model = lr_artifact["model"]
coefs = lr_model.coef_  # Shape (3, 5)

coef_df = pd.DataFrame(coefs.T, index=clf_features, columns=classes)

plt.figure(figsize=(9, 5))
x_indices = np.arange(len(clf_features))
width = 0.25

colors = ['#E9D8A6', '#E76F51', '#588157']

for i, cls_name in enumerate(classes):
    plt.bar(
        x_indices + (i - 1) * width,
        coef_df[cls_name],
        width=width,
        label=cls_name,
        color=colors[i],
        edgecolor='k',
        linewidth=0.8
    )

plt.axhline(0, color='black', linestyle='--', linewidth=1.2)
plt.xticks(x_indices, clf_features, fontweight='bold', fontsize=10)
plt.title("Logistic Regression: Feature Coefficients by Class", fontsize=12, fontweight='bold', pad=12)
plt.xlabel("Input Features", fontsize=11, fontweight='bold')
plt.ylabel("Coefficient Value", fontsize=11, fontweight='bold')
plt.legend(title="Diet Class", fontsize=9, loc='upper left')
plt.tight_layout()

lr_plot_path = SCRATCH_DIR / "logistic_regression_coefficients.png"
plt.savefig(lr_plot_path, dpi=300)
plt.close()
print(f"   Saved: {lr_plot_path}")

# ==============================================================================
# 6. SIMPLE LINEAR REGRESSION — RESIDUAL ANALYSIS SCATTER PLOT
# ==============================================================================
print("6. Generating Simple Linear Regression Residual Plot...")
slr_pkl_path = SCRATCH_DIR / "simple_linear_regression.pkl"
with open(slr_pkl_path, "rb") as f:
    slr_artifact = pickle.load(f)

slr_model = slr_artifact["model"]
X_test_slr = X_test_reg[:, 0].reshape(-1, 1)  # protein feature
y_pred_slr = slr_model.predict(X_test_slr)
residuals_slr = y_test_reg - y_pred_slr

plt.figure(figsize=(8, 5))
plt.scatter(y_pred_slr, residuals_slr, color='#457B9D', alpha=0.75, edgecolors='k', s=60)
plt.axhline(0, color='#E76F51', linestyle='--', linewidth=2, label='Zero Residual Line (Residual = 0)')

plt.title("Simple Linear Regression: Residual Analysis", fontsize=12, fontweight='bold', pad=12)
plt.xlabel("Predicted Calories (kcal)", fontsize=11, fontweight='bold')
plt.ylabel("Residual (Actual - Predicted kcal)", fontsize=11, fontweight='bold')
plt.legend(fontsize=9)
plt.tight_layout()

slr_res_path = SCRATCH_DIR / "simple_linear_regression_residuals.png"
plt.savefig(slr_res_path, dpi=300)
plt.close()
print(f"   Saved: {slr_res_path}")

# ==============================================================================
# 7. MULTIPLE LINEAR REGRESSION — RESIDUAL ANALYSIS SCATTER PLOT
# ==============================================================================
print("7. Generating Multiple Linear Regression Residual Plot...")
mlr_pkl_path = SCRATCH_DIR / "multiple_linear_regression.pkl"
with open(mlr_pkl_path, "rb") as f:
    mlr_artifact = pickle.load(f)

mlr_model = mlr_artifact["model"]
y_pred_mlr = mlr_model.predict(X_test_reg)
residuals_mlr = y_test_reg - y_pred_mlr

plt.figure(figsize=(8, 5))
plt.scatter(y_pred_mlr, residuals_mlr, color='#3A5A40', alpha=0.75, edgecolors='k', s=60)
plt.axhline(0, color='#E76F51', linestyle='--', linewidth=2, label='Zero Residual Line (Residual = 0)')

plt.title("Multiple Linear Regression: Residual Analysis", fontsize=12, fontweight='bold', pad=12)
plt.xlabel("Predicted Calories (kcal)", fontsize=11, fontweight='bold')
plt.ylabel("Residual (Actual - Predicted kcal)", fontsize=11, fontweight='bold')
plt.legend(fontsize=9)
plt.tight_layout()

mlr_res_path = SCRATCH_DIR / "multiple_linear_regression_residuals.png"
plt.savefig(mlr_res_path, dpi=300)
plt.close()
print(f"   Saved: {mlr_res_path}")

# ==============================================================================
# 8. POLYNOMIAL REGRESSION — RESIDUAL ANALYSIS SCATTER PLOT
# ==============================================================================
print("8. Generating Polynomial Regression Residual Plot...")
poly_pkl_path = SCRATCH_DIR / "polynomial_regression.pkl"
with open(poly_pkl_path, "rb") as f:
    poly_artifact = pickle.load(f)

poly_model = poly_artifact["model"]
poly_transformer = poly_artifact["poly_transformer"]

X_test_poly = poly_transformer.transform(X_test_reg)
y_pred_poly = poly_model.predict(X_test_poly)
residuals_poly = y_test_reg - y_pred_poly

plt.figure(figsize=(8, 5))
plt.scatter(y_pred_poly, residuals_poly, color='#7209B7', alpha=0.75, edgecolors='k', s=60)
plt.axhline(0, color='#E76F51', linestyle='--', linewidth=2, label='Zero Residual Line (Residual = 0)')

plt.title("Polynomial Regression: Residual Analysis", fontsize=12, fontweight='bold', pad=12)
plt.xlabel("Predicted Calories (kcal)", fontsize=11, fontweight='bold')
plt.ylabel("Residual (Actual - Predicted kcal)", fontsize=11, fontweight='bold')
plt.legend(fontsize=9)
plt.tight_layout()

poly_res_path = SCRATCH_DIR / "polynomial_regression_residuals.png"
plt.savefig(poly_res_path, dpi=300)
plt.close()
print(f"   Saved: {poly_res_path}")

print("\n" + "=" * 60)
print("ALL 8 DIVERSE ML VISUALIZATIONS GENERATED SUCCESSFULLY!")
print("=" * 60)
