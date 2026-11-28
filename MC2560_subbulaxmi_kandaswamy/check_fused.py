import pandas as pd
import glob
import os

files = glob.glob("fused_dataset/*.csv")

for f in files:
    df = pd.read_csv(f)

    print("\n========================================")
    print("FILE:", os.path.basename(f))
    print("========================================")
    print("ROWS:", len(df))
    print("COLUMNS:", len(df.columns))

    print("\nCOLUMN NAMES:")
    for col in df.columns:
        print("-", col)