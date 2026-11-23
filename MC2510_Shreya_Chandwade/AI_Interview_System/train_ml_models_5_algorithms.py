import pandas as pd
import numpy as np
from pathlib import Path
import joblib

import matplotlib.pyplot as plt

from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer

from sklearn.linear_model import LogisticRegression
from sklearn.naive_bayes import MultinomialNB
from sklearn.ensemble import RandomForestClassifier
from sklearn.svm import LinearSVC
from sklearn.neighbors import KNeighborsClassifier

from sklearn.metrics import (
    accuracy_score,
    precision_recall_fscore_support,
    classification_report,
    confusion_matrix
)


# ============================================================
# PROJECT PATHS
# ============================================================

BASE = Path(__file__).resolve().parent

DATA_FILE = BASE / "final_api_enriched_interview_dataset.csv"

OUTPUT_DIR = BASE / "ml_results_5_algorithms"
OUTPUT_DIR.mkdir(exist_ok=True)


# ============================================================
# START
# ============================================================

print("=" * 70)
print("        STAGE 6 — MACHINE LEARNING IMPLEMENTATION")
print("=" * 70)

print("\nLoading dataset...")

df = pd.read_csv(DATA_FILE)

print(f"Dataset loaded successfully.")
print(f"Total records in dataset: {len(df)}")
print(f"Total columns: {len(df.columns)}")


# ============================================================
# DATA PREPARATION
# ============================================================

print("\n" + "=" * 70)
print("DATA PREPARATION")
print("=" * 70)

# Remove records without difficulty
df = df[df["difficulty"].notna()].copy()

# Standardize difficulty
df["difficulty"] = (
    df["difficulty"]
    .astype(str)
    .str.strip()
    .str.title()
)

# Keep only valid classes
valid_classes = ["Easy", "Medium", "Hard"]

df = df[df["difficulty"].isin(valid_classes)].copy()


# Fill missing text values
text_columns = [
    "question",
    "category",
    "skill",
    "programming_language"
]

for column in text_columns:
    df[column] = df[column].fillna("").astype(str)


# Combine useful information
df["model_text"] = (
    "Question: " + df["question"]
    + " Category: " + df["category"]
    + " Skill: " + df["skill"]
    + " Language: " + df["programming_language"]
)


X = df["model_text"]
y = df["difficulty"]


print(f"\nUsable records for ML: {len(df)}")

print("\nDifficulty distribution:")
print(y.value_counts())


# ============================================================
# TRAIN TEST SPLIT
# ============================================================

print("\n" + "=" * 70)
print("TRAIN / TEST SPLIT")
print("=" * 70)

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.20,
    random_state=42,
    stratify=y
)

print(f"Training records: {len(X_train)}")
print(f"Testing records : {len(X_test)}")


# ============================================================
# ML ALGORITHMS
# ============================================================

models = {

    "Logistic Regression":
        LogisticRegression(
            max_iter=2000,
            class_weight="balanced",
            random_state=42
        ),

    "Naive Bayes":
        MultinomialNB(),

    "Random Forest":
        RandomForestClassifier(
            n_estimators=250,
            class_weight="balanced_subsample",
            random_state=42,
            n_jobs=-1
        ),

    "SVM":
        LinearSVC(
            class_weight="balanced",
            random_state=42
        ),

    "KNN":
        KNeighborsClassifier(
            n_neighbors=7,
            weights="distance",
            n_jobs=-1
        )
}


# ============================================================
# MODEL TRAINING
# ============================================================

print("\n" + "=" * 70)
print("TRAINING 5 MACHINE LEARNING ALGORITHMS")
print("=" * 70)


results = []

prediction_results = []


for model_name, model in models.items():

    print("\n" + "-" * 70)
    print(f"Training: {model_name}")
    print("-" * 70)

    pipeline = Pipeline([

        (
            "TF-IDF",
            TfidfVectorizer(
                lowercase=True,
                stop_words="english",
                ngram_range=(1, 2),
                min_df=2,
                max_features=20000
            )
        ),

        (
            "Model",
            model
        )
    ])


    # Train
    pipeline.fit(X_train, y_train)


    # Predict
    predictions = pipeline.predict(X_test)


    # Metrics
    accuracy = accuracy_score(
        y_test,
        predictions
    )

    precision, recall, f1, _ = (
        precision_recall_fscore_support(
            y_test,
            predictions,
            average="weighted",
            zero_division=0
        )
    )


    print(f"Accuracy : {accuracy:.4f}")
    print(f"Precision: {precision:.4f}")
    print(f"Recall   : {recall:.4f}")
    print(f"F1 Score : {f1:.4f}")


    # Classification report
    report = classification_report(
        y_test,
        predictions,
        labels=valid_classes,
        zero_division=0
    )

    print("\nClassification Report:")
    print(report)


    # Safe filename
    safe_name = (
        model_name
        .lower()
        .replace(" ", "_")
    )


    # Save report
    report_file = (
        OUTPUT_DIR /
        f"{safe_name}_classification_report.txt"
    )

    report_file.write_text(
        report,
        encoding="utf-8"
    )


    # Confusion matrix
    cm = confusion_matrix(
        y_test,
        predictions,
        labels=valid_classes
    )


    cm_file = (
        OUTPUT_DIR /
        f"{safe_name}_confusion_matrix.csv"
    )

    pd.DataFrame(
        cm,
        index=[
            "Actual Easy",
            "Actual Medium",
            "Actual Hard"
        ],
        columns=[
            "Pred Easy",
            "Pred Medium",
            "Pred Hard"
        ]
    ).to_csv(cm_file)


    # ========================================================
    # CONFUSION MATRIX GRAPH
    # ========================================================

    plt.figure(figsize=(7, 6))

    plt.imshow(cm)

    plt.title(
        f"Confusion Matrix - {model_name}"
    )

    plt.xlabel("Predicted Difficulty")
    plt.ylabel("Actual Difficulty")

    plt.xticks(
        range(3),
        valid_classes
    )

    plt.yticks(
        range(3),
        valid_classes
    )


    # Add values inside matrix
    for i in range(3):

        for j in range(3):

            plt.text(
                j,
                i,
                cm[i, j],
                ha="center",
                va="center"
            )


    plt.colorbar()

    plt.tight_layout()

    confusion_graph = (
        OUTPUT_DIR /
        f"{safe_name}_confusion_matrix.png"
    )

    plt.savefig(
        confusion_graph,
        dpi=300
    )

    plt.close()


    # Save trained model
    model_file = (
        OUTPUT_DIR /
        f"{safe_name}_model.pkl"
    )

    joblib.dump(
        pipeline,
        model_file
    )


    # Store metrics
    results.append({

        "Algorithm": model_name,

        "Accuracy": accuracy,

        "Precision": precision,

        "Recall": recall,

        "F1_Score": f1

    })


    # Store predictions
    prediction_results.append(

        pd.DataFrame({

            "Actual_Difficulty":
                y_test.values,

            "Predicted_Difficulty":
                predictions,

            "Algorithm":
                model_name

        })

    )


# ============================================================
# MODEL COMPARISON
# ============================================================

results_df = pd.DataFrame(results)

results_df = results_df.sort_values(
    by="F1_Score",
    ascending=False
)


print("\n" + "=" * 70)
print("FINAL MODEL COMPARISON")
print("=" * 70)

print(
    results_df.to_string(
        index=False
    )
)


# Save comparison
results_df.to_csv(
    OUTPUT_DIR /
    "model_comparison.csv",
    index=False
)


# ============================================================
# GRAPH 1 — MODEL PERFORMANCE
# ============================================================

algorithms = results_df["Algorithm"]

x = np.arange(len(algorithms))

width = 0.2

plt.figure(figsize=(12, 7))

plt.bar(
    x - width * 1.5,
    results_df["Accuracy"],
    width,
    label="Accuracy"
)

plt.bar(
    x - width / 2,
    results_df["Precision"],
    width,
    label="Precision"
)

plt.bar(
    x + width / 2,
    results_df["Recall"],
    width,
    label="Recall"
)

plt.bar(
    x + width * 1.5,
    results_df["F1_Score"],
    width,
    label="F1 Score"
)

plt.xticks(
    x,
    algorithms,
    rotation=20
)

plt.ylim(
    0,
    1
)

plt.ylabel(
    "Score"
)

plt.xlabel(
    "Machine Learning Algorithm"
)

plt.title(
    "Performance Comparison of Machine Learning Algorithms"
)

plt.legend()

plt.tight_layout()

plt.savefig(
    OUTPUT_DIR /
    "algorithm_performance_comparison.png",
    dpi=300
)

plt.close()


# ============================================================
# GRAPH 2 — ACCURACY
# ============================================================

plt.figure(figsize=(10, 6))

plt.bar(
    results_df["Algorithm"],
    results_df["Accuracy"]
)

plt.ylabel("Accuracy")

plt.xlabel("Algorithm")

plt.title(
    "Accuracy Comparison of ML Algorithms"
)

plt.ylim(0, 1)

plt.xticks(rotation=20)

plt.tight_layout()

plt.savefig(
    OUTPUT_DIR /
    "accuracy_comparison.png",
    dpi=300
)

plt.close()


# ============================================================
# GRAPH 3 — F1 SCORE
# ============================================================

plt.figure(figsize=(10, 6))

plt.bar(
    results_df["Algorithm"],
    results_df["F1_Score"]
)

plt.ylabel("F1 Score")

plt.xlabel("Algorithm")

plt.title(
    "F1 Score Comparison of ML Algorithms"
)

plt.ylim(0, 1)

plt.xticks(rotation=20)

plt.tight_layout()

plt.savefig(
    OUTPUT_DIR /
    "f1_score_comparison.png",
    dpi=300
)

plt.close()


# ============================================================
# GRAPH 4 — DIFFICULTY DISTRIBUTION
# ============================================================

difficulty_counts = (
    df["difficulty"]
    .value_counts()
    .reindex(valid_classes)
)


plt.figure(figsize=(8, 6))

plt.bar(
    difficulty_counts.index,
    difficulty_counts.values
)

plt.xlabel(
    "Difficulty Level"
)

plt.ylabel(
    "Number of Questions"
)

plt.title(
    "Interview Question Difficulty Distribution"
)

plt.tight_layout()

plt.savefig(
    OUTPUT_DIR /
    "difficulty_distribution.png",
    dpi=300
)

plt.close()


# ============================================================
# GRAPH 5 — ACTUAL VS PREDICTED
# ============================================================

best_algorithm = results_df.iloc[0]["Algorithm"]

best_predictions = None

for prediction_df in prediction_results:

    if prediction_df["Algorithm"].iloc[0] == best_algorithm:

        best_predictions = prediction_df


actual_counts = (
    best_predictions["Actual_Difficulty"]
    .value_counts()
    .reindex(valid_classes)
    .fillna(0)
)

predicted_counts = (
    best_predictions["Predicted_Difficulty"]
    .value_counts()
    .reindex(valid_classes)
    .fillna(0)
)


x = np.arange(3)

plt.figure(figsize=(9, 6))

plt.bar(
    x - 0.2,
    actual_counts.values,
    0.4,
    label="Actual"
)

plt.bar(
    x + 0.2,
    predicted_counts.values,
    0.4,
    label="Predicted"
)

plt.xticks(
    x,
    valid_classes
)

plt.xlabel(
    "Difficulty Level"
)

plt.ylabel(
    "Number of Questions"
)

plt.title(
    f"Actual vs Predicted Difficulty - {best_algorithm}"
)

plt.legend()

plt.tight_layout()

plt.savefig(
    OUTPUT_DIR /
    "actual_vs_predicted.png",
    dpi=300
)

plt.close()


# ============================================================
# SAVE ALL PREDICTIONS
# ============================================================

all_predictions = pd.concat(
    prediction_results,
    ignore_index=True
)

all_predictions.to_csv(
    OUTPUT_DIR /
    "all_model_predictions.csv",
    index=False
)


# ============================================================
# BEST MODEL
# ============================================================

best_row = results_df.iloc[0]

print("\n" + "=" * 70)
print("BEST MACHINE LEARNING MODEL")
print("=" * 70)

print(
    f"Algorithm : {best_row['Algorithm']}"
)

print(
    f"Accuracy  : {best_row['Accuracy']:.4f}"
)

print(
    f"Precision : {best_row['Precision']:.4f}"
)

print(
    f"Recall    : {best_row['Recall']:.4f}"
)

print(
    f"F1 Score  : {best_row['F1_Score']:.4f}"
)


# ============================================================
# FINAL OUTPUT
# ============================================================

print("\n" + "=" * 70)
print("STAGE 6 COMPLETED SUCCESSFULLY")
print("=" * 70)

print("\nML Task:")
print(
    "Interview Question → Easy / Medium / Hard"
)

print("\nAlgorithms implemented:")

for algorithm in models.keys():

    print(
        f"  ✓ {algorithm}"
    )


print("\nGraphs generated:")

graphs = [

    "algorithm_performance_comparison.png",

    "accuracy_comparison.png",

    "f1_score_comparison.png",

    "difficulty_distribution.png",

    "actual_vs_predicted.png",

    "logistic_regression_confusion_matrix.png",

    "naive_bayes_confusion_matrix.png",

    "random_forest_confusion_matrix.png",

    "svm_confusion_matrix.png",

    "knn_confusion_matrix.png"

]

for graph in graphs:

    print(
        f"  ✓ {graph}"
    )


print("\nAll ML results saved in:")

print(
    OUTPUT_DIR
)

print("\n" + "=" * 70)
print("READY FOR FINAL REPORT")
print("=" * 70)