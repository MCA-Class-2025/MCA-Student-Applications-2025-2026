# ============================================================
# train_emotion_model.py
# StoryVerse AI - Emotion Detection Data Science Module
# ============================================================

import os
import re
import pickle
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    precision_score,
    recall_score,
    f1_score
)


# ============================================================
# 1. CONFIGURATION
# ============================================================

DATA_DIR = "dataset"

TRAIN_FILE = os.path.join(
    DATA_DIR,
    "training.csv"
)

VALIDATION_FILE = os.path.join(
    DATA_DIR,
    "validation.csv"
)

TEST_FILE = os.path.join(
    DATA_DIR,
    "test.csv"
)

MODEL_DIR = "emotion_model"

os.makedirs(
    MODEL_DIR,
    exist_ok=True
)

print("=" * 60)
print("        STORYVERSE AI")
print("   EMOTION DETECTION MODEL TRAINING")
print("=" * 60)


# ============================================================
# 2. LOAD DATASET
# ============================================================

print("\n[1] Loading datasets...")

train_df = pd.read_csv(
    TRAIN_FILE
)

validation_df = pd.read_csv(
    VALIDATION_FILE
)

test_df = pd.read_csv(
    TEST_FILE
)

print(
    f"Training samples   : {len(train_df)}"
)

print(
    f"Validation samples : {len(validation_df)}"
)

print(
    f"Testing samples    : {len(test_df)}"
)

print(
    f"Total samples      : "
    f"{len(train_df) + len(validation_df) + len(test_df)}"
)


# ============================================================
# 3. DISPLAY DATASET INFORMATION
# ============================================================

print("\n" + "=" * 60)
print("DATASET INFORMATION")
print("=" * 60)

print("\nTraining columns:")
print(train_df.columns.tolist())

print("\nFirst 5 training records:")
print(train_df.head())

print("\nTraining dataset information:")
print(train_df.info())

print("\nMissing values:")
print(train_df.isnull().sum())


# ============================================================
# 4. CHECK REQUIRED COLUMNS
# ============================================================

required_columns = [
    "text",
    "label"
]

for column in required_columns:

    if column not in train_df.columns:

        raise ValueError(
            f"Required column '{column}' "
            f"not found in training.csv"
        )

    if column not in validation_df.columns:

        raise ValueError(
            f"Required column '{column}' "
            f"not found in validation.csv"
        )

    if column not in test_df.columns:

        raise ValueError(
            f"Required column '{column}' "
            f"not found in test.csv"
        )


# ============================================================
# 5. REMOVE MISSING VALUES
# ============================================================

print("\n[2] Removing missing values...")

print(
    "Training missing rows:",
    train_df.isnull().any(axis=1).sum()
)

print(
    "Validation missing rows:",
    validation_df.isnull().any(axis=1).sum()
)

print(
    "Testing missing rows:",
    test_df.isnull().any(axis=1).sum()
)

train_df = train_df.dropna(
    subset=[
        "text",
        "label"
    ]
)

validation_df = validation_df.dropna(
    subset=[
        "text",
        "label"
    ]
)

test_df = test_df.dropna(
    subset=[
        "text",
        "label"
    ]
)


# ============================================================
# 6. REMOVE DUPLICATES
# ============================================================

print("\n[3] Removing duplicate records...")

train_before = len(train_df)
validation_before = len(validation_df)
test_before = len(test_df)

train_df = train_df.drop_duplicates(
    subset=["text"]
)

validation_df = validation_df.drop_duplicates(
    subset=["text"]
)

test_df = test_df.drop_duplicates(
    subset=["text"]
)

print(
    "Training duplicates removed:",
    train_before - len(train_df)
)

print(
    "Validation duplicates removed:",
    validation_before - len(validation_df)
)

print(
    "Testing duplicates removed:",
    test_before - len(test_df)
)


# ============================================================
# 7. TEXT PREPROCESSING
# ============================================================

def clean_text(text):

    # Convert to string
    text = str(text)

    # Convert to lowercase
    text = text.lower()

    # Remove URLs
    text = re.sub(
        r"http\S+|www\S+",
        "",
        text
    )

    # Remove HTML tags
    text = re.sub(
        r"<.*?>",
        "",
        text
    )

    # Remove numbers
    text = re.sub(
        r"\d+",
        "",
        text
    )

    # Keep alphabetic characters and spaces
    text = re.sub(
        r"[^a-zA-Z\s]",
        " ",
        text
    )

    # Remove extra spaces
    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip()


print("\n[4] Preprocessing text...")

train_df["clean_text"] = (
    train_df["text"]
    .apply(clean_text)
)

validation_df["clean_text"] = (
    validation_df["text"]
    .apply(clean_text)
)

test_df["clean_text"] = (
    test_df["text"]
    .apply(clean_text)
)


print("\nExample preprocessing:")

print(
    "Original:",
    train_df.iloc[0]["text"]
)

print(
    "Cleaned :",
    train_df.iloc[0]["clean_text"]
)


# ============================================================
# 8. EXPLORATORY DATA ANALYSIS
# ============================================================

print("\n" + "=" * 60)
print("EXPLORATORY DATA ANALYSIS")
print("=" * 60)


print("\nEmotion labels:")

print(
    train_df["label"]
    .value_counts()
    .sort_index()
)


# ============================================================
# 9. EMOTION DISTRIBUTION
# ============================================================

plt.figure(
    figsize=(9, 6)
)

train_df["label"].value_counts().sort_index().plot(
    kind="bar"
)

plt.title(
    "Emotion Distribution in Training Dataset"
)

plt.xlabel(
    "Emotion Label"
)

plt.ylabel(
    "Number of Samples"
)

plt.xticks(
    rotation=0
)

plt.tight_layout()

plt.savefig(
    os.path.join(
        MODEL_DIR,
        "emotion_distribution.png"
    )
)

plt.show()


# ============================================================
# 10. TEXT LENGTH ANALYSIS
# ============================================================

train_df["text_length"] = (
    train_df["clean_text"]
    .apply(len)
)

plt.figure(
    figsize=(9, 6)
)

plt.hist(
    train_df["text_length"],
    bins=40
)

plt.title(
    "Distribution of Text Length"
)

plt.xlabel(
    "Text Length"
)

plt.ylabel(
    "Frequency"
)

plt.tight_layout()

plt.savefig(
    os.path.join(
        MODEL_DIR,
        "text_length_distribution.png"
    )
)

plt.show()


# ============================================================
# 11. PREPARE X AND Y
# ============================================================

X_train = train_df[
    "clean_text"
]

y_train = train_df[
    "label"
]

X_validation = validation_df[
    "clean_text"
]

y_validation = validation_df[
    "label"
]

X_test = test_df[
    "clean_text"
]

y_test = test_df[
    "label"
]


# ============================================================
# 12. TF-IDF FEATURE EXTRACTION
# ============================================================

print("\n" + "=" * 60)
print("TF-IDF FEATURE EXTRACTION")
print("=" * 60)

vectorizer = TfidfVectorizer(

    max_features=10000,

    ngram_range=(
        1,
        2
    ),

    min_df=2,

    sublinear_tf=True

)


print("\nFitting TF-IDF on training data...")

X_train_tfidf = vectorizer.fit_transform(
    X_train
)


print(
    "Transforming validation data..."
)

X_validation_tfidf = vectorizer.transform(
    X_validation
)


print(
    "Transforming test data..."
)

X_test_tfidf = vectorizer.transform(
    X_test
)


print(
    "\nTraining TF-IDF shape:",
    X_train_tfidf.shape
)

print(
    "Validation TF-IDF shape:",
    X_validation_tfidf.shape
)

print(
    "Testing TF-IDF shape:",
    X_test_tfidf.shape
)


# ============================================================
# 13. TRAIN MACHINE LEARNING MODEL
# ============================================================

print("\n" + "=" * 60)
print("MODEL TRAINING")
print("=" * 60)

print(
    "\nTraining Logistic Regression..."
)

model = LogisticRegression(

    max_iter=1000,

    class_weight="balanced",

    random_state=42

)

model.fit(
    X_train_tfidf,
    y_train
)

print(
    "Model training completed!"
)


# ============================================================
# 14. VALIDATION PREDICTION
# ============================================================

print("\n" + "=" * 60)
print("VALIDATION RESULTS")
print("=" * 60)

validation_predictions = (
    model.predict(
        X_validation_tfidf
    )
)

validation_accuracy = (
    accuracy_score(
        y_validation,
        validation_predictions
    )
)

validation_precision = (
    precision_score(
        y_validation,
        validation_predictions,
        average="weighted",
        zero_division=0
    )
)

validation_recall = (
    recall_score(
        y_validation,
        validation_predictions,
        average="weighted",
        zero_division=0
    )
)

validation_f1 = (
    f1_score(
        y_validation,
        validation_predictions,
        average="weighted",
        zero_division=0
    )
)

print(
    f"Accuracy  : {validation_accuracy:.4f}"
)

print(
    f"Precision : {validation_precision:.4f}"
)

print(
    f"Recall    : {validation_recall:.4f}"
)

print(
    f"F1 Score  : {validation_f1:.4f}"
)


# ============================================================
# 15. FINAL TEST PREDICTION
# ============================================================

print("\n" + "=" * 60)
print("FINAL TEST RESULTS")
print("=" * 60)

test_predictions = (
    model.predict(
        X_test_tfidf
    )
)

test_accuracy = (
    accuracy_score(
        y_test,
        test_predictions
    )
)

test_precision = (
    precision_score(
        y_test,
        test_predictions,
        average="weighted",
        zero_division=0
    )
)

test_recall = (
    recall_score(
        y_test,
        test_predictions,
        average="weighted",
        zero_division=0
    )
)

test_f1 = (
    f1_score(
        y_test,
        test_predictions,
        average="weighted",
        zero_division=0
    )
)

print(
    f"Accuracy  : {test_accuracy:.4f}"
)

print(
    f"Precision : {test_precision:.4f}"
)

print(
    f"Recall    : {test_recall:.4f}"
)

print(
    f"F1 Score  : {test_f1:.4f}"
)


# ============================================================
# 16. CLASSIFICATION REPORT
# ============================================================

print("\n" + "=" * 60)
print("CLASSIFICATION REPORT")
print("=" * 60)

print(
    classification_report(
        y_test,
        test_predictions,
        zero_division=0
    )
)


# ============================================================
# 17. CONFUSION MATRIX
# ============================================================

print("\nGenerating confusion matrix...")

cm = confusion_matrix(
    y_test,
    test_predictions
)

plt.figure(
    figsize=(8, 7)
)

sns.heatmap(
    cm,
    annot=True,
    fmt="d",
    cmap="Blues"
)

plt.title(
    "Emotion Classification Confusion Matrix"
)

plt.xlabel(
    "Predicted Label"
)

plt.ylabel(
    "Actual Label"
)

plt.tight_layout()

plt.savefig(
    os.path.join(
        MODEL_DIR,
        "confusion_matrix.png"
    )
)

plt.show()


# ============================================================
# 18. SAVE MODEL
# ============================================================

print("\n" + "=" * 60)
print("SAVING MODEL")
print("=" * 60)

model_path = os.path.join(
    MODEL_DIR,
    "emotion_model.pkl"
)

vectorizer_path = os.path.join(
    MODEL_DIR,
    "tfidf_vectorizer.pkl"
)

with open(
    model_path,
    "wb"
) as file:

    pickle.dump(
        model,
        file
    )


with open(
    vectorizer_path,
    "wb"
) as file:

    pickle.dump(
        vectorizer,
        file
    )


print(
    f"Model saved at:\n{model_path}"
)

print(
    f"Vectorizer saved at:\n{vectorizer_path}"
)


# ============================================================
# 19. SAVE LABEL INFORMATION
# ============================================================

labels = sorted(
    train_df["label"]
    .unique()
)

label_mapping = {
    int(label): int(label)
    for label in labels
}

label_mapping_path = os.path.join(
    MODEL_DIR,
    "label_mapping.pkl"
)

with open(
    label_mapping_path,
    "wb"
) as file:

    pickle.dump(
        label_mapping,
        file
    )


print(
    f"Label mapping saved at:\n"
    f"{label_mapping_path}"
)


# ============================================================
# 20. TEST THE SAVED MODEL
# ============================================================

print("\n" + "=" * 60)
print("TESTING SAVED MODEL")
print("=" * 60)

with open(
    model_path,
    "rb"
) as file:

    loaded_model = pickle.load(
        file
    )


with open(
    vectorizer_path,
    "rb"
) as file:

    loaded_vectorizer = pickle.load(
        file
    )


sample_text = (
    "I am extremely happy "
    "and excited today"
)

sample_clean = clean_text(
    sample_text
)

sample_vector = (
    loaded_vectorizer.transform(
        [sample_clean]
    )
)

sample_prediction = (
    loaded_model.predict(
        sample_vector
    )[0]
)

sample_probability = (
    loaded_model.predict_proba(
        sample_vector
    ).max()
)


print(
    "\nSample text:",
    sample_text
)

print(
    "Predicted label:",
    sample_prediction
)

print(
    "Confidence:",
    f"{sample_probability:.2%}"
)


# ============================================================
# 21. FINAL SUMMARY
# ============================================================

print("\n" + "=" * 60)
print("TRAINING COMPLETED SUCCESSFULLY")
print("=" * 60)

print(
    f"""
Dataset:
    Training   : {len(train_df)}
    Validation : {len(validation_df)}
    Testing    : {len(test_df)}

Algorithm:
    TF-IDF + Logistic Regression

Test Accuracy:
    {test_accuracy:.4f}

Test Precision:
    {test_precision:.4f}

Test Recall:
    {test_recall:.4f}

Test F1 Score:
    {test_f1:.4f}

Saved Files:
    {model_path}
    {vectorizer_path}
    {label_mapping_path}
    {MODEL_DIR}/emotion_distribution.png
    {MODEL_DIR}/text_length_distribution.png
    {MODEL_DIR}/confusion_matrix.png
"""
)

print("=" * 60)