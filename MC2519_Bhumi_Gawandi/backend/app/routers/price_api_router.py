from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from app.services.price_api_service import (
    PriceAPIService
)


router = APIRouter(
    prefix="/api/v1/price",
    tags=["Price API"]
)


# ============================================================
# PROJECT ROOT
# ============================================================

CURRENT_FILE = Path(__file__).resolve()


def find_project_root() -> Path:

    candidates = [
        CURRENT_FILE.parent,
        *CURRENT_FILE.parents
    ]

    for directory in candidates:

        try:

            if (
                directory / "ml"
            ).is_dir():

                return directory.resolve()

        except Exception:
            continue

    return (
        CURRENT_FILE
        .parents[3]
        .resolve()
    )


PROJECT_ROOT = find_project_root()


DATASET_DIRECTORY = (
    PROJECT_ROOT
    / "ml"
    / "dataset"
    / "processed"
)


GROCERY_FILE = (
    DATASET_DIRECTORY
    / "grocery_price_history.csv"
)


ELECTRONICS_FILE = (
    DATASET_DIRECTORY
    / "electronics_price_history.csv"
)


print(
    "============================================================"
)
print(
    "PRICE API PROJECT ROOT:",
    PROJECT_ROOT
)
print(
    "PRICE API DATASET DIRECTORY:",
    DATASET_DIRECTORY
)
print(
    "GROCERY FILE:",
    GROCERY_FILE
)
print(
    "ELECTRONICS FILE:",
    ELECTRONICS_FILE
)
print(
    "============================================================"
)


# ============================================================
# DATASET HELPERS
# ============================================================

def load_dataset(
    category: str
):

    import pandas as pd

    category = (
        category
        .strip()
        .lower()
    )

    if category == "grocery":
        file_path = GROCERY_FILE

    elif category == "electronics":
        file_path = ELECTRONICS_FILE

    else:
        raise HTTPException(
            status_code=400,
            detail=(
                "Category must be "
                "'grocery' or 'electronics'."
            )
        )

    if not file_path.exists():
        raise HTTPException(
            status_code=404,
            detail={
                "message":
                    "Historical dataset not found.",
                "dataset":
                    str(file_path)
            }
        )

    try:
        df = pd.read_csv(file_path)

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail={
                "message":
                    "Could not read historical dataset.",
                "error":
                    str(exc)
            }
        )

    if df.empty:
        raise HTTPException(
            status_code=404,
            detail="Historical dataset is empty."
        )

    return df


def get_product_column(df):

    for column in [
        "Product",
        "product",
        "product_name",
        "ProductName",
        "name",
        "Name"
    ]:

        if column in df.columns:
            return column

    return None


def get_price_column(df):

    for column in [
        "Price",
        "price",
        "current_price",
        "api_price"
    ]:

        if column in df.columns:
            return column

    return None


def normalize_text(value):

    if value is None:
        return ""

    return (
        str(value)
        .strip()
        .lower()
        .replace("_", " ")
        .replace("-", " ")
    )


def find_exact_product(
    df,
    product: str,
    brand: Optional[str] = None
):

    product_column = (
        get_product_column(df)
    )

    if not product_column:
        return df.iloc[0:0]

    requested = normalize_text(
        product
    )

    work = df.copy()

    work["_product_normalized"] = (
        work[product_column]
        .fillna("")
        .astype(str)
        .apply(normalize_text)
    )

    exact = work[
        work["_product_normalized"]
        == requested
    ]

    if (
        exact.empty
        and
        brand
        and
        "Brand" in work.columns
    ):

        brand_normalized = (
            normalize_text(
                brand
            )
        )

        exact = work[
            (
                work[
                    "_product_normalized"
                ]
                == requested
            )
            &
            (
                work["Brand"]
                .fillna("")
                .astype(str)
                .apply(normalize_text)
                == brand_normalized
            )
        ]

    return exact


def get_dataset_suggestions(
    df,
    product: str,
    limit: int = 10
):

    product_column = (
        get_product_column(df)
    )

    if not product_column:
        return []

    requested = normalize_text(
        product
    )

    suggestions = []

    for item in (
        df[product_column]
        .dropna()
        .astype(str)
        .drop_duplicates()
        .tolist()
    ):

        normalized = normalize_text(
            item
        )

        if (
            requested in normalized
            or
            normalized in requested
        ):

            suggestions.append(item)

    return suggestions[:limit]


# ============================================================
# CURRENT PRICE
#
# IMPORTANT:
# If product is absent from the CSV, the endpoint tries the
# external price API. It never substitutes another product.
# ============================================================

@router.get(
    "/{category}"
)
async def get_product_price(

    category: str,

    product: str = Query(
        ...,
        min_length=1
    ),

    brand: Optional[str] = None

):

    category_normalized = (
        category
        .strip()
        .lower()
    )

    if category_normalized not in [
        "grocery",
        "electronics"
    ]:

        raise HTTPException(
            status_code=400,
            detail=(
                "Category must be "
                "'grocery' or 'electronics'."
            )
        )

    df = load_dataset(
        category_normalized
    )

    product_column = (
        get_product_column(df)
    )

    price_column = (
        get_price_column(df)
    )

    if not product_column:
        raise HTTPException(
            status_code=500,
            detail={
                "message":
                    "Product column not found.",
                "available_columns":
                    list(df.columns)
            }
        )

    if not price_column:
        raise HTTPException(
            status_code=500,
            detail={
                "message":
                    "Price column not found.",
                "available_columns":
                    list(df.columns)
            }
        )

    # --------------------------------------------------------
    # 1. EXACT HISTORICAL MATCH
    # --------------------------------------------------------

    matches = find_exact_product(
        df,
        product,
        brand
    )

    # --------------------------------------------------------
    # 2. IF NOT IN DATASET, USE EXTERNAL PRICE API
    # --------------------------------------------------------

    if matches.empty:

        if category_normalized == "grocery":

            api_result = (
                PriceAPIService
                .fetch_grocery_price(
                    product
                )
            )

        else:

            api_result = (
                PriceAPIService
                .fetch_electronics_price(
                    product,
                    brand
                )
            )

        if api_result.get(
            "api_price"
        ) is not None:

            return {
                "success": True,
                "api_type":
                    "Own Project Price API",
                "product_type":
                    category_normalized.title(),
                "dataset":
                    (
                        "grocery_price_history.csv"
                        if category_normalized
                        == "grocery"
                        else
                        "electronics_price_history.csv"
                    ),
                "product":
                    product,
                "matched_product":
                    api_result.get(
                        "matched_product",
                        product
                    ),
                "brand":
                    brand or "Unknown",
                "current_price":
                    round(
                        float(
                            api_result[
                                "api_price"
                            ]
                        ),
                        2
                    ),
                "previous_price":
                    None,
                "previous_price_date":
                    None,
                "price_change":
                    None,
                "price_change_percentage":
                    None,
                "discount":
                    api_result.get(
                        "api_discount",
                        0
                    ),
                "historical_records":
                    0,
                "source":
                    api_result.get(
                        "api_source",
                        "External Price API"
                    ),
                "price_source":
                    "Current Price API",
                "historical_match":
                    False,
                "currency":
                    api_result.get(
                        "currency",
                        "INR"
                    ),
                "message":
                    (
                        "Product was not found in "
                        "the historical dataset. "
                        "Current price was obtained "
                        "from the price API."
                    )
            }

        suggestions = (
            get_dataset_suggestions(
                df,
                product
            )
        )

        raise HTTPException(
            status_code=404,
            detail={
                "message":
                    (
                        f"Product '{product}' "
                        "was not found in the "
                        "historical dataset and "
                        "the current price API "
                        "did not return a price."
                    ),
                "product":
                    product,
                "historical_match":
                    False,
                "api_available":
                    bool(
                        PriceAPIService
                        .get_api_url(
                            category_normalized
                        )
                    ),
                "suggestions":
                    suggestions
            }
        )

    # --------------------------------------------------------
    # 3. CLEAN HISTORICAL PRICE
    # --------------------------------------------------------

    import pandas as pd

    matches = matches.copy()

    matches[price_column] = (
        pd.to_numeric(
            matches[price_column],
            errors="coerce"
        )
    )

    matches = matches[
        matches[price_column] > 0
    ]

    if matches.empty:
        raise HTTPException(
            status_code=404,
            detail=(
                "Product exists in the dataset, "
                "but no valid price is available."
            )
        )

    # --------------------------------------------------------
    # 4. SORT BY DATE
    # --------------------------------------------------------

    if "Date" in matches.columns:

        matches["Date"] = pd.to_datetime(
            matches["Date"],
            errors="coerce",
            utc=True
        ).dt.tz_localize(None)

        matches = (
            matches
            .sort_values("Date")
        )

    latest = matches.iloc[-1]

    current_price = float(
        latest[price_column]
    )

    # --------------------------------------------------------
    # 5. PREVIOUS PRICE
    # --------------------------------------------------------

    if len(matches) >= 2:

        previous_price = float(
            matches
            .iloc[-2][price_column]
        )

    else:

        previous_price = (
            current_price
        )

    # --------------------------------------------------------
    # 6. CHANGE
    # --------------------------------------------------------

    price_change = (
        current_price
        -
        previous_price
    )

    if previous_price != 0:

        price_change_percentage = (
            price_change
            /
            previous_price
        ) * 100

    else:

        price_change_percentage = 0.0

    # --------------------------------------------------------
    # 7. DATE
    # --------------------------------------------------------

    latest_date = None

    if (
        "Date" in matches.columns
        and
        pd.notna(
            latest["Date"]
        )
    ):

        latest_date = (
            latest["Date"]
            .strftime(
                "%Y-%m-%d"
            )
        )

    # --------------------------------------------------------
    # 8. BRAND
    # --------------------------------------------------------

    result_brand = (
        "Unknown"
    )

    if "Brand" in matches.columns:

        value = latest.get(
            "Brand"
        )

        if pd.notna(value):

            result_brand = str(
                value
            )

    elif brand:

        result_brand = brand

    # --------------------------------------------------------
    # 9. RESPONSE
    # --------------------------------------------------------

    return {
        "success": True,
        "api_type":
            "Own Project Price API",
        "product_type":
            category_normalized.title(),
        "dataset":
            (
                "grocery_price_history.csv"
                if category_normalized
                == "grocery"
                else
                "electronics_price_history.csv"
            ),
        "product":
            product,
        "matched_product":
            str(
                latest[
                    product_column
                ]
            ),
        "brand":
            result_brand,
        "current_price":
            round(
                current_price,
                2
            ),
        "previous_price":
            round(
                previous_price,
                2
            ),
        "previous_price_date":
            latest_date,
        "price_change":
            round(
                price_change,
                2
            ),
        "price_change_percentage":
            round(
                price_change_percentage,
                2
            ),
        "discount": 0.0,
        "historical_records":
            int(
                len(matches)
            ),
        "source":
            "Project Historical Dataset",
        "price_source":
            "Historical Dataset",
        "historical_match":
            True,
        "currency":
            "INR"
    }
