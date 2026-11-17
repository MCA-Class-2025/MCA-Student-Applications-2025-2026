from pathlib import Path

import pandas as pd

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix
)
import joblib


# ============================================================
# PROJECT PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATA_DIR = PROJECT_ROOT / "data" / "processed"
MODEL_DIR = PROJECT_ROOT / "models"

TRAIN_FILE = DATA_DIR / "train.csv"
TEST_FILE = DATA_DIR / "test.csv"

MODEL_FILE = MODEL_DIR / "fake_news_model.pkl"
VECTORIZER_FILE = MODEL_DIR / "tfidf_vectorizer.pkl"


# ============================================================
# CREATE MODEL DIRECTORY
# ============================================================

MODEL_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# ============================================================
# LOAD DATA
# ============================================================

print("\n==============================================")
print(" MULTILINGUAL FAKE NEWS ML MODEL")
print("==============================================")

print("\nLoading training data...")

train_df = pd.read_csv(TRAIN_FILE)

print(
    "Training records:",
    len(train_df)
)

print("\nLoading testing data...")

test_df = pd.read_csv(TEST_FILE)

print(
    "Testing records:",
    len(test_df)
)


# ============================================================
# PREPARE TEXT
# ============================================================

X_train = (
    train_df["text"]
    .fillna("")
    .astype(str)
)

y_train = train_df["label"]


X_test = (
    test_df["text"]
    .fillna("")
    .astype(str)
)

y_test = test_df["label"]


# ============================================================
# TF-IDF
# ============================================================

print("\n==============================================")
print("CREATING TF-IDF FEATURES")
print("==============================================")

vectorizer = TfidfVectorizer(
    lowercase=True,
    ngram_range=(1, 2),
    min_df=2,
    max_df=0.95,
    sublinear_tf=True,
    max_features=150000
)


print("\nFitting TF-IDF on training data...")

X_train_tfidf = vectorizer.fit_transform(
    X_train
)

print(
    "Training feature matrix:",
    X_train_tfidf.shape
)


print("\nTransforming test data...")

X_test_tfidf = vectorizer.transform(
    X_test
)

print(
    "Testing feature matrix:",
    X_test_tfidf.shape
)


# ============================================================
# TRAIN LOGISTIC REGRESSION
# ============================================================

print("\n==============================================")
print("TRAINING LOGISTIC REGRESSION")
print("==============================================")

model = LogisticRegression(
    max_iter=1000,
    class_weight="balanced",
    random_state=42
)


print("\nTraining model...")

model.fit(
    X_train_tfidf,
    y_train
)

print("Model training completed.")


# ============================================================
# PREDICTIONS
# ============================================================

print("\n==============================================")
print("MAKING PREDICTIONS")
print("==============================================")

y_pred = model.predict(
    X_test_tfidf
)


# ============================================================
# OVERALL ACCURACY
# ============================================================

accuracy = accuracy_score(
    y_test,
    y_pred
)

print("\n==============================================")
print("OVERALL MODEL PERFORMANCE")
print("==============================================")

print(
    f"\nAccuracy: {accuracy * 100:.2f}%"
)


# ============================================================
# CLASSIFICATION REPORT
# ============================================================

print("\nClassification Report:")

print(
    classification_report(
        y_test,
        y_pred,
        digits=4
    )
)


# ============================================================
# CONFUSION MATRIX
# ============================================================

print("\nConfusion Matrix:")

print(
    confusion_matrix(
        y_test,
        y_pred,
        labels=["Fake", "Real"]
    )
)


# ============================================================
# LANGUAGE-WISE EVALUATION
# ============================================================

print("\n==============================================")
print("LANGUAGE-WISE PERFORMANCE")
print("==============================================")


for language in [
    "English",
    "Hindi",
    "Marathi"
]:

    language_mask = (
        test_df["language"] == language
    )

    language_true = y_test[
        language_mask
    ]

    language_pred = y_pred[
        language_mask
    ]

    if len(language_true) == 0:
        continue

    language_accuracy = accuracy_score(
        language_true,
        language_pred
    )

    print(
        f"\n{language}:"
    )

    print(
        f"Records: {len(language_true)}"
    )

    print(
        f"Accuracy: "
        f"{language_accuracy * 100:.2f}%"
    )


# ============================================================
# SAVE MODEL
# ============================================================

print("\n==============================================")
print("SAVING MODEL")
print("==============================================")

joblib.dump(
    model,
    MODEL_FILE
)

joblib.dump(
    vectorizer,
    VECTORIZER_FILE
)


print(
    "\nModel saved to:"
)

print(MODEL_FILE)

print(
    "\nTF-IDF vectorizer saved to:"
)

print(VECTORIZER_FILE)


# ============================================================
# COMPLETED
# ============================================================

print("\n==============================================")
print(" STEP 3 COMPLETED")
print("==============================================")