import pandas as pd

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.naive_bayes import GaussianNB
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix


# ==========================================
# 1. LOAD DATASET
# ==========================================

df = pd.read_csv(
    r"C:\Users\anita nayak\Documents\PROJECTS\DSA_PROJECT\backend\datasets\dataset_fusion.csv"
)

print("Dataset Shape:", df.shape)


# ==========================================
# 2. SELECT FEATURES AND TARGET
# ==========================================

X = df[["year", "source"]].copy()
y = df["document_type"].copy()


# ==========================================
# 3. REMOVE MISSING VALUES
# ==========================================

data = pd.concat([X, y], axis=1)
data = data.dropna()

X = data[["year", "source"]]
y = data["document_type"]


# ==========================================
# 4. ENCODE CATEGORICAL DATA
# ==========================================

source_encoder = LabelEncoder()
target_encoder = LabelEncoder()

X["source"] = source_encoder.fit_transform(X["source"])
y = target_encoder.fit_transform(y)


# ==========================================
# 5. TRAIN-TEST SPLIT
# ==========================================

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.20,
    random_state=42
)


# ==========================================
# 6. CREATE NAIVE BAYES MODEL
# ==========================================

model = GaussianNB()


# ==========================================
# 7. TRAIN MODEL
# ==========================================

model.fit(X_train, y_train)


# ==========================================
# 8. MAKE PREDICTIONS
# ==========================================

y_pred = model.predict(X_test)


# ==========================================
# 9. EVALUATE MODEL
# ==========================================

accuracy = accuracy_score(y_test, y_pred)

print("\nNaive Bayes Results")
print("===================")

print("Accuracy:", accuracy)

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