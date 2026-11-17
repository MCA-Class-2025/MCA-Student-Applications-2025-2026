import os
import pandas as pd


# ============================================================
# STEP 1: LOAD NEW FUSED DATASET
# ============================================================

print("=" * 70)
print("STEP 1 - LOADING FUSED DATASET")
print("=" * 70)


# ------------------------------------------------------------
# Project root directory
# ------------------------------------------------------------

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# ------------------------------------------------------------
# Dataset path
# ------------------------------------------------------------

DATASET_PATH = os.path.join(
    PROJECT_ROOT,
    "datasets",
    "fused_knowledge_dataset.csv"
)


print("\nDataset path:")
print(DATASET_PATH)


# ------------------------------------------------------------
# Check whether dataset exists
# ------------------------------------------------------------

if not os.path.exists(DATASET_PATH):
    print("\nERROR: Dataset file not found!")
    print("Please check that this file exists:")
    print(DATASET_PATH)
    exit()


# ------------------------------------------------------------
# Load dataset
# ------------------------------------------------------------

df = pd.read_csv(DATASET_PATH)


# ------------------------------------------------------------
# Dataset successfully loaded
# ------------------------------------------------------------

print("\n" + "=" * 70)
print("DATASET LOADED SUCCESSFULLY")
print("=" * 70)


# ------------------------------------------------------------
# Dataset shape
# ------------------------------------------------------------

print("\n1. DATASET SHAPE")
print("-" * 70)

print("Number of rows:", df.shape[0])
print("Number of columns:", df.shape[1])


# ------------------------------------------------------------
# Column names
# ------------------------------------------------------------

print("\n2. COLUMN NAMES")
print("-" * 70)

for number, column in enumerate(df.columns, start=1):
    print(f"{number}. {column}")


# ------------------------------------------------------------
# Data types
# ------------------------------------------------------------

print("\n3. DATA TYPES")
print("-" * 70)

print(df.dtypes)


# ------------------------------------------------------------
# First 5 records
# ------------------------------------------------------------

print("\n4. FIRST 5 RECORDS")
print("-" * 70)

print(df.head())


# ------------------------------------------------------------
# Last 5 records
# ------------------------------------------------------------

print("\n5. LAST 5 RECORDS")
print("-" * 70)

print(df.tail())


# ------------------------------------------------------------
# Dataset information
# ------------------------------------------------------------

print("\n6. DATASET INFORMATION")
print("-" * 70)

df.info()


# ------------------------------------------------------------
# Missing values
# ------------------------------------------------------------

print("\n7. MISSING VALUES")
print("-" * 70)

missing_values = df.isnull().sum()

print(missing_values)


# ------------------------------------------------------------
# Duplicate records
# ------------------------------------------------------------

print("\n8. DUPLICATE RECORDS")
print("-" * 70)

duplicates = df.duplicated().sum()

print("Number of duplicate rows:", duplicates)


# ------------------------------------------------------------
# Statistical summary
# ------------------------------------------------------------

print("\n9. STATISTICAL SUMMARY")
print("-" * 70)

print(df.describe(include="all"))


# ------------------------------------------------------------
# Unique values
# ------------------------------------------------------------

print("\n10. UNIQUE VALUES PER COLUMN")
print("-" * 70)

for column in df.columns:
    print(f"{column}: {df[column].nunique()} unique values")


# ------------------------------------------------------------
# End
# ------------------------------------------------------------

print("\n" + "=" * 70)
print("STEP 1 COMPLETED")
print("=" * 70)