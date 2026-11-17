from pathlib import Path
import json
import joblib
import pandas as pd

from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.tree import DecisionTreeClassifier
from sklearn.naive_bayes import GaussianNB
from sklearn.svm import SVC

from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    classification_report,
    confusion_matrix
)


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

DATASET_PATH = BASE_DIR / "dataset" / "personal_finance.csv"

MODEL_DIR = BASE_DIR / "models" / "classification"
RESULT_DIR = BASE_DIR / "models" / "results"

MODEL_DIR.mkdir(parents=True, exist_ok=True)
RESULT_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# LOAD DATASET
# ============================================================

print("\n" + "=" * 70)
print("AI SMART EXPENSE TRACKER")
print("CLASSIFICATION MODEL TRAINING")
print("=" * 70)

print(f"\nDataset path:")
print(DATASET_PATH)

if not DATASET_PATH.exists():
    raise FileNotFoundError(
        f"\nDataset not found:\n{DATASET_PATH}\n"
        "Please check that personal_finance.csv is inside ml/dataset/"
    )

df = pd.read_csv(DATASET_PATH)

print(f"\nDataset loaded successfully.")
print(f"Rows: {len(df)}")
print(f"Columns: {len(df.columns)}")

print("\nColumns:")
print(df.columns.tolist())


# ============================================================
# CHECK REQUIRED COLUMNS
# ============================================================

required_columns = [
    "Date",
    "Amount",
    "Type",
    "Category"
]

missing_columns = [
    col for col in required_columns
    if col not in df.columns
]

if missing_columns:
    raise ValueError(
        f"\nMissing required columns: {missing_columns}"
    )


# ============================================================
# DATE FEATURES
# ============================================================

df["Date"] = pd.to_datetime(
    df["Date"],
    errors="coerce"
)

df["Year"] = df["Date"].dt.year
df["Month"] = df["Date"].dt.month
df["Day"] = df["Date"].dt.day
df["DayOfWeek"] = df["Date"].dt.dayofweek
df["IsWeekend"] = (
    df["DayOfWeek"] >= 5
).astype(int)


# ============================================================
# TYPE ENCODING
# ============================================================

df["TypeEncoded"] = (
    df["Type"]
    .astype(str)
    .str.lower()
    .map({
        "expense": 0,
        "income": 1
    })
)


# ============================================================
# NUMERIC CONVERSION
# ============================================================

numeric_columns = [
    "Amount",
    "Year",
    "Month",
    "Day",
    "DayOfWeek",
    "IsWeekend",
    "TypeEncoded"
]

for column in numeric_columns:
    df[column] = pd.to_numeric(
        df[column],
        errors="coerce"
    )


# ============================================================
# REMOVE INVALID ROWS
# ============================================================

df = df.dropna(
    subset=[
        "Amount",
        "Year",
        "Month",
        "Day",
        "DayOfWeek",
        "IsWeekend",
        "TypeEncoded",
        "Category"
    ]
)

print(f"\nRows after preprocessing: {len(df)}")


# ============================================================
# FEATURES AND TARGET
# ============================================================

FEATURES = [
    "Amount",
    "Year",
    "Month",
    "Day",
    "DayOfWeek",
    "IsWeekend",
    "TypeEncoded"
]

TARGET = "Category"

X = df[FEATURES]
y = df[TARGET].astype(str)


# ============================================================
# CHECK TARGET
# ============================================================

print("\nCategory distribution:")

print(
    y.value_counts()
)


# ============================================================
# TRAIN TEST SPLIT
# ============================================================

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.20,
    random_state=42,
    stratify=y
)

print("\nTraining samples:", len(X_train))
print("Testing samples:", len(X_test))


# ============================================================
# MODELS
# ============================================================

models = {

    "Logistic Regression": Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler()),
        (
            "model",
            LogisticRegression(
                max_iter=2000,
                class_weight="balanced"
            )
        )
    ]),

    "Random Forest": Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        (
            "model",
            RandomForestClassifier(
                n_estimators=200,
                random_state=42,
                class_weight="balanced"
            )
        )
    ]),

    "Decision Tree": Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        (
            "model",
            DecisionTreeClassifier(
                random_state=42,
                class_weight="balanced"
            )
        )
    ]),

    "Naive Bayes": Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        (
            "model",
            GaussianNB()
        )
    ]),

    "SVM": Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler()),
        (
            "model",
            SVC(
                kernel="rbf",
                class_weight="balanced"
            )
        )
    ])
}


# ============================================================
# TRAIN MODELS
# ============================================================

results = {}

confusion_matrices = {}

classification_reports = {}


for model_name, model in models.items():

    print("\n" + "-" * 70)
    print(f"Training: {model_name}")
    print("-" * 70)

    model.fit(
        X_train,
        y_train
    )

    y_pred = model.predict(X_test)

    # Metrics
    accuracy = accuracy_score(
        y_test,
        y_pred
    )

    precision = precision_score(
        y_test,
        y_pred,
        average="weighted",
        zero_division=0
    )

    recall = recall_score(
        y_test,
        y_pred,
        average="weighted",
        zero_division=0
    )

    f1 = f1_score(
        y_test,
        y_pred,
        average="weighted",
        zero_division=0
    )

    print(f"Accuracy : {accuracy:.4f}")
    print(f"Precision: {precision:.4f}")
    print(f"Recall   : {recall:.4f}")
    print(f"F1 Score : {f1:.4f}")

    # Save metrics
    results[model_name] = {
        "accuracy": round(accuracy, 4),
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1_score": round(f1, 4)
    }

    # Classification report
    report = classification_report(
        y_test,
        y_pred,
        output_dict=True,
        zero_division=0
    )

    classification_reports[model_name] = report

    # Confusion matrix
    labels = sorted(y.unique())

    cm = confusion_matrix(
        y_test,
        y_pred,
        labels=labels
    )

    confusion_matrices[model_name] = {
        "labels": labels,
        "matrix": cm.tolist()
    }

    # Save model
    filename = (
        model_name
        .lower()
        .replace(" ", "_")
        + ".pkl"
    )

    model_path = MODEL_DIR / filename

    joblib.dump(
        model,
        model_path
    )

    print(f"Model saved: {model_path}")


# ============================================================
# SAVE COMPARISON RESULTS
# ============================================================

comparison_df = pd.DataFrame.from_dict(
    results,
    orient="index"
)

comparison_df.index.name = "Model"

comparison_path = (
    RESULT_DIR /
    "classification_model_comparison.csv"
)

comparison_df.to_csv(
    comparison_path
)


# ============================================================
# SAVE CONFUSION MATRICES
# ============================================================

confusion_path = (
    RESULT_DIR /
    "confusion_matrices.json"
)

with open(
    confusion_path,
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        confusion_matrices,
        f,
        indent=4
    )


# ============================================================
# SAVE CLASSIFICATION REPORTS
# ============================================================

reports_path = (
    RESULT_DIR /
    "classification_reports.json"
)

with open(
    reports_path,
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        classification_reports,
        f,
        indent=4
    )


# ============================================================
# FINAL OUTPUT
# ============================================================

print("\n" + "=" * 70)
print("TRAINING COMPLETED SUCCESSFULLY")
print("=" * 70)

print("\nModel comparison:")

print(
    comparison_df
)

print("\nModels saved in:")
print(MODEL_DIR)

print("\nResults saved in:")
print(RESULT_DIR)

print("\nGenerated files:")
print("1. classification_model_comparison.csv")
print("2. confusion_matrices.json")
print("3. classification_reports.json")

print("\nClassification models:")
print("1. Logistic Regression")
print("2. Random Forest")
print("3. Decision Tree")
print("4. Naive Bayes")
print("5. SVM")

print("\nDone.")