# ================================================================================
# STEP 8 - POLYNOMIAL REGRESSION
# ================================================================================

import os
import pandas as pd
import numpy as np

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import PolynomialFeatures
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score


# ================================================================================
# 1. PROJECT PATHS
# ================================================================================

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DATA_FILE = os.path.join(
    BASE_DIR,
    "ml_assignment",
    "results",
    "ml_ready_dataset.csv"
)

RESULTS_DIR = os.path.join(
    BASE_DIR,
    "ml_assignment",
    "results"
)

PREDICTIONS_FILE = os.path.join(
    RESULTS_DIR,
    "polynomial_regression_predictions.csv"
)

REPORT_FILE = os.path.join(
    RESULTS_DIR,
    "polynomial_regression_results.txt"
)

os.makedirs(RESULTS_DIR, exist_ok=True)


# ================================================================================
# 2. PROGRAM HEADER
# ================================================================================

print("=" * 80)
print("STEP 8 - POLYNOMIAL REGRESSION")
print("=" * 80)


# ================================================================================
# 3. LOADING ML-READY DATASET
# ================================================================================

print("\n")
print("=" * 80)
print("1. LOADING ML-READY DATASET")
print("=" * 80)

if not os.path.exists(DATA_FILE):
    print("\nERROR: Dataset file was not found.")
    print("Expected location:")
    print(DATA_FILE)
    raise SystemExit(1)

df = pd.read_csv(DATA_FILE)

print("Dataset loaded successfully.")
print(f"Rows: {len(df)}")
print(f"Columns: {len(df.columns)}")


# ================================================================================
# 4. CHECKING DATASET COLUMNS
# ================================================================================

print("\n")
print("=" * 80)
print("2. CHECKING DATASET COLUMNS")
print("=" * 80)

print("\nAvailable columns:")

for column in df.columns:
    print(f"- {column}")


# ================================================================================
# 5. DEFINING TARGET VARIABLE
# ================================================================================

print("\n")
print("=" * 80)
print("3. DEFINING TARGET VARIABLE")
print("=" * 80)

TARGET_COLUMN = "content_length"

if TARGET_COLUMN not in df.columns:
    print(f"\nERROR: Target column '{TARGET_COLUMN}' was not found.")

    print("\nAvailable columns:")
    print(df.columns.tolist())

    raise SystemExit(1)

print(f"Target variable: {TARGET_COLUMN}")

print(
    "\nThe model will predict content length "
    "using Polynomial Regression."
)


# ================================================================================
# 6. DEFINING INDEPENDENT VARIABLES
# ================================================================================

print("\n")
print("=" * 80)
print("4. DEFINING INDEPENDENT VARIABLES")
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

for index, feature in enumerate(FEATURE_COLUMNS, start=1):
    print(f"{index}. {feature}")


# ================================================================================
# 7. CHECKING REQUIRED COLUMNS
# ================================================================================

print("\n")
print("=" * 80)
print("5. CHECKING REQUIRED COLUMNS")
print("=" * 80)

required_columns = FEATURE_COLUMNS + [TARGET_COLUMN]

missing_columns = [
    column
    for column in required_columns
    if column not in df.columns
]

if missing_columns:

    print("\nERROR: Required columns are missing:")

    for column in missing_columns:
        print(f"- {column}")

    print("\nAvailable columns:")
    print(df.columns.tolist())

    raise SystemExit(1)

print("All required columns are available.")


# ================================================================================
# 8. PREPARING FEATURES AND TARGET
# ================================================================================

print("\n")
print("=" * 80)
print("6. PREPARING FEATURES AND TARGET")
print("=" * 80)

X = df[FEATURE_COLUMNS].copy()

y = df[TARGET_COLUMN].copy()

print("Features and target selected successfully.")


# ================================================================================
# 9. CONVERTING DATA TO NUMERIC
# ================================================================================

print("\n")
print("=" * 80)
print("7. CONVERTING DATA TO NUMERIC")
print("=" * 80)

for column in FEATURE_COLUMNS:
    X[column] = pd.to_numeric(
        X[column],
        errors="coerce"
    )

y = pd.to_numeric(
    y,
    errors="coerce"
)

print("Numeric conversion completed successfully.")


# ================================================================================
# 10. HANDLING MISSING VALUES
# ================================================================================

print("\n")
print("=" * 80)
print("8. HANDLING MISSING VALUES")
print("=" * 80)

# Replace infinite values with NaN
X = X.replace(
    [np.inf, -np.inf],
    np.nan
)

y = y.replace(
    [np.inf, -np.inf],
    np.nan
)


# Fill missing feature values using median

for column in FEATURE_COLUMNS:

    if X[column].isna().any():

        median_value = X[column].median()

        if pd.isna(median_value):
            median_value = 0

        X[column] = X[column].fillna(
            median_value
        )


# Remove rows where target is missing

valid_rows = y.notna()

X = X.loc[valid_rows].copy()

y = y.loc[valid_rows].copy()

print("Missing values handled successfully.")


# ================================================================================
# 11. DATASET SHAPE
# ================================================================================

print("\n")
print("=" * 80)
print("9. DATASET SHAPE")
print("=" * 80)

print(f"Feature matrix shape: {X.shape}")

print(f"Target vector shape: {y.shape}")


# ================================================================================
# 12. TRAIN / TEST SPLIT
# ================================================================================

print("\n")
print("=" * 80)
print("10. TRAIN / TEST SPLIT")
print("=" * 80)

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.20,
    random_state=42
)

print("Training data: 80%")
print("Testing data: 20%")

print(f"\nTraining samples: {len(X_train)}")

print(f"Testing samples: {len(X_test)}")


# ================================================================================
# 13. CREATING POLYNOMIAL FEATURES
# ================================================================================

print("\n")
print("=" * 80)
print("11. CREATING POLYNOMIAL FEATURES")
print("=" * 80)

# Degree 2 means:
#
# Original feature:
# X
#
# Polynomial features:
# X
# X²
#
# It also creates interaction terms between different features.

DEGREE = 2

print(f"Polynomial degree: {DEGREE}")

polynomial_features = PolynomialFeatures(
    degree=DEGREE,
    include_bias=False
)


# Fit ONLY on training data

X_train_poly = polynomial_features.fit_transform(
    X_train
)


# Transform test data using the same transformation

X_test_poly = polynomial_features.transform(
    X_test
)


print("Polynomial features created successfully.")

print(
    f"Original number of features: {X_train.shape[1]}"
)

print(
    f"Polynomial number of features: {X_train_poly.shape[1]}"
)


# ================================================================================
# 14. CREATING POLYNOMIAL REGRESSION MODEL
# ================================================================================

print("\n")
print("=" * 80)
print("12. CREATING POLYNOMIAL REGRESSION MODEL")
print("=" * 80)

model = LinearRegression()

print("Algorithm: Polynomial Regression")

print(f"Polynomial degree: {DEGREE}")

print("Underlying algorithm: Linear Regression")

print("\nPolynomial Regression model created successfully.")


# ================================================================================
# 15. TRAINING MODEL
# ================================================================================

print("\n")
print("=" * 80)
print("13. TRAINING POLYNOMIAL REGRESSION MODEL")
print("=" * 80)

model.fit(
    X_train_poly,
    y_train
)

print("Polynomial Regression model trained successfully.")


# ================================================================================
# 16. MAKING PREDICTIONS
# ================================================================================

print("\n")
print("=" * 80)
print("14. MAKING PREDICTIONS")
print("=" * 80)

y_pred = model.predict(
    X_test_poly
)

print("Predictions generated successfully.")


# ================================================================================
# 17. MODEL PERFORMANCE
# ================================================================================

print("\n")
print("=" * 80)
print("15. POLYNOMIAL REGRESSION PERFORMANCE")
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


# ================================================================================
# 18. ACTUAL VS PREDICTED VALUES
# ================================================================================

print("\n")
print("=" * 80)
print("16. ACTUAL VS PREDICTED VALUES")
print("=" * 80)

comparison_df = pd.DataFrame({

    "Actual_Content_Length":
        y_test.values,

    "Predicted_Content_Length":
        y_pred

})

comparison_df["Absolute_Error"] = (
    abs(
        comparison_df["Actual_Content_Length"]
        -
        comparison_df["Predicted_Content_Length"]
    )
)


print(
    comparison_df.to_string(
        index=False,
        float_format=lambda value:
        f"{value:.6f}"
    )
)


# ================================================================================
# 19. POLYNOMIAL FEATURE INFORMATION
# ================================================================================

print("\n")
print("=" * 80)
print("17. POLYNOMIAL FEATURE INFORMATION")
print("=" * 80)

polynomial_feature_names = (
    polynomial_features.get_feature_names_out(
        FEATURE_COLUMNS
    )
)

print(
    f"Total polynomial features: "
    f"{len(polynomial_feature_names)}"
)

print("\nFirst 20 polynomial features:")

for index, feature_name in enumerate(
    polynomial_feature_names[:20],
    start=1
):

    print(
        f"{index}. {feature_name}"
    )


if len(polynomial_feature_names) > 20:

    print(
        f"\n... and "
        f"{len(polynomial_feature_names) - 20} "
        f"more polynomial features."
    )


# ================================================================================
# 20. SAVING PREDICTIONS
# ================================================================================

print("\n")
print("=" * 80)
print("18. SAVING POLYNOMIAL REGRESSION PREDICTIONS")
print("=" * 80)

comparison_df.to_csv(
    PREDICTIONS_FILE,
    index=False
)

print("Predictions saved to:")

print(PREDICTIONS_FILE)


# ================================================================================
# 21. SAVING RESULTS REPORT
# ================================================================================

print("\n")
print("=" * 80)
print("19. SAVING POLYNOMIAL REGRESSION REPORT")
print("=" * 80)

report_lines = [

    "=" * 80,

    "STEP 8 - POLYNOMIAL REGRESSION RESULTS",

    "=" * 80,

    "",

    f"Dataset rows: {len(df)}",

    f"Training samples: {len(X_train)}",

    f"Testing samples: {len(X_test)}",

    "",

    f"Target variable: {TARGET_COLUMN}",

    "",

    "Independent variables:"
]


for index, feature in enumerate(
    FEATURE_COLUMNS,
    start=1
):

    report_lines.append(
        f"{index}. {feature}"
    )


report_lines.extend([

    "",

    f"Polynomial degree: {DEGREE}",

    "",

    "Performance:",

    f"MAE: {mae:.4f}",

    f"MSE: {mse:.4f}",

    f"RMSE: {rmse:.4f}",

    f"R² Score: {r2:.4f}",

    "",

    "=" * 80

])


with open(
    REPORT_FILE,
    "w",
    encoding="utf-8"
) as report_file:

    report_file.write(
        "\n".join(report_lines)
    )


print("Report saved to:")

print(REPORT_FILE)


# ================================================================================
# 22. COMPLETION MESSAGE
# ================================================================================

print("\n")
print("=" * 80)
print("STEP 8 - POLYNOMIAL REGRESSION COMPLETED SUCCESSFULLY")
print("=" * 80)

print(
    f"\nTarget variable: {TARGET_COLUMN}"
)

print(
    f"Polynomial degree: {DEGREE}"
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
    f"1. {PREDICTIONS_FILE}"
)

print(
    f"2. {REPORT_FILE}"
)

print("\n")
print("=" * 80)
print("READY FOR NEXT ALGORITHM")
print("=" * 80)