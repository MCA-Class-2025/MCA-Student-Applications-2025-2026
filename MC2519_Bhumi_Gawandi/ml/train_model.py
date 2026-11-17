import os
import joblib
import pandas as pd

from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix
)

from preprocessing import load_and_preprocess_data


# ==========================================
# 1. Load and preprocess dataset
# ==========================================

df = load_and_preprocess_data()


# ==========================================
# 2. Select features
# ==========================================

features = [
    "Amount",
    "Year",
    "Month",
    "Day",
    "DayOfWeek",
    "IsWeekend",
    "TypeEncoded"
]

X = df[features]

# Target variable
y = df["Category"]


# ==========================================
# 3. Train/Test Split
# ==========================================

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.20,
    random_state=42,
    stratify=y
)


print("\n========== DATA SPLIT ==========")

print("Total records:", len(df))
print("Training records:", len(X_train))
print("Testing records:", len(X_test))


# ==========================================
# 4. Create Random Forest model
# ==========================================

model = RandomForestClassifier(
    n_estimators=200,
    random_state=42,
    class_weight="balanced"
)


# ==========================================
# 5. Train model
# ==========================================

print("\n========== TRAINING MODEL ==========")

model.fit(X_train, y_train)

print("Training completed successfully.")


# ==========================================
# 6. Make predictions
# ==========================================

y_pred = model.predict(X_test)


# ==========================================
# 7. Evaluate model
# ==========================================

accuracy = accuracy_score(y_test, y_pred)

print("\n========== MODEL EVALUATION ==========")

print(f"Accuracy: {accuracy:.4f}")
print(f"Accuracy Percentage: {accuracy * 100:.2f}%")


print("\n========== CLASSIFICATION REPORT ==========")

print(
    classification_report(
        y_test,
        y_pred,
        zero_division=0
    )
)


print("\n========== CONFUSION MATRIX ==========")

print(confusion_matrix(y_test, y_pred))


# ==========================================
# 8. Feature importance
# ==========================================

print("\n========== FEATURE IMPORTANCE ==========")

importance = pd.DataFrame({
    "Feature": features,
    "Importance": model.feature_importances_
})

importance = importance.sort_values(
    by="Importance",
    ascending=False
)

print(importance)


# ==========================================
# 9. Save trained model
# ==========================================

os.makedirs("models", exist_ok=True)

model_path = "models/category_model.pkl"

joblib.dump(model, model_path)

print("\n========== MODEL SAVED ==========")

print(f"Model saved at: {model_path}")