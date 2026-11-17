import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix

# Load dataset
df = pd.read_csv("data/Task2_Prepared_Dataset.csv")

# Remove missing values
df = df.dropna(
    subset=[
        "rating_category",
        "average_rating",
        "ratings_count",
        "published_year",
        "num_pages",
    ]
)

# Features and target
X = df[["average_rating", "ratings_count", "published_year", "num_pages"]]

y = df["rating_category"]

# Train-test split
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

# Create Decision Tree model
model = DecisionTreeClassifier(random_state=42, max_depth=10)

# Train
model.fit(X_train, y_train)

# Prediction
pred = model.predict(X_test)

# Results
print("=== DECISION TREE ===")
print("Training records:", len(X_train))
print("Testing records:", len(X_test))
print("Accuracy:", round(accuracy_score(y_test, pred), 4))

print("\n=== CLASSIFICATION REPORT ===")
print(classification_report(y_test, pred, zero_division=0))

print("=== CONFUSION MATRIX ===")
print(confusion_matrix(y_test, pred))
