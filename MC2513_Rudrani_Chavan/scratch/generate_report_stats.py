# -*- coding: utf-8 -*-
"""
Calculate all exact dataset statistics, missing value percentages, distributions,
categorical breakdowns, correlation metrics, and API coverage for the NutriMate report.
"""

import csv
import sqlite3
import numpy as np
import pandas as pd
import json
from pathlib import Path

BASE_DIR = Path(r"C:\nutrimate")

def run_stats():
    ds1_path = BASE_DIR / "data/datasets/Indian_Food_Nutrition_Processed.csv"
    ds2_path = BASE_DIR / "data/datasets/nutrimate_api_records.csv"
    ds3_path = BASE_DIR / "data/datasets/nutrimate_fused_dataset.csv"

    df1 = pd.read_csv(ds1_path)
    df2 = pd.read_csv(ds2_path)
    df3 = pd.read_csv(ds3_path)

    print("=== DATASET 1 (Kaggle) STATS ===")
    print(f"Shape: {df1.shape}")
    print(df1.info())
    print("\nDescriptive statistics:")
    print(df1.describe().T[['count', 'mean', 'std', 'min', '50%', 'max']])

    print("\nMissing values in DS1:")
    print(df1.isnull().sum())

    print("\n=== DATASET 2 (API Records) STATS ===")
    print(f"Shape: {df2.shape}")
    print("API Name distribution:")
    print(df2['api_name'].value_counts())
    print("Status code distribution:")
    print(df2['status_code'].value_counts())

    print("\n=== DATASET 3 (Fused Dataset) STATS ===")
    print(f"Shape: {df3.shape}")
    print("\nDiet type counts:")
    print(df3['diet_type'].value_counts())
    print("\nSource counts:")
    print(df3['source'].value_counts())

    # Convert numerical columns in df3
    num_cols3 = ['calories', 'protein', 'carbohydrates', 'fat', 'fiber', 'sugar', 'sodium', 'calcium', 'iron', 'vitamin_c', 'folate']
    for col in num_cols3:
        df3[col + '_num'] = pd.to_numeric(df3[col].replace('Not Available', np.nan), errors='coerce')

    print("\nFused Dataset Numeric Stats:")
    print(df3[[c + '_num' for c in num_cols3]].describe().T[['count', 'mean', 'std', 'min', '50%', 'max']])

    print("\nFused Dataset Non-Missing Percentages:")
    for c in num_cols3 + ['vitamins', 'minerals', 'ingredients', 'health_benefits', 'detected_allergens', 'substitutions']:
        if c in num_cols3:
            non_na = df3[c + '_num'].notnull().sum()
        else:
            non_na = (df3[c] != 'Not Available').sum()
        pct = (non_na / len(df3)) * 100
        print(f"  {c:<24}: {non_na}/{len(df3)} ({pct:.1f}%)")

if __name__ == "__main__":
    run_stats()
