from pathlib import Path
from datetime import datetime
import pandas as pd
import numpy as np


# ============================================================
# PROJECT PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[3]

DATASET_DIR = PROJECT_ROOT / "ml" / "dataset"
PROCESSED_DIR = DATASET_DIR / "processed"

PROCESSED_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# ============================================================
# INPUT FILES
# ============================================================

ELECTRONICS_FILE = (
    PROCESSED_DIR /
    "electronics_price_history.csv"
)

GROCERY_FILE = (
    PROCESSED_DIR /
    "grocery_price_history.csv"
)

FINAL_FILE = (
    PROCESSED_DIR /
    "final_fused_dataset.csv"
)


# ============================================================
# FINAL CSV SCHEMA
# ============================================================

FINAL_COLUMNS = [

    "date",
    "user_id",
    "product_id",
    "product_name",
    "category",
    "subcategory",
    "brand",
    "price",
    "discount",
    "rating",
    "quantity",

    "monthly_income",
    "monthly_expense",
    "category_expense",
    "previous_month_expense",
    "average_expense",
    "purchase_frequency",
    "budget",
    "remaining_budget",
    "savings",

    "inflation_rate",
    "exchange_rate",
    "temperature",
    "demand_index",
    "market_trend",
    "api_price",
    "api_discount",

    "month",
    "quarter",
    "day_of_week",
    "is_weekend",
    "is_festival",

    "price_change",
    "price_change_percentage",
    "rolling_avg_price",

    "future_price",

    "api_source",
    "data_source",
]


# ============================================================
# COLUMN HELPERS
# ============================================================

def first_existing_column(
    df,
    possible_columns,
    default=None
):

    for column in possible_columns:

        if column in df.columns:

            return df[column]

    return pd.Series(
        [default] * len(df),
        index=df.index
    )


def clean_number(
    series,
    default=0.0
):

    return pd.to_numeric(
        series,
        errors="coerce"
    ).fillna(default)


def clean_text(
    series,
    default=""
):

    return (
        series
        .fillna(default)
        .astype(str)
        .str.strip()
    )


# ============================================================
# LOAD CSV
# ============================================================

def load_csv(
    file_path,
    dataset_name
):

    print()
    print("=" * 70)
    print(f"LOADING {dataset_name.upper()} DATASET")
    print("=" * 70)

    if not file_path.exists():

        raise FileNotFoundError(
            f"{dataset_name} dataset not found:\n"
            f"{file_path}"
        )

    df = pd.read_csv(
        file_path
    )

    if df.empty:

        raise ValueError(
            f"{dataset_name} dataset is empty."
        )

    print(
        f"{dataset_name} rows:",
        len(df)
    )

    print(
        f"{dataset_name} columns:",
        list(df.columns)
    )

    return df


# ============================================================
# NORMALIZE DATE
# ============================================================

def normalize_date(df):

    date_column = first_existing_column(
        df,
        [
            "date",
            "Date",
            "DATE",
            "timestamp",
            "Timestamp",
            "transaction_date",
        ],
        None
    )

    date = pd.to_datetime(
        date_column,
        errors="coerce"
    )

    # If date is unavailable, create a date
    # so the final CSV always has a valid date.
    date = date.fillna(
        pd.Timestamp.today().normalize()
    )

    return date


# ============================================================
# NORMALIZE ELECTRONICS
# ============================================================

def normalize_electronics(
    df
):

    df = df.copy()

    result = pd.DataFrame(
        index=df.index
    )


    # --------------------------------------------------------
    # DATE
    # --------------------------------------------------------

    result["date"] = normalize_date(
        df
    )


    # --------------------------------------------------------
    # PRODUCT
    # --------------------------------------------------------

    result["product_id"] = clean_text(
        first_existing_column(
            df,
            [
                "product_id",
                "Product ID",
                "id",
                "ID",
            ],
            ""
        )
    )

    result["product_name"] = clean_text(
        first_existing_column(
            df,
            [
                "product_name",
                "Product",
                "product",
                "name",
                "Name",
            ],
            "Unknown Product"
        )
    )


    # --------------------------------------------------------
    # CATEGORY
    # --------------------------------------------------------

    result["category"] = "Electronics"

    result["subcategory"] = clean_text(
        first_existing_column(
            df,
            [
                "subcategory",
                "Subcategory",
                "sub_category",
                "Sub Category",
                "category",
                "Category",
            ],
            "Electronics"
        )
    )


    # --------------------------------------------------------
    # BRAND
    # --------------------------------------------------------

    result["brand"] = clean_text(
        first_existing_column(
            df,
            [
                "brand",
                "Brand",
                "manufacturer",
                "Manufacturer",
            ],
            "Unknown"
        )
    )


    # --------------------------------------------------------
    # PRICE
    # --------------------------------------------------------

    result["price"] = clean_number(
        first_existing_column(
            df,
            [
                "price",
                "Price",
                "current_price",
                "Current Price",
            ],
            0
        )
    )


    # --------------------------------------------------------
    # DISCOUNT
    # --------------------------------------------------------

    result["discount"] = clean_number(
        first_existing_column(
            df,
            [
                "discount",
                "Discount",
                "discount_percent",
                "Discount %",
            ],
            0
        )
    )


    # --------------------------------------------------------
    # RATING
    # --------------------------------------------------------

    result["rating"] = clean_number(
        first_existing_column(
            df,
            [
                "rating",
                "Rating",
                "stars",
                "Stars",
            ],
            0
        )
    )


    # --------------------------------------------------------
    # QUANTITY
    # --------------------------------------------------------

    result["quantity"] = 1


    # --------------------------------------------------------
    # DATA SOURCE
    # --------------------------------------------------------

    result["data_source"] = "Electronics"


    return result


# ============================================================
# NORMALIZE GROCERY
# ============================================================

def normalize_grocery(
    df
):

    df = df.copy()

    result = pd.DataFrame(
        index=df.index
    )


    # --------------------------------------------------------
    # DATE
    # --------------------------------------------------------

    result["date"] = normalize_date(
        df
    )


    # --------------------------------------------------------
    # PRODUCT
    # --------------------------------------------------------

    result["product_id"] = clean_text(
        first_existing_column(
            df,
            [
                "product_id",
                "Product ID",
                "id",
                "ID",
            ],
            ""
        )
    )

    result["product_name"] = clean_text(
        first_existing_column(
            df,
            [
                "product_name",
                "Product",
                "product",
                "item",
                "Item",
                "name",
                "Name",
            ],
            "Unknown Product"
        )
    )


    # --------------------------------------------------------
    # CATEGORY
    # --------------------------------------------------------

    result["category"] = "Grocery"

    result["subcategory"] = clean_text(
        first_existing_column(
            df,
            [
                "subcategory",
                "Subcategory",
                "sub_category",
                "Sub Category",
                "category",
                "Category",
            ],
            "Grocery"
        )
    )


    # --------------------------------------------------------
    # BRAND
    # --------------------------------------------------------

    result["brand"] = clean_text(
        first_existing_column(
            df,
            [
                "brand",
                "Brand",
                "manufacturer",
                "Manufacturer",
            ],
            "Unknown"
        )
    )


    # --------------------------------------------------------
    # PRICE
    # --------------------------------------------------------

    result["price"] = clean_number(
        first_existing_column(
            df,
            [
                "price",
                "Price",
                "current_price",
                "Current Price",
            ],
            0
        )
    )


    # --------------------------------------------------------
    # DISCOUNT
    # --------------------------------------------------------

    result["discount"] = clean_number(
        first_existing_column(
            df,
            [
                "discount",
                "Discount",
                "discount_percent",
                "Discount %",
            ],
            0
        )
    )


    # --------------------------------------------------------
    # RATING
    # --------------------------------------------------------

    result["rating"] = clean_number(
        first_existing_column(
            df,
            [
                "rating",
                "Rating",
                "stars",
                "Stars",
            ],
            0
        )
    )


    # --------------------------------------------------------
    # QUANTITY
    # --------------------------------------------------------

    result["quantity"] = 1


    # --------------------------------------------------------
    # DATA SOURCE
    # --------------------------------------------------------

    result["data_source"] = "Grocery"


    return result


# ============================================================
# ADD USER DATA
# ============================================================

def add_user_data(
    df,
    user_data=None
):

    df = df.copy()

    if user_data is None:

        user_data = {}


    # --------------------------------------------------------
    # USER ID
    # --------------------------------------------------------

    df["user_id"] = user_data.get(
        "user_id",
        ""
    )


    # --------------------------------------------------------
    # MONTHLY INCOME
    # --------------------------------------------------------

    df["monthly_income"] = clean_number(
        pd.Series(
            user_data.get(
                "monthly_income",
                0
            ),
            index=df.index
        )
    )


    # --------------------------------------------------------
    # USER EXPENSES
    # --------------------------------------------------------

    df["monthly_expense"] = clean_number(
        pd.Series(
            user_data.get(
                "monthly_expense",
                0
            ),
            index=df.index
        )
    )


    # --------------------------------------------------------
    # CATEGORY EXPENSE
    # --------------------------------------------------------

    df["category_expense"] = clean_number(
        pd.Series(
            user_data.get(
                "category_expense",
                0
            ),
            index=df.index
        )
    )


    # --------------------------------------------------------
    # PREVIOUS MONTH EXPENSE
    # --------------------------------------------------------

    df["previous_month_expense"] = clean_number(
        pd.Series(
            user_data.get(
                "previous_month_expense",
                0
            ),
            index=df.index
        )
    )


    # --------------------------------------------------------
    # AVERAGE EXPENSE
    # --------------------------------------------------------

    df["average_expense"] = clean_number(
        pd.Series(
            user_data.get(
                "average_expense",
                0
            ),
            index=df.index
        )
    )


    # --------------------------------------------------------
    # PURCHASE FREQUENCY
    # --------------------------------------------------------

    df["purchase_frequency"] = clean_number(
        pd.Series(
            user_data.get(
                "purchase_frequency",
                0
            ),
            index=df.index
        )
    )


    # --------------------------------------------------------
    # BUDGET
    # --------------------------------------------------------

    df["budget"] = clean_number(
        pd.Series(
            user_data.get(
                "budget",
                0
            ),
            index=df.index
        )
    )


    # --------------------------------------------------------
    # REMAINING BUDGET
    # --------------------------------------------------------

    df["remaining_budget"] = (
        df["budget"]
        -
        df["category_expense"]
    )


    # --------------------------------------------------------
    # SAVINGS
    # --------------------------------------------------------

    df["savings"] = (
        df["monthly_income"]
        -
        df["monthly_expense"]
    )


    return df


# ============================================================
# ADD API DATA
# ============================================================

def add_api_data(
    df,
    api_data=None
):

    df = df.copy()

    if api_data is None:

        api_data = {}


    # --------------------------------------------------------
    # INFLATION
    # --------------------------------------------------------

    df["inflation_rate"] = clean_number(
        pd.Series(
            api_data.get(
                "inflation_rate",
                0
            ),
            index=df.index
        )
    )


    # --------------------------------------------------------
    # EXCHANGE RATE
    # --------------------------------------------------------

    df["exchange_rate"] = clean_number(
        pd.Series(
            api_data.get(
                "exchange_rate",
                0
            ),
            index=df.index
        )
    )


    # --------------------------------------------------------
    # TEMPERATURE
    # --------------------------------------------------------

    df["temperature"] = clean_number(
        pd.Series(
            api_data.get(
                "temperature",
                0
            ),
            index=df.index
        )
    )


    # --------------------------------------------------------
    # DEMAND
    # --------------------------------------------------------

    df["demand_index"] = clean_number(
        pd.Series(
            api_data.get(
                "demand_index",
                0
            ),
            index=df.index
        )
    )


    # --------------------------------------------------------
    # MARKET TREND
    # --------------------------------------------------------

    df["market_trend"] = clean_number(
        pd.Series(
            api_data.get(
                "market_trend",
                0
            ),
            index=df.index
        )
    )


    # --------------------------------------------------------
    # API PRICE
    # --------------------------------------------------------

    df["api_price"] = clean_number(
        pd.Series(
            api_data.get(
                "api_price",
                0
            ),
            index=df.index
        )
    )


    # --------------------------------------------------------
    # API DISCOUNT
    # --------------------------------------------------------

    df["api_discount"] = clean_number(
        pd.Series(
            api_data.get(
                "api_discount",
                0
            ),
            index=df.index
        )
    )


    # --------------------------------------------------------
    # API SOURCE
    # --------------------------------------------------------

    df["api_source"] = api_data.get(
        "api_source",
        "External API"
    )


    return df


# ============================================================
# ADD TIME FEATURES
# ============================================================

def add_time_features(
    df
):

    df = df.copy()

    df["date"] = pd.to_datetime(
        df["date"],
        errors="coerce"
    )

    df["date"] = df["date"].fillna(
        pd.Timestamp.today().normalize()
    )


    # --------------------------------------------------------
    # MONTH
    # --------------------------------------------------------

    df["month"] = (
        df["date"]
        .dt.month
        .astype(int)
    )


    # --------------------------------------------------------
    # QUARTER
    # --------------------------------------------------------

    df["quarter"] = (
        df["date"]
        .dt.quarter
        .astype(int)
    )


    # --------------------------------------------------------
    # DAY OF WEEK
    # Monday = 0
    # Sunday = 6
    # --------------------------------------------------------

    df["day_of_week"] = (
        df["date"]
        .dt.dayofweek
        .astype(int)
    )


    # --------------------------------------------------------
    # WEEKEND
    # --------------------------------------------------------

    df["is_weekend"] = (
        df["day_of_week"]
        >= 5
    ).astype(int)


    # --------------------------------------------------------
    # FESTIVAL
    #
    # Keep this simple initially.
    # Can later connect to a festival API/calendar.
    # --------------------------------------------------------

    df["is_festival"] = 0


    return df


# ============================================================
# ADD PRICE FEATURES
# ============================================================

def add_price_features(
    df
):

    df = df.copy()

    df["price"] = clean_number(
        df["price"]
    )


    # --------------------------------------------------------
    # Sort first
    # --------------------------------------------------------

    df = df.sort_values(
        [
            "category",
            "product_name",
            "date",
        ]
    ).reset_index(
        drop=True
    )


    # --------------------------------------------------------
    # PRICE CHANGE
    # --------------------------------------------------------

    df["price_change"] = (
        df.groupby(
            [
                "category",
                "product_name",
            ]
        )["price"]
        .diff()
        .fillna(0)
    )


    # --------------------------------------------------------
    # PRICE CHANGE %
    # --------------------------------------------------------

    previous_price = (
        df.groupby(
            [
                "category",
                "product_name",
            ]
        )["price"]
        .shift(1)
    )


    df["price_change_percentage"] = np.where(

        previous_price.notna()
        &
        (previous_price != 0),

        (
            (
                df["price"]
                -
                previous_price
            )
            /
            previous_price
        )
        *
        100,

        0

    )


    # --------------------------------------------------------
    # ROLLING AVERAGE
    #
    # IMPORTANT:
    # This uses only current and previous rows.
    # --------------------------------------------------------

    df["rolling_avg_price"] = (

        df.groupby(
            [
                "category",
                "product_name",
            ]
        )["price"]

        .transform(
            lambda x:
            x.rolling(
                window=3,
                min_periods=1
            )
            .mean()
        )

    )


    return df


# ============================================================
# CREATE FUTURE PRICE TARGET
# ============================================================

def create_future_price(
    df
):

    df = df.copy()

    # --------------------------------------------------------
    # Future price is the NEXT available price for the
    # same product.
    #
    # This is the ML TARGET.
    # --------------------------------------------------------

    df["future_price"] = (

        df.groupby(
            [
                "category",
                "product_name",
            ]
        )["price"]

        .shift(-1)

    )


    return df


# ============================================================
# CLEAN DATA
# ============================================================

def clean_final_dataset(
    df
):

    df = df.copy()


    # --------------------------------------------------------
    # Ensure every requested column exists
    # --------------------------------------------------------

    for column in FINAL_COLUMNS:

        if column not in df.columns:

            if column in [
                "date"
            ]:

                df[column] = (
                    pd.Timestamp.today()
                    .normalize()
                )

            elif column in [
                "product_name",
                "category",
                "subcategory",
                "brand",
                "api_source",
                "data_source",
                "user_id",
                "product_id",
            ]:

                df[column] = ""

            else:

                df[column] = 0.0


    # --------------------------------------------------------
    # Remove invalid prices
    # --------------------------------------------------------

    df["price"] = pd.to_numeric(
        df["price"],
        errors="coerce"
    )

    df = df[
        df["price"] > 0
    ].copy()


    # --------------------------------------------------------
    # Remove duplicate product/date rows
    # --------------------------------------------------------

    df = df.drop_duplicates(
        subset=[
            "date",
            "product_name",
            "category",
        ],
        keep="last"
    )


    # --------------------------------------------------------
    # Date format
    # --------------------------------------------------------

    df["date"] = pd.to_datetime(
        df["date"],
        errors="coerce"
    ).dt.strftime(
        "%Y-%m-%d"
    )


    # --------------------------------------------------------
    # Numeric columns
    # --------------------------------------------------------

    numeric_columns = [

        "price",
        "discount",
        "rating",
        "quantity",

        "monthly_income",
        "monthly_expense",
        "category_expense",
        "previous_month_expense",
        "average_expense",
        "purchase_frequency",
        "budget",
        "remaining_budget",
        "savings",

        "inflation_rate",
        "exchange_rate",
        "temperature",
        "demand_index",
        "market_trend",
        "api_price",
        "api_discount",

        "month",
        "quarter",
        "day_of_week",
        "is_weekend",
        "is_festival",

        "price_change",
        "price_change_percentage",
        "rolling_avg_price",
        "future_price",
    ]


    for column in numeric_columns:

        df[column] = pd.to_numeric(
            df[column],
            errors="coerce"
        )


    # --------------------------------------------------------
    # Fill numeric missing values
    # --------------------------------------------------------

    for column in numeric_columns:

        if column != "future_price":

            df[column] = (
                df[column]
                .fillna(0)
            )


    # --------------------------------------------------------
    # Text columns
    # --------------------------------------------------------

    text_columns = [

        "user_id",
        "product_id",
        "product_name",
        "category",
        "subcategory",
        "brand",
        "api_source",
        "data_source",
    ]


    for column in text_columns:

        df[column] = (
            df[column]
            .fillna("")
            .astype(str)
            .str.strip()
        )


    # --------------------------------------------------------
    # FINAL COLUMN ORDER
    # --------------------------------------------------------

    df = df[
        FINAL_COLUMNS
    ]


    return df


# ============================================================
# BUILD USER SUMMARY
# ============================================================

def build_user_summary(
    user_expenses=None,
    monthly_income=0,
    budget=0,
    user_id=""
):

    if user_expenses is None:

        user_expenses = []


    if len(user_expenses) == 0:

        return {

            "user_id":
                user_id,

            "monthly_income":
                float(monthly_income),

            "monthly_expense":
                0.0,

            "category_expense":
                0.0,

            "previous_month_expense":
                0.0,

            "average_expense":
                0.0,

            "purchase_frequency":
                0.0,

            "budget":
                float(budget),

        }


    expense_df = pd.DataFrame(
        user_expenses
    )


    if "amount" not in expense_df.columns:

        expense_df["amount"] = 0


    expense_df["amount"] = pd.to_numeric(
        expense_df["amount"],
        errors="coerce"
    ).fillna(0)


    monthly_expense = float(
        expense_df["amount"].sum()
    )


    average_expense = float(
        expense_df["amount"].mean()
    )


    purchase_frequency = float(
        len(expense_df)
    )


    # --------------------------------------------------------
    # Current category expense
    # --------------------------------------------------------

    category_expense = monthly_expense


    # --------------------------------------------------------
    # Previous month expense
    # --------------------------------------------------------

    previous_month_expense = 0.0


    return {

        "user_id":
            user_id,

        "monthly_income":
            float(monthly_income),

        "monthly_expense":
            monthly_expense,

        "category_expense":
            category_expense,

        "previous_month_expense":
            previous_month_expense,

        "average_expense":
            average_expense,

        "purchase_frequency":
            purchase_frequency,

        "budget":
            float(budget),

    }


# ============================================================
# MAIN DATA FUSION
# ============================================================

def create_final_fused_dataset(

    user_data=None,

    api_data=None,

):

    print()
    print("=" * 70)
    print("              DATA FUSION STARTED")
    print("=" * 70)


    # ========================================================
    # LOAD DATASETS
    # ========================================================

    electronics_raw = load_csv(
        ELECTRONICS_FILE,
        "Electronics"
    )

    grocery_raw = load_csv(
        GROCERY_FILE,
        "Grocery"
    )


    # ========================================================
    # NORMALIZE
    # ========================================================

    electronics = normalize_electronics(
        electronics_raw
    )

    grocery = normalize_grocery(
        grocery_raw
    )


    print()
    print(
        "Normalized Electronics:",
        len(electronics)
    )

    print(
        "Normalized Grocery:",
        len(grocery)
    )


    # ========================================================
    # COMBINE ROWS
    # ========================================================

    fused = pd.concat(
        [
            electronics,
            grocery,
        ],
        ignore_index=True
    )


    print()
    print(
        "Combined product records:",
        len(fused)
    )


    # ========================================================
    # USER DATA
    # ========================================================

    fused = add_user_data(
        fused,
        user_data
    )


    # ========================================================
    # API DATA
    # ========================================================

    fused = add_api_data(
        fused,
        api_data
    )


    # ========================================================
    # TIME FEATURES
    # ========================================================

    fused = add_time_features(
        fused
    )


    # ========================================================
    # PRICE FEATURES
    # ========================================================

    fused = add_price_features(
        fused
    )


    # ========================================================
    # FUTURE PRICE TARGET
    # ========================================================

    fused = create_future_price(
        fused
    )


    # ========================================================
    # CLEAN
    # ========================================================

    fused = clean_final_dataset(
        fused
    )


    # ========================================================
    # SAVE
    # ========================================================

    fused.to_csv(
        FINAL_FILE,
        index=False
    )


    # ========================================================
    # REPORT
    # ========================================================

    print()
    print("=" * 70)
    print("              DATA FUSION COMPLETED")
    print("=" * 70)

    print()
    print(
        "Final CSV:",
        FINAL_FILE
    )

    print(
        "Total rows:",
        len(fused)
    )

    print(
        "Total columns:",
        len(fused.columns)
    )

    print()
    print(
        "Final columns:"
    )

    for index, column in enumerate(
        fused.columns,
        start=1
    ):

        print(
            f"{index:02d}. {column}"
        )


    print()
    print(
        "Category distribution:"
    )

    print(
        fused[
            "category"
        ]
        .value_counts()
        .to_string()
    )


    print()
    print(
        "Data source distribution:"
    )

    print(
        fused[
            "data_source"
        ]
        .value_counts()
        .to_string()
    )


    print()
    print(
        "First 5 rows:"
    )

    print(
        fused.head().to_string(
            index=False
        )
    )


    print()
    print("=" * 70)


    return fused


# ============================================================
# EXAMPLE RUN
# ============================================================

if __name__ == "__main__":

    # --------------------------------------------------------
    # Replace these values with your real logged-in user
    # data later.
    #
    # The API endpoint can pass the same structure when you
    # connect this script to FastAPI.
    # --------------------------------------------------------

    user_data = {

        "user_id":
            "U001",

        "monthly_income":
            45000,

        "monthly_expense":
            28000,

        "category_expense":
            7000,

        "previous_month_expense":
            6500,

        "average_expense":
            3500,

        "purchase_frequency":
            8,

        "budget":
            10000,

    }


    api_data = {

        "inflation_rate":
            4.2,

        "exchange_rate":
            83.5,

        "temperature":
            28.5,

        "demand_index":
            82,

        "market_trend":
            1.12,

        "api_price":
            0,

        "api_discount":
            0,

        "api_source":
            "External API",

    }


    create_final_fused_dataset(

        user_data=user_data,

        api_data=api_data,

    )