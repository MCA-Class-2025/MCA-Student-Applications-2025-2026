import pandas as pd
import os
import glob


# =========================================================
# CONFIGURATION
# =========================================================

# Fused CSV location
FUSED_FOLDER = "api_data"

# Output file
OUTPUT_FILE = "data_fusion/cleaned_waste_dataset.csv"


# =========================================================
# FIND FUSED CSV
# =========================================================

print("\n========================================")
print("       DATA CLEANING STARTED")
print("========================================")


# Find CSV files inside data_fusion folder
csv_files = glob.glob(
    os.path.join(FUSED_FOLDER, "*.csv")
)

# Do not use already cleaned file
csv_files = [
    file for file in csv_files
    if "cleaned_waste_dataset" not in file.lower()
]


if not csv_files:

    print("\nERROR: No CSV file found inside data_fusion folder.")

    print("\nPlease make sure your fused CSV is inside:")
    print("data_fusion/")

    exit()


# Select the first CSV
INPUT_FILE = csv_files[0]


print("\nFused dataset found:")
print(INPUT_FILE)


# =========================================================
# LOAD DATASET
# =========================================================

df = pd.read_csv(
    INPUT_FILE
)


print("\nOriginal dataset information:")
print("----------------------------------------")

print(
    f"Rows    : {len(df)}"
)

print(
    f"Columns : {len(df.columns)}"
)


# =========================================================
# DISPLAY ORIGINAL COLUMNS
# =========================================================

print("\nOriginal columns:")

for i, column in enumerate(df.columns, start=1):

    print(
        f"{i}. {column}"
    )


# =========================================================
# STANDARDIZE COLUMN NAMES
# =========================================================

print("\nStandardizing column names...")

df.columns = (
    df.columns
    .str.strip()
    .str.replace(" ", "_")
    .str.replace("/", "_")
    .str.replace("-", "_")
)


# =========================================================
# REMOVE COMPLETELY EMPTY COLUMNS
# =========================================================

print("\nChecking empty columns...")

empty_columns = []

for column in df.columns:

    if df[column].isna().all():

        empty_columns.append(
            column
        )


if empty_columns:

    print(
        "Removing completely empty columns:"
    )

    for column in empty_columns:

        print(
            f" - {column}"
        )

    df = df.drop(
        columns=empty_columns
    )

else:

    print(
        "No completely empty columns found."
    )


# =========================================================
# REMOVE DUPLICATE ROWS
# =========================================================

print("\nChecking duplicate rows...")

duplicate_count = df.duplicated().sum()


print(
    f"Duplicate rows found: {duplicate_count}"
)


if duplicate_count > 0:

    df = df.drop_duplicates(
        keep="first"
    ).reset_index(drop=True)

    print(
        "Duplicate rows removed."
    )

else:

    print(
        "No duplicate rows found."
    )


# =========================================================
# CLEAN STRING VALUES
# =========================================================

print("\nCleaning text values...")

for column in df.select_dtypes(
    include=["object"]
).columns:

    df[column] = (
        df[column]
        .astype(str)
        .str.strip()
    )


# Convert common fake missing values to real NaN
missing_values = [
    "",
    " ",
    "nan",
    "NaN",
    "None",
    "none",
    "NULL",
    "null",
    "N/A",
    "n/a",
    "-"
]


df = df.replace(
    missing_values,
    pd.NA
)


# =========================================================
# CONVERT NUMERIC COLUMNS
# =========================================================

print("\nConverting numeric columns...")


numeric_keywords = [

    "Latitude",
    "Longitude",

    "Temperature",
    "Feels_Like",
    "Minimum_Temperature",
    "Maximum_Temperature",

    "Pressure",
    "Humidity",
    "Visibility",

    "Wind",
    "Rain",
    "Cloud",

    "PM10",
    "PM2_5",

    "Carbon_Monoxide",
    "Carbon_Dioxide",

    "Nitrogen_Dioxide",
    "Sulphur_Dioxide",
    "Ozone",

    "Dust",
    "UV_Index",

    "AQI",

    "Distance",

    "Facility_Count",

    "Precipitation",

    "Gust"
]


for column in df.columns:

    for keyword in numeric_keywords:

        if keyword.lower() in column.lower():

            df[column] = pd.to_numeric(
                df[column],
                errors="coerce"
            )

            break


# =========================================================
# HANDLE MISSING NUMERIC VALUES
# =========================================================

print("\nHandling missing numeric values...")


numeric_columns = df.select_dtypes(
    include=["number"]
).columns


for column in numeric_columns:

    if df[column].isna().sum() > 0:

        median_value = df[column].median()

        if pd.notna(median_value):

            df[column] = df[column].fillna(
                median_value
            )


# =========================================================
# HANDLE MISSING TEXT VALUES
# =========================================================

print("\nHandling missing text values...")


text_columns = df.select_dtypes(
    include=["object"]
).columns


for column in text_columns:

    df[column] = df[column].fillna(
        "Unknown"
    )


# =========================================================
# REMOVE INVALID COORDINATES
# =========================================================

print("\nChecking geographical coordinates...")


if "Latitude" in df.columns:

    df.loc[
        (df["Latitude"] < -90) |
        (df["Latitude"] > 90),
        "Latitude"
    ] = pd.NA


if "Longitude" in df.columns:

    df.loc[
        (df["Longitude"] < -180) |
        (df["Longitude"] > 180),
        "Longitude"
    ] = pd.NA


# =========================================================
# RESET INDEX
# =========================================================

df = df.reset_index(
    drop=True
)


# =========================================================
# CREATE OUTPUT DIRECTORY
# =========================================================

os.makedirs(
    "data_fusion",
    exist_ok=True
)


# =========================================================
# SAVE CLEANED DATASET
# =========================================================

df.to_csv(
    OUTPUT_FILE,
    index=False
)


# =========================================================
# FINAL REPORT
# =========================================================

print("\n========================================")
print("       DATA CLEANING COMPLETED")
print("========================================")


print(
    f"Original rows      : {len(pd.read_csv(INPUT_FILE))}"
)

print(
    f"Cleaned rows       : {len(df)}"
)

print(
    f"Cleaned columns    : {len(df.columns)}"
)

print(
    f"Output saved at    : {OUTPUT_FILE}"
)


# =========================================================
# SHOW FIRST 5 RECORDS
# =========================================================

print("\nFirst 5 cleaned records:")

print(
    df.head()
)


# =========================================================
# SHOW FINAL COLUMNS
# =========================================================

print("\nFinal columns:")

for i, column in enumerate(
    df.columns,
    start=1
):

    print(
        f"{i}. {column}"
    )


print(
    "\n✅ Cleaned waste dataset created successfully!"
)