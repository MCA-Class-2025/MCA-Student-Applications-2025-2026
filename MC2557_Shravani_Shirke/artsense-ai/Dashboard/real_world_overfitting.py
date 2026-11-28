
# PRACTICAL 5.2 - REAL WORLD DATASET
# STEP 1: LOAD DATA, TAKE SAMPLE AND SPLIT

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import re

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import PolynomialFeatures, StandardScaler
from sklearn.pipeline import make_pipeline
from sklearn.linear_model import LinearRegression


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


# Select required columns and remove missing values
df = df[["year_numeric", "price"]].dropna()

print("Cleaned Dataset Shape:", df.shape)


# Take a random sample of 300 records
sample_df = df.sample(n=300, random_state=42)

# Select input and target
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
print("\n===== DATASET SPLIT =====")
print("Sample Records:", len(sample_df))
print("Training Records:", len(X_train))
print("Testing Records:", len(X_test))
print("Input Features:", X.shape[1])

print("\nInput Feature: year_numeric")
print("Target Feature: price")

# STEP 2: FIT POLYNOMIAL MODELS FROM DEGREE 1 TO 10

score_table = []

for degree in range(1, 11):

    model = make_pipeline(
        PolynomialFeatures(degree=degree),
        StandardScaler(),
        LinearRegression()
    )

    model.fit(X_train, y_train)

    # Calculate training and testing R-squared
    train_r2 = model.score(X_train, y_train)
    test_r2 = model.score(X_test, y_test)

    score_table.append({
        "Degree": degree,
        "Train R2": train_r2,
        "Test R2": test_r2
    })


# Display comparison table
score_df = pd.DataFrame(score_table)

print("\n===== POLYNOMIAL MODEL COMPARISON =====")
print(score_df.round(4).to_string(index=False))

# STEP 3: FIND BEST DEGREE AND PLOT SCORES

best_index = score_df["Test R2"].idxmax()

best_degree = int(score_df.loc[best_index, "Degree"])
best_test_score = score_df.loc[best_index, "Test R2"]

print("\n===== BEST POLYNOMIAL DEGREE =====")
print("Best Degree:", best_degree)
print("Best Test R2:", round(best_test_score, 4))


# Plot training and testing scores
plt.figure(figsize=(10, 5))

plt.plot(
    score_df["Degree"],
    score_df["Train R2"],
    marker="o",
    label="Train R2"
)

plt.plot(
    score_df["Degree"],
    score_df["Test R2"],
    marker="s",
    label="Test R2"
)

plt.axvline(
    best_degree,
    color="green",
    linestyle="--",
    label=f"Best Degree = {best_degree}"
)

plt.xlabel("Polynomial Degree")
plt.ylabel("R-squared Score")
plt.title("Polynomial Regression Model Comparison")
plt.xticks(range(1, 11))
plt.legend()
plt.grid(True)
plt.show()

# STEP 4: SHOW UNDER-FIT, GOOD-FIT AND HIGH-DEGREE CURVES

degrees_to_plot = [1, best_degree, 10]

# Create a smooth range of year values
grid = np.linspace(
    X_train["year_numeric"].min(),
    X_train["year_numeric"].max(),
    300
).reshape(-1, 1)

plt.figure(figsize=(15, 5))

for i, degree in enumerate(degrees_to_plot):

    model = make_pipeline(
        PolynomialFeatures(degree=degree),
        StandardScaler(),
        LinearRegression()
    )

    model.fit(X_train, y_train)

    plt.subplot(1, 3, i + 1)

    # Training data
    plt.scatter(
        X_train["year_numeric"],
        y_train,
        label="Training Data"
    )

    # Testing data
    plt.scatter(
        X_test["year_numeric"],
        y_test,
        label="Testing Data"
    )

    # Predicted curve
    plt.plot(
        grid,
        model.predict(grid),
        color="red",
        label="Predicted Curve"
    )

    plt.title(f"Polynomial Degree {degree}")
    plt.xlabel("Year of Creation")
    plt.ylabel("Artwork Price")
    plt.legend()

plt.tight_layout()
plt.show()
