
# STEP 1: IMPORT LIBRARIES

import pandas as pd
import numpy as np

from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score, mean_squared_error

# STEP 2: LOAD AND PREPARE DATASET

df = pd.read_csv("data/artworks.csv.csv")

# Clean artwork price
df["price"] = (
    df["price"]
    .astype(str)
    .str.replace("USD", "", regex=False)
    .str.replace(",", "", regex=False)
    .str.strip()
)

df["price"] = pd.to_numeric(df["price"], errors="coerce")

# Convert creation year into numerical format
df["year_numeric"] = pd.to_numeric(
    df["yearCreation"].astype(str).str.extract(r"(\d{4})")[0],
    errors="coerce"
)

data = df[["year_numeric", "price"]].dropna()

X = data[["year_numeric"]]
y = data["price"]

# STEP 3: TRAIN SIMPLE LINEAR REGRESSION

model = LinearRegression()
model.fit(X, y)

# Generate predictions
y_pred = model.predict(X)

# STEP 4: MANUAL CALCULATION

y_true = y.values
y_hat = y_pred

n = len(y_true)

# Sum of Squared Errors
sse = np.sum((y_true - y_hat) ** 2)

# Total Sum of Squares
sst = np.sum((y_true - y_true.mean()) ** 2)

# Mean Squared Error
mse_manual = sse / n

# R-squared
r2_manual = 1 - (sse / sst)

# STEP 5: VERIFY USING SCIKIT-LEARN

mse_sklearn = mean_squared_error(y_true, y_hat)
r2_sklearn = r2_score(y_true, y_hat)

print("\n===== MANUAL CALCULATION =====")

print("Number of Records:", n)
print("SSE:", round(sse, 4))
print("SST:", round(sst, 4))

print("\nMSE (Manual):", round(mse_manual, 4))
print("MSE (Scikit-learn):", round(mse_sklearn, 4))

print("\nR-squared (Manual):", round(r2_manual, 4))
print("R-squared (Scikit-learn):", round(r2_sklearn, 4))

# STEP 6: CALCULATE RMSE AND ADJUSTED R-SQUARED

rmse = np.sqrt(mse_sklearn)

# Number of predictors in Simple Linear Regression
p = X.shape[1]

if n - p - 1 > 0:
    adjusted_r2 = 1 - (
        (1 - r2_sklearn) * (n - 1) / (n - p - 1)
    )
else:
    adjusted_r2 = np.nan

print("\n===== ADDITIONAL EVALUATION METRICS =====")
print("RMSE:", round(rmse, 4))
print("Adjusted R-squared:", round(adjusted_r2, 4))

# STEP 7: FIVE-MODEL COMPARISON

from sklearn.preprocessing import StandardScaler, PolynomialFeatures
from sklearn.pipeline import Pipeline

# Prepare input and target
X_year = data[["year_numeric"]]
y_actual = data["price"]

# Model 1: Simple Linear Regression
simple_model = LinearRegression()
simple_model.fit(X_year, y_actual)
pred_simple = simple_model.predict(X_year)

# Model 2: Multiple Linear Regression
df_multi = pd.read_csv("data/artworks.csv.csv")

df_multi["price"] = (
    df_multi["price"].astype(str)
    .str.replace("USD", "", regex=False)
    .str.replace(",", "", regex=False)
    .str.strip()
)
df_multi["price"] = pd.to_numeric(
    df_multi["price"], errors="coerce"
)

df_multi["year_numeric"] = pd.to_numeric(
    df_multi["yearCreation"].astype(str).str.extract(r"(\d{4})")[0],
    errors="coerce"
)

multi_data = df_multi[
    ["year_numeric", "signed", "condition", "period", "movement", "price"]
].dropna()

X_multi_raw = multi_data.drop(columns=["price"])
y_multi = multi_data["price"]

X_multi = pd.get_dummies(
    X_multi_raw,
    columns=["signed", "condition", "period", "movement"],
    drop_first=True,
    dtype=int
)

multi_model = LinearRegression()
multi_model.fit(X_multi, y_multi)
pred_multi = multi_model.predict(X_multi)

# Polynomial model predictions
poly_predictions = []

for degree in [1, 2, 3]:
    pipe = Pipeline([
        ("scaler", StandardScaler()),
        ("poly", PolynomialFeatures(
            degree=degree,
            include_bias=False
        )),
        ("model", LinearRegression())
    ])

    pipe.fit(X_year, y_actual)
    prediction = pipe.predict(X_year)

    poly_predictions.append((degree, prediction))

# Store all models
models = [
    ("Simple Linear Regression", y_actual, pred_simple, 1),
    ("Multiple Linear Regression", y_multi, pred_multi, X_multi.shape[1])
]

for degree, prediction in poly_predictions:
    models.append((
        f"Polynomial Degree {degree}",
        y_actual,
        prediction,
        degree
    ))

# Calculate evaluation metrics
rows = []

for name, actual, predicted, p in models:
    n = len(actual)

    r2 = r2_score(actual, predicted)
    mse = mean_squared_error(actual, predicted)
    rmse = np.sqrt(mse)

    if n - p - 1 > 0:
        adj_r2 = 1 - ((1 - r2) * (n - 1) / (n - p - 1))
        adj_display = round(adj_r2, 4)
    else:
        adj_display = "N/A"

    rows.append([
        name, p, r2, adj_display, mse, rmse
    ])

comparison = pd.DataFrame(
    rows,
    columns=[
        "Model", "Predictors", "R-squared",
        "Adjusted R-squared", "MSE", "RMSE"
    ]
)

print("\n===== FIVE-MODEL EVALUATION COMPARISON =====")
print(comparison.round(4).to_string(index=False))

# STEP 8: CORRECTED BAR CHARTS

import matplotlib.pyplot as plt
import numpy as np

# Model names and values from comparison table
names = comparison["Model"].tolist()
r2_values = comparison["R-squared"].astype(float).tolist()
mse_values = comparison["MSE"].astype(float).tolist()

# Numeric positions ensure correct label alignment
positions = np.arange(len(names))

fig, axes = plt.subplots(1, 2, figsize=(16, 7))

# R-squared chart
axes[0].bar(positions, r2_values)

axes[0].set_title("R-squared Comparison (Higher is Better)")
axes[0].set_ylabel("R-squared")
axes[0].set_ylim(0, 1.05)
axes[0].set_xticks(positions)
axes[0].set_xticklabels(names, rotation=35, ha="right")

for i, value in enumerate(r2_values):
    axes[0].text(i, value + 0.01, f"{value:.4f}",
                 ha="center")

# MSE chart
axes[1].bar(positions, mse_values)

axes[1].set_title("MSE Comparison (Lower is Better)")
axes[1].set_ylabel("Mean Squared Error")
axes[1].set_xticks(positions)
axes[1].set_xticklabels(names, rotation=35, ha="right")

for i, value in enumerate(mse_values):
    axes[1].text(i, value + max(mse_values) * 0.01,
                 f"{value:.2f}", ha="center")

plt.suptitle("Regression Model Evaluation Comparison")
plt.tight_layout()
plt.show()
