import os
import pandas as pd

from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix
)


# =============================================================================
# STEP 9 - RANDOM FOREST CLASSIFICATION
# =============================================================================

print("=" * 80)
print("STEP 9 - RANDOM FOREST CLASSIFICATION")
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
    "train_data.csv"
)

TEST_FILE = os.path.join(
    RESULTS_DIR,
    "test_data.csv"
)

TARGET_COLUMN = "target"


# =============================================================================
# 2. LOAD TRAINING AND TESTING DATA
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
# 3. DISPLAY COLUMNS
# =============================================================================

print("\n")
print("=" * 80)
print("2. AVAILABLE COLUMNS")
print("=" * 80)

print("\nTraining columns:")

for column in train_df.columns:
    print("-", column)

print("\nTesting columns:")

for column in test_df.columns:
    print("-", column)


# =============================================================================
# 4. DETERMINE TARGET COLUMN
# =============================================================================

print("\n")
print("=" * 80)
print("3. IDENTIFYING TARGET VARIABLE")
print("=" * 80)

# The Step 5 script may save the target column with a different name.
# We check the available columns safely.

possible_target_columns = [
    "target",
    "source_type_encoded",
    "source_type",
    "Target",
    "TARGET"
]

TARGET_COLUMN = None

for column in possible_target_columns:
    if column in train_df.columns and column in test_df.columns:
        TARGET_COLUMN = column
        break


if TARGET_COLUMN is None:

    print("\nERROR: Target column could not be found.")

    print("\nAvailable training columns:")
    print(train_df.columns.tolist())

    print("\nAvailable testing columns:")
    print(test_df.columns.tolist())

    raise ValueError(
        "Target column not found in train_data.csv and test_data.csv"
    )


print("Target variable found:", TARGET_COLUMN)


# =============================================================================
# 5. DEFINE FEATURES
# =============================================================================

print("\n")
print("=" * 80)
print("4. SEPARATING FEATURES AND TARGET")
print("=" * 80)


# Use only numerical ML features.
# This prevents text columns such as title/content/metadata from
# accidentally entering the Random Forest model.

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


# Check that all features exist

missing_features = [
    column
    for column in FEATURE_COLUMNS
    if column not in train_df.columns or column not in test_df.columns
]

if missing_features:

    print("\nERROR: The following feature columns are missing:")

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
# 6. HANDLE MISSING VALUES
# =============================================================================

print("\n")
print("=" * 80)
print("5. HANDLING MISSING VALUES")
print("=" * 80)

X_train = X_train.fillna(0)
X_test = X_test.fillna(0)

print("Missing feature values handled successfully.")


# =============================================================================
# 7. CREATE RANDOM FOREST MODEL
# =============================================================================

print("\n")
print("=" * 80)
print("6. CREATING RANDOM FOREST MODEL")
print("=" * 80)

print("Algorithm: Random Forest Classifier")
print("Number of trees: 100")
print("Random state: 42")

model = RandomForestClassifier(
    n_estimators=100,
    random_state=42
)

print("\nRandom Forest model created successfully.")


# =============================================================================
# 8. TRAIN MODEL
# =============================================================================

print("\n")
print("=" * 80)
print("7. TRAINING RANDOM FOREST MODEL")
print("=" * 80)

model.fit(X_train, y_train)

print("Random Forest model trained successfully.")


# =============================================================================
# 9. MAKE PREDICTIONS
# =============================================================================

print("\n")
print("=" * 80)
print("8. MAKING PREDICTIONS")
print("=" * 80)

y_pred = model.predict(X_test)

print("Predictions generated successfully.")


# =============================================================================
# 10. ACCURACY
# =============================================================================

print("\n")
print("=" * 80)
print("9. MODEL ACCURACY")
print("=" * 80)

accuracy = accuracy_score(y_test, y_pred)

print(f"Random Forest Accuracy: {accuracy * 100:.2f}%")


# =============================================================================
# 11. CLASSIFICATION REPORT
# =============================================================================

print("\n")
print("=" * 80)
print("10. CLASSIFICATION REPORT")
print("=" * 80)

print(
    classification_report(
        y_test,
        y_pred,
        zero_division=0
    )
)


# =============================================================================
# 12. CONFUSION MATRIX
# =============================================================================

print("\n")
print("=" * 80)
print("11. CONFUSION MATRIX")
print("=" * 80)

cm = confusion_matrix(y_test, y_pred)

print(cm)


# =============================================================================
# 13. ACTUAL VS PREDICTED
# =============================================================================

print("\n")
print("=" * 80)
print("12. ACTUAL VS PREDICTED VALUES")
print("=" * 80)

comparison_df = pd.DataFrame({
    "Actual": y_test.values,
    "Predicted": y_pred
})

print(comparison_df.to_string(index=False))


# =============================================================================
# 14. FEATURE IMPORTANCE
# =============================================================================

print("\n")
print("=" * 80)
print("13. FEATURE IMPORTANCE")
print("=" * 80)

importance_df = pd.DataFrame({
    "Feature": FEATURE_COLUMNS,
    "Importance": model.feature_importances_
})

importance_df = importance_df.sort_values(
    by="Importance",
    ascending=False
)

print(importance_df.to_string(index=False))


# =============================================================================
# 15. SAVE PREDICTIONS
# =============================================================================

print("\n")
print("=" * 80)
print("14. SAVING RANDOM FOREST RESULTS")
print("=" * 80)

prediction_file = os.path.join(
    RESULTS_DIR,
    "random_forest_predictions.csv"
)

comparison_df.to_csv(
    prediction_file,
    index=False
)

print("Predictions saved to:")
print(prediction_file)


# =============================================================================
# 16. SAVE FEATURE IMPORTANCE
# =============================================================================

importance_file = os.path.join(
    RESULTS_DIR,
    "random_forest_feature_importance.csv"
)

importance_df.to_csv(
    importance_file,
    index=False
)

print("\nFeature importance saved to:")
print(importance_file)


# =============================================================================
# 17. SAVE RESULTS REPORT
# =============================================================================

results_file = os.path.join(
    RESULTS_DIR,
    "random_forest_results.txt"
)

with open(results_file, "w", encoding="utf-8") as file:

    file.write("RANDOM FOREST CLASSIFICATION RESULTS\n")
    file.write("=" * 60 + "\n\n")

    file.write(f"Algorithm: Random Forest Classifier\n")
    file.write(f"Number of trees: 100\n")
    file.write(f"Random state: 42\n\n")

    file.write(f"Training samples: {len(X_train)}\n")
    file.write(f"Testing samples: {len(X_test)}\n")
    file.write(f"Number of features: {len(FEATURE_COLUMNS)}\n\n")

    file.write(
        f"Accuracy: {accuracy * 100:.2f}%\n\n"
    )

    file.write("Classification Report\n")
    file.write("-" * 60 + "\n")

    file.write(
        classification_report(
            y_test,
            y_pred,
            zero_division=0
        )
    )

    file.write("\n\nConfusion Matrix\n")
    file.write("-" * 60 + "\n")

    file.write(str(cm))

    file.write("\n\nFeature Importance\n")
    file.write("-" * 60 + "\n")

    file.write(
        importance_df.to_string(index=False)
    )


print("\nResults report saved to:")
print(results_file)


# =============================================================================
# 18. FINAL MESSAGE
# =============================================================================

print("\n")
print("=" * 80)
print("STEP 9 - RANDOM FOREST COMPLETED SUCCESSFULLY")
print("=" * 80)

print(f"\nFinal Random Forest Accuracy: {accuracy * 100:.2f}%")

print("\nGenerated files:")
print("1.", prediction_file)
print("2.", importance_file)
print("3.", results_file)

print("\n")
print("=" * 80)
print("READY FOR ALGORITHM 5 - LOGISTIC REGRESSION")
print("=" * 80)