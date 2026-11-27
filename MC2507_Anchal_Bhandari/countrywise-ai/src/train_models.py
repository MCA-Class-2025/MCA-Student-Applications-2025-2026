import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split, cross_val_score, KFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.tree import DecisionTreeRegressor
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error

os.makedirs("report/figures", exist_ok=True)

# 1. Load Fused Dataset
df = pd.read_csv("data/fused_dataset.csv")
features = [
    "log_gdp_per_capita",
    "social_support",
    "wb_life_expectancy",
    "freedom",
    "annual_mean_temp_c"
]
clean_df = df[["country", "region"] + features + ["happiness_score"]].dropna().reset_index(drop=True)

X = clean_df[features]
y = clean_df["happiness_score"]

# 2. 80/20 Train-Test Split + Shuffled 5-Fold Cross-Validation
X_train, X_test, y_train, y_test, idx_train, idx_test = train_test_split(
    X, y, clean_df.index, test_size=0.20, random_state=42
)
kf = KFold(n_splits=5, shuffle=True, random_state=42)

models = {
    "Linear Regression": make_pipeline(StandardScaler(), LinearRegression()),
    "Ridge Regression": make_pipeline(StandardScaler(), Ridge(alpha=1.0)),
    "Decision Tree": DecisionTreeRegressor(max_depth=4, random_state=42),
    "Random Forest": RandomForestRegressor(n_estimators=100, max_depth=5, random_state=42)
}

results = []
test_preds = {}

for name, model in models.items():
    model.fit(X_train, y_train)
    preds = model.predict(X_test)
    cv_scores = cross_val_score(model, X, y, cv=kf, scoring="r2")

    r2 = r2_score(y_test, preds)
    mae = mean_absolute_error(y_test, preds)
    rmse = np.sqrt(mean_squared_error(y_test, preds))

    results.append({
        "Model": name,
        "Test_Accuracy_R2_Pct": round(r2 * 100, 2),
        "CV_5Fold_Accuracy_Pct": round(cv_scores.mean() * 100, 2),
        "Avg_Error_MAE": round(mae, 3),
        "Typical_Error_RMSE": round(rmse, 3)
    })
    test_preds[name] = preds

results_df = pd.DataFrame(results).sort_values("Test_Accuracy_R2_Pct", ascending=False).reset_index(drop=True)
best_model_name = results_df.iloc[0]["Model"]

# 3. Build Actual vs. Predicted Country Matrix
matrix_df = pd.DataFrame({
    "Country": clean_df.loc[idx_test, "country"].values,
    "Region": clean_df.loc[idx_test, "region"].values,
    "Actual_Score": np.round(y_test.values, 2),
    "Ridge_Predicted": np.round(test_preds["Ridge Regression"], 2),
    "Random_Forest_Predicted": np.round(test_preds["Random Forest"], 2),
    "Error_Difference": np.round(test_preds[best_model_name] - y_test.values, 2)
}).sort_values("Actual_Score", ascending=False).reset_index(drop=True)

# 4. Save CSV Outputs directly to report/ folder (Visible in VS Code & GitHub)
results_df.to_csv("report/model_comparison_results.csv", index=False)
matrix_df.to_csv("report/actual_vs_predicted_matrix.csv", index=False)

# 5. Save High-Resolution Comparison & Actual-vs-Predicted Charts
fig, axes = plt.subplots(1, 2, figsize=(13, 5))

# Left Chart: Model Accuracy Comparison
x_pos = np.arange(len(results_df))
axes[0].bar(x_pos - 0.18, results_df["Test_Accuracy_R2_Pct"], width=0.35, label="Test Accuracy (%)", color="#4f46e5")
axes[0].bar(x_pos + 0.18, results_df["CV_5Fold_Accuracy_Pct"], width=0.35, label="5-Fold CV Accuracy (%)", color="#0ea5e9")
axes[0].set_xticks(x_pos)
axes[0].set_xticklabels(results_df["Model"], rotation=15)
axes[0].set_ylabel("Accuracy (R² %)")
axes[0].set_ylim(0, 100)
axes[0].set_title("Model Accuracy Comparison (Higher is Better)")
axes[0].legend()
axes[0].grid(axis="y", alpha=0.3)

# Right Chart: Actual vs. Predicted Scatter Plot
best_preds = test_preds[best_model_name]
axes[1].scatter(y_test, best_preds, color="#4f46e5", alpha=0.8, edgecolor="white", s=70)
min_val, max_val = y_test.min() - 0.3, y_test.max() + 0.3
axes[1].plot([min_val, max_val], [min_val, max_val], "r--", lw=1.8, label="Perfect Prediction Line")
axes[1].set_xlabel("Actual Happiness Score")
axes[1].set_ylabel("Predicted Happiness Score")
axes[1].set_title(f"Actual vs. Predicted ({best_model_name})")
axes[1].legend()
axes[1].grid(alpha=0.3)

plt.tight_layout()
plt.savefig("report/figures/fig5_model_comparison_matrix.png", dpi=150)
plt.close()

# 6. Print Clean Output in VS Code Terminal
print("=" * 68)
print("COUNTRYWISE AI — MODEL BENCHMARK & PREDICTION MATRIX SUMMARY")
print("=" * 68)
print("\n1. MODEL ACCURACY COMPARISON:")
print(results_df.to_string(index=False))
print(f"\n--> Best Performing Model: {best_model_name} ({results_df.iloc[0]['Test_Accuracy_R2_Pct']}% Test Accuracy)")
print("\n2. SAMPLE ACTUAL VS. PREDICTED COUNTRIES (UNSEEN TEST SET):")
print(matrix_df.head(10).to_string(index=False))
print("\nSaved permanent outputs to:")
print("  - report/model_comparison_results.csv")
print("  - report/actual_vs_predicted_matrix.csv")
print("  - report/figures/fig5_model_comparison_matrix.png")