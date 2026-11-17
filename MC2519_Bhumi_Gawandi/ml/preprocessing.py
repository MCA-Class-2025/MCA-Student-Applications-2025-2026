from pathlib import Path
import pandas as pd
import numpy as np
import ast
import re


# ============================================================
# PROJECT PATHS
# ============================================================

ML_ROOT = Path(__file__).resolve().parent

DATASET_DIR = ML_ROOT / "dataset"

ORIGINAL_DIR = DATASET_DIR / "original"
PROCESSED_DIR = DATASET_DIR / "processed"

ORIGINAL_DIR.mkdir(
    parents=True,
    exist_ok=True
)

PROCESSED_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# ============================================================
# INPUT FILES
# ============================================================

PERSONAL_FINANCE_PATH = (
    DATASET_DIR / "personal_finance.csv"
)

GROCERY_PATH = (
    ORIGINAL_DIR / "historic_groceries.csv"
)

ELECTRONICS_PATH = (
    ORIGINAL_DIR /
    "DatafinitiElectronicsProductsPricingData.csv"
)


# ============================================================
# OUTPUT FILES
# ============================================================

GROCERY_OUTPUT = (
    PROCESSED_DIR /
    "grocery_price_history.csv"
)

ELECTRONICS_OUTPUT = (
    PROCESSED_DIR /
    "electronics_price_history.csv"
)


# ============================================================
# 1. PERSONAL FINANCE DATA
# ============================================================

def load_and_preprocess_personal_finance():

    if not PERSONAL_FINANCE_PATH.exists():

        print(
            "\nPersonal finance file not found:"
        )

        print(
            PERSONAL_FINANCE_PATH
        )

        return None

    df = pd.read_csv(
        PERSONAL_FINANCE_PATH
    )

    print("\n========================================")
    print("PERSONAL FINANCE DATA")
    print("========================================")

    print(
        "Rows:",
        len(df)
    )

    print(
        "Columns:",
        len(df.columns)
    )

    # --------------------------------------------------------
    # DATE FEATURES
    # --------------------------------------------------------

    if "Date" in df.columns:

        df["Date"] = pd.to_datetime(
            df["Date"],
            errors="coerce"
        )

        df["Year"] = (
            df["Date"].dt.year
        )

        df["Month"] = (
            df["Date"].dt.month
        )

        df["Day"] = (
            df["Date"].dt.day
        )

        df["DayOfWeek"] = (
            df["Date"].dt.dayofweek
        )

        df["IsWeekend"] = (
            df["DayOfWeek"] >= 5
        ).astype(int)

    # --------------------------------------------------------
    # TYPE ENCODING
    # --------------------------------------------------------

    if "Type" in df.columns:

        df["TypeEncoded"] = (
            df["Type"]
            .astype(str)
            .str.strip()
            .str.lower()
            .map({
                "expense": 0,
                "income": 1
            })
        )

    return df


# ============================================================
# 2. GROCERY DATASET
# ============================================================

def load_and_preprocess_grocery():

    print("\n========================================")
    print("GROCERY PRICE DATASET")
    print("========================================")

    # --------------------------------------------------------
    # CHECK FILE
    # --------------------------------------------------------

    if not GROCERY_PATH.exists():

        print(
            "\nERROR: Grocery dataset not found:"
        )

        print(
            GROCERY_PATH
        )

        return None

    # --------------------------------------------------------
    # READ DATA
    # --------------------------------------------------------

    df = pd.read_csv(
        GROCERY_PATH
    )

    print("\nOriginal shape:")

    print(
        df.shape
    )

    print("\nOriginal columns:")

    print(
        df.columns.tolist()
    )

    # --------------------------------------------------------
    # FIND DATE COLUMN
    # --------------------------------------------------------

    date_column = None

    possible_date_columns = [
        "Month",
        "Date",
        "month",
        "date"
    ]

    for column in possible_date_columns:

        if column in df.columns:

            date_column = column

            break

    if date_column is None:

        raise ValueError(
            "Could not find Month or Date "
            "column in grocery dataset."
        )

    # --------------------------------------------------------
    # CONVERT DATE
    # --------------------------------------------------------

    df["Date"] = pd.to_datetime(
        df[date_column],
        errors="coerce"
    )

    # --------------------------------------------------------
    # SECOND DATE PARSING ATTEMPT
    # --------------------------------------------------------

    if df["Date"].isna().all():

        df["Date"] = pd.to_datetime(
            df[date_column]
            .astype(str),
            errors="coerce",
            format="mixed"
        )

    # --------------------------------------------------------
    # REMOVE INVALID DATES
    # --------------------------------------------------------

    df = df.dropna(
        subset=["Date"]
    ).copy()

    # --------------------------------------------------------
    # FIND PRODUCT COLUMNS
    # --------------------------------------------------------

    product_columns = [
        column
        for column in df.columns
        if column not in [
            date_column,
            "Date"
        ]
    ]

    print("\nProducts found:")

    for product in product_columns:

        print(
            " -",
            product
        )

    # --------------------------------------------------------
    # CONVERT WIDE DATA TO LONG DATA
    # --------------------------------------------------------

    rows = []

    for _, record in df.iterrows():

        date = record["Date"]

        for product in product_columns:

            value = record[product]

            price = pd.to_numeric(
                value,
                errors="coerce"
            )

            rows.append({

                "Date":
                    date,

                "Product":
                    product,

                "Category":
                    "Grocery",

                "Price":
                    price,

                "Source":
                    "Historical Grocery Dataset"

            })

    processed = pd.DataFrame(
        rows
    )

    # --------------------------------------------------------
    # SORT DATA
    # --------------------------------------------------------

    processed = (
        processed
        .sort_values(
            [
                "Product",
                "Date"
            ]
        )
        .reset_index(drop=True)
    )

    # ========================================================
    # HANDLE MISSING PRICES
    # ========================================================

    processed["Price"] = (
        processed
        .groupby("Product")["Price"]
        .transform(
            lambda x:
            x.interpolate(
                method="linear",
                limit_direction="both"
            )
        )
    )

    # --------------------------------------------------------
    # USE PRODUCT MEDIAN IF STILL MISSING
    # --------------------------------------------------------

    processed["Price"] = (
        processed
        .groupby("Product")["Price"]
        .transform(
            lambda x:
            x.fillna(
                x.median()
            )
        )
    )

    # --------------------------------------------------------
    # REMOVE REMAINING INVALID PRICES
    # --------------------------------------------------------

    processed = processed.dropna(
        subset=["Price"]
    ).copy()

    # --------------------------------------------------------
    # KEEP POSITIVE PRICES
    # --------------------------------------------------------

    processed = processed[
        processed["Price"] >= 0
    ].copy()

    # ========================================================
    # TIME FEATURES
    # ========================================================

    processed["Year"] = (
        processed["Date"].dt.year
    )

    processed["Month"] = (
        processed["Date"].dt.month
    )

    processed["Quarter"] = (
        processed["Date"].dt.quarter
    )

    # ========================================================
    # PREVIOUS PRICE
    # ========================================================

    processed["PreviousPrice"] = (
        processed
        .groupby("Product")["Price"]
        .shift(1)
    )

    # --------------------------------------------------------
    # IMPORTANT FIX
    #
    # First record of every product has no previous price.
    # Therefore shift(1) creates NaN.
    #
    # We replace those NaN values with 0.
    # --------------------------------------------------------

    processed["PreviousPrice"] = (
        processed["PreviousPrice"]
        .fillna(0)
    )

    # ========================================================
    # PRICE CHANGE
    # ========================================================

    processed["PriceChange"] = (
        processed["Price"]
        -
        processed["PreviousPrice"]
    )

    # ========================================================
    # PRICE CHANGE PERCENTAGE
    # ========================================================

    processed["PriceChangePercent"] = (
        processed["PriceChange"]
        /
        processed["PreviousPrice"].replace(
            0,
            np.nan
        )
    ) * 100

    # ========================================================
    # CLEAN CALCULATED COLUMNS
    # ========================================================

    processed["PriceChange"] = (
        pd.to_numeric(
            processed["PriceChange"],
            errors="coerce"
        )
        .replace(
            [np.inf, -np.inf],
            np.nan
        )
        .fillna(0)
    )

    processed["PriceChangePercent"] = (
        pd.to_numeric(
            processed["PriceChangePercent"],
            errors="coerce"
        )
        .replace(
            [np.inf, -np.inf],
            np.nan
        )
        .fillna(0)
    )

    # ========================================================
    # FINAL SAFETY CLEANING
    # ========================================================

    processed["PreviousPrice"] = (
        pd.to_numeric(
            processed["PreviousPrice"],
            errors="coerce"
        )
        .replace(
            [np.inf, -np.inf],
            np.nan
        )
        .fillna(0)
    )

    processed["Price"] = (
        pd.to_numeric(
            processed["Price"],
            errors="coerce"
        )
        .replace(
            [np.inf, -np.inf],
            np.nan
        )
        .fillna(0)
    )

    # --------------------------------------------------------
    # TEXT COLUMNS
    # --------------------------------------------------------

    processed["Product"] = (
        processed["Product"]
        .fillna("Unknown")
        .astype(str)
    )

    processed["Category"] = (
        processed["Category"]
        .fillna("Grocery")
        .astype(str)
    )

    processed["Source"] = (
        processed["Source"]
        .fillna(
            "Historical Grocery Dataset"
        )
        .astype(str)
    )

    # ========================================================
    # FINAL COLUMN ORDER
    # ========================================================

    processed = processed[
        [
            "Date",
            "Year",
            "Month",
            "Quarter",
            "Product",
            "Category",
            "Price",
            "PreviousPrice",
            "PriceChange",
            "PriceChangePercent",
            "Source"
        ]
    ]

    # ========================================================
    # FINAL MISSING VALUE SAFETY CHECK
    # ========================================================

    processed = processed.fillna({
        "PreviousPrice": 0,
        "PriceChange": 0,
        "PriceChangePercent": 0,
        "Product": "Unknown",
        "Category": "Grocery",
        "Source": "Historical Grocery Dataset"
    })

    # ========================================================
    # SAVE CSV
    # ========================================================

    processed.to_csv(
        GROCERY_OUTPUT,
        index=False
    )

    # ========================================================
    # PRINT RESULTS
    # ========================================================

    print(
        "\nProcessed grocery shape:"
    )

    print(
        processed.shape
    )

    print(
        "\nMissing values after preprocessing:"
    )

    print(
        processed.isnull().sum()
    )

    print(
        "\nTOTAL MISSING VALUES:"
    )

    print(
        processed.isnull()
        .sum()
        .sum()
    )

    print(
        "\nSaved:"
    )

    print(
        GROCERY_OUTPUT
    )

    return processed


# ============================================================
# 3. ELECTRONICS HELPER
# ============================================================

def clean_list_string(value):

    """
    Converts values such as:

    ['2020-01-01', '2020-01-05']

    into:

    ['2020-01-01', '2020-01-05']
    """

    if pd.isna(value):

        return []

    value = str(value).strip()

    if not value:

        return []

    # --------------------------------------------------------
    # Try Python list
    # --------------------------------------------------------

    try:

        parsed = ast.literal_eval(
            value
        )

        if isinstance(
            parsed,
            list
        ):

            return parsed

        if isinstance(
            parsed,
            tuple
        ):

            return list(parsed)

    except Exception:

        pass

    # --------------------------------------------------------
    # Remove brackets
    # --------------------------------------------------------

    value = value.strip(
        "[]"
    )

    # --------------------------------------------------------
    # Detect separator
    # --------------------------------------------------------

    if "," in value:

        parts = value.split(",")

    elif "|" in value:

        parts = value.split("|")

    elif ";" in value:

        parts = value.split(";")

    else:

        parts = [value]

    cleaned = []

    for item in parts:

        item = str(item).strip()

        item = item.strip("'")

        item = item.strip('"')

        if item:

            cleaned.append(
                item
            )

    return cleaned


# ============================================================
# 4. ELECTRONICS DATE PARSER
# ============================================================

def parse_date_list(value):

    values = clean_list_string(
        value
    )

    dates = []

    for item in values:

        parsed = pd.to_datetime(
            item,
            errors="coerce"
        )

        if pd.notna(parsed):

            dates.append(
                parsed
            )

    return dates


# ============================================================
# 5. ELECTRONICS PRICE PARSER
# ============================================================

def parse_price_list(value):

    values = clean_list_string(
        value
    )

    prices = []

    for item in values:

        if item is None:

            continue

        text = str(item)

        # ----------------------------------------------------
        # Remove currency symbols
        # ----------------------------------------------------

        text = re.sub(
            r"[^\d.\-]",
            "",
            text
        )

        try:

            number = float(
                text
            )

            prices.append(
                number
            )

        except ValueError:

            continue

    return prices


# ============================================================
# 6. ELECTRONICS DATASET
# ============================================================

def load_and_preprocess_electronics():

    print("\n========================================")
    print("ELECTRONICS PRICE DATASET")
    print("========================================")

    # --------------------------------------------------------
    # CHECK FILE
    # --------------------------------------------------------

    if not ELECTRONICS_PATH.exists():

        print(
            "\nERROR: Electronics dataset not found:"
        )

        print(
            ELECTRONICS_PATH
        )

        return None

    # --------------------------------------------------------
    # READ DATA
    # --------------------------------------------------------

    df = pd.read_csv(
        ELECTRONICS_PATH,
        low_memory=False
    )

    print(
        "\nOriginal shape:"
    )

    print(
        df.shape
    )

    print(
        "\nOriginal columns:"
    )

    for column in df.columns:

        print(
            " -",
            column
        )

    # ========================================================
    # DETECT COLUMNS
    # ========================================================

    price_max_column = (
        "prices.amountMax"
        if "prices.amountMax"
        in df.columns
        else None
    )

    price_min_column = (
        "prices.amountMin"
        if "prices.amountMin"
        in df.columns
        else None
    )

    date_seen_column = (
        "prices.dateSeen"
        if "prices.dateSeen"
        in df.columns
        else None
    )

    name_column = (
        "name"
        if "name"
        in df.columns
        else None
    )

    brand_column = (
        "brand"
        if "brand"
        in df.columns
        else None
    )

    category_column = (
        "primaryCategories"
        if "primaryCategories"
        in df.columns
        else
        "categories"
        if "categories"
        in df.columns
        else None
    )

    merchant_column = (
        "prices.merchant"
        if "prices.merchant"
        in df.columns
        else None
    )

    currency_column = (
        "prices.currency"
        if "prices.currency"
        in df.columns
        else None
    )

    print(
        "\nDetected columns:"
    )

    print(
        "Price Max:",
        price_max_column
    )

    print(
        "Price Min:",
        price_min_column
    )

    print(
        "Date Seen:",
        date_seen_column
    )

    print(
        "Product:",
        name_column
    )

    print(
        "Brand:",
        brand_column
    )

    print(
        "Category:",
        category_column
    )

    # ========================================================
    # VALIDATE REQUIRED COLUMNS
    # ========================================================

    if price_max_column is None:

        raise ValueError(
            "prices.amountMax column was not found "
            "in the electronics dataset."
        )

    if date_seen_column is None:

        raise ValueError(
            "prices.dateSeen column was not found "
            "in the electronics dataset."
        )

    # ========================================================
    # BUILD HISTORICAL OBSERVATIONS
    # ========================================================

    rows = []

    for _, record in df.iterrows():

        # ----------------------------------------------------
        # Product
        # ----------------------------------------------------

        product = (
            str(
                record[name_column]
            )
            if name_column
            and pd.notna(
                record[name_column]
            )
            else "Unknown Product"
        )

        # ----------------------------------------------------
        # Brand
        # ----------------------------------------------------

        brand = (
            str(
                record[brand_column]
            )
            if brand_column
            and pd.notna(
                record[brand_column]
            )
            else "Unknown"
        )

        # ----------------------------------------------------
        # Category
        # ----------------------------------------------------

        category = (
            str(
                record[category_column]
            )
            if category_column
            and pd.notna(
                record[category_column]
            )
            else "Electronics"
        )

        # ----------------------------------------------------
        # Merchant
        # ----------------------------------------------------

        merchant = (
            str(
                record[merchant_column]
            )
            if merchant_column
            and pd.notna(
                record[merchant_column]
            )
            else "Unknown"
        )

        # ----------------------------------------------------
        # Currency
        # ----------------------------------------------------

        currency = (
            str(
                record[currency_column]
            )
            if currency_column
            and pd.notna(
                record[currency_column]
            )
            else "Unknown"
        )

        # ----------------------------------------------------
        # Dates
        # ----------------------------------------------------

        dates = parse_date_list(
            record[date_seen_column]
        )

        # ----------------------------------------------------
        # Maximum prices
        # ----------------------------------------------------

        max_prices = parse_price_list(
            record[price_max_column]
        )

        # ----------------------------------------------------
        # Minimum prices
        # ----------------------------------------------------

        min_prices = []

        if price_min_column:

            min_prices = parse_price_list(
                record[price_min_column]
            )

        # ----------------------------------------------------
        # No price
        # ----------------------------------------------------

        if not max_prices:

            continue

        # ----------------------------------------------------
        # No date
        # ----------------------------------------------------

        if not dates:

            continue

        # ====================================================
        # CREATE HISTORICAL RECORDS
        # ====================================================

        for index, date in enumerate(
            dates
        ):

            # ------------------------------------------------
            # Maximum price
            # ------------------------------------------------

            if index < len(
                max_prices
            ):

                max_price = (
                    max_prices[index]
                )

            else:

                max_price = (
                    max_prices[-1]
                )

            # ------------------------------------------------
            # Minimum price
            # ------------------------------------------------

            if min_prices:

                if index < len(
                    min_prices
                ):

                    min_price = (
                        min_prices[index]
                    )

                else:

                    min_price = (
                        min_prices[-1]
                    )

            else:

                min_price = max_price

            # ------------------------------------------------
            # Average price
            # ------------------------------------------------

            price = (
                max_price
                +
                min_price
            ) / 2

            rows.append({

                "Date":
                    date,

                "Product":
                    product,

                "Category":
                    category,

                "Brand":
                    brand,

                "Merchant":
                    merchant,

                "Currency":
                    currency,

                "Price":
                    price,

                "Source":
                    "Datafiniti Electronics Dataset"

            })

    processed = pd.DataFrame(
        rows
    )

    # ========================================================
    # VALIDATE
    # ========================================================

    if processed.empty:

        raise ValueError(
            "No electronics historical records "
            "could be generated."
        )

    # ========================================================
    # CLEAN DATE
    # ========================================================

    processed["Date"] = pd.to_datetime(
        processed["Date"],
        errors="coerce"
    )

    # ========================================================
    # CLEAN PRICE
    # ========================================================

    processed["Price"] = pd.to_numeric(
        processed["Price"],
        errors="coerce"
    )

    # --------------------------------------------------------
    # Remove invalid date/price
    # --------------------------------------------------------

    processed = processed.dropna(
        subset=[
            "Date",
            "Price"
        ]
    ).copy()

    # --------------------------------------------------------
    # Positive prices
    # --------------------------------------------------------

    processed = processed[
        processed["Price"] >= 0
    ].copy()

    # ========================================================
    # SORT
    # ========================================================

    processed = (
        processed
        .sort_values(
            [
                "Product",
                "Date"
            ]
        )
        .reset_index(
            drop=True
        )
    )

    # ========================================================
    # REMOVE EXACT DUPLICATES
    # ========================================================

    processed = (
        processed
        .drop_duplicates(
            subset=[
                "Date",
                "Product",
                "Brand",
                "Merchant",
                "Price"
            ]
        )
        .reset_index(
            drop=True
        )
    )

    # ========================================================
    # TIME FEATURES
    # ========================================================

    processed["Year"] = (
        processed["Date"].dt.year
    )

    processed["Month"] = (
        processed["Date"].dt.month
    )

    processed["Quarter"] = (
        processed["Date"].dt.quarter
    )

    # ========================================================
    # PREVIOUS PRICE
    # ========================================================

    processed["PreviousPrice"] = (
        processed
        .groupby("Product")["Price"]
        .shift(1)
    )

    # --------------------------------------------------------
    # FIRST RECORD HAS NO PREVIOUS PRICE
    # --------------------------------------------------------

    processed["PreviousPrice"] = (
        processed["PreviousPrice"]
        .fillna(0)
    )

    # ========================================================
    # PRICE CHANGE
    # ========================================================

    processed["PriceChange"] = (
        processed["Price"]
        -
        processed["PreviousPrice"]
    )

    # ========================================================
    # PRICE CHANGE PERCENT
    # ========================================================

    processed["PriceChangePercent"] = (
        processed["PriceChange"]
        /
        processed["PreviousPrice"].replace(
            0,
            np.nan
        )
    ) * 100

    # ========================================================
    # CLEAN PRICE CHANGE
    # ========================================================

    processed["PriceChange"] = (
        pd.to_numeric(
            processed["PriceChange"],
            errors="coerce"
        )
        .replace(
            [np.inf, -np.inf],
            np.nan
        )
        .fillna(0)
    )

    processed["PriceChangePercent"] = (
        pd.to_numeric(
            processed["PriceChangePercent"],
            errors="coerce"
        )
        .replace(
            [np.inf, -np.inf],
            np.nan
        )
        .fillna(0)
    )

    # ========================================================
    # FINAL PREVIOUS PRICE CLEANING
    # ========================================================

    processed["PreviousPrice"] = (
        pd.to_numeric(
            processed["PreviousPrice"],
            errors="coerce"
        )
        .replace(
            [np.inf, -np.inf],
            np.nan
        )
        .fillna(0)
    )

    # ========================================================
    # TEXT CLEANING
    # ========================================================

    processed["Product"] = (
        processed["Product"]
        .fillna("Unknown Product")
        .astype(str)
    )

    processed["Category"] = (
        processed["Category"]
        .fillna("Electronics")
        .astype(str)
    )

    processed["Brand"] = (
        processed["Brand"]
        .fillna("Unknown")
        .astype(str)
    )

    processed["Merchant"] = (
        processed["Merchant"]
        .fillna("Unknown")
        .astype(str)
    )

    processed["Currency"] = (
        processed["Currency"]
        .fillna("Unknown")
        .astype(str)
    )

    processed["Source"] = (
        processed["Source"]
        .fillna(
            "Datafiniti Electronics Dataset"
        )
        .astype(str)
    )

    # ========================================================
    # FINAL COLUMN ORDER
    # ========================================================

    processed = processed[
        [
            "Date",
            "Year",
            "Month",
            "Quarter",
            "Product",
            "Category",
            "Brand",
            "Merchant",
            "Currency",
            "Price",
            "PreviousPrice",
            "PriceChange",
            "PriceChangePercent",
            "Source"
        ]
    ]

    # ========================================================
    # FINAL SAFETY CHECK
    # ========================================================

    processed = processed.fillna({
        "PreviousPrice": 0,
        "PriceChange": 0,
        "PriceChangePercent": 0,
        "Product": "Unknown Product",
        "Category": "Electronics",
        "Brand": "Unknown",
        "Merchant": "Unknown",
        "Currency": "Unknown",
        "Source": "Datafiniti Electronics Dataset"
    })

    # ========================================================
    # SAVE
    # ========================================================

    processed.to_csv(
        ELECTRONICS_OUTPUT,
        index=False
    )

    # ========================================================
    # PRINT RESULTS
    # ========================================================

    print(
        "\nProcessed electronics shape:"
    )

    print(
        processed.shape
    )

    print(
        "\nMissing values after preprocessing:"
    )

    print(
        processed.isnull().sum()
    )

    print(
        "\nTOTAL MISSING VALUES:"
    )

    print(
        processed.isnull()
        .sum()
        .sum()
    )

    print(
        "\nUnique products:",
        processed["Product"].nunique()
    )

    print(
        "\nDate range:"
    )

    print(
        processed["Date"].min(),
        "to",
        processed["Date"].max()
    )

    print(
        "\nSaved:"
    )

    print(
        ELECTRONICS_OUTPUT
    )

    return processed


# ============================================================
# 7. DATASET SUMMARY
# ============================================================

def print_dataset_summary(
    name,
    df
):

    if df is None:

        return

    print(
        "\n========================================"
    )

    print(
        name
    )

    print(
        "========================================"
    )

    print(
        "Rows:",
        len(df)
    )

    print(
        "Columns:",
        len(df.columns)
    )

    print(
        "Missing values:",
        int(
            df.isnull()
            .sum()
            .sum()
        )
    )

    print(
        "Duplicate rows:",
        int(
            df.duplicated()
            .sum()
        )
    )


# ============================================================
# 8. MAIN PROGRAM
# ============================================================

if __name__ == "__main__":

    print(
        "\n"
        "========================================\n"
        "AI SMART EXPENSE TRACKER\n"
        "DATA PREPROCESSING\n"
        "========================================"
    )

    # ========================================================
    # PERSONAL FINANCE
    # ========================================================

    personal_df = (
        load_and_preprocess_personal_finance()
    )

    # ========================================================
    # GROCERY
    # ========================================================

    grocery_df = (
        load_and_preprocess_grocery()
    )

    # ========================================================
    # ELECTRONICS
    # ========================================================

    electronics_df = (
        load_and_preprocess_electronics()
    )

    # ========================================================
    # FINAL SUMMARY
    # ========================================================

    print_dataset_summary(
        "PERSONAL FINANCE",
        personal_df
    )

    print_dataset_summary(
        "GROCERY PRICE HISTORY",
        grocery_df
    )

    print_dataset_summary(
        "ELECTRONICS PRICE HISTORY",
        electronics_df
    )

    # ========================================================
    # FINAL STATUS
    # ========================================================

    print(
        "\n========================================"
    )

    print(
        "PREPROCESSING COMPLETED"
    )

    print(
        "========================================"
    )

    print(
        "\nOutput files:"
    )

    print(
        "1.",
        GROCERY_OUTPUT
    )

    print(
        "2.",
        ELECTRONICS_OUTPUT
    )

    print(
        "\n========================================\n"
    )