import os
import pandas as pd

DATASET_FOLDER = os.path.join("backend", "datasets")

print("===== DATASET FILES =====")

files = os.listdir(DATASET_FOLDER)

for file in files:
    print(file)

    if file.endswith(".csv"):
        path = os.path.join(DATASET_FOLDER, file)

        df = pd.read_csv(path)

        print("Rows:", len(df))
        print("Columns:", len(df.columns))
        print("Column names:")
        print(list(df.columns))
        print("-" * 50)