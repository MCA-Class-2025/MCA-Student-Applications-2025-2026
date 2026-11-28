import pandas as pd

# ==========================================
# ALGORITHM COMPARISON
# ==========================================

results = {
    "Algorithm": [
        "Naive Bayes",
        "SVM",
        "Decision Tree",
        "Random Forest",
        "Logistic Regression",
        "Regression Analysis",
        "Multiple Linear Regression",
        "Polynomial Regression"
    ],

    "Metric": [
        "Accuracy",
        "Accuracy",
        "Accuracy",
        "Accuracy",
        "Accuracy",
        "R2 Score",
        "R2 Score",
        "R2 Score"
    ],

    "Score": [
        20.00,
        65.00,
        56.67,
        58.33,
        58.33,
        0.38,
        0.38,
        -0.21
    ]
}

df = pd.DataFrame(results)

print("\n===== ALGORITHM COMPARISON TABLE =====")
print(df.to_string(index=False))

# Save table
df.to_csv("algorithm_comparison.csv", index=False)

print("\nComparison table saved as: algorithm_comparison.csv")

# run:
# python generate_graphs.py