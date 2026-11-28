
# STEP 1: IMPORT LIBRARIES

import pandas as pd
import numpy as np

from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler, PolynomialFeatures
from sklearn.pipeline import Pipeline
from sklearn.metrics import r2_score, mean_squared_error

# STEP 2: LOAD AND PREPARE DATASET

df = pd.read_csv("data/artworks.csv.csv")

df["price"] = (
    df["price"]
    .astype(str)
    .str.replace("USD", "", regex=False)
    .str.replace(",", "", regex=False)
    .str.strip()
)

df["price"] = pd.to_numeric(df["price"], errors="coerce")

df["year_numeric"] = pd.to_numeric(
    df["yearCreation"].astype(str).str.extract(r"(\d{4})")[0],
    errors="coerce"
)

data = df[["year_numeric", "price"]].dropna()

X = data[["year_numeric"]]
y = data["price"]

# STEP 3: TRAIN LINEAR REGRESSION MODEL

linear_model = LinearRegression()
linear_model.fit(X, y)

# STEP 4: TRAIN POLYNOMIAL MODELS DEGREE 1 TO 6

poly_models = {}

for degree in range(1, 7):

    pipeline = Pipeline([
        ("scaler", StandardScaler()),
        ("poly", PolynomialFeatures(
            degree=degree,
            include_bias=False
        )),
        ("model", LinearRegression())
    ])

    pipeline.fit(X, y)

    poly_models[degree] = pipeline

print("All Linear and Polynomial Models Trained Successfully.")

print("Dataset Records:", len(data))
print("Training Year Range:",
      X["year_numeric"].min(), "to",
      X["year_numeric"].max())

# STEP 5: PREDICT PRICES FOR NEW ARTWORK YEARS

# New years within the training range
new_years = pd.DataFrame({
    "year_numeric": [1950, 1980, 2000, 2020]
})

prediction_results = new_years.copy()

# Linear Regression prediction
prediction_results["Linear Regression"] = (
    linear_model.predict(new_years)
)

# Polynomial Regression predictions
for degree, model in poly_models.items():
    prediction_results[f"Degree {degree}"] = (
        model.predict(new_years)
    )

print("\n===== NEW ARTWORK PRICE PREDICTIONS =====")
print(prediction_results.round(4).to_string(index=False))

# STEP 6: CHECK FOR NEGATIVE PREDICTIONS

print("\n===== NEGATIVE PREDICTION CHECK =====")

model_columns = [
    "Linear Regression",
    "Degree 1",
    "Degree 2",
    "Degree 3",
    "Degree 4",
    "Degree 5",
    "Degree 6"
]

for model_name in model_columns:

    negative_count = (
        prediction_results[model_name] < 0
    ).sum()

    print(
        model_name,
        "Negative Predictions:",
        negative_count
    )

print("\n===== UNREALISTIC PREDICTIONS =====")

negative_values = prediction_results[
    prediction_results[model_columns].lt(0).any(axis=1)
]

print(negative_values.to_string(index=False))

# STEP 7: PREDICTIONS OUTSIDE THE TRAINING RANGE

outside_years = pd.DataFrame({
    "year_numeric": [1850, 2050, 2100]
})

outside_results = outside_years.copy()

# Linear Regression predictions
outside_results["Linear Regression"] = (
    linear_model.predict(outside_years)
)

# Polynomial Regression predictions
for degree, model in poly_models.items():
    outside_results[f"Degree {degree}"] = (
        model.predict(outside_years)
    )

print("\n===== PREDICTIONS OUTSIDE TRAINING RANGE =====")
print(outside_results.round(4).to_string(index=False))

print("\nTraining Year Range: 1877 to 2022")
print("Test Years: 1850, 2050, 2100")

# STEP 8: FINAL MODEL SELECTION

# Calculate training R-squared for each polynomial model
model_scores = []

for degree, model in poly_models.items():

    predictions = model.predict(X)

    score = r2_score(y, predictions)

    model_scores.append({
        "Degree": degree,
        "R-squared": score
    })

scores_df = pd.DataFrame(model_scores)

# Find the highest R-squared
best_score = scores_df["R-squared"].max()

# Select the simplest degree within 0.005
# of the highest R-squared
eligible_models = scores_df[
    scores_df["R-squared"] >= best_score - 0.005
]

selected_degree = int(
    eligible_models["Degree"].min()
)

selected_model = poly_models[selected_degree]

print("\n===== FINAL MODEL SELECTION =====")

print(scores_df.round(4).to_string(index=False))

print("\nHighest R-squared:", best_score)
print("Selected Polynomial Degree:", selected_degree)

# Predict price using selected model
selected_prediction = selected_model.predict(
    pd.DataFrame({"year_numeric": [2000]})
)[0]

print("Predicted Price for Year 2000:",
      round(selected_prediction, 4))
