import os
import pandas as pd

from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix
)


# =============================================================================
# STEP 10 - LOGISTIC REGRESSION CLASSIFICATION
# =============================================================================

print("=" * 80)
print("STEP 10 - LOGISTIC REGRESSION CLASSIFICATION")
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

TRAIN_FILE = os.path.join(
    RESULTS_DIR,
    "train_data_scaled.csv"
)

TEST_FILE = os.path.join(
    RESULTS_DIR,
    "test_data_scaled.csv"
)


# =============================================================================
# 2. LOAD DATA
# =============================================================================

print("\n")
print("=" * 80)
print("1. LOADING TRAINING AND TESTING DATA")
print("=" * 80)

train_df = pd.read_csv(TRAIN_FILE)
test_df = pd.read_csv(TEST_FILE)

print("Training data loaded successfully.")
print("Training rows:", len(train_df))

print("\nTesting data loaded successfully.")
print("Testing rows:", len(test_df))


# =============================================================================
# 3. IDENTIFY TARGET COLUMN
# =============================================================================

print("\n")
print("=" * 80)
print("2. IDENTIFYING TARGET VARIABLE")
print("=" * 80)

possible_targets = [
    "target",
    "source_type_encoded",
    "source_type",
    "Target",
    "TARGET"
]

TARGET_COLUMN = None

for column in possible_targets:
    if column in train_df.columns and column in test_df.columns:
        TARGET_COLUMN = column
        break

if TARGET_COLUMN is None:
    raise ValueError(
        "Target column not found in train_data_scaled.csv "
        "and test_data_scaled.csv"
    )

print("Target variable found:", TARGET_COLUMN)


# =============================================================================
# 4. DEFINE FEATURES
# =============================================================================

print("\n")
print("=" * 80)
print("3. SEPARATING FEATURES AND TARGET")
print("=" * 80)

FEATURE_COLUMNS = [
    "content_length",
    "title_length",
    "content_word_count",
    "title_word_count",
    "metadata_length",
    "has_url",
    "modified_year",
    "modified_month",
    "modified_day",
    "language_encoded"
]

missing_features = [
    column
    for column in FEATURE_COLUMNS
    if column not in train_df.columns
    or column not in test_df.columns
]

if missing_features:

    print("\nMissing features:")

    for column in missing_features:
        print("-", column)

    raise ValueError("Required feature columns are missing.")


X_train = train_df[FEATURE_COLUMNS].copy()
X_test = test_df[FEATURE_COLUMNS].copy()

y_train = train_df[TARGET_COLUMN].copy()
y_test = test_df[TARGET_COLUMN].copy()


print("\nFeatures used:")

for number, column in enumerate(FEATURE_COLUMNS, start=1):
    print(f"{number}. {column}")

print("\nNumber of features:", len(FEATURE_COLUMNS))

print("\nTraining feature shape:", X_train.shape)
print("Testing feature shape:", X_test.shape)


# =============================================================================
# 5. HANDLE MISSING VALUES
# =============================================================================

print("\n")
print("=" * 80)
print("4. HANDLING MISSING VALUES")
print("=" * 80)

X_train = X_train.fillna(0)
X_test = X_test.fillna(0)

print("Missing feature values handled successfully.")


# =============================================================================
# 6. CREATE LOGISTIC REGRESSION MODEL
# =============================================================================

print("\n")
print("=" * 80)
print("5. CREATING LOGISTIC REGRESSION MODEL")
print("=" * 80)

print("Algorithm: Logistic Regression")
print("Maximum iterations: 1000")

model = LogisticRegression(
    max_iter=1000,
    random_state=42
)

print("\nLogistic Regression model created successfully.")


# =============================================================================
# 7. TRAIN MODEL
# =============================================================================

print("\n")
print("=" * 80)
print("6. TRAINING LOGISTIC REGRESSION MODEL")
print("=" * 80)

model.fit(X_train, y_train)

print("Logistic Regression model trained successfully.")


# =============================================================================
# 8. MAKE PREDICTIONS
# =============================================================================

print("\n")
print("=" * 80)
print("7. MAKING PREDICTIONS")
print("=" * 80)

y_pred = model.predict(X_test)

print("Predictions generated successfully.")


# =============================================================================
# 9. MODEL ACCURACY
# =============================================================================

print("\n")
print("=" * 80)
print("8. MODEL ACCURACY")
print("=" * 80)

accuracy = accuracy_score(y_test, y_pred)

print(f"Logistic Regression Accuracy: {accuracy * 100:.2f}%")


# =============================================================================
# 10. CLASSIFICATION REPORT
# =============================================================================

print("\n")
print("=" * 80)
print("9. CLASSIFICATION REPORT")
print("=" * 80)

report = classification_report(
    y_test,
    y_pred,
    zero_division=0
)

print(report)


# =============================================================================
# 11. CONFUSION MATRIX
# =============================================================================

print("\n")
print("=" * 80)
print("10. CONFUSION MATRIX")
print("=" * 80)

cm = confusion_matrix(y_test, y_pred)

print(cm)


# =============================================================================
# 12. ACTUAL VS PREDICTED
# =============================================================================

print("\n")
print("=" * 80)
print("11. ACTUAL VS PREDICTED VALUES")
print("=" * 80)

comparison_df = pd.DataFrame({
    "Actual": y_test.values,
    "Predicted": y_pred
})

print(comparison_df.to_string(index=False))


# =============================================================================
# 13. SAVE PREDICTIONS
# =============================================================================

print("\n")
print("=" * 80)
print("12. SAVING LOGISTIC REGRESSION RESULTS")
print("=" * 80)

prediction_file = os.path.join(
    RESULTS_DIR,
    "logistic_regression_predictions.csv"
)

comparison_df.to_csv(
    prediction_file,
    index=False
)

print("Predictions saved to:")
print(prediction_file)


# =============================================================================
# 14. SAVE RESULTS REPORT
# =============================================================================

results_file = os.path.join(
    RESULTS_DIR,
    "logistic_regression_results.txt"
)

with open(
    results_file,
    "w",
    encoding="utf-8"
) as file:

    file.write("LOGISTIC REGRESSION CLASSIFICATION RESULTS\n")
    file.write("=" * 60 + "\n\n")

    file.write("Algorithm: Logistic Regression\n")
    file.write("Maximum iterations: 1000\n")
    file.write("Random state: 42\n\n")

    file.write(
        f"Training samples: {len(X_train)}\n"
    )

    file.write(
        f"Testing samples: {len(X_test)}\n"
    )

    file.write(
        f"Number of features: {len(FEATURE_COLUMNS)}\n\n"
    )

    file.write(
        f"Accuracy: {accuracy * 100:.2f}%\n\n"
    )

    file.write("Classification Report\n")
    file.write("-" * 60 + "\n")
    file.write(report)

    file.write("\n\nConfusion Matrix\n")
    file.write("-" * 60 + "\n")
    file.write(str(cm))

    file.write("\n\nFeatures Used\n")
    file.write("-" * 60 + "\n")

    for column in FEATURE_COLUMNS:
        file.write(column + "\n")


print("\nResults report saved to:")
print(results_file)


# =============================================================================
# 15. FINAL MESSAGE
# =============================================================================

print("\n")
print("=" * 80)
print("STEP 10 - LOGISTIC REGRESSION COMPLETED SUCCESSFULLY")
print("=" * 80)

print(
    f"\nFinal Logistic Regression Accuracy: "
    f"{accuracy * 100:.2f}%"
)

print("\nGenerated files:")
print("1.", prediction_file)
print("2.", results_file)

print("\n")
print("=" * 80)
print("READY FOR ALGORITHM 6 - REGRESSION ANALYSIS")
print("=" * 80)