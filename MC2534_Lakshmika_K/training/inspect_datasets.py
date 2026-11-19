import pandas as pd
import os

DATASET_PATH = "dataset"

files = [
    "cities_master.csv",
    "Waste_Management_and_Recycling_India.csv",
    "Waste_Management_India_20K.csv"
]

for file in files:

    path = os.path.join(DATASET_PATH, file)

    print("\n" + "=" * 70)
    print(f"FILE: {file}")
    print("=" * 70)

    if not os.path.exists(path):
        print("❌ File not found:", path)
        continue

    df = pd.read_csv(path)

    print("Rows:", df.shape[0])
    print("Columns:", df.shape[1])

    print("\nColumn Names:")
    for column in df.columns:
        print(" -", column)

    print("\nFirst 3 Records:")
    print(df.head(3).to_string(index=False))