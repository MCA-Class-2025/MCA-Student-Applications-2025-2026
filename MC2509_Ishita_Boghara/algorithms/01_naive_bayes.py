import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.naive_bayes import GaussianNB
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix


# Load prepared dataset
df = pd.read_csv("data/Task2_Prepared_Dataset.csv")

# Remove records with missing values required for classification
df = df.dropna(
    subset=[
        "rating_category",
        "average_rating",
        "ratings_count",
        "published_year",
        "num_pages"
    ]
)

# Input features
X = df[
    [
        "average_rating",
        "ratings_count",
        "published_year",
        "num_pages"
    ]
]

# Target variable
y = df["rating_category"]

# Split dataset into training and testing data
X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    random_state=42,
    stratify=y
)

# Create and train Naive Bayes model
model = GaussianNB()
model.fit(X_train, y_train)

# Make predictions
pred = model.predict(X_test)

# Display results
print("=== NAIVE BAYES ===")
print("Training records:", len(X_train))
print("Testing records:", len(X_test))
print("Accuracy:", round(accuracy_score(y_test, pred), 4))

print("\n=== CLASSIFICATION REPORT ===")
print(classification_report(y_test, pred, zero_division=0))

print("=== CONFUSION MATRIX ===")
print(confusion_matrix(y_test, pred))
