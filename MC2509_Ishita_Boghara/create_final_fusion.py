import pandas as pd
import os

STATIC_FILE = "data/books.csv"
API_FILE = "data/BookMuse_Data_Fusion.xlsx"
OUTPUT_FILE = "data/final_fused_dataset.csv"
OUTPUT_EXCEL = "data/Final_Fused_Dataset.xlsx"


# ============================================================
# LOAD DATASETS
# ============================================================

static_df = pd.read_csv(STATIC_FILE)
api_df = pd.read_excel(API_FILE)


# ============================================================
# CREATE NORMALIZED TITLE FOR MATCHING
# ============================================================

static_df["match_title"] = static_df["title"].astype(str).str.strip().str.lower()

api_df["match_title"] = api_df["title"].astype(str).str.strip().str.lower()


# ============================================================
# REMOVE DUPLICATE MATCH TITLES FROM API DATA
# ============================================================

api_df = api_df.drop_duplicates(subset=["match_title"], keep="last")


# ============================================================
# KEEP API COLUMNS EXCEPT ORIGINAL TITLE
# ============================================================

api_columns = [
    "match_title",
    "summary",
    "summary_source",
    "author",
    "author_source",
    "first_publish_year",
    "first_publish_year_source",
    "isbn",
    "isbn_source",
    "languages",
    "languages_source",
    "download_count",
    "download_count_source",
    "subjects",
    "subjects_source",
    "publication_date",
    "publication_date_source",
    "internet_archive_id",
    "internet_archive_id_source",
    "archive_author",
    "archive_author_source",
    "archive_publication_date",
    "archive_publication_date_source",
    "archive_language",
    "archive_language_source",
    "successful_sources",
    "source_count",
]

api_df = api_df[api_columns]


# ============================================================
# FUSE DATASETS
# LEFT JOIN = KEEP ALL 6810 ORIGINAL RECORDS
# ============================================================

final_df = static_df.merge(api_df, on="match_title", how="left")


# ============================================================
# ADD FUSION STATUS
# ============================================================

final_df["api_data_available"] = final_df["source_count"].notna()


# ============================================================
# REMOVE TEMPORARY MATCH COLUMN
# ============================================================

final_df = final_df.drop(columns=["match_title"])


# ============================================================
# SAVE FINAL DATASET
# ============================================================

os.makedirs("data", exist_ok=True)

final_df.to_csv(OUTPUT_FILE, index=False, encoding="utf-8-sig")

final_df.to_excel(OUTPUT_EXCEL, index=False, sheet_name="Final Fused Dataset")


# ============================================================
# OUTPUT VALIDATION
# ============================================================

print("FINAL FUSION COMPLETED")
print("ROWS:", len(final_df))
print("COLUMNS:", len(final_df.columns))

print("\nAPI ENRICHED RECORDS:")
print(final_df["api_data_available"].sum())

print("\nORIGINAL ONLY RECORDS:")
print((~final_df["api_data_available"]).sum())

print("\nCSV:", OUTPUT_FILE)
print("EXCEL:", OUTPUT_EXCEL)
