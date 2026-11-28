import pandas as pd

from sklearn.model_selection import train_test_split
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.naive_bayes import GaussianNB
from sklearn.metrics import accuracy_score, classification_report


# ==========================================
# 1. LOAD DATASET
# ==========================================

df = pd.read_csv("AI_Event_Planner_Dataset.csv")

print("Dataset loaded successfully!")
print("Dataset shape:", df.shape)


# ==========================================
# 2. CREATE CLASSIFICATION TARGET
# ==========================================

# Convert success_score into 3 classes
# Low      : below 65
# Medium   : 65 to below 80
# High     : 80 and above

def classify_success(score):

    if score < 65:
        return "Low"

    elif score < 80:
        return "Medium"

    else:
        return "High"


df["success_class"] = df["success_score"].apply(
    classify_success
)



# ==========================================
# 3. SELECT FEATURES
# ==========================================

X = df.drop(
    columns=[
        "success_score",
        "success_class",
        "event_id",
        "event_date"
    ]
)

y = df["success_class"]


# ==========================================
# 4. IDENTIFY COLUMNS
# ==========================================

categorical_columns = X.select_dtypes(
    include=["object", "bool"]
).columns.tolist()

numeric_columns = X.select_dtypes(
    include=["int64", "float64"]
).columns.tolist()


print("\nCategorical columns:")
print(categorical_columns)

print("\nNumeric columns:")
print(numeric_columns)


# ==========================================
# 5. PREPROCESSING
# ==========================================

preprocessor = ColumnTransformer(
    transformers=[
        (
            "categorical",
           OneHotEncoder(
             handle_unknown="ignore",
             sparse_output=False
     ),
            categorical_columns
        ),
        (
            "numeric",
            StandardScaler(),
            numeric_columns
        )
    ]
)
# ==========================================
# 7. SPLIT DATA
# ==========================================

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.20,
    random_state=42
)

print("\nTraining samples:", len(X_train))
print("Testing samples:", len(X_test))

# ==========================================
# 6. NAIVE BAYES MODEL
# ==========================================

model = GaussianNB()
# ==========================================
# SVM
# ==========================================

from sklearn.svm import SVC

print("\nTraining SVM model...")

svm_model = SVC(
    kernel="rbf",
    random_state=42
)

svm_pipeline = Pipeline(
    steps=[
        ("preprocessor", preprocessor),
        ("model", svm_model)
    ]
)

svm_pipeline.fit(X_train, y_train)

print("SVM training completed!")

svm_pred = svm_pipeline.predict(X_test)

svm_accuracy = accuracy_score(y_test, svm_pred)

print("\n===== SVM PERFORMANCE =====")
print("Accuracy:", round(svm_accuracy * 100, 2), "%")

print("\nClassification Report:")
print(classification_report(y_test, svm_pred))
# ==========================================
# DECISION TREE
# ==========================================

from sklearn.tree import DecisionTreeClassifier

print("\nTraining Decision Tree model...")

dt_model = DecisionTreeClassifier(
    random_state=42,
    max_depth=10
)

dt_pipeline = Pipeline(
    steps=[
        ("preprocessor", preprocessor),
        ("model", dt_model)
    ]
)

dt_pipeline.fit(X_train, y_train)

print("Decision Tree training completed!")

dt_pred = dt_pipeline.predict(X_test)

dt_accuracy = accuracy_score(
    y_test,
    dt_pred
)

print("\n===== DECISION TREE PERFORMANCE =====")
print(
    "Accuracy:",
    round(dt_accuracy * 100, 2),
    "%"
)

print("\nClassification Report:")
print(
    classification_report(
        y_test,
        dt_pred,
        zero_division=0
    )
)
# ==========================================
# RANDOM FOREST
# ==========================================

from sklearn.ensemble import RandomForestClassifier

print("\nTraining Random Forest model...")

rf_model = RandomForestClassifier(
    n_estimators=200,
    random_state=42,
    max_depth=10
)

rf_pipeline = Pipeline(
    steps=[
        ("preprocessor", preprocessor),
        ("model", rf_model)
    ]
)

rf_pipeline.fit(X_train, y_train)

print("Random Forest training completed!")

rf_pred = rf_pipeline.predict(X_test)

rf_accuracy = accuracy_score(
    y_test,
    rf_pred
)

print("\n===== RANDOM FOREST PERFORMANCE =====")

print(
    "Accuracy:",
    round(rf_accuracy * 100, 2),
    "%"
)

print("\nClassification Report:")

print(
    classification_report(
        y_test,
        rf_pred,
        zero_division=0
    )
)
# ==========================================
# LOGISTIC REGRESSION
# ==========================================

from sklearn.linear_model import LogisticRegression

print("\nTraining Logistic Regression model...")

lr_model = LogisticRegression(
    max_iter=5000,
    solver="liblinear"
)

lr_pipeline = Pipeline(
    steps=[
        ("preprocessor", preprocessor),
        ("model", lr_model)
    ]
)

lr_pipeline.fit(X_train, y_train)

print("Logistic Regression training completed!")

lr_pred = lr_pipeline.predict(X_test)

lr_accuracy = accuracy_score(
    y_test,
    lr_pred
)

print("\n===== LOGISTIC REGRESSION PERFORMANCE =====")

print(
    "Accuracy:",
    round(lr_accuracy * 100, 2),
    "%"
)

print("\nClassification Report:")

print(
    classification_report(
        y_test,
        lr_pred,
        zero_division=0
    )
)
# ==========================================
# 7. CREATE PIPELINE
# ==========================================

pipeline = Pipeline(
    steps=[
        ("preprocessor", preprocessor),
        ("model", model)
    ]
)


# ==========================================
# 8. SPLIT DATA
# ==========================================

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.20,
    random_state=42,
    stratify=y
)


print("\nTraining samples:", len(X_train))
print("Testing samples:", len(X_test))


# ==========================================
# 9. TRAIN MODEL
# ==========================================

print("\nTraining Naive Bayes model...")

pipeline.fit(X_train, y_train)

print("Naive Bayes training completed!")


# ==========================================
# 10. PREDICTION
# ==========================================

y_pred = pipeline.predict(X_test)


# ==========================================
# 11. EVALUATION
# ==========================================

accuracy = accuracy_score(
    y_test,
    y_pred
)

print("\n===== NAIVE BAYES PERFORMANCE =====")

print(
    "Accuracy:",
    round(accuracy * 100, 2),
    "%"
)

print("\nClassification Report:")

print(
    classification_report(
        y_test,
        y_pred
    )
)
# ==========================================
# REGRESSION ANALYSIS
# ==========================================

from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import numpy as np

print("\nTraining Regression Analysis model...")

# Target
y_reg = df["success_score"]

# Features
X_reg = df.drop(
    columns=[
        "success_score",
        "event_id",
        "event_date"
    ]
)

# Identify columns
reg_categorical_columns = X_reg.select_dtypes(
    include=["object", "bool"]
).columns.tolist()

reg_numeric_columns = X_reg.select_dtypes(
    include=["int64", "float64"]
).columns.tolist()

# Regression preprocessing
reg_preprocessor = ColumnTransformer(
    transformers=[
        (
            "categorical",
            OneHotEncoder(handle_unknown="ignore"),
            reg_categorical_columns
        ),
        (
            "numeric",
            "passthrough",
            reg_numeric_columns
        )
    ]
)

# Split data
X_reg_train, X_reg_test, y_reg_train, y_reg_test = train_test_split(
    X_reg,
    y_reg,
    test_size=0.20,
    random_state=42
)

# Create model
reg_model = LinearRegression()

# Create pipeline
reg_pipeline = Pipeline(
    steps=[
        ("preprocessor", reg_preprocessor),
        ("model", reg_model)
    ]
)

# Train
reg_pipeline.fit(
    X_reg_train,
    y_reg_train
)

print("Regression Analysis training completed!")

# Prediction
reg_pred = reg_pipeline.predict(X_reg_test)

# Evaluation
reg_mae = mean_absolute_error(
    y_reg_test,
    reg_pred
)

reg_rmse = np.sqrt(
    mean_squared_error(
        y_reg_test,
        reg_pred
    )
)

reg_r2 = r2_score(
    y_reg_test,
    reg_pred
)

print("\n===== REGRESSION ANALYSIS PERFORMANCE =====")

print("MAE:", round(reg_mae, 2))

print("RMSE:", round(reg_rmse, 2))

print("R2 Score:", round(reg_r2, 2))
# ==========================================
# MULTIPLE LINEAR REGRESSION
# ==========================================

from sklearn.linear_model import LinearRegression

print("\nTraining Multiple Linear Regression model...")

mlr_model = LinearRegression()

mlr_pipeline = Pipeline(
    steps=[
        ("preprocessor", reg_preprocessor),
        ("model", mlr_model)
    ]
)

mlr_pipeline.fit(
    X_reg_train,
    y_reg_train
)

print("Multiple Linear Regression training completed!")

mlr_pred = mlr_pipeline.predict(X_reg_test)

mlr_mae = mean_absolute_error(
    y_reg_test,
    mlr_pred
)

mlr_rmse = np.sqrt(
    mean_squared_error(
        y_reg_test,
        mlr_pred
    )
)

mlr_r2 = r2_score(
    y_reg_test,
    mlr_pred
)

print("\n===== MULTIPLE LINEAR REGRESSION PERFORMANCE =====")

print("MAE:", round(mlr_mae, 2))

print("RMSE:", round(mlr_rmse, 2))

print("R2 Score:", round(mlr_r2, 2))
# ==========================================
# POLYNOMIAL REGRESSION
# ==========================================

from sklearn.preprocessing import PolynomialFeatures
from sklearn.linear_model import LinearRegression

print("\nTraining Polynomial Regression model...")

poly_pipeline = Pipeline(
    steps=[
        ("preprocessor", reg_preprocessor),
        ("polynomial", PolynomialFeatures(
            degree=2,
            include_bias=False
        )),
        ("model", LinearRegression())
    ]
)

poly_pipeline.fit(
    X_reg_train,
    y_reg_train
)

print("Polynomial Regression training completed!")

poly_pred = poly_pipeline.predict(
    X_reg_test
)

poly_mae = mean_absolute_error(
    y_reg_test,
    poly_pred
)

poly_rmse = np.sqrt(
    mean_squared_error(
        y_reg_test,
        poly_pred
    )
)

poly_r2 = r2_score(
    y_reg_test,
    poly_pred
)

print("\n===== POLYNOMIAL REGRESSION PERFORMANCE =====")

print("MAE:", round(poly_mae, 2))

print("RMSE:", round(poly_rmse, 2))

print("R2 Score:", round(poly_r2, 2))