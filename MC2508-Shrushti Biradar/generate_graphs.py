import pandas as pd
import matplotlib.pyplot as plt

# ==========================================
# 1. LOAD DATASET
# ==========================================

df = pd.read_csv("AI_Event_Planner_Dataset.csv")

print("Dataset loaded successfully!")


# ==========================================
# 2. GRAPH 1 - ALGORITHM ACCURACY
# ==========================================

accuracy_data = {
    "Algorithm": [
        "Naive Bayes",
        "SVM",
        "Decision Tree",
        "Random Forest",
        "Logistic Regression"
    ],
    "Accuracy": [
        20.00,
        65.00,
        56.67,
        58.33,
        58.33
    ]
}

accuracy_df = pd.DataFrame(accuracy_data)

plt.figure(figsize=(10, 6))

plt.bar(
    accuracy_df["Algorithm"],
    accuracy_df["Accuracy"]
)

plt.title("Classification Algorithm Accuracy")
plt.xlabel("Algorithm")
plt.ylabel("Accuracy (%)")
plt.xticks(rotation=30)
plt.ylim(0, 100)
plt.tight_layout()

plt.savefig("classification_accuracy.png")
plt.show()


# ==========================================
# 3. GRAPH 2 - REGRESSION R2 SCORE
# ==========================================

regression_data = {
    "Algorithm": [
        "Regression Analysis",
        "Multiple Linear Regression",
        "Polynomial Regression"
    ],
    "R2 Score": [
        0.38,
        0.38,
        -0.21
    ]
}

regression_df = pd.DataFrame(regression_data)

plt.figure(figsize=(10, 6))

plt.bar(
    regression_df["Algorithm"],
    regression_df["R2 Score"]
)

plt.title("Regression Algorithm R2 Score")
plt.xlabel("Algorithm")
plt.ylabel("R2 Score")
plt.xticks(rotation=20)
plt.axhline(y=0)
plt.tight_layout()

plt.savefig("regression_r2_comparison.png")
plt.show()


# ==========================================
# 4. GRAPH 3 - SUCCESS SCORE DISTRIBUTION
# ==========================================

plt.figure(figsize=(10, 6))

plt.hist(
    df["success_score"],
    bins=10
)

plt.title("Distribution of Event Success Scores")
plt.xlabel("Success Score")
plt.ylabel("Number of Events")
plt.tight_layout()

plt.savefig("success_score_distribution.png")
plt.show()


# ==========================================
# 5. COMPLETED
# ==========================================

print("\n===== GRAPHS GENERATED SUCCESSFULLY =====")

print("1. classification_accuracy.png")
print("2. regression_r2_comparison.png")
print("3. success_score_distribution.png")