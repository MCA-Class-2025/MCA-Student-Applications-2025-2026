import pandas as pd

DATASET_PATH = "dataset/personal_finance.csv"

df = pd.read_csv(DATASET_PATH)

print("\n========== DATASET INFORMATION ==========\n")

print("Number of rows:", len(df))
print("Number of columns:", len(df.columns))

print("\nColumns:")
print(df.columns.tolist())

print("\nFirst 10 records:")
print(df.head(10))

print("\nData types:")
print(df.dtypes)

print("\nMissing values:")
print(df.isnull().sum())

print("\nDuplicate rows:")
print(df.duplicated().sum())

print("\nDataset statistics:")
print(df.describe(include="all"))

print("\nUnique values per column:")
for column in df.columns:
    print(f"\n{column}:")
    print(df[column].unique()[:20])