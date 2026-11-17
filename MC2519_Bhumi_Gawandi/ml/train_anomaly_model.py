import os
import joblib
import pandas as pd

from sklearn.ensemble import IsolationForest


# ==========================================
# 1. Load dataset
# ==========================================

DATASET_PATH = "dataset/personal_finance.csv"

df = pd.read_csv(DATASET_PATH)

print("\n========== ANOMALY DATASET ==========\n")

print("Total transactions:", len(df))


# ==========================================
# 2. Convert Date
# ==========================================

df["Date"] = pd.to_datetime(df["Date"])


# ==========================================
# 3. Create date features
# ==========================================

df["Year"] = df["Date"].dt.year
df["Month"] = df["Date"].dt.month
df["Day"] = df["Date"].dt.day
df["DayOfWeek"] = df["Date"].dt.dayofweek

df["IsWeekend"] = (
    df["DayOfWeek"] >= 5
).astype(int)


# ==========================================
# 4. Encode transaction type
# ==========================================

df["TypeEncoded"] = df["Type"].map({
    "Expense": 0,
    "Income": 1
})


# ==========================================
# 5. Select features
# ==========================================

features = [
    "Amount",
    "Year",
    "Month",
    "DayOfWeek",
    "IsWeekend",
    "TypeEncoded"
]

X = df[features]


# ==========================================
# 6. Create Isolation Forest
# ==========================================

model = IsolationForest(
    n_estimators=200,
    contamination=0.05,
    random_state=42
)


# ==========================================
# 7. Train model
# ==========================================

print("\n========== TRAINING ANOMALY MODEL ==========\n")

model.fit(X)

print("Training completed successfully.")


# ==========================================
# 8. Predict anomalies
# ==========================================

df["Anomaly_Prediction"] = model.predict(X)

df["Anomaly_Score"] = model.decision_function(X)


# ==========================================
# 9. Convert prediction to readable value
# ==========================================

df["Status"] = df["Anomaly_Prediction"].map({
    1: "Normal",
    -1: "Anomaly"
})


# ==========================================
# 10. Count anomalies
# ==========================================

total_anomalies = (
    df["Anomaly_Prediction"] == -1
).sum()

total_normal = (
    df["Anomaly_Prediction"] == 1
).sum()


print("\n========== ANOMALY RESULTS ==========\n")

print("Total transactions:", len(df))

print("Normal transactions:", total_normal)

print("Anomalies detected:", total_anomalies)

print(
    "Anomaly percentage:",
    round((total_anomalies / len(df)) * 100, 2),
    "%"
)


# ==========================================
# 11. Display anomalies
# ==========================================

print("\n========== DETECTED ANOMALIES ==========\n")

anomalies = df[
    df["Anomaly_Prediction"] == -1
]

print(
    anomalies[
        [
            "Date",
            "Transaction Description",
            "Category",
            "Amount",
            "Type",
            "Anomaly_Score",
            "Status"
        ]
    ].to_string(index=False)
)


# ==========================================
# 12. Feature importance is not available
# ==========================================
# Isolation Forest does not provide the same
# feature_importances_ attribute as Random Forest.
#
# We therefore use anomaly scores to determine
# how unusual individual transactions are.


# ==========================================
# 13. Save model
# ==========================================

os.makedirs("models", exist_ok=True)

MODEL_PATH = "models/anomaly_model.pkl"

joblib.dump(model, MODEL_PATH)


# ==========================================
# 14. Save anomaly results
# ==========================================

OUTPUT_PATH = "dataset/anomaly_results.csv"

df.to_csv(
    OUTPUT_PATH,
    index=False
)


print("\n========== MODEL SAVED ==========\n")

print("Model:", MODEL_PATH)

print("Results:", OUTPUT_PATH)