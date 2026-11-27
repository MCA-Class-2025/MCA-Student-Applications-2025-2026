
import pandas as pd
import os

# Correct Excel file path
file_path = r"data/original/Food_Dataset.xlsx"

if not os.path.exists(file_path):
    print("Dataset file not found!")
    print("Check the file name and location.")

else:
    # Read Excel dataset
    df = pd.read_excel(file_path, engine="openpyxl")

    print("\n========== DATASET OVERVIEW ==========")
    print("Dataset Name: Food Dataset")
    print("Number of Records:", df.shape[0])
    print("Number of Attributes:", df.shape[1])

    print("\n========== COLUMN NAMES ==========")
    print(df.columns.tolist())

    print("\n========== DATA TYPES ==========")
    print(df.dtypes)

    print("\n========== FIRST FIVE RECORDS ==========")
    print(df.head())

    print("\n========== MISSING VALUES ==========")
    print(df.isnull().sum())

    print("\n========== DUPLICATE RECORDS ==========")
    print(df.duplicated().sum())

    print("\n========== STATISTICAL SUMMARY ==========")
    print(df.describe(include="all").T)

    print("\nDataset inspection completed successfully!")
