import pandas as pd

DATASET_PATH = "dataset/personal_finance.csv"

df = pd.read_csv(DATASET_PATH)

print("\n========== CATEGORY DISTRIBUTION ==========\n")

category_counts = df["Category"].value_counts()

print(category_counts)

print("\nTotal categories:", df["Category"].nunique())

print("\nPercentage distribution:")

print(
    (df["Category"].value_counts(normalize=True) * 100)
    .round(2)
)