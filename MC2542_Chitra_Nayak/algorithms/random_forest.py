import pandas as pd

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix


# Load dataset
df = pd.read_csv(
    r"C:\Users\anita nayak\Documents\PROJECTS\DSA_PROJECT\backend\datasets\dataset_fusion.csv"
)

print("Dataset Shape:", df.shape)


# Select features and target
X = df[["year", "source"]].copy()
y = df["document_type"].copy()


# Remove missing values
data = pd.concat([X, y], axis=1).dropna()

X = data[["year", "source"]].copy()
y = data["document_type"].copy()


# Encode categorical data
source_encoder = LabelEncoder()
target_encoder = LabelEncoder()

X["source"] = source_encoder.fit_transform(X["source"])
y = target_encoder.fit_transform(y)


# Train-test split
X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.20,
    random_state=42
)


# Create Random Forest model
model = RandomForestClassifier(
    n_estimators=100,
    random_state=42
)


# Train model
model.fit(X_train, y_train)


# Predictions
y_pred = model.predict(X_test)


# Evaluation
print("\nRandom Forest Results")
print("=====================")

print("Accuracy:", accuracy_score(y_test, y_pred))

print("\nClassification Report:")
print(
    classification_report(
        y_test,
        y_pred,
        labels=sorted(set(y_test) | set(y_pred)),
        target_names=target_encoder.inverse_transform(
            sorted(set(y_test) | set(y_pred))
        ),
        zero_division=0
    )
)

print("\nConfusion Matrix:")
print(confusion_matrix(y_test, y_pred))