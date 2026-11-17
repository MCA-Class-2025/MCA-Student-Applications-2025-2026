from pathlib import Path
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]

TRAIN_FILE = PROJECT_ROOT / "data" / "processed" / "train.csv"
TEST_FILE = PROJECT_ROOT / "data" / "processed" / "test.csv"

train = pd.read_csv(TRAIN_FILE)
test = pd.read_csv(TEST_FILE)

print("\n======================================")
print(" ENGLISH DATA INSPECTION")
print("======================================")

english_train = train[train["language"] == "English"].copy()
english_test = test[test["language"] == "English"].copy()

print("\nTRAINING DATA")
print("Total:", len(english_train))
print("\nLabels:")
print(english_train["label"].value_counts())

print("\nTEST DATA")
print("Total:", len(english_test))
print("\nLabels:")
print(english_test["label"].value_counts())

print("\nTEXT LENGTH")
english_train["length"] = english_train["text"].astype(str).str.len()

print(english_train["length"].describe())

print("\nSOURCES")
print(english_train["source"].value_counts())

print("\nDOMAINS")
print(english_train["domain"].value_counts())

print("\nSAMPLE ENGLISH NEWS")
print(
    english_train[
        ["text", "label", "source", "domain", "topic"]
    ].head(5).to_string()
)

print("\n======================================")
print(" INSPECTION COMPLETED")
print("======================================")