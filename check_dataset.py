import pandas as pd
import os

files = [
    "dataset/interior_design_dataset.csv",
    "dataset/cleaned_decor.csv"
]

for file_path in files:

    print("\n" + "=" * 70)
    print("DATASET:", file_path)
    print("=" * 70)

    if not os.path.exists(file_path):
        print("FILE NOT FOUND")
        continue

    try:
        df = pd.read_csv(file_path)

        print("\nNumber of rows:", len(df))
        print("Number of columns:", len(df.columns))

        print("\nCOLUMN NAMES:")
        for column in df.columns:
            print(" -", column)

        print("\nFIRST 3 RECORDS:")
        print(df.head(3).to_string())

        print("\nMISSING VALUES:")
        print(df.isnull().sum().to_string())

    except Exception as e:
        print("ERROR:", e)