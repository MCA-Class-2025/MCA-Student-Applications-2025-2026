from pathlib import Path
import pandas as pd


# ============================================================
# PROJECT PATH
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATA_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "multilingual_fake_news.csv"
)


# ============================================================
# LOAD DATASET
# ============================================================

print("\n==============================================")
print(" MULTILINGUAL FAKE NEWS DATASET ANALYSIS")
print("==============================================")

print("\nLoading dataset...")

df = pd.read_csv(DATA_FILE)

print("Dataset loaded successfully.")


# ============================================================
# BASIC INFORMATION
# ============================================================

print("\n==============================================")
print("BASIC INFORMATION")
print("==============================================")

print("Number of rows:", len(df))
print("Number of columns:", len(df.columns))

print("\nColumns:")

for column in df.columns:
    print("-", column)


# ============================================================
# MISSING VALUES
# ============================================================

print("\n==============================================")
print("MISSING VALUES")
print("==============================================")

missing = df.isnull().sum()

print(missing)


# ============================================================
# DUPLICATE CHECK
# ============================================================

print("\n==============================================")
print("DUPLICATE CHECK")
print("==============================================")

duplicates = df.duplicated(
    subset=["text", "language", "label"]
).sum()

print("Duplicate records:", duplicates)


# ============================================================
# LANGUAGE DISTRIBUTION
# ============================================================

print("\n==============================================")
print("LANGUAGE DISTRIBUTION")
print("==============================================")

language_counts = df["language"].value_counts()

print(language_counts)


# ============================================================
# LABEL DISTRIBUTION
# ============================================================

print("\n==============================================")
print("FAKE / REAL DISTRIBUTION")
print("==============================================")

label_counts = df["label"].value_counts()

print(label_counts)


# ============================================================
# LANGUAGE + LABEL
# ============================================================

print("\n==============================================")
print("LANGUAGE + LABEL DISTRIBUTION")
print("==============================================")

language_label = pd.crosstab(
    df["language"],
    df["label"]
)

print(language_label)


# ============================================================
# SOURCE DISTRIBUTION
# ============================================================

print("\n==============================================")
print("SOURCE DISTRIBUTION")
print("==============================================")

source_counts = df["source"].value_counts()

print(source_counts)


# ============================================================
# TEXT LENGTH
# ============================================================

print("\n==============================================")
print("TEXT LENGTH ANALYSIS")
print("==============================================")

df["text_length"] = df["text"].astype(str).str.len()

print("\nOverall text length:")

print(
    df["text_length"].describe()
)


# ============================================================
# TEXT LENGTH BY LANGUAGE
# ============================================================

print("\n==============================================")
print("TEXT LENGTH BY LANGUAGE")
print("==============================================")

print(
    df.groupby("language")["text_length"]
    .describe()
)


# ============================================================
# TEXT LENGTH BY LABEL
# ============================================================

print("\n==============================================")
print("TEXT LENGTH BY LABEL")
print("==============================================")

print(
    df.groupby("label")["text_length"]
    .describe()
)


# ============================================================
# SHORT TEXT RECORDS
# ============================================================

print("\n==============================================")
print("VERY SHORT RECORDS")
print("==============================================")

short_records = df[
    df["text_length"] < 20
]

print(
    "Records with less than 20 characters:",
    len(short_records)
)


# ============================================================
# EMPTY TEXT
# ============================================================

print("\n==============================================")
print("EMPTY TEXT CHECK")
print("==============================================")

empty_text = (
    df["text"]
    .astype(str)
    .str.strip()
    .eq("")
    .sum()
)

print("Empty text records:", empty_text)


# ============================================================
# FINAL SUMMARY
# ============================================================

print("\n==============================================")
print("FINAL SUMMARY")
print("==============================================")

print("Total records:", len(df))

print(
    "\nLanguages:"
)

print(language_counts)

print(
    "\nLabels:"
)

print(label_counts)

print(
    "\nLanguage + Label:"
)

print(language_label)

print("\n==============================================")
print("ANALYSIS COMPLETED")
print("==============================================")