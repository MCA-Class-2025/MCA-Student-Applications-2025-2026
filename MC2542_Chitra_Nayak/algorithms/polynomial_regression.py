import pandas as pd

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import PolynomialFeatures
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score


# Load dataset
df = pd.read_csv(
    r"C:\Users\anita nayak\Documents\PROJECTS\DSA_PROJECT\backend\datasets\dataset_fusion.csv"
)

print("Dataset Shape:", df.shape)


# Select data
data = df[["year", "source"]].dropna().copy()


# Convert categorical source into numeric values
data["source"] = pd.factorize(data["source"])[0]


# Feature and target
X = data[["source"]]
y = data["year"]


# Train-test split
X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.20,
    random_state=42
)


# Create polynomial features
poly = PolynomialFeatures(degree=2)

X_train_poly = poly.fit_transform(X_train)
X_test_poly = poly.transform(X_test)


# Create model
model = LinearRegression()


# Train model
model.fit(X_train_poly, y_train)


# Predictions
y_pred = model.predict(X_test_poly)


# Evaluation
print("\nPolynomial Regression Results")
print("=============================")

print("Mean Absolute Error (MAE):", mean_absolute_error(y_test, y_pred))
print("Mean Squared Error (MSE):", mean_squared_error(y_test, y_pred))
print("R2 Score:", r2_score(y_test, y_pred))