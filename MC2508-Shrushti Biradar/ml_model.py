import pandas as pd
import numpy as np

from sklearn.model_selection import train_test_split
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import joblib


# ==========================================
# 1. LOAD DATASET
# ==========================================

df = pd.read_csv("AI_Event_Planner_Dataset.csv")

print("Dataset loaded successfully!")
print("Dataset shape:", df.shape)


# ==========================================
# 2. SELECT FEATURES AND TARGET
# ==========================================

target = "success_score"

X = df.drop(columns=[target, "event_id", "event_date"])
y = df[target]


# ==========================================
# 3. IDENTIFY COLUMNS
# ==========================================

categorical_columns = X.select_dtypes(
    include=["object", "bool"]
).columns.tolist()

numeric_columns = X.select_dtypes(
    include=["int64", "float64"]
).columns.tolist()


print("\nCategorical columns:")
print(categorical_columns)

print("\nNumeric columns:")
print(numeric_columns)


# ==========================================
# 4. PREPROCESSING
# ==========================================

preprocessor = ColumnTransformer(
    transformers=[
        (
            "categorical",
            OneHotEncoder(handle_unknown="ignore"),
            categorical_columns
        ),
        (
            "numeric",
            "passthrough",
            numeric_columns
        )
    ]
)


# ==========================================
# 5. CREATE ML MODEL
# ==========================================

model = RandomForestRegressor(
    n_estimators=200,
    random_state=42,
    max_depth=10
)


# ==========================================
# 6. CREATE PIPELINE
# ==========================================

pipeline = Pipeline(
    steps=[
        ("preprocessor", preprocessor),
        ("model", model)
    ]
)


# ==========================================
# 7. SPLIT DATA
# ==========================================

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.20,
    random_state=42
)


print("\nTraining samples:", len(X_train))
print("Testing samples:", len(X_test))


# ==========================================
# 8. TRAIN MODEL
# ==========================================

print("\nTraining model...")

pipeline.fit(X_train, y_train)

print("Model training completed!")


# ==========================================
# 9. MAKE PREDICTIONS
# ==========================================

y_pred = pipeline.predict(X_test)


# ==========================================
# 10. EVALUATE MODEL
# ==========================================

mae = mean_absolute_error(y_test, y_pred)
rmse = np.sqrt(mean_squared_error(y_test, y_pred))
r2 = r2_score(y_test, y_pred)

print("\n===== MODEL PERFORMANCE =====")

print("MAE:", round(mae, 2))
print("RMSE:", round(rmse, 2))
print("R2 Score:", round(r2, 2))


# ==========================================
# 11. SAVE MODEL
# ==========================================

joblib.dump(
    pipeline,
    "event_success_model.pkl"
)

print("\nModel saved as: event_success_model.pkl")


# ==========================================
# 12. TEST SAMPLE PREDICTION
# ==========================================

sample = X_test.iloc[[0]]

prediction = pipeline.predict(sample)[0]

print("\n===== SAMPLE PREDICTION =====")
print("Predicted Success Score:", round(prediction, 2))
print("Actual Success Score:", round(y_test.iloc[0], 2))