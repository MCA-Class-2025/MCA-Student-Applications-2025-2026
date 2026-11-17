import os
import joblib
import pandas as pd

from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
    r2_score
)


# ==========================================
# 1. Load monthly dataset
# ==========================================

DATASET_PATH = "dataset/monthly_expenses.csv"

df = pd.read_csv(DATASET_PATH)

print("\n========== MONTHLY DATASET ==========\n")

print("Total months:", len(df))
print(df.head())


# ==========================================
# 2. Sort chronologically
# ==========================================

df = df.sort_values("YearMonth").reset_index(drop=True)


# ==========================================
# 3. Create previous-month features
# ==========================================

df["Previous_Expense"] = df["Total_Expense"].shift(1)

df["Previous_Income"] = df["Total_Income"].shift(1)

df["Previous_Transaction_Count"] = (
    df["Transaction_Count"].shift(1)
)


# ==========================================
# 4. Create rolling average
# ==========================================

df["Expense_Rolling_Average"] = (
    df["Total_Expense"]
    .rolling(window=3)
    .mean()
)


# ==========================================
# 5. Remove rows without previous data
# ==========================================

df = df.dropna().reset_index(drop=True)


# ==========================================
# 6. Select features
# ==========================================

features = [
    "Year",
    "Month",
    "Previous_Expense",
    "Previous_Income",
    "Previous_Transaction_Count",
    "Expense_Rolling_Average"
]

X = df[features]

# Target
y = df["Total_Expense"]


# ==========================================
# 7. Time-based train/test split
# ==========================================

# IMPORTANT:
# For forecasting we should NOT randomly shuffle
# the data because future data must not leak
# into the past.

split_index = int(len(df) * 0.80)

X_train = X.iloc[:split_index]
X_test = X.iloc[split_index:]

y_train = y.iloc[:split_index]
y_test = y.iloc[split_index:]


print("\n========== DATA SPLIT ==========")

print("Total usable months:", len(df))

print("Training months:", len(X_train))

print("Testing months:", len(X_test))


# ==========================================
# 8. Create Random Forest Regressor
# ==========================================

model = RandomForestRegressor(
    n_estimators=200,
    random_state=42,
    max_depth=10,
    min_samples_leaf=2
)


# ==========================================
# 9. Train model
# ==========================================

print("\n========== TRAINING FORECAST MODEL ==========\n")

model.fit(X_train, y_train)

print("Training completed successfully.")


# ==========================================
# 10. Predict test data
# ==========================================

y_pred = model.predict(X_test)


# ==========================================
# 11. Evaluate model
# ==========================================

mae = mean_absolute_error(y_test, y_pred)

mse = mean_squared_error(y_test, y_pred)

rmse = mse ** 0.5

r2 = r2_score(y_test, y_pred)


print("\n========== MODEL EVALUATION ==========\n")

print(f"MAE  : ₹{mae:.2f}")

print(f"MSE  : {mse:.2f}")

print(f"RMSE : ₹{rmse:.2f}")

print(f"R²   : {r2:.4f}")


# ==========================================
# 12. Show actual vs predicted
# ==========================================

results = pd.DataFrame({
    "Actual_Expense": y_test.values,
    "Predicted_Expense": y_pred
})

print("\n========== ACTUAL VS PREDICTED ==========\n")

print(results.to_string(index=False))


# ==========================================
# 13. Feature importance
# ==========================================

importance = pd.DataFrame({
    "Feature": features,
    "Importance": model.feature_importances_
})

importance = importance.sort_values(
    by="Importance",
    ascending=False
)

print("\n========== FEATURE IMPORTANCE ==========\n")

print(importance.to_string(index=False))


# ==========================================
# 14. Save model
# ==========================================

os.makedirs("models", exist_ok=True)

MODEL_PATH = "models/expense_forecast_model.pkl"

joblib.dump(model, MODEL_PATH)


# Save feature list too
FEATURE_PATH = "models/forecast_features.pkl"

joblib.dump(features, FEATURE_PATH)


print("\n========== MODEL SAVED ==========\n")

print("Model:", MODEL_PATH)

print("Features:", FEATURE_PATH)