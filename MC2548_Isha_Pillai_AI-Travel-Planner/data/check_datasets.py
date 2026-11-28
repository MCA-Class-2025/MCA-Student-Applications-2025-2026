import pandas as pd
import os
# Files we want to check
files = [
    "Travel details dataset.csv",
    "flights.csv",
    "weather.csv",
    "exchange_rates.csv",
    "places.csv",
    "images.csv"
]
print("\n======================================")
print("       DATASET INSPECTION")
print("======================================\n")
for file in files:
    path = os.path.join("data", file)
    print("\n--------------------------------------")
    print(f"FILE: {file}")
    print("--------------------------------------")
    try:
        # Original dataset is tab-separated
        if file == "Travel details dataset.csv":
            df = pd.read_csv(path, sep="\t")
        else:
            df = pd.read_csv(path)
        print("Records :", len(df))
        print("Columns :", len(df.columns))
        print("\nColumn names:")
        print(list(df.columns))
        print("\nMissing values:")
        print(df.isnull().sum().to_dict())
        print("\nDuplicate rows:")
        print(df.duplicated().sum())
    except Exception as e:
        print("ERROR:", e)
print("\n======================================")
print("       INSPECTION COMPLETE")
print("======================================")