import os
import pandas as pd

from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix
)


# ================================================================
# STEP 10 - RANDOM FOREST CLASSIFICATION
# ================================================================

print("=" * 80)
print("STEP 10 - RANDOM FOREST CLASSIFICATION")
print("=" * 80)


# ------------------------------------------------
# PATHS
# ------------------------------------------------

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

MAPPING_FILE = os.path.join(
    RESULTS_DIR,
    "target_mapping.csv"
)

PREDICTION_FILE = os.path.join(
    RESULTS_DIR,
    "random_forest_predictions.csv"
)

RESULT_FILE = os.path.join(
    RESULTS_DIR,
    "random_forest_results.txt"
)


# ------------------------------------------------
# FEATURES
# ------------------------------------------------

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


# ================================================================
# 1. LOAD TRAINING AND TESTING DATA
# ================================================================

print("\n" + "=" * 80)
print("1. LOADING TRAINING AND TESTING DATA")
print("=" * 80)

train_df = pd.read_csv(TRAIN_FILE)
test_df = pd.read_csv(TEST_FILE)

print("Training data loaded successfully.")
print(f"Training rows: {len(train_df)}")

print("\nTesting data loaded successfully.")
print(f"Testing rows: {len(test_df)}")


# ================================================================
# 2. SEPARATE FEATURES AND TARGET
# ================================================================

print("\n" + "=" * 80)
print("2. SEPARATING FEATURES AND TARGET")
print("=" * 80)

X_train = train_df[FEATURE_COLUMNS]
X_test = test_df[FEATURE_COLUMNS]

y_train = train_df["target"]
y_test = test_df["target"]

print("Features used:")

for number, feature in enumerate(FEATURE_COLUMNS, start=1):
    print(f"{number}. {feature}")

print(f"\nNumber of features: {len(FEATURE_COLUMNS)}")


# ================================================================
# 3. CREATE RANDOM FOREST MODEL
# ================================================================

print("\n" + "=" * 80)
print("3. CREATING RANDOM FOREST MODEL")
print("=" * 80)

print("Algorithm: Random Forest Classifier")
print("Number of trees: 100")
print("Random state: 42")

model = RandomForestClassifier(
    n_estimators=100,
    random_state=42
)

print("\nRandom Forest model created successfully.")


# ================================================================
# 4. TRAIN MODEL
# ================================================================

print("\n" + "=" * 80)
print("4. TRAINING RANDOM FOREST MODEL")
print("=" * 80)

model.fit(X_train, y_train)

print("Random Forest model trained successfully.")


# ================================================================
# 5. MAKE PREDICTIONS
# ================================================================

print("\n" + "=" * 80)
print("5. MAKING PREDICTIONS")
print("=" * 80)

y_pred = model.predict(X_test)

print("Predictions generated successfully.")


# ================================================================
# 6. MODEL ACCURACY
# ================================================================

print("\n" + "=" * 80)
print("6. MODEL ACCURACY")
print("=" * 80)

accuracy = accuracy_score(y_test, y_pred)

print(f"Random Forest Accuracy: {accuracy * 100:.2f}%")


# ================================================================
# 7. CLASSIFICATION REPORT
# ================================================================

print("\n" + "=" * 80)
print("7. CLASSIFICATION REPORT")
print("=" * 80)

report = classification_report(
    y_test,
    y_pred,
    zero_division=0
)

print(report)


# ================================================================
# 8. CONFUSION MATRIX
# ================================================================

print("\n" + "=" * 80)
print("8. CONFUSION MATRIX")
print("=" * 80)

cm = confusion_matrix(y_test, y_pred)

print(cm)


# ================================================================
# 9. ACTUAL VS PREDICTED
# ================================================================

print("\n" + "=" * 80)
print("9. ACTUAL VS PREDICTED VALUES")
print("=" * 80)

comparison_df = pd.DataFrame({
    "Actual": y_test.values,
    "Predicted": y_pred
})

print(comparison_df.to_string(index=False))


# ================================================================
# 10. TARGET CLASS MAPPING
# ================================================================

print("\n" + "=" * 80)
print("10. TARGET CLASS MAPPING")
print("=" * 80)

if os.path.exists(MAPPING_FILE):

    mapping_df = pd.read_csv(MAPPING_FILE)

    print(mapping_df.to_string(index=False))

else:

    print("Target mapping file not found.")


# ================================================================
# 11. FEATURE IMPORTANCE
# ================================================================

print("\n" + "=" * 80)
print("11. FEATURE IMPORTANCE")
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


# ================================================================
# 12. SAVE PREDICTIONS
# ================================================================

print("\n" + "=" * 80)
print("12. SAVING RANDOM FOREST RESULTS")
print("=" * 80)

prediction_output = test_df.copy()

prediction_output["actual_source_type"] = y_test.values
prediction_output["predicted_source_type"] = y_pred

prediction_output.to_csv(
    PREDICTION_FILE,
    index=False
)

print("Predictions saved to:")
print(PREDICTION_FILE)


# ================================================================
# 13. SAVE RESULTS REPORT
# ================================================================

with open(RESULT_FILE, "w", encoding="utf-8") as file:

    file.write("STEP 10 - RANDOM FOREST CLASSIFICATION\n")
    file.write("=" * 80 + "\n\n")

    file.write(f"Training rows: {len(train_df)}\n")
    file.write(f"Testing rows: {len(test_df)}\n")
    file.write(f"Number of features: {len(FEATURE_COLUMNS)}\n\n")

    file.write("Features:\n")

    for feature in FEATURE_COLUMNS:
        file.write(f"- {feature}\n")

    file.write("\n")

    file.write(f"Random Forest Accuracy: {accuracy * 100:.2f}%\n\n")

    file.write("Classification Report:\n")
    file.write(report)

    file.write("\n\nConfusion Matrix:\n")
    file.write(str(cm))

    file.write("\n\nFeature Importance:\n")
    file.write(importance_df.to_string(index=False))


# ================================================================
# FINAL MESSAGE
# ================================================================

print("\n" + "=" * 80)
print("STEP 10 - RANDOM FOREST COMPLETED SUCCESSFULLY")
print("=" * 80)

print(f"\nFinal Random Forest Accuracy: {accuracy * 100:.2f}%")

print("\nGenerated files:")

print(f"1. {PREDICTION_FILE}")
print(f"2. {RESULT_FILE}")

print("\n" + "=" * 80)
print("READY FOR ALGORITHM 5 - LOGISTIC REGRESSION")
print("=" * 80)