import os
import pandas as pd

from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix
)


# ============================================================
# STEP 8 - DECISION TREE CLASSIFICATION
# ============================================================

print("=" * 80)
print("STEP 8 - DECISION TREE CLASSIFICATION")
print("=" * 80)
print()


# ============================================================
# 1. PATHS
# ============================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

RESULTS_DIR = os.path.join(
    BASE_DIR,
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

TARGET_MAPPING_FILE = os.path.join(
    RESULTS_DIR,
    "target_mapping.csv"
)

PREDICTIONS_FILE = os.path.join(
    RESULTS_DIR,
    "decision_tree_predictions.csv"
)

RESULTS_TEXT_FILE = os.path.join(
    RESULTS_DIR,
    "decision_tree_results.txt"
)


TARGET_COLUMN = "source_type"


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


# ============================================================
# 2. LOAD TRAINING AND TESTING DATA
# ============================================================

print("=" * 80)
print("1. LOADING TRAINING AND TESTING DATA")
print("=" * 80)

if not os.path.exists(TRAIN_FILE):
    raise FileNotFoundError(
        f"Training file not found:\n{TRAIN_FILE}"
    )

if not os.path.exists(TEST_FILE):
    raise FileNotFoundError(
        f"Testing file not found:\n{TEST_FILE}"
    )

train_df = pd.read_csv(TRAIN_FILE)
test_df = pd.read_csv(TEST_FILE)

print("Training data loaded successfully.")
print("Training rows:", len(train_df))
print()

print("Testing data loaded successfully.")
print("Testing rows:", len(test_df))
print()


# ============================================================
# 3. CHECK AVAILABLE COLUMNS
# ============================================================

print("=" * 80)
print("2. CHECKING DATASET COLUMNS")
print("=" * 80)

print("Training columns:")
for column in train_df.columns:
    print("-", column)

print()

print("Testing columns:")
for column in test_df.columns:
    print("-", column)

print()


# ============================================================
# 4. SEPARATING FEATURES
# ============================================================

print("=" * 80)
print("3. SEPARATING FEATURES AND TARGET")
print("=" * 80)

print("Features used:")

for number, feature in enumerate(FEATURE_COLUMNS, start=1):
    print(f"{number}. {feature}")

print()
print("Number of features:", len(FEATURE_COLUMNS))
print()


# ============================================================
# 5. CHECK FEATURES
# ============================================================

missing_train_features = [
    feature
    for feature in FEATURE_COLUMNS
    if feature not in train_df.columns
]

missing_test_features = [
    feature
    for feature in FEATURE_COLUMNS
    if feature not in test_df.columns
]

if missing_train_features:
    raise ValueError(
        "Missing features in training data:\n"
        + "\n".join(missing_train_features)
    )

if missing_test_features:
    raise ValueError(
        "Missing features in testing data:\n"
        + "\n".join(missing_test_features)
    )


# ============================================================
# 6. LOAD TARGET VARIABLE
# ============================================================

print("=" * 80)
print("4. LOADING TARGET VARIABLE")
print("=" * 80)

# ------------------------------------------------------------
# The train/test files created in Step 5 may contain the target
# either as 'source_type' or as the encoded target column.
# We therefore detect it safely.
# ------------------------------------------------------------

possible_target_columns = [
    "source_type",
    "target",
    "target_encoded",
    "source_type_encoded"
]

train_target_column = None
test_target_column = None

for column in possible_target_columns:
    if column in train_df.columns:
        train_target_column = column
        break

for column in possible_target_columns:
    if column in test_df.columns:
        test_target_column = column
        break


if train_target_column is None:
    raise ValueError(
        "\nTarget column was not found in train_data.csv.\n"
        "Available columns are:\n"
        + "\n".join(train_df.columns)
        + "\n\nPlease check Step 5 output."
    )

if test_target_column is None:
    raise ValueError(
        "\nTarget column was not found in test_data.csv.\n"
        "Available columns are:\n"
        + "\n".join(test_df.columns)
        + "\n\nPlease check Step 5 output."
    )


print("Training target column:", train_target_column)
print("Testing target column:", test_target_column)
print()


# ============================================================
# 7. CREATE X AND Y
# ============================================================

X_train = train_df[FEATURE_COLUMNS].copy()
X_test = test_df[FEATURE_COLUMNS].copy()

y_train = train_df[train_target_column].copy()
y_test = test_df[test_target_column].copy()


# ============================================================
# 8. CONVERT TARGET TO NUMERIC IF NECESSARY
# ============================================================

print("=" * 80)
print("5. PREPARING TARGET VARIABLE")
print("=" * 80)

# If target contains names such as Google Drive, GitHub etc.,
# convert them using the target mapping file.

if not pd.api.types.is_numeric_dtype(y_train):

    if os.path.exists(TARGET_MAPPING_FILE):

        mapping_df = pd.read_csv(TARGET_MAPPING_FILE)

        print("Target mapping file loaded.")

        print()
        print("Target mapping:")
        print(mapping_df.to_string(index=False))
        print()

        # Detect mapping column names
        if (
            "source_type" in mapping_df.columns
            and "target_value" in mapping_df.columns
        ):

            mapping = dict(
                zip(
                    mapping_df["source_type"],
                    mapping_df["target_value"]
                )
            )

            y_train = y_train.map(mapping)
            y_test = y_test.map(mapping)

        elif (
            "source_type" in mapping_df.columns
            and "target" in mapping_df.columns
        ):

            mapping = dict(
                zip(
                    mapping_df["source_type"],
                    mapping_df["target"]
                )
            )

            y_train = y_train.map(mapping)
            y_test = y_test.map(mapping)

        else:

            raise ValueError(
                "Could not understand target_mapping.csv format."
            )

    else:

        # Fallback: encode alphabetically
        all_targets = pd.concat(
            [y_train, y_test]
        ).astype(str).unique()

        all_targets = sorted(all_targets)

        mapping = {
            value: index
            for index, value in enumerate(all_targets)
        }

        print("Target mapping created automatically:")
        print(mapping)
        print()

        y_train = y_train.astype(str).map(mapping)
        y_test = y_test.astype(str).map(mapping)


# Convert to integers
y_train = pd.to_numeric(
    y_train,
    errors="coerce"
)

y_test = pd.to_numeric(
    y_test,
    errors="coerce"
)


# Check for invalid target values
if y_train.isna().any():
    raise ValueError(
        "Invalid or missing target values found in training data."
    )

if y_test.isna().any():
    raise ValueError(
        "Invalid or missing target values found in testing data."
    )


y_train = y_train.astype(int)
y_test = y_test.astype(int)


print("Target variable prepared successfully.")
print()

print("Training target distribution:")
print(y_train.value_counts().sort_index())

print()

print("Testing target distribution:")
print(y_test.value_counts().sort_index())

print()


# ============================================================
# 9. CREATE DECISION TREE MODEL
# ============================================================

print("=" * 80)
print("6. CREATING DECISION TREE MODEL")
print("=" * 80)

model = DecisionTreeClassifier(
    criterion="gini",
    max_depth=5,
    random_state=42
)

print("Algorithm: Decision Tree")
print("Criterion: Gini")
print("Maximum depth: 5")
print("Random state: 42")
print()

print("Decision Tree model created successfully.")
print()


# ============================================================
# 10. TRAIN MODEL
# ============================================================

print("=" * 80)
print("7. TRAINING DECISION TREE MODEL")
print("=" * 80)

model.fit(
    X_train,
    y_train
)

print("Decision Tree model trained successfully.")
print()


# ============================================================
# 11. MAKE PREDICTIONS
# ============================================================

print("=" * 80)
print("8. MAKING PREDICTIONS")
print("=" * 80)

y_pred = model.predict(
    X_test
)

print("Predictions generated successfully.")
print()


# ============================================================
# 12. MODEL ACCURACY
# ============================================================

print("=" * 80)
print("9. MODEL ACCURACY")
print("=" * 80)

accuracy = accuracy_score(
    y_test,
    y_pred
)

print(
    f"Decision Tree Accuracy: {accuracy * 100:.2f}%"
)

print()


# ============================================================
# 13. CLASSIFICATION REPORT
# ============================================================

print("=" * 80)
print("10. CLASSIFICATION REPORT")
print("=" * 80)

unique_classes = sorted(
    set(y_test.tolist()) | set(y_pred.tolist())
)

report = classification_report(
    y_test,
    y_pred,
    labels=unique_classes,
    zero_division=0
)

print(report)


# ============================================================
# 14. CONFUSION MATRIX
# ============================================================

print("=" * 80)
print("11. CONFUSION MATRIX")
print("=" * 80)

cm = confusion_matrix(
    y_test,
    y_pred,
    labels=unique_classes
)

print(cm)
print()


# ============================================================
# 15. ACTUAL VS PREDICTED
# ============================================================

print("=" * 80)
print("12. ACTUAL VS PREDICTED VALUES")
print("=" * 80)

comparison_df = pd.DataFrame(
    {
        "Actual": y_test,
        "Predicted": y_pred
    }
)

print(
    comparison_df.to_string(index=False)
)

print()


# ============================================================
# 16. TARGET CLASS MAPPING
# ============================================================

print("=" * 80)
print("13. TARGET CLASS MAPPING")
print("=" * 80)

if os.path.exists(TARGET_MAPPING_FILE):

    mapping_df = pd.read_csv(
        TARGET_MAPPING_FILE
    )

    print(
        mapping_df.to_string(index=False)
    )

else:

    print(
        "Target mapping file not found."
    )

print()


# ============================================================
# 17. SAVE PREDICTIONS
# ============================================================

print("=" * 80)
print("14. SAVING DECISION TREE RESULTS")
print("=" * 80)

# Save predictions
predictions_output = test_df.copy()

predictions_output["actual_target"] = y_test.values
predictions_output["predicted_target"] = y_pred

predictions_output.to_csv(
    PREDICTIONS_FILE,
    index=False
)

print("Predictions saved to:")
print(PREDICTIONS_FILE)
print()


# ============================================================
# 18. SAVE TEXT RESULTS
# ============================================================

with open(
    RESULTS_TEXT_FILE,
    "w",
    encoding="utf-8"
) as file:

    file.write(
        "STEP 8 - DECISION TREE CLASSIFICATION\n"
    )

    file.write(
        "=" * 70 + "\n\n"
    )

    file.write(
        f"Training rows: {len(X_train)}\n"
    )

    file.write(
        f"Testing rows: {len(X_test)}\n"
    )

    file.write(
        f"Number of features: {len(FEATURE_COLUMNS)}\n"
    )

    file.write(
        f"Accuracy: {accuracy * 100:.2f}%\n\n"
    )

    file.write(
        "Features:\n"
    )

    for feature in FEATURE_COLUMNS:
        file.write(
            f"- {feature}\n"
        )

    file.write(
        "\nClassification Report:\n"
    )

    file.write(
        report
    )

    file.write(
        "\n\nConfusion Matrix:\n"
    )

    file.write(
        str(cm)
    )

    file.write(
        "\n\nActual vs Predicted:\n"
    )

    file.write(
        comparison_df.to_string(index=False)
    )


# ============================================================
# 19. FINAL OUTPUT
# ============================================================

print("=" * 80)
print("STEP 8 - DECISION TREE COMPLETED SUCCESSFULLY")
print("=" * 80)

print()

print(
    f"Final Decision Tree Accuracy: {accuracy * 100:.2f}%"
)

print()

print("Generated files:")
print(
    f"1. {PREDICTIONS_FILE}"
)

print(
    f"2. {RESULTS_TEXT_FILE}"
)

print()

print("=" * 80)
print("READY FOR ALGORITHM 4 - RANDOM FOREST")
print("=" * 80)