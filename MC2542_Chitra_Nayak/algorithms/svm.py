import pandas as pd

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.svm import SVC
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix


df = pd.read_csv(
    r"C:\Users\anita nayak\Documents\PROJECTS\DSA_PROJECT\backend\datasets\dataset_fusion.csv"
)

X = df[["year", "source"]].copy()
y = df["document_type"].copy()

data = pd.concat([X, y], axis=1).dropna()

X = data[["year", "source"]].copy()
y = data["document_type"].copy()

source_encoder = LabelEncoder()
target_encoder = LabelEncoder()

X["source"] = source_encoder.fit_transform(X["source"])
y = target_encoder.fit_transform(y)

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.20, random_state=42
)

scaler = StandardScaler()

X_train = scaler.fit_transform(X_train)
X_test = scaler.transform(X_test)

model = SVC(kernel="linear")

model.fit(X_train, y_train)

y_pred = model.predict(X_test)

print("SVM Results")
print("===========")
print("Accuracy:", accuracy_score(y_test, y_pred))

print("\nClassification Report:")
print(classification_report(
    y_test,
    y_pred,
    labels=sorted(set(y_test) | set(y_pred)),
    target_names=target_encoder.inverse_transform(
        sorted(set(y_test) | set(y_pred))
    ),
    zero_division=0
))

print("\nConfusion Matrix:")
print(confusion_matrix(y_test, y_pred))