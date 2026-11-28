
# UNDER-FITTING AND OVER-FITTING USING POLYNOMIAL REGRESSION

import numpy as np
import matplotlib.pyplot as plt

from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import PolynomialFeatures
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import cross_val_score


# STEP 1: Generate a cosine-based dataset

def true_fun(X):
    return np.cos(1.5 * np.pi * X)


np.random.seed(0)

X = np.sort(np.random.rand(30))
y = true_fun(X) + np.random.randn(30) * 0.1

X = X.reshape(-1, 1)


# STEP 2: Compare polynomial degrees

degrees = [1, 4, 15]

X_plot = np.linspace(0, 1, 100).reshape(-1, 1)

plt.figure(figsize=(15, 5))

for i, degree in enumerate(degrees):

    model = make_pipeline(
        PolynomialFeatures(degree=degree),
        LinearRegression()
    )

    model.fit(X, y)

    # Calculate cross-validation error
    scores = cross_val_score(
        model,
        X,
        y,
        scoring="neg_mean_squared_error",
        cv=10
    )

    # Plot the model
    plt.subplot(1, 3, i + 1)

    plt.scatter(X, y, color="blue", label="Data Points")

    plt.plot(
        X_plot,
        true_fun(X_plot),
        color="green",
        linestyle="--",
        label="Actual Pattern"
    )

    plt.plot(
        X_plot,
        model.predict(X_plot),
        color="red",
        label="Predicted Curve"
    )

    plt.title(
        f"Degree {degree}\nMSE: {-scores.mean():.4f}"
    )

    plt.xlabel("X")
    plt.ylabel("Y")
    plt.legend()

plt.tight_layout()
plt.show()
