import os
import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import joblib

from sklearn.model_selection import train_test_split
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
    confusion_matrix,
    classification_report,
    mean_absolute_error,
    mean_squared_error,
    r2_score
)

# ---------------------------------------------------------
# PATH SETUP & DIRECTORY CREATION
# ---------------------------------------------------------
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR) if os.path.basename(SCRIPT_DIR) == 'eda' else SCRIPT_DIR

# Determine dataset path safely
DATA_FILENAME = "PrepGenius_FUSED_DATASET_50000.csv"
DATA_PATH = os.path.join(PROJECT_ROOT, "data", "fused", DATA_FILENAME)

if not os.path.exists(DATA_PATH):
    # Fallback search if path differs
    DATA_PATH = os.path.join("data", "fused", DATA_FILENAME)

RESULTS_DIR = os.path.join(PROJECT_ROOT, "ml_results")
MODELS_DIR = os.path.join(RESULTS_DIR, "models")

os.makedirs(RESULTS_DIR, exist_ok=True)
os.makedirs(MODELS_DIR, exist_ok=True)

print("=" * 80)
print(" PREPGENIUS AI - TASK 2 MACHINE LEARNING PIPELINE")
print("=" * 80)

# ---------------------------------------------------------
# 1. DATASET INSPECTION & SUMMARY
# ---------------------------------------------------------
print(f"\n[STEP 1] Loading Fused Dataset from: {DATA_PATH}")

df = pd.read_csv(DATA_PATH)

num_rows, num_cols = df.shape
missing_values_series = df.isnull().sum()
total_missing = missing_values_series.sum()
duplicate_count = df.duplicated().sum()

print("\n--- DATASET PROFILE SUMMARY ---")
print(f"Dataset Filename: {DATA_FILENAME}")
print(f"Number of Rows  : {num_rows}")
print(f"Number of Cols  : {num_cols}")
print(f"Total Missing   : {total_missing}")
print(f"Duplicate Count : {duplicate_count}")

print("\n--- COLUMN NAMES & DATA TYPES ---")
for idx, (col, dtype) in enumerate(zip(df.columns, df.dtypes), 1):
    missing_in_col = df[col].isnull().sum()
    print(f"{idx:02d}. {col:<32} | Type: {str(dtype):<10} | Missing: {missing_in_col}")

# ---------------------------------------------------------
# 2. FEATURE SELECTION & PREPROCESSING
# ---------------------------------------------------------
print("\n[STEP 2] Preprocessing Features and Targets")

# Identification of targets
cls_target = "Placement_Status"
reg_target = "Starting_Salary_USD"

print(f"Classification Target Selected: '{cls_target}' (Categorical/Binary)")
print(f"Regression Target Selected    : '{reg_target}' (Numerical)")

# Student profile features
num_features = [
    'Age', 'Attendance_Percentage', 'Study_Hours_Per_Week', 'CGPA',
    'Programming_Skill', 'Projects_Completed', 'Certifications',
    'Hackathons', 'Internships', 'Resume_Score', 'Communication_Skills',
    'Teamwork', 'Problem_Solving', 'Interview_Score', 'Employability_Score'
]

cat_features = [
    'Gender', 'University_Year', 'Major', 'Academic_Performance',
    'Leadership_Experience', 'English_Proficiency'
]

feature_cols = num_features + cat_features
print(f"Total Selected Base Features: {len(feature_cols)} ({len(num_features)} Numerical, {len(cat_features)} Categorical)")

# Handle missing values safely (if any)
df_clean = df.copy()
for col in num_features:
    if df_clean[col].isnull().sum() > 0:
        df_clean[col] = df_clean[col].fillna(df_clean[col].median())
for col in cat_features:
    if df_clean[col].isnull().sum() > 0:
        df_clean[col] = df_clean[col].fillna(df_clean[col].mode()[0])

# One-Hot Encoding for categorical features
X_raw = df_clean[feature_cols]
X_encoded = pd.get_dummies(X_raw, columns=cat_features, drop_first=True)

y_cls = df_clean[cls_target]
y_reg = df_clean[reg_target]

# Train / Test splits (80/20)
X_train_c, X_test_c, y_train_c, y_test_c = train_test_split(
    X_encoded, y_cls, test_size=0.20, random_state=42, stratify=y_cls
)

X_train_r, X_test_r, y_train_r, y_test_r = train_test_split(
    X_encoded, y_reg, test_size=0.20, random_state=42
)

# Standard Scaling for models requiring scaled input (SVM, Logistic Regression)
scaler_cls = StandardScaler()
X_train_c_scaled = scaler_cls.fit_transform(X_train_c)
X_test_c_scaled = scaler_cls.transform(X_test_c)

joblib.dump(scaler_cls, os.path.join(MODELS_DIR, "scaler_cls.joblib"))

# ---------------------------------------------------------
# 3. CLASSIFICATION ALGORITHMS (1 to 5)
# ---------------------------------------------------------
print("\n[STEP 3] Executing 5 Classification Algorithms...")

cls_models = {
    "Naive Bayes": (GaussianNB(), False),
    "SVM": (SVC(kernel='rbf', cache_size=1000, random_state=42), True),
    "Decision Tree": (DecisionTreeClassifier(random_state=42), False),
    "Random Forest": (RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1), False),
    "Logistic Regression": (LogisticRegression(random_state=42, max_iter=1000), True)
}

cls_results = []
confusion_matrices = {}

for name, (model, needs_scaling) in cls_models.items():
    print(f"\n---> Training {name} Classifier...")
    X_tr = X_train_c_scaled if needs_scaling else X_train_c
    X_te = X_test_c_scaled if needs_scaling else X_test_c
    
    model.fit(X_tr, y_train_c)
    preds = model.predict(X_te)
    
    acc = accuracy_score(y_test_c, preds)
    prec = precision_score(y_test_c, preds, pos_label='Placed')
    rec = recall_score(y_test_c, preds, pos_label='Placed')
    f1 = f1_score(y_test_c, preds, pos_label='Placed')
    cm = confusion_matrix(y_test_c, preds)
    
    confusion_matrices[name] = cm
    
    cls_results.append({
        'Model': name,
        'Type': 'Classification',
        'Accuracy': round(acc, 4),
        'Precision': round(prec, 4),
        'Recall': round(rec, 4),
        'F1 Score': round(f1, 4)
    })
    
    # Save fitted model
    model_filename = f"{name.lower().replace(' ', '_')}.joblib"
    joblib.dump(model, os.path.join(MODELS_DIR, model_filename))
    
    print(f"Results for {name}: Accuracy={acc:.4f} | Precision={prec:.4f} | Recall={rec:.4f} | F1={f1:.4f}")
    print(f"Classification Report for {name}:\n")
    print(classification_report(y_test_c, preds))

# Save classification results CSV
df_cls_results = pd.DataFrame(cls_results)
df_cls_results.to_csv(os.path.join(RESULTS_DIR, "classification_results.csv"), index=False)

# ---------------------------------------------------------
# 4. REGRESSION ALGORITHMS (6 to 8)
# ---------------------------------------------------------
print("\n[STEP 4] Executing 3 Regression Algorithms...")

reg_results = []
reg_predictions = {}

# 6. Simple Linear Regression (Single feature: Employability_Score)
print("\n---> Training 6. Simple Linear Regression (Employability_Score)...")
slr_feature = ['Employability_Score']
X_tr_slr = X_train_r[slr_feature]
X_te_slr = X_test_r[slr_feature]

slr_model = LinearRegression()
slr_model.fit(X_tr_slr, y_train_r)
pred_slr = slr_model.predict(X_te_slr)

mae_slr = mean_absolute_error(y_test_r, pred_slr)
rmse_slr = np.sqrt(mean_squared_error(y_test_r, pred_slr))
r2_slr = r2_score(y_test_r, pred_slr)

reg_predictions['Simple Linear Regression'] = (y_test_r, pred_slr)
reg_results.append({
    'Model': 'Simple Linear Regression',
    'Type': 'Regression',
    'MAE': round(mae_slr, 2),
    'RMSE': round(rmse_slr, 2),
    'R2': round(r2_slr, 4)
})
joblib.dump(slr_model, os.path.join(MODELS_DIR, "simple_linear_regression.joblib"))
print(f"Simple Linear Regression: MAE=${mae_slr:,.2f} | RMSE=${rmse_slr:,.2f} | R²={r2_slr:.4f}")

# 7. Multiple Linear Regression (All features)
print("\n---> Training 7. Multiple Linear Regression...")
mlr_model = LinearRegression()
mlr_model.fit(X_train_r, y_train_r)
pred_mlr = mlr_model.predict(X_test_r)

mae_mlr = mean_absolute_error(y_test_r, pred_mlr)
rmse_mlr = np.sqrt(mean_squared_error(y_test_r, pred_mlr))
r2_mlr = r2_score(y_test_r, pred_mlr)

reg_predictions['Multiple Linear Regression'] = (y_test_r, pred_mlr)
reg_results.append({
    'Model': 'Multiple Linear Regression',
    'Type': 'Regression',
    'MAE': round(mae_mlr, 2),
    'RMSE': round(rmse_mlr, 2),
    'R2': round(r2_mlr, 4)
})
joblib.dump(mlr_model, os.path.join(MODELS_DIR, "multiple_linear_regression.joblib"))
print(f"Multiple Linear Regression: MAE=${mae_mlr:,.2f} | RMSE=${rmse_mlr:,.2f} | R²={r2_mlr:.4f}")

# 8. Polynomial Regression (Degree 2)
print("\n---> Training 8. Polynomial Regression (Degree = 2)...")
poly = PolynomialFeatures(degree=2, include_bias=False)
X_tr_poly = poly.fit_transform(X_train_r[num_features])
X_te_poly = poly.transform(X_test_r[num_features])

poly_model = LinearRegression()
poly_model.fit(X_tr_poly, y_train_r)
pred_poly = poly_model.predict(X_te_poly)

mae_poly = mean_absolute_error(y_test_r, pred_poly)
rmse_poly = np.sqrt(mean_squared_error(y_test_r, pred_poly))
r2_poly = r2_score(y_test_r, pred_poly)

reg_predictions['Polynomial Regression'] = (y_test_r, pred_poly)
reg_results.append({
    'Model': 'Polynomial Regression',
    'Type': 'Regression',
    'MAE': round(mae_poly, 2),
    'RMSE': round(rmse_poly, 2),
    'R2': round(r2_poly, 4)
})
joblib.dump(poly_model, os.path.join(MODELS_DIR, "polynomial_regression.joblib"))
joblib.dump(poly, os.path.join(MODELS_DIR, "polynomial_features.joblib"))
print(f"Polynomial Regression: MAE=${mae_poly:,.2f} | RMSE=${rmse_poly:,.2f} | R²={r2_poly:.4f}")

# Save regression results CSV
df_reg_results = pd.DataFrame(reg_results)
df_reg_results.to_csv(os.path.join(RESULTS_DIR, "regression_results.csv"), index=False)

# ---------------------------------------------------------
# 5. UNIFIED COMPARISON TABLE
# ---------------------------------------------------------
print("\n[STEP 5] Building Unified Comparison Table...")

comparison_rows = []

for r in cls_results:
    comparison_rows.append({
        'Model': r['Model'],
        'Type': r['Type'],
        'Accuracy/Metric': f"{r['Accuracy']:.4f}",
        'Precision': f"{r['Precision']:.4f}",
        'Recall': f"{r['Recall']:.4f}",
        'F1 Score': f"{r['F1 Score']:.4f}",
        'MAE': '--',
        'RMSE': '--',
        'R2': '--'
    })

for r in reg_results:
    comparison_rows.append({
        'Model': r['Model'],
        'Type': r['Type'],
        'Accuracy/Metric': f"R2={r['R2']:.4f}",
        'Precision': '--',
        'Recall': '--',
        'F1 Score': '--',
        'MAE': f"{r['MAE']:,.2f}",
        'RMSE': f"{r['RMSE']:,.2f}",
        'R2': f"{r['R2']:.4f}"
    })

df_comparison = pd.DataFrame(comparison_rows)
df_comparison.to_csv(os.path.join(RESULTS_DIR, "model_comparison.csv"), index=False)

# ---------------------------------------------------------
# 6. GENERATING GRAPHICAL PLOTS
# ---------------------------------------------------------
print("\n[STEP 6] Generating High-Resolution Plot Visualizations...")

sns.set_theme(style="whitegrid")

# Plot 1: Target Distribution
fig, axes = plt.subplots(1, 2, figsize=(14, 5))

# Classification Target
sns.countplot(x=df_clean[cls_target], ax=axes[0], palette="viridis")
axes[0].set_title(f"Classification Target Distribution ({cls_target})", fontsize=12, fontweight='bold')
axes[0].set_ylabel("Count")

for p in axes[0].patches:
    height = p.get_height()
    axes[0].annotate(f'{height:,} ({height/len(df_clean):.1%})',
                     (p.get_x() + p.get_width() / 2., height / 2),
                     ha='center', va='center', fontsize=10, color='white', fontweight='bold')

# Regression Target
sns.histplot(df_clean[reg_target], ax=axes[1], kde=True, color="teal", bins=30)
axes[1].set_title(f"Regression Target Distribution ({reg_target})", fontsize=12, fontweight='bold')
axes[1].set_xlabel("Starting Salary (USD)")
axes[1].set_ylabel("Frequency")

plt.tight_layout()
target_dist_path = os.path.join(RESULTS_DIR, "target_distribution.png")
plt.savefig(target_dist_path, dpi=300)
plt.close()
print(f"Saved: {target_dist_path}")

# Plot 2: Confusion Matrices
fig, axes = plt.subplots(2, 3, figsize=(15, 10))
axes = axes.flatten()

class_labels = sorted(y_cls.unique())

for idx, (name, cm) in enumerate(confusion_matrices.items()):
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', ax=axes[idx],
                xticklabels=class_labels, yticklabels=class_labels, cbar=False)
    axes[idx].set_title(f"Confusion Matrix: {name}", fontsize=11, fontweight='bold')
    axes[idx].set_xlabel("Predicted Label")
    axes[idx].set_ylabel("True Label")

# Hide 6th empty subplot
axes[5].axis('off')

plt.tight_layout()
cm_path = os.path.join(RESULTS_DIR, "confusion_matrices.png")
plt.savefig(cm_path, dpi=300)
plt.close()
print(f"Saved: {cm_path}")

# Plot 3: Actual vs Predicted for Regression
fig, axes = plt.subplots(1, 3, figsize=(18, 5))

for idx, (name, (y_true, y_pred)) in enumerate(reg_predictions.items()):
    ax = axes[idx]
    # Sample 1000 points for clear visualization
    sample_idx = np.random.choice(len(y_true), size=min(1000, len(y_true)), replace=False)
    y_true_s = y_true.iloc[sample_idx]
    y_pred_s = y_pred[sample_idx]
    
    ax.scatter(y_true_s, y_pred_s, alpha=0.4, color='dodgerblue', edgecolors='k', linewidth=0.3)
    max_val = max(y_true.max(), y_pred.max())
    min_val = min(y_true.min(), y_pred.min())
    ax.plot([min_val, max_val], [min_val, max_val], 'r--', label='Ideal Perfect Fit ($y = x$)')
    
    ax.set_title(f"{name}\nActual vs Predicted", fontsize=11, fontweight='bold')
    ax.set_xlabel("Actual Starting Salary ($)")
    ax.set_ylabel("Predicted Starting Salary ($)")
    ax.legend(loc="upper left")

plt.tight_layout()
reg_avp_path = os.path.join(RESULTS_DIR, "regression_actual_vs_predicted.png")
plt.savefig(reg_avp_path, dpi=300)
plt.close()
print(f"Saved: {reg_avp_path}")

# Plot 4: Model Comparison Chart
fig, axes = plt.subplots(1, 2, figsize=(16, 6))

# Classification Comparison
df_cls_melt = df_cls_results.melt(id_vars=['Model'], value_vars=['Accuracy', 'Precision', 'Recall', 'F1 Score'],
                                  var_name='Metric', value_name='Score')
sns.barplot(data=df_cls_melt, x='Model', y='Score', hue='Metric', ax=axes[0], palette='magma')
axes[0].set_title("Classification Models Performance Comparison", fontsize=12, fontweight='bold')
axes[0].set_ylim(0.5, 1.0)
axes[0].set_ylabel("Score (0.0 to 1.0)")
axes[0].tick_params(axis='x', rotation=15)
axes[0].legend(loc="lower right")

# Regression Comparison (R2 Metric)
sns.barplot(data=df_reg_results, x='Model', y='R2', ax=axes[1], palette='crest')
axes[1].set_title("Regression Models Comparison (R² Score)", fontsize=12, fontweight='bold')
axes[1].set_ylabel("R² Score")
axes[1].set_ylim(0.0, 0.4)
axes[1].tick_params(axis='x', rotation=15)

for p in axes[1].patches:
    height = p.get_height()
    axes[1].annotate(f'{height:.4f}',
                     (p.get_x() + p.get_width() / 2., height + 0.005),
                     ha='center', va='bottom', fontsize=10, fontweight='bold')

plt.tight_layout()
comp_chart_path = os.path.join(RESULTS_DIR, "model_comparison.png")
plt.savefig(comp_chart_path, dpi=300)
plt.close()
print(f"Saved: {comp_chart_path}")

# ---------------------------------------------------------
# 7. FINAL SUMMARY & VERIFICATION REPORT
# ---------------------------------------------------------
print("\n" + "=" * 80)
print(" TASK 2 EXECUTION COMPLETE - FINAL SUMMARY REPORT")
print("=" * 80)
print(f"Dataset Used       : {DATA_FILENAME}")
print(f"Dataset Shape      : {num_rows} Rows, {num_cols} Columns")
print(f"Classification Target: {cls_target}")
print(f"Regression Target  : {reg_target}")

print("\n--- FINAL COMPARISON TABLE FOR ALL 8 ALGORITHMS ---")
print(df_comparison.to_string(index=False))

print("\n--- GENERATED RESULTS & MODEL ARTIFACT PATHS ---")
print(f"1. Classification Results CSV : {os.path.join(RESULTS_DIR, 'classification_results.csv')}")
print(f"2. Regression Results CSV     : {os.path.join(RESULTS_DIR, 'regression_results.csv')}")
print(f"3. Model Comparison CSV       : {os.path.join(RESULTS_DIR, 'model_comparison.csv')}")
print(f"4. Target Distribution Plot   : {target_dist_path}")
print(f"5. Confusion Matrices Plot    : {cm_path}")
print(f"6. Regression Act vs Pred Plot: {reg_avp_path}")
print(f"7. Model Comparison Plot     : {comp_chart_path}")
print(f"8. Trained Models Directory   : {MODELS_DIR}")
print("=" * 80)
