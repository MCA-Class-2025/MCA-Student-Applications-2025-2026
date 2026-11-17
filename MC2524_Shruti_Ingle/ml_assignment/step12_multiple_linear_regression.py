import os
import pandas as pd
import numpy as np

from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
    r2_score
)


# =============================================================================
# STEP 12 - MULTIPLE LINEAR REGRESSION
# =============================================================================

print("=" * 80)
print("STEP 12 - MULTIPLE LINEAR REGRESSION")
print("=" * 80)


# =============================================================================
# 1. PATHS
# =============================================================================

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

RESULTS_DIR = os.path.join(
    BASE_DIR,
    "ml_assignment",
    "results"
)

INPUT_FILE = os.path.join(
    RESULTS_DIR,
    "ml_ready_dataset.csv"
)

PREDICTION_FILE = os.path.join(
    RESULTS_DIR,
    "multiple_linear_regression_predictions.csv"
)

REPORT_FILE = os.path.join(
    RESULTS_DIR,
    "multiple_linear_regression_results.txt"
)


# =============================================================================
# 2. LOAD DATASET
# =============================================================================

print("\n")
print("=" * 80)
print("1. LOADING ML-READY DATASET")
print("=" * 80)

df = pd.read_csv(INPUT_FILE)

print("Dataset loaded successfully.")
print("Rows:", len(df))
print("Columns:", len(df.columns))


# =============================================================================
# 3. DEFINE TARGET VARIABLE
# =============================================================================

print("\n")
print("=" * 80)
print("2. DEFINING TARGET VARIABLE")
print("=" * 80)

TARGET_COLUMN = "content_length"

print("Target variable:", TARGET_COLUMN)

print(
    "\nThe model will predict the content length "
    "using multiple independent variables."
)


# =============================================================================
# 4. DEFINE MULTIPLE FEATURES
# =============================================================================

print("\n")
print("=" * 80)
print("3. DEFINING MULTIPLE INDEPENDENT VARIABLES")
print("=" * 80)

FEATURE_COLUMNS = [
    "title_length",
    "content_word_count",
    "title_word_count",
    "metadata_length",
    "has_url",
    "modified_year",
    "modified_month",
    "modified_day",
    "language_encoded",
    "source_type_encoded"
]

print("Independent variables:")

for number, column in enumerate(FEATURE_COLUMNS, start=1):
    print(f"{number}. {column}")


# =============================================================================
# 5. CHECK REQUIRED COLUMNS
# =============================================================================

print("\n")
print("=" * 80)
print("4. CHECKING REQUIRED COLUMNS")
print("=" * 80)

required_columns = FEATURE_COLUMNS + [TARGET_COLUMN]

missing_columns = [
    column
    for column in required_columns
    if column not in df.columns
]

if missing_columns:

    print("The following columns are missing:")

    for column in missing_columns:
        print("-", column)

    raise ValueError(
        "Required columns are missing from the dataset."
    )

print("All required columns are available.")


# =============================================================================
# 6. PREPARE FEATURES AND TARGET
# =============================================================================

print("\n")
print("=" * 80)
print("5. PREPARING FEATURES AND TARGET")
print("=" * 80)

X = df[FEATURE_COLUMNS].copy()

y = df[TARGET_COLUMN].copy()

# Handle missing values
X = X.fillna(0)
y = y.fillna(0)

print("Missing values handled successfully.")

print("\nFeature matrix shape:", X.shape)
print("Target vector shape:", y.shape)


# =============================================================================
# 7. TRAIN / TEST SPLIT
# =============================================================================

print("\n")
print("=" * 80)
print("6. TRAIN / TEST SPLIT")
print("=" * 80)

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.20,
    random_state=42
)

print("Training data: 80%")
print("Testing data: 20%")

print("\nTraining samples:", len(X_train))
print("Testing samples:", len(X_test))


# =============================================================================
# 8. CREATE MODEL
# =============================================================================

print("\n")
print("=" * 80)
print("7. CREATING MULTIPLE LINEAR REGRESSION MODEL")
print("=" * 80)

model = LinearRegression()

print("Algorithm: Multiple Linear Regression")

print("Model created successfully.")


# =============================================================================
# 9. TRAIN MODEL
# =============================================================================

print("\n")
print("=" * 80)
print("8. TRAINING MODEL")
print("=" * 80)

model.fit(X_train, y_train)

print("Multiple Linear Regression model trained successfully.")


# =============================================================================
# 10. MAKE PREDICTIONS
# =============================================================================

print("\n")
print("=" * 80)
print("9. MAKING PREDICTIONS")
print("=" * 80)

y_pred = model.predict(X_test)

print("Predictions generated successfully.")


# =============================================================================
# 11. CALCULATE PERFORMANCE METRICS
# =============================================================================

print("\n")
print("=" * 80)
print("10. MODEL PERFORMANCE")
print("=" * 80)

mae = mean_absolute_error(
    y_test,
    y_pred
)

mse = mean_squared_error(
    y_test,
    y_pred
)

rmse = np.sqrt(mse)

r2 = r2_score(
    y_test,
    y_pred
)

print(f"Mean Absolute Error (MAE): {mae:.4f}")

print(f"Mean Squared Error (MSE): {mse:.4f}")

print(f"Root Mean Squared Error (RMSE): {rmse:.4f}")

print(f"R-squared (R²): {r2:.4f}")


# =============================================================================
# 12. MODEL COEFFICIENTS
# =============================================================================

print("\n")
print("=" * 80)
print("11. MODEL COEFFICIENTS")
print("=" * 80)

coefficient_df = pd.DataFrame({
    "Feature": FEATURE_COLUMNS,
    "Coefficient": model.coef_
})

print(
    coefficient_df.to_string(index=False)
)

print("\nIntercept:")
print(model.intercept_)


# =============================================================================
# 13. ACTUAL VS PREDICTED
# =============================================================================

print("\n")
print("=" * 80)
print("12. ACTUAL VS PREDICTED VALUES")
print("=" * 80)

comparison_df = pd.DataFrame({
    "Actual_Content_Length": y_test.values,
    "Predicted_Content_Length": y_pred
})

comparison_df["Absolute_Error"] = (
    comparison_df["Actual_Content_Length"]
    - comparison_df["Predicted_Content_Length"]
).abs()

print(
    comparison_df.to_string(index=False)
)


# =============================================================================
# 14. SAVE PREDICTIONS
# =============================================================================

print("\n")
print("=" * 80)
print("13. SAVING PREDICTIONS")
print("=" * 80)

comparison_df.to_csv(
    PREDICTION_FILE,
    index=False
)

print("Predictions saved to:")
print(PREDICTION_FILE)


# =============================================================================
# 15. SAVE RESULTS REPORT
# =============================================================================

print("\n")
print("=" * 80)
print("14. SAVING MODEL REPORT")
print("=" * 80)

with open(
    REPORT_FILE,
    "w",
    encoding="utf-8"
) as file:

    file.write(
        "MULTIPLE LINEAR REGRESSION RESULTS\n"
    )

    file.write("=" * 70 + "\n\n")

    file.write(
        "Algorithm: Multiple Linear Regression\n"
    )

    file.write(
        f"Target Variable: {TARGET_COLUMN}\n"
    )

    file.write(
        "Train/Test Split: 80% / 20%\n"
    )

    file.write(
        "Random State: 42\n\n"
    )

    file.write(
        "Independent Variables\n"
    )

    file.write("-" * 70 + "\n")

    for column in FEATURE_COLUMNS:
        file.write(column + "\n")

    file.write("\n")

    file.write(
        "Performance Metrics\n"
    )

    file.write("-" * 70 + "\n")

    file.write(
        f"MAE: {mae:.4f}\n"
    )

    file.write(
        f"MSE: {mse:.4f}\n"
    )

    file.write(
        f"RMSE: {rmse:.4f}\n"
    )

    file.write(
        f"R2 Score: {r2:.4f}\n\n"
    )

    file.write(
        "Regression Coefficients\n"
    )

    file.write("-" * 70 + "\n")

    for _, row in coefficient_df.iterrows():

        file.write(
            f"{row['Feature']}: "
            f"{row['Coefficient']:.6f}\n"
        )

    file.write(
        f"\nIntercept: {model.intercept_:.6f}\n"
    )


print("Model report saved to:")
print(REPORT_FILE)


# =============================================================================
# 16. FINAL SUMMARY
# =============================================================================

print("\n")
print("=" * 80)
print("STEP 12 - MULTIPLE LINEAR REGRESSION COMPLETED SUCCESSFULLY")
print("=" * 80)

print(
    "\nTarget variable:",
    TARGET_COLUMN
)

print(
    f"MAE: {mae:.4f}"
)

print(
    f"MSE: {mse:.4f}"
)

print(
    f"RMSE: {rmse:.4f}"
)

print(
    f"R² Score: {r2:.4f}"
)

print("\nGenerated files:")

print(
    "1.",
    PREDICTION_FILE
)

print(
    "2.",
    REPORT_FILE
)

print("\n")
print("=" * 80)
print("READY FOR ALGORITHM 8 - POLYNOMIAL REGRESSION")
print("=" * 80)