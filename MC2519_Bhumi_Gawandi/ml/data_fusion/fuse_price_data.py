from pathlib import Path
import pandas as pd
import numpy as np


# ============================================================
# PROJECT PATHS
# ============================================================

PROJECT_ROOT = (
    Path(__file__).resolve().parents[2]
)


DATASET_DIR = (
    PROJECT_ROOT
    / "ml"
    / "dataset"
)


FUSION_DIR = (
    PROJECT_ROOT
    / "ml"
    / "data_fusion"
    / "results"
)


# ============================================================
# INPUT FILES
# ============================================================

# IMPORTANT:
# Change these names ONLY if your actual CSV names are different.

GROCERY_FILE = (
    DATASET_DIR
    / "grocery.csv"
)

ELECTRONICS_FILE = (
    DATASET_DIR
    / "electronics.csv"
)


# ============================================================
# OUTPUT FILE
# ============================================================

OUTPUT_FILE = (
    FUSION_DIR
    / "fused_price_data.csv"
)


# ============================================================
# CREATE OUTPUT DIRECTORY
# ============================================================

FUSION_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# ============================================================
# HELPER FUNCTION
# ============================================================

def find_column(
    df,
    possible_names,
    default=None
):

    # Create lowercase mapping
    column_mapping = {
        str(column).strip().lower():
            column
        for column in df.columns
    }

    for name in possible_names:

        key = (
            str(name)
            .strip()
            .lower()
        )

        if key in column_mapping:

            return column_mapping[key]

    return default


# ============================================================
# CLEAN NUMBER
# ============================================================

def clean_number(
    series,
    default=0
):

    return (
        pd.to_numeric(
            series,
            errors="coerce"
        )
        .fillna(default)
    )


# ============================================================
# CLEAN TEXT
# ============================================================

def clean_text(
    series,
    default="Unknown"
):

    series = (
        series
        .astype(str)
        .replace(
            [
                "nan",
                "NaN",
                "None",
                "none",
                "",
                "null",
                "NULL"
            ],
            np.nan
        )
    )

    return (
        series
        .fillna(default)
        .astype(str)
        .str.strip()
    )


# ============================================================
# CALCULATE PRICE CHANGE
# ============================================================

def calculate_price_change(
    current_price,
    previous_price
):

    change = (
        current_price
        - previous_price
    )

    percentage = np.where(
        previous_price > 0,
        (
            change
            / previous_price
        ) * 100,
        0
    )

    return (
        change,
        percentage
    )


# ============================================================
# GROCERY DATA PREPARATION
# ============================================================

def prepare_grocery_data():

    print("\n========================================")
    print("PREPARING GROCERY DATA")
    print("========================================")

    if not GROCERY_FILE.exists():

        print(
            "Grocery file not found:"
        )

        print(
            GROCERY_FILE
        )

        return pd.DataFrame()


    df = pd.read_csv(
        GROCERY_FILE
    )


    print(
        "Original rows:",
        len(df)
    )

    print(
        "Original columns:"
    )

    print(
        df.columns.tolist()
    )


    # --------------------------------------------------------
    # PRODUCT
    # --------------------------------------------------------

    product_column = find_column(
        df,
        [
            "Product",
            "product",
            "Item",
            "item",
            "Commodity",
            "commodity",
            "Name",
            "name"
        ]
    )

    if product_column:

        product = clean_text(
            df[product_column]
        )

    else:

        product = pd.Series(
            [
                f"Grocery Item {i + 1}"
                for i in range(len(df))
            ]
        )


    # --------------------------------------------------------
    # CURRENT PRICE
    # --------------------------------------------------------

    current_price_column = find_column(
        df,
        [
            "Price",
            "price",
            "CurrentPrice",
            "current_price",
            "Current Price",
            "Unit Price",
            "unit_price"
        ]
    )

    if current_price_column:

        current_price = clean_number(
            df[current_price_column]
        )

    else:

        current_price = pd.Series(
            np.zeros(len(df))
        )


    # --------------------------------------------------------
    # PREVIOUS PRICE
    # --------------------------------------------------------

    previous_price_column = find_column(
        df,
        [
            "PreviousPrice",
            "previous_price",
            "Previous Price",
            "Previous_Price"
        ]
    )

    if previous_price_column:

        previous_price = clean_number(
            df[previous_price_column]
        )

    else:

        # If previous price doesn't exist,
        # use current price as the base.
        previous_price = (
            current_price.copy()
        )


    # --------------------------------------------------------
    # YEAR
    # --------------------------------------------------------

    year_column = find_column(
        df,
        [
            "Year",
            "year"
        ]
    )

    if year_column:

        year = clean_number(
            df[year_column],
            default=2026
        )

    else:

        year = pd.Series(
            [2026] * len(df)
        )


    # --------------------------------------------------------
    # MONTH
    # --------------------------------------------------------

    month_column = find_column(
        df,
        [
            "Month",
            "month"
        ]
    )

    if month_column:

        month = clean_number(
            df[month_column],
            default=1
        )

    else:

        month = pd.Series(
            [1] * len(df)
        )


    # --------------------------------------------------------
    # QUARTER
    # --------------------------------------------------------

    quarter_column = find_column(
        df,
        [
            "Quarter",
            "quarter"
        ]
    )

    if quarter_column:

        quarter = clean_number(
            df[quarter_column],
            default=1
        )

    else:

        quarter = (
            ((month - 1) // 3) + 1
        )


    # --------------------------------------------------------
    # PRICE CHANGE
    # --------------------------------------------------------

    price_change, price_change_percent = (
        calculate_price_change(
            current_price,
            previous_price
        )
    )


    # --------------------------------------------------------
    # PREDICTED FUTURE PRICE
    #
    # The actual API will later replace this
    # calculated placeholder.
    #
    # For now we keep it deterministic so
    # there are no NULL values.
    # --------------------------------------------------------

    predicted_future_price = (
        current_price
        + (
            price_change
            * 0.10
        )
    )


    # --------------------------------------------------------
    # CREATE STANDARDIZED DATAFRAME
    # --------------------------------------------------------

    result = pd.DataFrame({

        "Product":
            product,

        "Category":
            "Grocery",

        "Brand":
            "Not Applicable",

        "Merchant":
            "Historical Dataset",

        "Currency":
            "USD",

        "CurrentPrice":
            current_price,

        "PreviousPrice":
            previous_price,

        "PriceChange":
            price_change,

        "PriceChangePercent":
            price_change_percent,

        "Year":
            year,

        "Month":
            month,

        "Quarter":
            quarter,

        "DatasetSource":
            "Historical Grocery Dataset",

        "APIPrice":
            current_price,

        "APIPriceSource":
            "Price Prediction API",

        "PredictedFuturePrice":
            predicted_future_price,

        "MLModel":
            "Gradient Boosting",

        "MLDataset":
            "Grocery Dataset",

        "DataType":
            "Grocery"
    })


    return result


# ============================================================
# ELECTRONICS DATA PREPARATION
# ============================================================

def prepare_electronics_data():

    print("\n========================================")
    print("PREPARING ELECTRONICS DATA")
    print("========================================")

    if not ELECTRONICS_FILE.exists():

        print(
            "Electronics file not found:"
        )

        print(
            ELECTRONICS_FILE
        )

        return pd.DataFrame()


    df = pd.read_csv(
        ELECTRONICS_FILE
    )


    print(
        "Original rows:",
        len(df)
    )

    print(
        "Original columns:"
    )

    print(
        df.columns.tolist()
    )


    # --------------------------------------------------------
    # PRODUCT
    # --------------------------------------------------------

    product_column = find_column(
        df,
        [
            "Product",
            "product",
            "Product Name",
            "product_name",
            "Name",
            "name",
            "Title",
            "title"
        ]
    )

    if product_column:

        product = clean_text(
            df[product_column]
        )

    else:

        product = pd.Series(
            [
                f"Electronics Item {i + 1}"
                for i in range(len(df))
            ]
        )


    # --------------------------------------------------------
    # CATEGORY
    # --------------------------------------------------------

    category_column = find_column(
        df,
        [
            "Category",
            "category",
            "Categories",
            "categories"
        ]
    )

    if category_column:

        category = clean_text(
            df[category_column],
            default="Electronics"
        )

    else:

        category = pd.Series(
            [
                "Electronics"
            ] * len(df)
        )


    # --------------------------------------------------------
    # BRAND
    # --------------------------------------------------------

    brand_column = find_column(
        df,
        [
            "Brand",
            "brand"
        ]
    )

    if brand_column:

        brand = clean_text(
            df[brand_column]
        )

    else:

        brand = pd.Series(
            [
                "Unknown"
            ] * len(df)
        )


    # --------------------------------------------------------
    # MERCHANT
    # --------------------------------------------------------

    merchant_column = find_column(
        df,
        [
            "Merchant",
            "merchant",
            "Retailer",
            "retailer",
            "Seller",
            "seller",
            "Store",
            "store"
        ]
    )

    if merchant_column:

        merchant = clean_text(
            df[merchant_column]
        )

    else:

        merchant = pd.Series(
            [
                "Historical Dataset"
            ] * len(df)
        )


    # --------------------------------------------------------
    # CURRENCY
    # --------------------------------------------------------

    currency_column = find_column(
        df,
        [
            "Currency",
            "currency"
        ]
    )

    if currency_column:

        currency = clean_text(
            df[currency_column],
            default="USD"
        )

    else:

        currency = pd.Series(
            [
                "USD"
            ] * len(df)
        )


    # --------------------------------------------------------
    # CURRENT PRICE
    # --------------------------------------------------------

    current_price_column = find_column(
        df,
        [
            "Price",
            "price",
            "CurrentPrice",
            "current_price",
            "Current Price",
            "SellingPrice",
            "selling_price"
        ]
    )

    if current_price_column:

        current_price = clean_number(
            df[current_price_column]
        )

    else:

        current_price = pd.Series(
            np.zeros(len(df))
        )


    # --------------------------------------------------------
    # PREVIOUS PRICE
    # --------------------------------------------------------

    previous_price_column = find_column(
        df,
        [
            "PreviousPrice",
            "previous_price",
            "Previous Price"
        ]
    )

    if previous_price_column:

        previous_price = clean_number(
            df[previous_price_column]
        )

    else:

        previous_price = (
            current_price.copy()
        )


    # --------------------------------------------------------
    # YEAR
    # --------------------------------------------------------

    year_column = find_column(
        df,
        [
            "Year",
            "year"
        ]
    )

    if year_column:

        year = clean_number(
            df[year_column],
            default=2026
        )

    else:

        year = pd.Series(
            [2026] * len(df)
        )


    # --------------------------------------------------------
    # MONTH
    # --------------------------------------------------------

    month_column = find_column(
        df,
        [
            "Month",
            "month"
        ]
    )

    if month_column:

        month = clean_number(
            df[month_column],
            default=1
        )

    else:

        month = pd.Series(
            [1] * len(df)
        )


    # --------------------------------------------------------
    # QUARTER
    # --------------------------------------------------------

    quarter_column = find_column(
        df,
        [
            "Quarter",
            "quarter"
        ]
    )

    if quarter_column:

        quarter = clean_number(
            df[quarter_column],
            default=1
        )

    else:

        quarter = (
            ((month - 1) // 3) + 1
        )


    # --------------------------------------------------------
    # PRICE CHANGE
    # --------------------------------------------------------

    price_change, price_change_percent = (
        calculate_price_change(
            current_price,
            previous_price
        )
    )


    # --------------------------------------------------------
    # TEMPORARY PREDICTED PRICE
    # --------------------------------------------------------

    predicted_future_price = (
        current_price
        + (
            price_change
            * 0.10
        )
    )


    # --------------------------------------------------------
    # CREATE STANDARDIZED DATAFRAME
    # --------------------------------------------------------

    result = pd.DataFrame({

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

        "CurrentPrice":
            current_price,

        "PreviousPrice":
            previous_price,

        "PriceChange":
            price_change,

        "PriceChangePercent":
            price_change_percent,

        "Year":
            year,

        "Month":
            month,

        "Quarter":
            quarter,

        "DatasetSource":
            "Datafiniti Electronics Dataset",

        "APIPrice":
            current_price,

        "APIPriceSource":
            "Price Prediction API",

        "PredictedFuturePrice":
            predicted_future_price,

        "MLModel":
            "Gradient Boosting",

        "MLDataset":
            "Electronics Dataset",

        "DataType":
            "Electronics"
    })


    return result


# ============================================================
# DATA FUSION
# ============================================================

def fuse_datasets():

    print("\n========================================")
    print("        AI SMART EXPENSE TRACKER")
    print("             DATA FUSION")
    print("========================================")


    # --------------------------------------------------------
    # LOAD GROCERY
    # --------------------------------------------------------

    grocery_df = (
        prepare_grocery_data()
    )


    # --------------------------------------------------------
    # LOAD ELECTRONICS
    # --------------------------------------------------------

    electronics_df = (
        prepare_electronics_data()
    )


    # --------------------------------------------------------
    # CHECK DATA
    # --------------------------------------------------------

    print(
        "\nGrocery rows:",
        len(grocery_df)
    )

    print(
        "Electronics rows:",
        len(electronics_df)
    )


    # --------------------------------------------------------
    # COMBINE
    # --------------------------------------------------------

    frames = []

    if not grocery_df.empty:

        frames.append(
            grocery_df
        )


    if not electronics_df.empty:

        frames.append(
            electronics_df
        )


    if not frames:

        print(
            "\nERROR:"
        )

        print(
            "No datasets were found."
        )

        return None


    fused_df = pd.concat(
        frames,
        ignore_index=True
    )


    # ========================================================
    # ENSURE NO NULL VALUES
    # ========================================================

    # Numeric columns

    numeric_columns = [

        "CurrentPrice",

        "PreviousPrice",

        "PriceChange",

        "PriceChangePercent",

        "Year",

        "Month",

        "Quarter",

        "APIPrice",

        "PredictedFuturePrice"
    ]


    for column in numeric_columns:

        if column in fused_df.columns:

            fused_df[column] = (
                pd.to_numeric(
                    fused_df[column],
                    errors="coerce"
                )
                .fillna(0)
            )


    # Text columns

    text_columns = [

        "Product",

        "Category",

        "Brand",

        "Merchant",

        "Currency",

        "DatasetSource",

        "APIPriceSource",

        "MLModel",

        "MLDataset",

        "DataType"
    ]


    for column in text_columns:

        if column in fused_df.columns:

            fused_df[column] = (
                fused_df[column]
                .astype(str)
                .replace(
                    [
                        "nan",
                        "NaN",
                        "None",
                        "null",
                        "NULL"
                    ],
                    "Unknown"
                )
                .fillna("Unknown")
            )


    # ========================================================
    # ROUND PRICES
    # ========================================================

    price_columns = [

        "CurrentPrice",

        "PreviousPrice",

        "PriceChange",

        "PriceChangePercent",

        "APIPrice",

        "PredictedFuturePrice"
    ]


    for column in price_columns:

        if column in fused_df.columns:

            fused_df[column] = (
                fused_df[column]
                .round(2)
            )


    # ========================================================
    # INTEGER COLUMNS
    # ========================================================

    for column in [

        "Year",

        "Month",

        "Quarter"

    ]:

        if column in fused_df.columns:

            fused_df[column] = (
                fused_df[column]
                .astype(int)
            )


    # ========================================================
    # FINAL COLUMN ORDER
    # ========================================================

    final_columns = [

        "Product",

        "Category",

        "Brand",

        "Merchant",

        "Currency",

        "CurrentPrice",

        "PreviousPrice",

        "PriceChange",

        "PriceChangePercent",

        "Year",

        "Month",

        "Quarter",

        "DatasetSource",

        "APIPrice",

        "APIPriceSource",

        "PredictedFuturePrice",

        "MLModel",

        "MLDataset",

        "DataType"
    ]


    # Keep only columns that exist

    final_columns = [

        column

        for column in final_columns

        if column in fused_df.columns
    ]


    fused_df = fused_df[
        final_columns
    ]


    # ========================================================
    # FINAL NULL CHECK
    # ========================================================

    null_count = (
        fused_df
        .isnull()
        .sum()
        .sum()
    )


    print(
        "\nTotal NULL values:",
        null_count
    )


    # ========================================================
    # REMOVE DUPLICATES
    # ========================================================

    before_duplicates = (
        len(fused_df)
    )


    fused_df = (
        fused_df
        .drop_duplicates()
        .reset_index(
            drop=True
        )
    )


    after_duplicates = (
        len(fused_df)
    )


    print(
        "Duplicates removed:",
        before_duplicates
        - after_duplicates
    )


    # ========================================================
    # SAVE CSV
    # ========================================================

    fused_df.to_csv(
        OUTPUT_FILE,
        index=False
    )


    # ========================================================
    # FINAL REPORT
    # ========================================================

    print(
        "\n========================================"
    )

    print(
        "        FUSION COMPLETED"
    )

    print(
        "========================================"
    )

    print(
        "Rows:",
        len(fused_df)
    )

    print(
        "Columns:",
        len(fused_df.columns)
    )

    print(
        "\nFinal columns:"
    )

    for index, column in enumerate(
        fused_df.columns,
        start=1
    ):

        print(
            f"{index}. {column}"
        )


    print(
        "\nOutput file:"
    )

    print(
        OUTPUT_FILE
    )


    # ========================================================
    # DISPLAY SAMPLE
    # ========================================================

    print(
        "\n========================================"
    )

    print(
        "FIRST 10 ROWS"
    )

    print(
        "========================================"
    )

    print(
        fused_df.head(10).to_string(
            index=False
        )
    )


    # ========================================================
    # FINAL VALIDATION
    # ========================================================

    print(
        "\n========================================"
    )

    print(
        "VALIDATION"
    )

    print(
        "========================================"
    )

    print(
        "Shape:",
        fused_df.shape
    )

    print(
        "Missing values:"
    )

    print(
        fused_df.isnull().sum()
    )


    return fused_df


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    fuse_datasets()