
# STEP 1: IMPORT LIBRARIES

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score, mean_squared_error

# STEP 2: LOAD DATASET

df = pd.read_csv("data/artworks.csv.csv")

print("Dataset Loaded Successfully")

print("\nOriginal Dataset Shape:")
print(df.shape)

print("\nFirst Five Records:")
print(df.head())

print("\nDataset Information:")
print(df.info())

# STEP 3: CLEAN ARTWORK PRICE

df["price"] = (
    df["price"]
    .astype(str)
    .str.replace("USD", "", regex=False)
    .str.replace(",", "", regex=False)
    .str.strip()
)

df["price"] = pd.to_numeric(
    df["price"], errors="coerce"
)

# STEP 4: CONVERT CREATION YEAR INTO NUMERICAL FORMAT

df["year_numeric"] = pd.to_numeric(
    df["yearCreation"].astype(str).str.extract(r"(\d{4})")[0],
    errors="coerce"
)

# STEP 5: SELECT REQUIRED COLUMNS AND REMOVE MISSING VALUES

data = df[["year_numeric", "price"]].dropna()

X = data[["year_numeric"]]
y = data["price"]

print("\n===== CLEANED DATASET INFORMATION =====")

print("Cleaned Dataset Shape:", data.shape)

print("\nFirst Five Cleaned Records:")
print(data.head())

print("\nMissing Values:")
print(data.isnull().sum())

print("\nStatistical Summary:")
print(data.describe())

# STEP 6: SPLIT DATASET INTO TRAINING AND TESTING SETS

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.20,
    random_state=42
)

print("\n===== TRAIN TEST SPLIT =====")

print("Total Records:", len(data))

print("Training Records:", len(X_train))
print("Testing Records:", len(X_test))

print("Training Percentage:",
      round(len(X_train) / len(data) * 100, 2), "%")

print("Testing Percentage:",
      round(len(X_test) / len(data) * 100, 2), "%")

# STEP 7: TRAIN THE MODEL AND PREDICT

model = LinearRegression()

# Train the model
model.fit(X_train, y_train)

# Predict on training and testing data
pred_train = model.predict(X_train)
pred_test = model.predict(X_test)

print("\n===== MODEL TRAINING COMPLETED =====")
print("Model: Linear Regression")
print("Training Predictions:", len(pred_train))
print("Testing Predictions:", len(pred_test))

print("\nFirst 5 Actual Test Prices:")
print(y_test.head().values)

print("\nFirst 5 Predicted Test Prices:")
print(pred_test[:5])

# STEP 8: CALCULATE MODEL EVALUATION METRICS

from sklearn.metrics import r2_score, mean_squared_error

def scores(actual, predicted):
    r2 = r2_score(actual, predicted)
    mse = mean_squared_error(actual, predicted)
    rmse = np.sqrt(mse)

    return r2, mse, rmse


# Calculate training scores
train_r2, train_mse, train_rmse = scores(y_train, pred_train)

# Calculate testing scores
test_r2, test_mse, test_rmse = scores(y_test, pred_test)


# Display comparison table
results = pd.DataFrame({
    "Metric": ["R-squared", "MSE", "RMSE"],
    "Train Score": [train_r2, train_mse, train_rmse],
    "Test Score": [test_r2, test_mse, test_rmse]
})

print("\n===== MODEL EVALUATION RESULTS =====")
print(results.round(4).to_string(index=False))

# STEP 9: 5-FOLD CROSS-VALIDATION

from sklearn.model_selection import cross_val_score

cv_scores = cross_val_score(
    model,
    X_train,
    y_train,
    cv=5,
    scoring="r2"
)

print("\n===== 5-FOLD CROSS-VALIDATION =====")

print("Cross-validation R2 Scores:")
print(cv_scores)

print("Mean CV R2 Score:", round(cv_scores.mean(), 4))

# STEP 10: ACTUAL VS PREDICTED AND RESIDUAL PLOTS

residuals = y_test - pred_test

plt.figure(figsize=(12, 5))

# Actual vs Predicted Plot
plt.subplot(1, 2, 1)
plt.scatter(y_test, pred_test)
plt.plot(
    [y_test.min(), y_test.max()],
    [y_test.min(), y_test.max()],
    'r--'
)
plt.xlabel("Actual Price")
plt.ylabel("Predicted Price")
plt.title("Actual vs Predicted Prices")

# Residual Plot
plt.subplot(1, 2, 2)
plt.scatter(pred_test, residuals)
plt.axhline(y=0, color='r', linestyle='--')
plt.xlabel("Predicted Price")
plt.ylabel("Residuals")
plt.title("Residual Plot")

plt.tight_layout()
plt.show()
