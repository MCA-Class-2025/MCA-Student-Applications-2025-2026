from pathlib import Path
import pandas as pd

# ---------------------------------------------------------
# FOLDERS
# ---------------------------------------------------------

DATA_DIR = Path("data")
OUTPUT_DIR = Path("cleaned_data")

OUTPUT_DIR.mkdir(exist_ok=True)


# ---------------------------------------------------------
# FIND MUMBAI AND PUNE FILES AUTOMATICALLY
# ---------------------------------------------------------

csv_files = list(DATA_DIR.glob("*.csv"))

mumbai_file = None
pune_file = None

for file in csv_files:

    name = file.name.lower()

    if "mum" in name or "mumbai" in name:
        mumbai_file = file

    elif "pune" in name:
        pune_file = file


if mumbai_file is None:
    print("Mumbai CSV file not found.")

if pune_file is None:
    print("Pune CSV file not found.")


# ---------------------------------------------------------
# COLUMNS WE WANT
# ---------------------------------------------------------

KEEP_COLUMNS = [
    "Station ID",
    "State",
    "City",
    "Station Name",
    "Timestamp",

    "PM2.5 (µg/m³)",
    "PM10 (µg/m³)",
    "NO2 (µg/m³)",
    "NH3 (µg/m³)",
    "SO2 (µg/m³)",
    "CO (mg/m³)",
    "Ozone (µg/m³)",

    "AT (°C)",
    "RH (%)",
    "WS (m/s)",
    "WD (deg)",
    "RF (mm)",
    "SR (W/mt2)"
]


# ---------------------------------------------------------
# CLEANING FUNCTION
# ---------------------------------------------------------

def clean_dataset(file, city_name):

    print("\n" + "=" * 80)
    print("CLEANING:", city_name)
    print("=" * 80)

    df = pd.read_csv(
        file,
        low_memory=False
    )

    print("Original rows:", len(df))

    # Remove completely empty rows
    df = df.dropna(how="all").copy()

    # -----------------------------------------------------
    # TIMESTAMP
    # -----------------------------------------------------

    df["Timestamp"] = pd.to_datetime(
        df["Timestamp"],
        errors="coerce",
        utc=True
    )

    invalid_timestamp = df["Timestamp"].isna().sum()

    print(
        "Invalid timestamps removed:",
        invalid_timestamp
    )

    df = df.dropna(
        subset=["Timestamp"]
    ).copy()

    # -----------------------------------------------------
    # KEEP REQUIRED COLUMNS
    # -----------------------------------------------------

    available_columns = [
        column
        for column in KEEP_COLUMNS
        if column in df.columns
    ]

    df = df[available_columns].copy()

    # Set city explicitly
    df["City"] = city_name

    # -----------------------------------------------------
    # SORT
    # -----------------------------------------------------

    df = df.sort_values(
        "Timestamp"
    ).reset_index(drop=True)

    # -----------------------------------------------------
    # DUPLICATES
    # -----------------------------------------------------

    duplicate_count = df.duplicated(
        subset=["Timestamp"]
    ).sum()

    print(
        "Duplicate timestamps:",
        duplicate_count
    )

    df = df.drop_duplicates(
        subset=["Timestamp"],
        keep="first"
    ).reset_index(drop=True)

    # -----------------------------------------------------
    # MISSING VALUES
    # -----------------------------------------------------

    print("\nMissing values:")

    print(
        df.isnull()
        .sum()
        .to_string()
    )

    # -----------------------------------------------------
    # DATE RANGE
    # -----------------------------------------------------

    print("\nTime range:")

    print(
        "Start:",
        df["Timestamp"].min()
    )

    print(
        "End:",
        df["Timestamp"].max()
    )

    # -----------------------------------------------------
    # FINAL ROW COUNT
    # -----------------------------------------------------

    print(
        "\nRows after cleaning:",
        len(df)
    )

    # -----------------------------------------------------
    # SAVE
    # -----------------------------------------------------

    output_file = (
        OUTPUT_DIR /
        f"{city_name.lower()}_cleaned.csv"
    )

    df.to_csv(
        output_file,
        index=False
    )

    print(
        "\nSaved:",
        output_file
    )

    return df


# ---------------------------------------------------------
# PROCESS DATASETS
# ---------------------------------------------------------

datasets = []


if mumbai_file is not None:

    mumbai_df = clean_dataset(
        mumbai_file,
        "Mumbai"
    )

    datasets.append(mumbai_df)


if pune_file is not None:

    pune_df = clean_dataset(
        pune_file,
        "Pune"
    )

    datasets.append(pune_df)


# ---------------------------------------------------------
# COMBINE MUMBAI + PUNE
# ---------------------------------------------------------

if datasets:

    combined = pd.concat(
        datasets,
        ignore_index=True
    )

    combined = combined.sort_values(
        ["City", "Timestamp"]
    ).reset_index(drop=True)

    combined_file = (
        OUTPUT_DIR /
        "maharashtra_pune_mumbai_cleaned.csv"
    )

    combined.to_csv(
        combined_file,
        index=False
    )

    print("\n" + "=" * 80)
    print("COMBINED DATASET")
    print("=" * 80)

    print(
        "Rows:",
        len(combined)
    )

    print(
        "Columns:",
        len(combined.columns)
    )

    print(
        "Cities:",
        combined["City"]
        .unique()
        .tolist()
    )

    print(
        "Saved:",
        combined_file
    )

    print("\n" + "=" * 80)
    print("CLEANING COMPLETE")
    print("=" * 80)

else:

    print("\nNo historical datasets were processed.")