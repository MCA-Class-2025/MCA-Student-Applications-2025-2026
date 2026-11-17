import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import numpy as np

# Load dataset
df = pd.read_csv("data/Task2_Prepared_Dataset.csv")

# Remove missing values
df = df.dropna(
    subset=["ratings_count", "average_rating", "published_year", "num_pages"]
)

# Multiple input features
X = df[["average_rating", "published_year", "num_pages"]]

# Target
y = df["ratings_count"]

# Train-test split
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# Create Multiple Linear Regression model
model = LinearRegression()

# Train
model.fit(X_train, y_train)

# Prediction
pred = model.predict(X_test)

# Evaluation metrics
mae = mean_absolute_error(y_test, pred)
rmse = np.sqrt(mean_squared_error(y_test, pred))
r2 = r2_score(y_test, pred)

# Results
print("=== MULTIPLE LINEAR REGRESSION ===")
print("Training records:", len(X_train))
print("Testing records:", len(X_test))
print("MAE:", round(mae, 2))
print("RMSE:", round(rmse, 2))
print("R2 Score:", round(r2, 4))

print("\n=== COEFFICIENTS ===")
for feature, coefficient in zip(X.columns, model.coef_):
    print(feature, ":", coefficient)

print("Intercept:", model.intercept_)
