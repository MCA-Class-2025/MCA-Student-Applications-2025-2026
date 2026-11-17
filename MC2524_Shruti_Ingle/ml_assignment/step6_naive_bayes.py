import os
import pandas as pd

from sklearn.naive_bayes import GaussianNB
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix
)


# ============================================================
# STEP 6 - NAIVE BAYES CLASSIFICATION
# ============================================================

print("=" * 80)
print("STEP 6 - NAIVE BAYES CLASSIFICATION")
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
print(f"Training rows: {len(train_df)}")

print("\nTesting data loaded successfully.")
print(f"Testing rows: {len(test_df)}")


# ============================================================
# 3. SEPARATE FEATURES AND TARGET
# ============================================================

print("\n" + "=" * 80)
print("2. SEPARATING FEATURES AND TARGET")
print("=" * 80)

X_train = train_df.drop(
    columns=["target"]
)

y_train = train_df["target"]

X_test = test_df.drop(
    columns=["target"]
)

y_test = test_df["target"]

print("Features:")
for number, column in enumerate(X_train.columns, start=1):
    print(f"{number}. {column}")

print("\nNumber of features:", X_train.shape[1])


# ============================================================
# 4. CREATE NAIVE BAYES MODEL
# ============================================================

print("\n" + "=" * 80)
print("3. CREATING NAIVE BAYES MODEL")
print("=" * 80)

model = GaussianNB()

print("Algorithm: Gaussian Naive Bayes")
print("Model created successfully.")


# ============================================================
# 5. TRAIN MODEL
# ============================================================

print("\n" + "=" * 80)
print("4. TRAINING NAIVE BAYES MODEL")
print("=" * 80)

model.fit(
    X_train,
    y_train
)

print("Naive Bayes model trained successfully.")


# ============================================================
# 6. MAKE PREDICTIONS
# ============================================================

print("\n" + "=" * 80)
print("5. MAKING PREDICTIONS")
print("=" * 80)

y_pred = model.predict(X_test)

print("Predictions generated successfully.")


# ============================================================
# 7. ACCURACY
# ============================================================

print("\n" + "=" * 80)
print("6. MODEL ACCURACY")
print("=" * 80)

accuracy = accuracy_score(
    y_test,
    y_pred
)

print(
    f"Naive Bayes Accuracy: "
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
# 10. DISPLAY ACTUAL VS PREDICTED
# ============================================================

print("\n" + "=" * 80)
print("9. ACTUAL VS PREDICTED VALUES")
print("=" * 80)

comparison = pd.DataFrame({
    "Actual": y_test.values,
    "Predicted": y_pred
})

print(comparison.to_string(index=False))


# ============================================================
# 11. LOAD TARGET MAPPING
# ============================================================

print("\n" + "=" * 80)
print("10. TARGET CLASS MAPPING")
print("=" * 80)

if os.path.exists(MAPPING_FILE):

    mapping_df = pd.read_csv(
        MAPPING_FILE
    )

    print(mapping_df.to_string(index=False))

else:

    print("Target mapping file not found.")


# ============================================================
# 12. SAVE RESULTS
# ============================================================

print("\n" + "=" * 80)
print("11. SAVING NAIVE BAYES RESULTS")
print("=" * 80)

results_file = os.path.join(
    RESULTS_DIR,
    "naive_bayes_predictions.csv"
)

comparison.to_csv(
    results_file,
    index=False
)

print(
    f"Predictions saved to:\n"
    f"{results_file}"
)


# ============================================================
# 13. SAVE MODEL SUMMARY
# ============================================================

summary_file = os.path.join(
    RESULTS_DIR,
    "naive_bayes_results.txt"
)

with open(
    summary_file,
    "w",
    encoding="utf-8"
) as file:

    file.write(
        "NAIVE BAYES CLASSIFICATION RESULTS\n"
    )

    file.write(
        "=" * 60 + "\n\n"
    )

    file.write(
        f"Training samples: {len(X_train)}\n"
    )

    file.write(
        f"Testing samples: {len(X_test)}\n"
    )

    file.write(
        f"Number of features: {X_train.shape[1]}\n"
    )

    file.write(
        f"Accuracy: {accuracy * 100:.2f}%\n\n"
    )

    file.write(
        "Classification Report\n"
    )

    file.write(
        "-" * 60 + "\n"
    )

    file.write(
        classification_report(
            y_test,
            y_pred,
            zero_division=0
        )
    )

    file.write(
        "\nConfusion Matrix\n"
    )

    file.write(
        "-" * 60 + "\n"
    )

    file.write(
        str(cm)
    )


# ============================================================
# FINAL
# ============================================================

print("\n" + "=" * 80)
print("STEP 6 - NAIVE BAYES COMPLETED SUCCESSFULLY")
print("=" * 80)

print(
    f"\nFinal Accuracy: "
    f"{accuracy * 100:.2f}%"
)

print("\nGenerated files:")

print(
    f"1. {results_file}"
)

print(
    f"2. {summary_file}"
)

print("\n" + "=" * 80)
print("READY FOR ALGORITHM 2 - SVM")
print("=" * 80)