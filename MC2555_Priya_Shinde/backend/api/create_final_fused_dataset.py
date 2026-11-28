import pandas as pd
from pathlib import Path


# ============================================================
# PHASE 1 - FINAL FUSED DATASET
# PRESENTATION-READY VERSION
# ============================================================

print("=" * 90)
print("PHASE 1 - FINAL FUSED DATASET CREATION")
print("=" * 90)


# ============================================================
# PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

ORIGINAL_FILE = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "ISOT_Fake_Real_News"
    / "Fake.csv"
)

REAL_FILE = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "ISOT_Fake_Real_News"
    / "True.csv"
)

API_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "realtime_api_fusion.csv"
)

OUTPUT_DIR = (
    PROJECT_ROOT
    / "data"
    / "processed"
)

OUTPUT_FILE = OUTPUT_DIR / "fused_dataset_final.csv"


# ============================================================
# DISPLAY PATHS
# ============================================================

print("\nProject root:")
print(PROJECT_ROOT)

print("\nOriginal Fake dataset:")
print(ORIGINAL_FILE)

print("\nOriginal Real dataset:")
print(REAL_FILE)

print("\nRealtime API dataset:")
print(API_FILE)

print("\nFinal output:")
print(OUTPUT_FILE)


# ============================================================
# CHECK FILES
# ============================================================

print("\n" + "=" * 90)
print("CHECKING INPUT FILES")
print("=" * 90)

for file_path in [ORIGINAL_FILE, REAL_FILE, API_FILE]:

    if not file_path.exists():
        raise FileNotFoundError(
            f"\nRequired file not found:\n{file_path}"
        )

    print(f"OK: {file_path.name}")


# ============================================================
# LOAD ORIGINAL DATA
# ============================================================

print("\n" + "=" * 90)
print("LOADING ORIGINAL ISOT DATA")
print("=" * 90)

fake_df = pd.read_csv(ORIGINAL_FILE, low_memory=False)
real_df = pd.read_csv(REAL_FILE, low_memory=False)

print(f"Fake records : {len(fake_df)}")
print(f"Real records : {len(real_df)}")


# ============================================================
# ADD LABELS
# ============================================================

fake_df["label"] = "Fake"
real_df["label"] = "Real"


# ============================================================
# COMBINE ORIGINAL DATA
# ============================================================

original_df = pd.concat(
    [fake_df, real_df],
    ignore_index=True
)

print(f"\nCombined original records: {len(original_df)}")


# ============================================================
# PREPARE ORIGINAL DATA
# ============================================================

print("\n" + "=" * 90)
print("PREPARING ORIGINAL DATA")
print("=" * 90)

# Standardize column names
original_df.columns = [
    str(col).strip().lower()
    for col in original_df.columns
]

# Create presentation columns
original_clean = pd.DataFrame()

original_clean["record_type"] = "ORIGINAL"

original_clean["record_id"] = range(
    1,
    len(original_df) + 1
)

original_clean["title"] = (
    original_df["title"]
    .fillna("")
    .astype(str)
    .str.strip()
)

original_clean["content"] = (
    original_df["text"]
    .fillna("")
    .astype(str)
    .str.strip()
)

original_clean["category"] = (
    original_df["subject"]
    .fillna("")
    .astype(str)
    .str.strip()
)

original_clean["source"] = "ISOT"

original_clean["date"] = (
    original_df["date"]
    .fillna("")
    .astype(str)
    .str.strip()
)

# Original ISOT dataset does not contain article URLs
original_clean["url"] = ""


# ============================================================
# LOAD API DATA
# ============================================================

print("\n" + "=" * 90)
print("LOADING REAL-TIME API DATA")
print("=" * 90)

api_df = pd.read_csv(
    API_FILE,
    low_memory=False
)

print(f"API records: {len(api_df)}")

print("\nAPI columns:")
print(list(api_df.columns))


# ============================================================
# PREPARE API DATA
# ============================================================

print("\n" + "=" * 90)
print("PREPARING API DATA")
print("=" * 90)

api_clean = pd.DataFrame()

api_clean["record_type"] = "API"

# API record IDs are explicitly marked
api_clean["record_id"] = [
    f"API_{i:04d}"
    for i in range(1, len(api_df) + 1)
]

api_clean["title"] = (
    api_df["title"]
    .fillna("")
    .astype(str)
    .str.strip()
)

api_clean["content"] = (
    api_df["description"]
    .fillna("")
    .astype(str)
    .str.strip()
)

# API data does not have the ISOT subject/category field
api_clean["category"] = "News"

# IMPORTANT:
# Use the API provider name from the "api" column.
# Example: GNews, NewsAPI, Currents, etc.
api_clean["source"] = (
    api_df["api"]
    .fillna("Unknown API")
    .astype(str)
    .str.strip()
)

api_clean["date"] = (
    api_df["published"]
    .fillna("")
    .astype(str)
    .str.strip()
)

api_clean["url"] = (
    api_df["url"]
    .fillna("")
    .astype(str)
    .str.strip()
)


# ============================================================
# CLEAN API SOURCE NAMES
# ============================================================

print("\n" + "=" * 90)
print("API SOURCE DISTRIBUTION")
print("=" * 90)

# Standardize known provider names
api_source_mapping = {
    "gnews": "GNews",
    "newsapi": "NewsAPI",
    "currents": "Currents",
    "newsdata.io": "NewsData.io",
    "thenewsapi": "TheNewsAPI",
    "google news rss": "Google News RSS",
}

api_clean["source"] = (
    api_clean["source"]
    .str.strip()
    .map(
        lambda x: api_source_mapping.get(
            x.lower(),
            x
        )
    )
)

print(
    api_clean["source"]
    .value_counts()
    .to_string()
)


# ============================================================
# CREATE FUSED DATASET
# ============================================================

print("\n" + "=" * 90)
print("CREATING FINAL FUSED DATASET")
print("=" * 90)

fused = pd.concat(
    [
        original_clean,
        api_clean
    ],
    ignore_index=True
)


# ============================================================
# CREATE FUSED IDS
# ============================================================

fused["fused_id"] = [
    f"FUSED_{i:05d}"
    for i in range(1, len(fused) + 1)
]


# ============================================================
# FINAL COLUMN ORDER
# ============================================================

fused = fused[
    [
        "fused_id",
        "record_type",
        "record_id",
        "title",
        "content",
        "category",
        "source",
        "date",
        "url",
    ]
]


# ============================================================
# REMOVE COMPLETELY EMPTY VALUES
# ============================================================

for column in fused.columns:

    fused[column] = (
        fused[column]
        .fillna("")
        .astype(str)
        .str.strip()
    )


# ============================================================
# VALIDATION
# ============================================================

print("\n" + "=" * 90)
print("FINAL DATASET VALIDATION")
print("=" * 90)

print(f"\nTotal records       : {len(fused)}")
print(f"Total attributes    : {len(fused.columns)}")

print("\nRecord type distribution:")
print(
    fused["record_type"]
    .value_counts()
    .to_string()
)

print("\nSource distribution:")
print(
    fused["source"]
    .value_counts()
    .head(20)
    .to_string()
)

print("\nDuplicate rows:")
print(
    fused.duplicated().sum()
)

print("\nDuplicate fused IDs:")
print(
    fused["fused_id"].duplicated().sum()
)

print("\nDuplicate record IDs:")
print(
    fused["record_id"].duplicated().sum()
)


# ============================================================
# EMPTY VALUE ANALYSIS
# ============================================================

print("\n" + "=" * 90)
print("EMPTY VALUE ANALYSIS")
print("=" * 90)

for column in fused.columns:

    empty_count = (
        fused[column]
        .astype(str)
        .str.strip()
        .eq("")
        .sum()
    )

    percentage = (
        empty_count / len(fused)
    ) * 100

    print(
        f"{column:<15} "
        f"empty = {empty_count:<7} "
        f"({percentage:.2f}%)"
    )


# ============================================================
# SAVE
# ============================================================

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)

fused.to_csv(
    OUTPUT_FILE,
    index=False,
    encoding="utf-8-sig"
)


# ============================================================
# FINAL CHECK
# ============================================================

print("\n" + "=" * 90)
print("FINAL OUTPUT")
print("=" * 90)

print(f"\nSaved successfully:")
print(OUTPUT_FILE)

print(f"\nRows    : {len(fused)}")
print(f"Columns : {len(fused.columns)}")

print("\nColumns:")
for column in fused.columns:
    print(f" - {column}")


# ============================================================
# SHOW API SAMPLE
# ============================================================

print("\n" + "=" * 90)
print("SAMPLE API RECORDS")
print("=" * 90)

api_sample = fused[
    fused["record_type"] == "API"
].head(5)

print(
    api_sample[
        [
            "fused_id",
            "record_type",
            "record_id",
            "title",
            "source",
            "date",
            "url",
        ]
    ].to_string(index=False)
)


# ============================================================
# SHOW ORIGINAL SAMPLE
# ============================================================

print("\n" + "=" * 90)
print("SAMPLE ORIGINAL RECORDS")
print("=" * 90)

original_sample = fused[
    fused["record_type"] == "ORIGINAL"
].head(3)

print(
    original_sample[
        [
            "fused_id",
            "record_type",
            "record_id",
            "title",
            "category",
            "source",
            "date",
        ]
    ].to_string(index=False)
)


print("\n" + "=" * 90)
print("FINAL FUSED DATASET CREATED SUCCESSFULLY")
print("=" * 90)