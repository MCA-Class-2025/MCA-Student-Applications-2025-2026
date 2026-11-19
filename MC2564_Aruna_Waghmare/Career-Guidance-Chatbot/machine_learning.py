
# ================================================================
# CAREER GUIDANCE PROJECT
# MACHINE LEARNING IMPLEMENTATION
#
# Classification:
# 1. Naive Bayes
# 2. Support Vector Machine (SVM)
# 3. Decision Tree
# 4. Random Forest
# 5. Logistic Regression
#
# Regression:
# 6. Linear Regression
#
# Evaluation and Model Comparison
# ================================================================

import os
import re
import warnings
import joblib
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer

from sklearn.naive_bayes import MultinomialNB
from sklearn.svm import LinearSVC
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression, LinearRegression

from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    classification_report,
    confusion_matrix,
    mean_absolute_error,
    mean_squared_error,
    r2_score
)

warnings.filterwarnings("ignore")


# ================================================================
# 1. CONFIGURATION
# ================================================================

INPUT_FILE = "processed_data/career_fused_dataset.csv"

OUTPUT_DIR = "machine_learning_results"

CLASSIFICATION_DIR = os.path.join(
    OUTPUT_DIR, "classification"
)

REGRESSION_DIR = os.path.join(
    OUTPUT_DIR, "regression"
)

MODEL_DIR = os.path.join(
    OUTPUT_DIR, "saved_models"
)

RANDOM_STATE = 42
TEST_SIZE = 0.20

os.makedirs(CLASSIFICATION_DIR, exist_ok=True)
os.makedirs(REGRESSION_DIR, exist_ok=True)
os.makedirs(MODEL_DIR, exist_ok=True)


# ================================================================
# 2. LOAD FUSED DATASET
# ================================================================

print("\n" + "=" * 65)
print("LOADING FUSED DATASET")
print("=" * 65)

if not os.path.exists(INPUT_FILE):
    raise FileNotFoundError(
        f"Dataset not found: {INPUT_FILE}\n"
        "Run this script from your main project directory."
    )

df = pd.read_csv(
    INPUT_FILE,
    encoding="utf-8-sig"
)

# Remove unnamed columns

df = df.loc[
    :,
    ~df.columns.astype(str).str.contains(
        r"^Unnamed",
        case=False,
        regex=True
    )
]

# Remove extra spaces from column names

df.columns = [
    str(col).strip() for col in df.columns
]

print("\nDataset loaded successfully!")

print("Number of records:", df.shape[0])
print("Number of columns:", df.shape[1])

print("\nDataset columns:")

print(df.columns.tolist())


# ================================================================
# 3. FEATURE SELECTION
# ================================================================

print("\n" + "=" * 65)
print("FEATURE SELECTION")
print("=" * 65)

# Use original career information as input features.
# Job Title is excluded to reduce direct target leakage
# when career_role is mapped from the job title.

feature_columns = [
    "Job Description",
    "Skills",
    "Certifications"
]

missing_features = [
    col for col in feature_columns
    if col not in df.columns
]

if missing_features:
    raise ValueError(
        f"Missing feature columns: {missing_features}"
    )

# Combine selected text features

for col in feature_columns:
    df[col] = df[col].fillna("").astype(str)

df["combined_features"] = df[
    feature_columns
].agg(" ".join, axis=1)

df["combined_features"] = (
    df["combined_features"]
    .str.replace(r"\s+", " ", regex=True)
    .str.strip()
)

# Remove empty feature records

df = df[
    df["combined_features"].str.len() > 0
].copy()

print("\nSelected features:")

for col in feature_columns:
    print("-", col)


# ================================================================
# 4. CREATE RESOURCE COUNT FEATURES
# ================================================================

print("\n" + "=" * 65)
print("CALCULATING RESOURCE COUNTS")
print("=" * 65)

resource_columns = [
    "resume_samples",
    "remotive_jobs",
    "youtube_resources",
    "github_projects",
    "technical_books",
    "research_papers"
]

available_resource_columns = [
    col for col in resource_columns
    if col in df.columns
]

if not available_resource_columns:
    raise ValueError(
        "No career resource columns found."
    )


def count_resources(value):

    if pd.isna(value):
        return 0

    text = str(value).strip()

    if text.lower() in [
        "", "nan", "none", "null", "[]",
        "0", "no data", "not available"
    ]:
        return 0

    items = re.split(r"\s*[|;\n]\s*", text)

    return sum(
        1 for item in items
        if item.strip() and item.strip() != "[]"
    )


for col in available_resource_columns:

    df[col + "_count"] = df[col].apply(
        count_resources
    )

count_columns = [
    col + "_count"
    for col in available_resource_columns
]

# Calculate total resources

df["total_resources"] = df[
    count_columns
].sum(axis=1)

print("\nResource count summary:")

print(
    df["total_resources"].describe()
)


# ================================================================
# 5. CLASSIFICATION TARGET
# ================================================================

print("\n" + "=" * 65)
print("CLASSIFICATION TARGET PREPARATION")
print("=" * 65)

TARGET_COLUMN = "career_role"

if TARGET_COLUMN not in df.columns:
    raise ValueError(
        "career_role column not found in the dataset."
    )

classification_df = df.copy()

classification_df[TARGET_COLUMN] = (
    classification_df[TARGET_COLUMN]
    .fillna("")
    .astype(str)
    .str.strip()
)

classification_df = classification_df[
    classification_df[TARGET_COLUMN] != ""
].copy()

# Remove classes having fewer than two records.
# At least two samples per class are required for
# a stratified train-test split.

class_counts = classification_df[
    TARGET_COLUMN
].value_counts()

valid_classes = class_counts[
    class_counts >= 2
].index

removed_classes = len(class_counts) - len(valid_classes)

classification_df = classification_df[
    classification_df[TARGET_COLUMN].isin(valid_classes)
].copy()

if removed_classes > 0:
    print(
        "\nRare classes removed:",
        removed_classes
    )

X = classification_df["combined_features"]

y = classification_df[TARGET_COLUMN]

if y.nunique() < 2:
    raise ValueError(
        "Classification requires at least two career_role "
        "classes with two or more records each. "
        "Check the career_role distribution."
    )

number_of_classes = y.nunique()

number_of_records = len(y)

# Ensure enough records for both training and testing.

test_records = max(
    int(np.ceil(number_of_records * TEST_SIZE)),
    number_of_classes
)

if number_of_records - test_records < number_of_classes:
    raise ValueError(
        "Insufficient records for stratified classification. "
        "You need more labelled examples per career role."
    )

actual_test_size = test_records / number_of_records

print("\nClassification target:", TARGET_COLUMN)

print("Number of classes:", number_of_classes)

print("\nClass distribution:")

print(y.value_counts())


# ================================================================
# 6. TRAIN-TEST SPLIT
# ================================================================

print("\n" + "=" * 65)
print("SPLITTING CLASSIFICATION DATA")
print("=" * 65)

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=actual_test_size,
    random_state=RANDOM_STATE,
    stratify=y
)

print("Training records:", len(X_train))

print("Testing records:", len(X_test))


# ================================================================
# 7. DEFINE CLASSIFICATION ALGORITHMS
# ================================================================

models = {

    "Naive Bayes": MultinomialNB(),

    "SVM": LinearSVC(
        random_state=RANDOM_STATE,
        max_iter=5000
    ),

    "Decision Tree": DecisionTreeClassifier(
        max_depth=20,
        random_state=RANDOM_STATE,
        class_weight="balanced"
    ),

    "Random Forest": RandomForestClassifier(
        n_estimators=200,
        max_depth=20,
        random_state=RANDOM_STATE,
        class_weight="balanced",
        n_jobs=-1
    ),

    "Logistic Regression": LogisticRegression(
        max_iter=3000,
        class_weight="balanced",
        random_state=RANDOM_STATE
    )
}


# ================================================================
# 8. TRAIN AND EVALUATE CLASSIFICATION MODELS
# ================================================================

print("\n" + "=" * 65)
print("CLASSIFICATION MODEL TRAINING")
print("=" * 65)

classification_results = []

for model_name, algorithm in models.items():

    print("\n" + "-" * 65)

    print("Training:", model_name)

    # TF-IDF converts text into numerical features.

    pipeline = Pipeline([

        (
            "tfidf",
            TfidfVectorizer(
                max_features=5000,
                ngram_range=(1, 2),
                stop_words="english",
                sublinear_tf=True
            )
        ),

        (
            "classifier",
            algorithm
        )
    ])

    # Train

    pipeline.fit(X_train, y_train)

    # Predict

    predictions = pipeline.predict(X_test)

    # Evaluation metrics

    accuracy = accuracy_score(
        y_test, predictions
    )

    precision = precision_score(
        y_test,
        predictions,
        average="weighted",
        zero_division=0
    )

    recall = recall_score(
        y_test,
        predictions,
        average="weighted",
        zero_division=0
    )

    f1 = f1_score(
        y_test,
        predictions,
        average="weighted",
        zero_division=0
    )

    print("\nAccuracy:", round(accuracy * 100, 2), "%")

    print("Precision:", round(precision, 4))

    print("Recall:", round(recall, 4))

    print("F1 Score:", round(f1, 4))

    print("\nClassification Report:")

    print(
        classification_report(
            y_test,
            predictions,
            zero_division=0
        )
    )

    # Save model

    filename = (
        model_name.lower().replace(" ", "_")
        + ".pkl"
    )

    joblib.dump(
        pipeline,
        os.path.join(MODEL_DIR, filename)
    )

    # Save confusion matrix

    cm = confusion_matrix(
        y_test,
        predictions,
        labels=pipeline.classes_
    )

    plt.figure(figsize=(10, 8))

    sns.heatmap(
        cm,
        annot=True,
        fmt="d",
        cmap="Blues",
        xticklabels=pipeline.classes_,
        yticklabels=pipeline.classes_
    )

    plt.title(model_name + " - Confusion Matrix")

    plt.xlabel("Predicted Label")

    plt.ylabel("Actual Label")

    plt.xticks(rotation=45, ha="right")

    plt.yticks(rotation=0)

    plt.tight_layout()

    plt.savefig(
        os.path.join(
            CLASSIFICATION_DIR,
            filename.replace(
                ".pkl",
                "_confusion_matrix.png"
            )
        ),
        dpi=300
    )

    plt.close()

    # Store results

    classification_results.append({

        "Algorithm": model_name,

        "Accuracy": round(accuracy * 100, 2),

        "Precision": round(precision, 4),

        "Recall": round(recall, 4),

        "F1 Score": round(f1, 4)

    })


# ================================================================
# 9. CLASSIFICATION RESULTS
# ================================================================

classification_results_df = pd.DataFrame(
    classification_results
)

classification_results_df = (
    classification_results_df.sort_values(
        by="F1 Score",
        ascending=False
    )
)

classification_results_df.to_csv(
    os.path.join(
        CLASSIFICATION_DIR,
        "classification_results.csv"
    ),
    index=False
)

print("\n" + "=" * 65)

print("FINAL CLASSIFICATION RESULTS")

print("=" * 65)

print(
    classification_results_df.to_string(
        index=False
    )
)


# ================================================================
# 10. CLASSIFICATION COMPARISON GRAPH
# ================================================================

plot_data = classification_results_df.melt(
    id_vars="Algorithm",
    value_vars=[
        "Accuracy",
        "Precision",
        "Recall",
        "F1 Score"
    ],
    var_name="Metric",
    value_name="Score"
)

plt.figure(figsize=(12, 7))

sns.barplot(
    data=plot_data,
    x="Algorithm",
    y="Score",
    hue="Metric"
)

plt.title(
    "Classification Algorithm Performance Comparison"
)

plt.xlabel("Machine Learning Algorithms")

plt.ylabel("Performance Score")

plt.xticks(rotation=20)

plt.tight_layout()

plt.savefig(
    os.path.join(
        CLASSIFICATION_DIR,
        "classification_comparison.png"
    ),
    dpi=300
)

plt.close()


# ================================================================
# 11. REGRESSION ANALYSIS
# ================================================================

print("\n" + "=" * 65)

print("LINEAR REGRESSION ANALYSIS")

print("=" * 65)

# Input features

X_reg = df["combined_features"]

# Numerical target

y_reg = df["total_resources"]

# Remove invalid target records

valid_rows = y_reg.notna()

X_reg = X_reg[valid_rows]

y_reg = y_reg[valid_rows]

if len(y_reg) < 5:
    raise ValueError(
        "Insufficient records for regression analysis."
    )

if y_reg.nunique() < 2:
    raise ValueError(
        "Regression requires variation in the numerical target."
    )


# ================================================================
# 12. REGRESSION TRAIN-TEST SPLIT
# ================================================================

X_train_reg, X_test_reg, y_train_reg, y_test_reg = (
    train_test_split(
        X_reg,
        y_reg,
        test_size=TEST_SIZE,
        random_state=RANDOM_STATE
    )
)

print("\nRegression training records:", len(X_train_reg))

print("Regression testing records:", len(X_test_reg))


# ================================================================
# 13. LINEAR REGRESSION MODEL
# ================================================================

regression_model = Pipeline([

    (
        "tfidf",
        TfidfVectorizer(
            max_features=5000,
            ngram_range=(1, 2),
            stop_words="english",
            sublinear_tf=True
        )
    ),

    (
        "regressor",
        LinearRegression()
    )

])


# ================================================================
# 14. TRAIN REGRESSION MODEL
# ================================================================

print("\nTraining Linear Regression...")

regression_model.fit(
    X_train_reg,
    y_train_reg
)


# ================================================================
# 15. REGRESSION PREDICTIONS
# ================================================================

regression_predictions = regression_model.predict(
    X_test_reg
)


# ================================================================
# 16. REGRESSION EVALUATION
# ================================================================

mae = mean_absolute_error(
    y_test_reg,
    regression_predictions
)

mse = mean_squared_error(
    y_test_reg,
    regression_predictions
)

rmse = np.sqrt(mse)

r2 = r2_score(
    y_test_reg,
    regression_predictions
)

print("\n" + "=" * 65)

print("REGRESSION PERFORMANCE")

print("=" * 65)

print("MAE:", round(mae, 4))

print("MSE:", round(mse, 4))

print("RMSE:", round(rmse, 4))

print("R2 Score:", round(r2, 4))


# ================================================================
# 17. SAVE REGRESSION RESULTS
# ================================================================

regression_results = pd.DataFrame({

    "Metric": [
        "MAE",
        "MSE",
        "RMSE",
        "R2 Score"
    ],

    "Value": [
        mae,
        mse,
        rmse,
        r2
    ]

})

regression_results.to_csv(
    os.path.join(
        REGRESSION_DIR,
        "regression_metrics.csv"
    ),
    index=False
)

# Save actual and predicted values

prediction_results = pd.DataFrame({

    "Actual Resources": y_test_reg.values,

    "Predicted Resources": regression_predictions

})

prediction_results.to_csv(
    os.path.join(
        REGRESSION_DIR,
        "regression_predictions.csv"
    ),
    index=False
)


# ================================================================
# 18. ACTUAL VS PREDICTED GRAPH
# ================================================================

plt.figure(figsize=(9, 6))

plt.scatter(
    y_test_reg,
    regression_predictions,
    alpha=0.7
)

minimum = min(
    y_test_reg.min(),
    regression_predictions.min()
)

maximum = max(
    y_test_reg.max(),
    regression_predictions.max()
)

plt.plot(
    [minimum, maximum],
    [minimum, maximum],
    linestyle="--"
)

plt.title(
    "Linear Regression - Actual vs Predicted"
)

plt.xlabel("Actual Resource Count")

plt.ylabel("Predicted Resource Count")

plt.tight_layout()

plt.savefig(
    os.path.join(
        REGRESSION_DIR,
        "actual_vs_predicted.png"
    ),
    dpi=300
)

plt.close()


# ================================================================
# 19. REGRESSION ERROR DISTRIBUTION
# ================================================================

errors = y_test_reg.values - regression_predictions

plt.figure(figsize=(9, 6))

sns.histplot(
    errors,
    kde=True
)

plt.title("Regression Prediction Error Distribution")

plt.xlabel("Prediction Error")

plt.ylabel("Frequency")

plt.tight_layout()

plt.savefig(
    os.path.join(
        REGRESSION_DIR,
        "regression_error_distribution.png"
    ),
    dpi=300
)

plt.close()


# ================================================================
# 20. SAVE REGRESSION MODEL
# ================================================================

joblib.dump(
    regression_model,
    os.path.join(
        MODEL_DIR,
        "linear_regression.pkl"
    )
)


# ================================================================
# 21. FINAL PROJECT SUMMARY
# ================================================================

print("\n" + "=" * 65)

print("MACHINE LEARNING IMPLEMENTATION COMPLETED")

print("=" * 65)

print("\nClassification Algorithms:")

for name in models:
    print("-", name)

print("\nRegression Algorithm:")

print("- Linear Regression")

print("\nClassification Results:")

print(
    os.path.join(
        CLASSIFICATION_DIR,
        "classification_results.csv"
    )
)

print("\nRegression Results:")

print(
    os.path.join(
        REGRESSION_DIR,
        "regression_metrics.csv"
    )
)

print("\nSaved Models:")

print(MODEL_DIR)

print("\nAll results and graphs saved successfully!")

print("\n" + "=" * 65)
