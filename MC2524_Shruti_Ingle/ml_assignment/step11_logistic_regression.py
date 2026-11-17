import os
import pandas as pd

from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix
)


# ============================================================
# STEP 11 - LOGISTIC REGRESSION CLASSIFICATION
# ============================================================

print("=" * 80)
print("STEP 11 - LOGISTIC REGRESSION CLASSIFICATION")
print("=" * 80)


# ============================================================
# 1. PATHS
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

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

MAPPING_FILE = os.path.join(
    RESULTS_DIR,
    "target_mapping.csv"
)


# ============================================================
# 2. LOAD TRAINING AND TESTING DATA
# ============================================================

print("\n" + "=" * 80)
print("1. LOADING TRAINING AND TESTING DATA")
print("=" * 80)

train_df = pd.read_csv(TRAIN_FILE)
test_df = pd.read_csv(TEST_FILE)

print("Training data loaded successfully.")
print(f"Training rows: {len(train_df)}")

print("\nTesting data loaded successfully.")
print(f"Testing rows: {len(test_df)}")


# ============================================================
# 3. SEPARATE FEATURES AND TARGET
# ============================================================

print("\n" + "=" * 80)
print("2. SEPARATING FEATURES AND TARGET")
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

TARGET_COLUMN = "target"

X_train = train_df[FEATURE_COLUMNS]
X_test = test_df[FEATURE_COLUMNS]

y_train = train_df[TARGET_COLUMN]
y_test = test_df[TARGET_COLUMN]

print("Features used:")

for number, column in enumerate(
    FEATURE_COLUMNS,
    start=1
):
    print(f"{number}. {column}")

print(f"\nNumber of features: {len(FEATURE_COLUMNS)}")

print(f"\nTarget variable: {TARGET_COLUMN}")


# ============================================================
# 4. CREATE LOGISTIC REGRESSION MODEL
# ============================================================

print("\n" + "=" * 80)
print("3. CREATING LOGISTIC REGRESSION MODEL")
print("=" * 80)

print("Algorithm: Logistic Regression")
print("Maximum iterations: 1000")
print("Random state: 42")

model = LogisticRegression(
    max_iter=1000,
    random_state=42
)

print("\nLogistic Regression model created successfully.")


# ============================================================
# 5. TRAIN MODEL
# ============================================================

print("\n" + "=" * 80)
print("4. TRAINING LOGISTIC REGRESSION MODEL")
print("=" * 80)

model.fit(
    X_train,
    y_train
)

print("Logistic Regression model trained successfully.")


# ============================================================
# 6. MAKE PREDICTIONS
# ============================================================

print("\n" + "=" * 80)
print("5. MAKING PREDICTIONS")
print("=" * 80)

y_pred = model.predict(X_test)

print("Predictions generated successfully.")


# ============================================================
# 7. MODEL ACCURACY
# ============================================================

print("\n" + "=" * 80)
print("6. MODEL ACCURACY")
print("=" * 80)

accuracy = accuracy_score(
    y_test,
    y_pred
)

print(
    f"Logistic Regression Accuracy: "
    f"{accuracy * 100:.2f}%"
)


# ============================================================
# 8. CLASSIFICATION REPORT
# ============================================================

print("\n" + "=" * 80)
print("7. CLASSIFICATION REPORT")
print("=" * 80)

print(
    classification_report(
        y_test,
        y_pred,
        zero_division=0
    )
)


# ============================================================
# 9. CONFUSION MATRIX
# ============================================================

print("\n" + "=" * 80)
print("8. CONFUSION MATRIX")
print("=" * 80)

cm = confusion_matrix(
    y_test,
    y_pred
)

print(cm)


# ============================================================
# 10. ACTUAL VS PREDICTED
# ============================================================

print("\n" + "=" * 80)
print("9. ACTUAL VS PREDICTED VALUES")
print("=" * 80)

comparison_df = pd.DataFrame({
    "Actual": y_test.values,
    "Predicted": y_pred
})

print(comparison_df.to_string(index=False))


# ============================================================
# 11. TARGET CLASS MAPPING
# ============================================================

print("\n" + "=" * 80)
print("10. TARGET CLASS MAPPING")
print("=" * 80)

if os.path.exists(MAPPING_FILE):

    mapping_df = pd.read_csv(
        MAPPING_FILE
    )

    print(
        mapping_df.to_string(
            index=False
        )
    )

else:

    print(
        "Target mapping file not found."
    )


# ============================================================
# 12. MODEL COEFFICIENTS
# ============================================================

print("\n" + "=" * 80)
print("11. MODEL COEFFICIENTS")
print("=" * 80)

coefficient_df = pd.DataFrame(
    model.coef_,
    columns=FEATURE_COLUMNS
)

print(
    coefficient_df.to_string(
        index=False
    )
)


# ============================================================
# 13. SAVE PREDICTIONS
# ============================================================

print("\n" + "=" * 80)
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


# ============================================================
# 14. SAVE RESULTS SUMMARY
# ============================================================

results_file = os.path.join(
    RESULTS_DIR,
    "logistic_regression_results.txt"
)

with open(
    results_file,
    "w",
    encoding="utf-8"
) as file:

    file.write(
        "STEP 11 - LOGISTIC REGRESSION RESULTS\n"
    )

    file.write("=" * 60 + "\n")

    file.write(
        f"Accuracy: {accuracy * 100:.2f}%\n\n"
    )

    file.write(
        "Classification Report:\n"
    )

    file.write(
        classification_report(
            y_test,
            y_pred,
            zero_division=0
        )
    )

    file.write(
        "\nConfusion Matrix:\n"
    )

    file.write(
        str(cm)
    )

print("\nResults summary saved to:")
print(results_file)


# ============================================================
# 15. FINAL SUMMARY
# ============================================================

print("\n" + "=" * 80)
print("STEP 11 - LOGISTIC REGRESSION COMPLETED SUCCESSFULLY")
print("=" * 80)

print(
    f"\nFinal Logistic Regression Accuracy: "
    f"{accuracy * 100:.2f}%"
)

print("\nGenerated files:")

print(
    f"1. {prediction_file}"
)

print(
    f"2. {results_file}"
)

print("\n" + "=" * 80)
print("LOGISTIC REGRESSION COMPLETED")
print("=" * 80)