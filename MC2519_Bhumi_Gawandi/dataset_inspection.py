"""
AI SMART EXPENSE TRACKER
PART A-E DATASET INSPECTION

This script ONLY READS your datasets.
It does NOT modify or delete the original datasets.

Project structure:

AI_SMART_EXPENSE/
│
├── ml/
│   └── dataset/
│       ├── original/
│       ├── external/
│       ├── optional/
│       ├── processed/
│       ├── inspection/
│       ├── *.csv
│       └── *.txt
│
└── dataset_inspection.py

Run:

    py dataset_inspection.py
"""

from pathlib import Path
import pandas as pd
import numpy as np


# ============================================================
# 1. PROJECT PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

# IMPORTANT:
# Your actual datasets are inside ml/dataset
DATASET_DIR = BASE_DIR / "ml" / "dataset"

# Inspection results will be saved here
OUTPUT_DIR = DATASET_DIR / "inspection"

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# ============================================================
# 2. DATASET LOCATIONS
# ============================================================

DATASET_PATHS = {

    # --------------------------------------------------------
    # ORIGINAL DATASETS
    # --------------------------------------------------------

    "Datafiniti Electronics Original":
        DATASET_DIR
        / "original"
        / "DatafinitiElectronicsProductsPricingData.csv",

    "Historic Groceries Original":
        DATASET_DIR
        / "original"
        / "historic_groceries.csv",

    "Retail Transactions":
        DATASET_DIR
        / "original"
        / "Retail_Transaction_Dataset.csv",


    # --------------------------------------------------------
    # EXTERNAL DATASET
    # --------------------------------------------------------

    "Current Electronics External":
        DATASET_DIR
        / "external"
        / "electronics_dataset.csv",


    # --------------------------------------------------------
    # PROCESSED DATASETS
    # --------------------------------------------------------

    "Electronics Price History":
        DATASET_DIR
        / "processed"
        / "electronics_price_history.csv",

    "Grocery Price History":
        DATASET_DIR
        / "processed"
        / "grocery_price_history.csv",


    # --------------------------------------------------------
    # EXISTING PROJECT DATASETS
    # --------------------------------------------------------

    "Monthly Expenses":
        DATASET_DIR
        / "monthly_expenses.csv",

    "Anomaly Results":
        DATASET_DIR
        / "anomaly_results.csv",

    "Personal Finance":
        DATASET_DIR
        / "personal_finance.csv",

    "API Currency":
        DATASET_DIR
        / "api_currency.csv",

    "API Exchange Rate":
        DATASET_DIR
        / "api_exchange_rate.csv",

    "API Groq":
        DATASET_DIR
        / "api_groq.csv",

    "API News":
        DATASET_DIR
        / "api_news.csv",

    "API OCR":
        DATASET_DIR
        / "api_ocr.csv",


    # --------------------------------------------------------
    # OPTIONAL DATASET
    # --------------------------------------------------------

    "Household Power Consumption":
        DATASET_DIR
        / "optional"
        / "household_power_consumption.txt",
}


# ============================================================
# 3. FILE LOADING FUNCTIONS
# ============================================================

def load_csv(file_path):
    """
    Safely load CSV using multiple encodings.
    """

    encodings = [
        "utf-8",
        "utf-8-sig",
        "cp1252",
        "latin1"
    ]

    last_error = None

    for encoding in encodings:

        try:

            df = pd.read_csv(
                file_path,
                encoding=encoding,
                low_memory=False
            )

            return df

        except Exception as error:

            last_error = error

    raise last_error


def load_household_power(file_path):
    """
    Load household power consumption TXT file.

    The standard dataset uses semicolon separation.
    """

    try:

        df = pd.read_csv(
            file_path,
            sep=";",
            encoding="latin1",
            low_memory=False,
            na_values=["?", "NA", "N/A"]
        )

        return df

    except Exception as error:

        print(
            f"Could not load household dataset: {error}"
        )

        return None


def load_dataset(file_path):
    """
    Load dataset based on extension.
    """

    extension = file_path.suffix.lower()

    if extension == ".csv":

        return load_csv(file_path)

    elif extension == ".txt":

        return load_household_power(file_path)

    else:

        raise ValueError(
            f"Unsupported file type: {extension}"
        )


# ============================================================
# 4. COLUMN NAME CLEANING
# ============================================================

def normalize_column_name(column):
    """
    Normalize column names ONLY for comparison.

    Original dataset is never changed.
    """

    value = str(column).strip().lower()

    replacements = {
        " ": "_",
        "-": "_",
        "/": "_",
        "\\": "_",
        "(": "",
        ")": "",
        "%": "percent",
        ".": "_",
    }

    for old, new in replacements.items():

        value = value.replace(
            old,
            new
        )

    return value


# ============================================================
# 5. BASIC INFORMATION
# ============================================================

def get_basic_information(df):

    rows = df.shape[0]
    columns = df.shape[1]

    duplicate_rows = int(
        df.duplicated().sum()
    )

    total_missing = int(
        df.isna().sum().sum()
    )

    memory_mb = round(
        df.memory_usage(
            deep=True
        ).sum()
        / (1024 ** 2),
        2
    )

    return {

        "rows": rows,

        "columns": columns,

        "duplicate_rows":
            duplicate_rows,

        "missing_cells":
            total_missing,

        "memory_mb":
            memory_mb,
    }


# ============================================================
# 6. MISSING VALUE ANALYSIS
# ============================================================

def get_missing_information(df):

    missing_count = df.isna().sum()

    if len(df) > 0:

        missing_percent = (
            missing_count
            / len(df)
            * 100
        )

    else:

        missing_percent = missing_count

    result = pd.DataFrame({

        "Column":
            df.columns,

        "Missing_Count":
            missing_count.values,

        "Missing_Percentage":
            missing_percent.round(2).values,

    })

    result = result.sort_values(
        by="Missing_Count",
        ascending=False
    )

    return result


# ============================================================
# 7. DATA TYPE INFORMATION
# ============================================================

def get_data_type_information(df):

    rows = []

    for column in df.columns:

        rows.append({

            "Column":
                column,

            "Data_Type":
                str(df[column].dtype),

            "Unique_Values":
                int(
                    df[column]
                    .nunique(
                        dropna=True
                    )
                ),

            "Missing_Values":
                int(
                    df[column]
                    .isna()
                    .sum()
                ),

        })

    return pd.DataFrame(rows)


# ============================================================
# 8. NUMERIC STATISTICS
# ============================================================

def get_numeric_statistics(df):

    numeric_df = df.select_dtypes(
        include=np.number
    )

    if numeric_df.empty:

        return pd.DataFrame()

    statistics = numeric_df.describe().T

    statistics["missing"] = (
        numeric_df.isna().sum()
    )

    statistics["unique"] = (
        numeric_df.nunique()
    )

    return statistics


# ============================================================
# 9. DATE COLUMN DETECTION
# ============================================================

def detect_date_columns(df):

    keywords = [

        "date",

        "time",

        "timestamp",

        "created",

        "updated",

        "transaction",

        "datetime",

        "year",

        "month",

        "seen",

        "scraped",

    ]

    detected = []

    for column in df.columns:

        normalized = normalize_column_name(
            column
        )

        if any(
            keyword in normalized
            for keyword in keywords
        ):

            detected.append(
                column
            )

    return detected


# ============================================================
# 10. POTENTIAL FUSION KEY DETECTION
# ============================================================

def detect_fusion_candidates(df):

    keywords = [

        "id",

        "product",

        "name",

        "title",

        "brand",

        "category",

        "merchant",

        "seller",

        "sku",

        "model",

        "customer",

        "store",

        "currency",

        "price",

        "date",

    ]

    candidates = []

    for column in df.columns:

        normalized = normalize_column_name(
            column
        )

        if any(
            keyword in normalized
            for keyword in keywords
        ):

            candidates.append(
                column
            )

    return candidates


# ============================================================
# 11. DATASET REPORT
# ============================================================

def print_dataset_report(
    dataset_name,
    file_path,
    df
):

    print("\n")
    print("=" * 90)

    print(
        f"DATASET: {dataset_name}"
    )

    print(
        f"FILE: {file_path}"
    )

    print("=" * 90)


    # --------------------------------------------------------
    # BASIC
    # --------------------------------------------------------

    basic = get_basic_information(df)

    print("\n--- BASIC INFORMATION ---")

    print(
        f"Rows              : "
        f"{basic['rows']:,}"
    )

    print(
        f"Columns           : "
        f"{basic['columns']:,}"
    )

    print(
        f"Duplicate rows    : "
        f"{basic['duplicate_rows']:,}"
    )

    print(
        f"Missing cells     : "
        f"{basic['missing_cells']:,}"
    )

    print(
        f"Memory usage      : "
        f"{basic['memory_mb']} MB"
    )


    # --------------------------------------------------------
    # COLUMNS
    # --------------------------------------------------------

    print("\n--- COLUMNS ---")

    for number, column in enumerate(
        df.columns,
        start=1
    ):

        print(
            f"{number:>3}. {column}"
        )


    # --------------------------------------------------------
    # DATA TYPES
    # --------------------------------------------------------

    print("\n--- DATA TYPES ---")

    type_info = (
        get_data_type_information(df)
    )

    print(
        type_info.to_string(
            index=False
        )
    )


    # --------------------------------------------------------
    # MISSING VALUES
    # --------------------------------------------------------

    print("\n--- MISSING VALUES ---")

    missing = (
        get_missing_information(df)
    )

    missing_nonzero = missing[
        missing["Missing_Count"] > 0
    ]

    if missing_nonzero.empty:

        print(
            "No missing values found."
        )

    else:

        print(
            missing_nonzero.to_string(
                index=False
            )
        )


    # --------------------------------------------------------
    # NUMERIC STATISTICS
    # --------------------------------------------------------

    print(
        "\n--- NUMERIC STATISTICS ---"
    )

    numeric_statistics = (
        get_numeric_statistics(df)
    )

    if numeric_statistics.empty:

        print(
            "No numeric columns found."
        )

    else:

        print(
            numeric_statistics
            .round(3)
            .to_string()
        )


    # --------------------------------------------------------
    # DATE COLUMNS
    # --------------------------------------------------------

    print(
        "\n--- POSSIBLE DATE COLUMNS ---"
    )

    date_columns = (
        detect_date_columns(df)
    )

    if date_columns:

        for column in date_columns:

            print(
                f"- {column}"
            )

    else:

        print(
            "No obvious date columns detected."
        )


    # --------------------------------------------------------
    # FUSION CANDIDATES
    # --------------------------------------------------------

    print(
        "\n--- POTENTIAL FUSION KEY CANDIDATES ---"
    )

    candidates = (
        detect_fusion_candidates(df)
    )

    if candidates:

        for column in candidates:

            print(
                f"- {column}"
            )

    else:

        print(
            "No obvious fusion candidates."
        )


    # --------------------------------------------------------
    # FIRST 5 ROWS
    # --------------------------------------------------------

    print(
        "\n--- FIRST 5 RECORDS ---"
    )

    try:

        print(
            df.head(5)
            .to_string(
                index=False
            )
        )

    except Exception:

        print(
            "Unable to display sample."
        )


# ============================================================
# 12. SAVE DATASET REPORTS
# ============================================================

def save_dataset_reports(
    dataset_name,
    df
):

    safe_name = (
        dataset_name
        .replace(" ", "_")
        .replace("/", "_")
        .replace("\\", "_")
    )


    # --------------------------------------------------------
    # Missing values
    # --------------------------------------------------------

    missing_file = (
        OUTPUT_DIR
        / f"{safe_name}_missing_values.csv"
    )

    get_missing_information(
        df
    ).to_csv(
        missing_file,
        index=False
    )


    # --------------------------------------------------------
    # Data types
    # --------------------------------------------------------

    types_file = (
        OUTPUT_DIR
        / f"{safe_name}_data_types.csv"
    )

    get_data_type_information(
        df
    ).to_csv(
        types_file,
        index=False
    )


    # --------------------------------------------------------
    # Numeric statistics
    # --------------------------------------------------------

    numeric_file = (
        OUTPUT_DIR
        / f"{safe_name}_numeric_statistics.csv"
    )

    numeric_statistics = (
        get_numeric_statistics(df)
    )

    if not numeric_statistics.empty:

        numeric_statistics.to_csv(
            numeric_file
        )


    # --------------------------------------------------------
    # Sample
    # --------------------------------------------------------

    sample_file = (
        OUTPUT_DIR
        / f"{safe_name}_sample.csv"
    )

    df.head(10).to_csv(
        sample_file,
        index=False
    )


# ============================================================
# 13. GLOBAL DATASET SUMMARY
# ============================================================

def create_global_summary(results):

    if not results:

        return

    summary = pd.DataFrame(
        results
    )

    output_file = (
        OUTPUT_DIR
        / "dataset_summary.csv"
    )

    summary.to_csv(
        output_file,
        index=False
    )

    print("\n")
    print("=" * 90)
    print("GLOBAL DATASET SUMMARY")
    print("=" * 90)

    print(
        summary.to_string(
            index=False
        )
    )

    print(
        f"\nSaved to:"
        f"\n{output_file}"
    )


# ============================================================
# 14. COLUMN COMPARISON
# ============================================================

def create_column_comparison(
    dataset_frames
):

    rows = []

    for dataset_name, df in (
        dataset_frames.items()
    ):

        for column in df.columns:

            rows.append({

                "Dataset":
                    dataset_name,

                "Original_Column":
                    column,

                "Normalized_Column":
                    normalize_column_name(
                        column
                    ),

            })

    if not rows:

        return

    comparison = pd.DataFrame(
        rows
    )

    output_file = (
        OUTPUT_DIR
        / "column_comparison.csv"
    )

    comparison.to_csv(
        output_file,
        index=False
    )

    print(
        f"\nColumn comparison saved to:"
        f"\n{output_file}"
    )


# ============================================================
# 15. FIND COMMON COLUMNS
# ============================================================

def find_common_columns(
    dataset_frames
):

    column_map = {}

    for dataset_name, df in (
        dataset_frames.items()
    ):

        for column in df.columns:

            normalized = (
                normalize_column_name(
                    column
                )
            )

            if normalized not in column_map:

                column_map[
                    normalized
                ] = []

            column_map[
                normalized
            ].append(
                (
                    dataset_name,
                    column
                )
            )


    common_columns = {

        normalized:
            values

        for normalized, values
        in column_map.items()

        if len(values) >= 2

    }


    print("\n")
    print("=" * 90)
    print("COMMON COLUMN CANDIDATES")
    print("=" * 90)


    if not common_columns:

        print(
            "No common column names found."
        )

    else:

        for normalized, values in (
            common_columns.items()
        ):

            print(
                f"\n{normalized}"
            )

            for (
                dataset_name,
                original_column
            ) in values:

                print(
                    f"    "
                    f"{dataset_name}"
                    f" -> "
                    f"{original_column}"
                )


    # --------------------------------------------------------
    # SAVE COMMON COLUMNS
    # --------------------------------------------------------

    rows = []

    for normalized, values in (
        common_columns.items()
    ):

        for (
            dataset_name,
            original_column
        ) in values:

            rows.append({

                "Normalized_Column":
                    normalized,

                "Dataset":
                    dataset_name,

                "Original_Column":
                    original_column,

            })


    if rows:

        common_df = pd.DataFrame(
            rows
        )

        output_file = (
            OUTPUT_DIR
            / "common_columns.csv"
        )

        common_df.to_csv(
            output_file,
            index=False
        )

        print(
            f"\nCommon-column report saved to:"
            f"\n{output_file}"
        )


# ============================================================
# 16. CHECK DATASET DIRECTORY
# ============================================================

def check_dataset_directory():

    print("\n")
    print("=" * 90)
    print("DIRECTORY CHECK")
    print("=" * 90)

    print(
        f"\nProject directory:"
        f"\n{BASE_DIR}"
    )

    print(
        f"\nDataset directory:"
        f"\n{DATASET_DIR}"
    )


    if not DATASET_DIR.exists():

        print(
            "\nERROR:"
            "\nml/dataset folder does not exist."
        )

        return False


    print(
        "\nDataset directory exists."
    )

    return True


# ============================================================
# 17. MAIN
# ============================================================

def main():

    print("\n")
    print("=" * 90)
    print("AI SMART EXPENSE TRACKER")
    print("PART A-E DATASET INSPECTION")
    print("=" * 90)


    # --------------------------------------------------------
    # DIRECTORY CHECK
    # --------------------------------------------------------

    if not check_dataset_directory():

        return


    all_results = []

    dataset_frames = {}


    # --------------------------------------------------------
    # LOAD DATASETS
    # --------------------------------------------------------

    for dataset_name, file_path in (
        DATASET_PATHS.items()
    ):

        print("\n")
        print("-" * 90)

        print(
            f"Checking: {dataset_name}"
        )

        print(
            f"Path: {file_path}"
        )


        # ----------------------------------------------------
        # FILE DOES NOT EXIST
        # ----------------------------------------------------

        if not file_path.exists():

            print(
                "STATUS: NOT FOUND"
            )

            continue


        print(
            "STATUS: FOUND"
        )


        # ----------------------------------------------------
        # LOAD
        # ----------------------------------------------------

        try:

            df = load_dataset(
                file_path
            )

        except Exception as error:

            print(
                "\nERROR while loading:"
            )

            print(error)

            continue


        # ----------------------------------------------------
        # EMPTY DATASET
        # ----------------------------------------------------

        if df is None:

            print(
                "STATUS: FAILED TO LOAD"
            )

            continue


        if df.empty:

            print(
                "WARNING: Dataset is empty."
            )

            continue


        # ----------------------------------------------------
        # STORE
        # ----------------------------------------------------

        dataset_frames[
            dataset_name
        ] = df


        # ----------------------------------------------------
        # PRINT REPORT
        # ----------------------------------------------------

        print_dataset_report(
            dataset_name,
            file_path,
            df
        )


        # ----------------------------------------------------
        # BASIC INFORMATION
        # ----------------------------------------------------

        basic = (
            get_basic_information(
                df
            )
        )


        # ----------------------------------------------------
        # SUMMARY RESULT
        # ----------------------------------------------------

        all_results.append({

            "Dataset":
                dataset_name,

            "File":
                file_path.name,

            "Location":
                str(
                    file_path
                    .relative_to(
                        BASE_DIR
                    )
                ),

            "Rows":
                basic["rows"],

            "Columns":
                basic["columns"],

            "Duplicate_Rows":
                basic[
                    "duplicate_rows"
                ],

            "Missing_Cells":
                basic[
                    "missing_cells"
                ],

            "Memory_MB":
                basic["memory_mb"],

            "Numeric_Columns":
                len(
                    df.select_dtypes(
                        include=np.number
                    ).columns
                ),

            "Date_Column_Candidates":
                len(
                    detect_date_columns(
                        df
                    )
                ),

            "Fusion_Key_Candidates":
                len(
                    detect_fusion_candidates(
                        df
                    )
                ),

        })


        # ----------------------------------------------------
        # SAVE REPORTS
        # ----------------------------------------------------

        save_dataset_reports(
            dataset_name,
            df
        )


    # ========================================================
    # GLOBAL REPORTS
    # ========================================================

    create_global_summary(
        all_results
    )


    create_column_comparison(
        dataset_frames
    )


    find_common_columns(
        dataset_frames
    )


    # ========================================================
    # FINISH
    # ========================================================

    print("\n")
    print("=" * 90)
    print("INSPECTION COMPLETE")
    print("=" * 90)

    print(
        "\nDatasets successfully inspected:"
    )

    print(
        f"{len(dataset_frames)}"
    )

    print(
        "\nInspection reports:"
    )

    print(
        OUTPUT_DIR
    )

    print("\nImportant files generated:")

    print(
        "1. dataset_summary.csv"
    )

    print(
        "2. column_comparison.csv"
    )

    print(
        "3. common_columns.csv"
    )

    print(
        "4. *_missing_values.csv"
    )

    print(
        "5. *_data_types.csv"
    )

    print(
        "6. *_numeric_statistics.csv"
    )

    print(
        "7. *_sample.csv"
    )

    print("\n")
    print("=" * 90)

    print(
        "NEXT STEP:"
    )

    print(
        "Send me the output from this terminal,"
    )

    print(
        "especially the COMMON COLUMN CANDIDATES section."
    )

    print("=" * 90)


# ============================================================
# RUN PROGRAM
# ============================================================

if __name__ == "__main__":

    main()