
# PRACTICAL 5.3 - MODEL SELECTION
# STEP 1: IMPORT LIBRARIES, LOAD DATA AND SPLIT

import pandas as pd
import numpy as np
import re

from sklearn.model_selection import train_test_split
from sklearn.model_selection import cross_val_score

from sklearn.preprocessing import PolynomialFeatures, StandardScaler
from sklearn.pipeline import make_pipeline

from sklearn.linear_model import LinearRegression, Ridge
from sklearn.metrics import r2_score, mean_squared_error


# Load dataset
df = pd.read_csv("data/artworks.csv.csv")

print("Original Dataset Shape:", df.shape)


# Clean price column
df["price"] = (
    df["price"]
    .astype(str)
    .str.replace("USD", "", regex=False)
    .str.replace(",", "", regex=False)
    .str.strip()
)

df["price"] = pd.to_numeric(df["price"], errors="coerce")


# Extract year from yearCreation
def extract_year(value):
    match = re.search(r"\d{4}", str(value))
    return int(match.group()) if match else np.nan


df["year_numeric"] = df["yearCreation"].apply(extract_year)


# Select columns and remove missing values
df = df[["year_numeric", "price"]].dropna()

print("Cleaned Dataset Shape:", df.shape)


# Take random sample of 300 records
sample_df = df.sample(n=300, random_state=42)

X = sample_df[["year_numeric"]]
y = sample_df["price"]


# Split into 70% training and 30% testing
X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.30,
    random_state=42
)


# Display dataset information
print("\n===== MODEL SELECTION DATASET =====")
print("Sample Records:", len(sample_df))
print("Training Records:", len(X_train))
print("Testing Records:", len(X_test))
print("Input Features:", X.shape[1])

# STEP 2: DEFINE CANDIDATE MODELS

models = {
    "Linear Regression": make_pipeline(
        StandardScaler(),
        LinearRegression()
    ),

    "Polynomial Degree 2": make_pipeline(
        PolynomialFeatures(degree=2),
        StandardScaler(),
        LinearRegression()
    ),

    "Polynomial Degree 3": make_pipeline(
        PolynomialFeatures(degree=3),
        StandardScaler(),
        LinearRegression()
    ),

    "Ridge Degree 2": make_pipeline(
        PolynomialFeatures(degree=2),
        StandardScaler(),
        Ridge(alpha=10)
    )
}

print("\n===== CANDIDATE MODELS =====")

for name in models:
    print(name)

# STEP 3: 5-FOLD CROSS-VALIDATION

results = []

for name, model in models.items():

    # Perform cross-validation on training data only
    cv_scores = cross_val_score(
        model,
        X_train,
        y_train,
        cv=5,
        scoring="r2"
    )

    # Train model on complete training data
    model.fit(X_train, y_train)

    # Calculate training R-squared
    train_r2 = model.score(X_train, y_train)

    results.append({
        "Model": name,
        "Train R2": train_r2,
        "CV Mean R2": cv_scores.mean(),
        "CV Std": cv_scores.std()
    })


# Create results table
results_df = pd.DataFrame(results)

print("\n===== MODEL SELECTION RESULTS =====")
print(results_df.round(4).to_string(index=False))


# STEP 4: BAR CHART OF CROSS-VALIDATION SCORES

import matplotlib.pyplot as plt

# Display actual CV scores before plotting
print("\n===== VERIFY CV SCORES FOR GRAPH =====")
print(
    results_df[["Model", "CV Mean R2", "CV Std"]]
    .round(4)
    .to_string(index=False)
)

# Draw bar chart
plt.figure(figsize=(10, 5))

plt.bar(
    results_df["Model"],
    results_df["CV Mean R2"],
    yerr=results_df["CV Std"],
    capsize=5
)

plt.xlabel("Machine Learning Models")
plt.ylabel("Mean CV R-squared")
plt.title("Model Comparison using 5-Fold Cross-Validation")

# Reference line at zero
plt.axhline(y=0, color="red", linestyle="--")

plt.xticks(rotation=15)
plt.tight_layout()
plt.show()

# STEP 5: SELECT THE BEST MODEL AND TEST IT ONCE

# Select model with highest CV Mean R2
best_index = results_df["CV Mean R2"].idxmax()

best_model_name = results_df.loc[best_index, "Model"]
best_model = models[best_model_name]

# Predict on test data
pred_test = best_model.predict(X_test)

# Calculate test performance
test_r2 = r2_score(y_test, pred_test)

test_mse = mean_squared_error(y_test, pred_test)

test_rmse = np.sqrt(test_mse)

print("\n===== BEST MODEL SELECTION =====")
print("Selected Model:", best_model_name)
print("Best CV Mean R2:",
      round(results_df.loc[best_index, "CV Mean R2"], 4))

print("\n===== FINAL TEST RESULTS =====")
print("Test R-squared:", round(test_r2, 4))
print("Test MSE:", round(test_mse, 4))
print("Test RMSE:", round(test_rmse, 4))
