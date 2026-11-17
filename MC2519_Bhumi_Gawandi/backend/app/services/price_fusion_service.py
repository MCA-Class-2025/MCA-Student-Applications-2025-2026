from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, List

import numpy as np
import pandas as pd

from app.services.price_api_service import (
    PriceAPIService
)


# ============================================================
# PROJECT PATHS
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
        .parents[2]
        .resolve()
    )


PROJECT_ROOT = find_project_root()


DATASET_DIRECTORY = (
    PROJECT_ROOT
    / "ml"
    / "dataset"
    / "processed"
)


GROCERY_DATASET = (
    DATASET_DIRECTORY
    / "grocery_price_history.csv"
)


ELECTRONICS_DATASET = (
    DATASET_DIRECTORY
    / "electronics_price_history.csv"
)


FUSED_DATASET = (
    DATASET_DIRECTORY
    / "fused_price_prediction_dataset.csv"
)


# ============================================================
# FUSED CSV COLUMNS
# ============================================================

FUSED_COLUMNS = [
    "date",
    "user_id",
    "product_id",
    "product_name",
    "category",
    "subcategory",
    "brand",
    "merchant",
    "currency",
    "price",
    "previous_price",
    "price_lag2",
    "price_lag3",
    "rolling_mean",
    "rolling_median",
    "price_change",
    "price_change_percentage",
    "price_ratio",
    "price_trend",
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
    "future_price",
    "api_source",
    "data_source",
    "historical_match",
]


class PriceFusionService:

    """
    Combines historical project data and current API data.

    Critical behavior:

    - A missing product is NOT replaced by another product.
    - If the requested product is not historical, the service
      uses the external API for the current price.
    - Historical trend features are calculated from the
      category dataset, not from an unrelated product.
    - future_price remains the ML target and is excluded from
      prediction inputs.
    """

    # ========================================================
    # TEXT
    # ========================================================

    @staticmethod
    def normalize_text(
        value: Any
    ) -> str:

        if value is None:
            return ""

        text = str(value).strip().lower()

        text = (
            text
            .replace("_", " ")
            .replace("-", " ")
        )

        return " ".join(
            text.split()
        )

    # ========================================================
    # DATASET PATH
    # ========================================================

    @classmethod
    def get_dataset_path(
        cls,
        product_type: str
    ) -> Path:

        product_type = (
            cls.normalize_text(
                product_type
            )
        )

        if product_type == "grocery":
            return GROCERY_DATASET

        if product_type == "electronics":
            return ELECTRONICS_DATASET

        raise ValueError(
            "product_type must be "
            "'grocery' or 'electronics'."
        )

    # ========================================================
    # LOAD DATASET
    # ========================================================

    @classmethod
    def load_dataset(
        cls,
        product_type: str
    ) -> pd.DataFrame:

        path = cls.get_dataset_path(
            product_type
        )

        if not path.exists():
            raise FileNotFoundError(
                f"Historical dataset not found: {path}"
            )

        df = pd.read_csv(path)

        if df.empty:
            raise ValueError(
                f"Historical dataset is empty: {path}"
            )

        return df

    # ========================================================
    # PREPARE DATASET
    # ========================================================

    @classmethod
    def prepare_dataset(
        cls,
        df: pd.DataFrame
    ) -> pd.DataFrame:

        df = df.copy()

        if "Product" not in df.columns:

            alternatives = [
                "product",
                "product_name",
                "ProductName",
                "name",
                "Name"
            ]

            found = next(
                (
                    column
                    for column in alternatives
                    if column in df.columns
                ),
                None
            )

            if found:
                df["Product"] = (
                    df[found]
                )
            else:
                raise ValueError(
                    "Historical dataset must contain "
                    "'Product'."
                )

        if "Price" not in df.columns:

            alternatives = [
                "price",
                "current_price",
                "api_price"
            ]

            found = next(
                (
                    column
                    for column in alternatives
                    if column in df.columns
                ),
                None
            )

            if found:
                df["Price"] = (
                    df[found]
                )
            else:
                raise ValueError(
                    "Historical dataset must contain "
                    "'Price'."
                )

        df["Product"] = (
            df["Product"]
            .fillna("")
            .astype(str)
            .str.strip()
        )

        df["Price"] = pd.to_numeric(
            df["Price"],
            errors="coerce"
        )

        if "Date" in df.columns:

            df["Date"] = pd.to_datetime(
                df["Date"],
                errors="coerce",
                utc=True
            ).dt.tz_localize(None)

        elif (
            "Year" in df.columns
            and
            "Month" in df.columns
        ):

            year = pd.to_numeric(
                df["Year"],
                errors="coerce"
            )

            month = pd.to_numeric(
                df["Month"],
                errors="coerce"
            )

            df["Date"] = pd.to_datetime(
                {
                    "year": year,
                    "month": month,
                    "day": 1
                },
                errors="coerce"
            )

        else:

            df["Date"] = pd.NaT

        df = df[
            df["Price"] > 0
        ].copy()

        df = df[
            df["Product"].str.len() > 0
        ].copy()

        return df

    # ========================================================
    # EXACT PRODUCT MATCH
    # ========================================================

    @classmethod
    def find_product(
        cls,
        df: pd.DataFrame,
        product: str,
        brand: Optional[str] = None
    ) -> pd.DataFrame:

        requested = cls.normalize_text(
            product
        )

        work = df.copy()

        work["_normalized_product"] = (
            work["Product"]
            .fillna("")
            .astype(str)
            .apply(
                cls.normalize_text
            )
        )

        exact = work[
            work["_normalized_product"]
            == requested
        ]

        if (
            exact.empty
            and
            brand
            and
            "Brand" in work.columns
        ):

            requested_brand = (
                cls.normalize_text(
                    brand
                )
            )

            exact = work[
                (
                    work[
                        "_normalized_product"
                    ]
                    == requested
                )
                &
                (
                    work["Brand"]
                    .fillna("")
                    .astype(str)
                    .apply(
                        cls.normalize_text
                    )
                    == requested_brand
                )
            ]

        return exact

    # ========================================================
    # SUGGEST PRODUCTS
    # ========================================================

    @classmethod
    def suggest_products(
        cls,
        df: pd.DataFrame,
        product: str,
        limit: int = 10
    ) -> List[str]:

        requested = cls.normalize_text(
            product
        )

        results = []

        for item in (
            df["Product"]
            .dropna()
            .astype(str)
            .drop_duplicates()
            .tolist()
        ):

            normalized = (
                cls.normalize_text(
                    item
                )
            )

            requested_tokens = set(
                requested.split()
            )

            item_tokens = set(
                normalized.split()
            )

            overlap = (
                requested_tokens
                &
                item_tokens
            )

            if (
                requested
                and
                (
                    requested in normalized
                    or
                    normalized in requested
                    or
                    len(overlap) > 0
                )
            ):

                results.append(item)

        return results[:limit]

    # ========================================================
    # API DATA
    # ========================================================

    @classmethod
    def get_api_data(
        cls,
        product: str,
        product_type: str,
        brand: Optional[str] = None
    ) -> Dict[str, Any]:

        try:

            if (
                cls.normalize_text(
                    product_type
                )
                == "grocery"
            ):

                result = (
                    PriceAPIService
                    .fetch_grocery_price(
                        product
                    )
                )

            else:

                result = (
                    PriceAPIService
                    .fetch_electronics_price(
                        product,
                        brand
                    )
                )

            return result or {}

        except Exception as exc:

            return {
                "success": False,
                "available": False,
                "api_price": None,
                "api_discount": 0.0,
                "api_source":
                    "Price API Error",
                "message":
                    str(exc)
            }

    # ========================================================
    # CATEGORY FALLBACK HISTORY
    # ========================================================

    @classmethod
    def get_category_fallback(
        cls,
        df: pd.DataFrame,
        target_date: pd.Timestamp,
        reference_price: Optional[float] = None
    ) -> Dict[str, Any]:

        """
        Used ONLY when the exact requested product does not
        exist in the historical dataset.

        We do not pretend that another product is the requested
        product. Instead, the historical values represent the
        category-level trend.
        """

        work = df.copy()

        if "Date" in work.columns:

            historical = work[
                work["Date"].notna()
                &
                (
                    work["Date"]
                    <
                    target_date
                )
            ].copy()

        else:

            historical = work.copy()

        if historical.empty:
            historical = work.copy()

        historical = (
            historical
            .sort_values("Date")
            .reset_index(drop=True)
        )

        prices = (
            pd.to_numeric(
                historical["Price"],
                errors="coerce"
            )
            .dropna()
            .astype(float)
            .tolist()
        )

        prices = [
            price
            for price in prices
            if price > 0
        ]

        if not prices:

            if (
                reference_price
                and
                reference_price > 0
            ):

                prices = [
                    float(
                        reference_price
                    )
                ]

            else:

                raise ValueError(
                    "No valid category price history "
                    "is available."
                )

        recent_prices = prices[-12:]

        latest_price = (
            float(
                reference_price
            )
            if (
                reference_price
                and
                reference_price > 0
            )
            else
            float(
                prices[-1]
            )
        )

        previous_price = (
            float(prices[-1])
            if prices
            else latest_price
        )

        if len(prices) >= 2:
            previous_price = float(
                prices[-2]
            )

        lag2 = (
            float(prices[-3])
            if len(prices) >= 3
            else previous_price
        )

        lag3 = (
            float(prices[-4])
            if len(prices) >= 4
            else lag2
        )

        rolling_mean = float(
            np.mean(
                recent_prices
            )
        )

        rolling_median = float(
            np.median(
                recent_prices
            )
        )

        price_change = (
            latest_price
            -
            previous_price
        )

        price_change_percentage = (
            (
                price_change
                /
                previous_price
            ) * 100
            if previous_price != 0
            else 0.0
        )

        price_ratio = (
            latest_price
            /
            lag2
            if lag2 != 0
            else 1.0
        )

        price_trend = (
            previous_price
            -
            lag2
            if lag2 != 0
            else 0.0
        )

        return {
            "matched_product":
                None,

            "historical_price":
                round(
                    latest_price,
                    2
                ),

            "previous_price":
                round(
                    previous_price,
                    2
                ),

            "price_lag2":
                round(
                    lag2,
                    2
                ),

            "price_lag3":
                round(
                    lag3,
                    2
                ),

            "rolling_mean":
                round(
                    rolling_mean,
                    2
                ),

            "rolling_median":
                round(
                    rolling_median,
                    2
                ),

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

            "price_ratio":
                round(
                    price_ratio,
                    6
                ),

            "price_trend":
                round(
                    price_trend,
                    2
                ),

            "previous_date":
                (
                    str(
                        historical.iloc[-1]
                        ["Date"]
                        .date()
                    )
                    if (
                        "Date" in historical.columns
                        and
                        pd.notna(
                            historical.iloc[-1]
                            ["Date"]
                        )
                    )
                    else None
                ),

            "historical_records":
                int(
                    len(historical)
                ),

            "historical_match":
                False,

            "historical_basis":
                "Category-level historical trend"
        }

    # ========================================================
    # HISTORICAL SUMMARY
    # ========================================================

    @classmethod
    def get_historical_summary(
        cls,
        product: str,
        product_type: str,
        year: int,
        month: int,
        brand: Optional[str] = None,
        reference_price: Optional[float] = None
    ) -> Dict[str, Any]:

        df = cls.prepare_dataset(
            cls.load_dataset(
                product_type
            )
        )

        target_date = pd.Timestamp(
            year=int(year),
            month=int(month),
            day=1
        )

        matches = cls.find_product(
            df,
            product,
            brand
        )

        # ----------------------------------------------------
        # PRODUCT EXISTS
        # ----------------------------------------------------

        if not matches.empty:

            historical = matches[
                matches["Date"].notna()
                &
                (
                    matches["Date"]
                    <
                    target_date
                )
            ].copy()

            if historical.empty:
                historical = matches.copy()

            historical = (
                historical
                .sort_values("Date")
                .reset_index(drop=True)
            )

            prices = (
                historical["Price"]
                .astype(float)
                .tolist()
            )

            latest_price = float(
                prices[-1]
            )

            if (
                reference_price
                and
                reference_price > 0
            ):
                latest_price = float(
                    reference_price
                )

            previous_price = (
                float(prices[-2])
                if len(prices) >= 2
                else float(prices[-1])
            )

            price_lag2 = (
                float(prices[-3])
                if len(prices) >= 3
                else previous_price
            )

            price_lag3 = (
                float(prices[-4])
                if len(prices) >= 4
                else price_lag2
            )

            recent_prices = prices[-5:]

            rolling_mean = float(
                np.mean(
                    recent_prices
                )
            )

            rolling_median = float(
                np.median(
                    recent_prices
                )
            )

            price_change = (
                latest_price
                -
                previous_price
            )

            price_change_percentage = (
                (
                    price_change
                    /
                    previous_price
                ) * 100
                if previous_price != 0
                else 0.0
            )

            price_ratio = (
                latest_price
                /
                price_lag2
                if price_lag2 != 0
                else 1.0
            )

            price_trend = (
                previous_price
                -
                price_lag2
                if price_lag2 != 0
                else 0.0
            )

            latest_row = (
                historical.iloc[-1]
            )

            previous_date = None

            if (
                "Date" in historical.columns
                and
                pd.notna(
                    latest_row["Date"]
                )
            ):

                previous_date = (
                    latest_row["Date"]
                    .strftime(
                        "%Y-%m-%d"
                    )
                )

            return {
                "matched_product":
                    str(
                        latest_row["Product"]
                    ),

                "historical_price":
                    round(
                        latest_price,
                        2
                    ),

                "previous_price":
                    round(
                        previous_price,
                        2
                    ),

                "price_lag2":
                    round(
                        price_lag2,
                        2
                    ),

                "price_lag3":
                    round(
                        price_lag3,
                        2
                    ),

                "rolling_mean":
                    round(
                        rolling_mean,
                        2
                    ),

                "rolling_median":
                    round(
                        rolling_median,
                        2
                    ),

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

                "price_ratio":
                    round(
                        price_ratio,
                        6
                    ),

                "price_trend":
                    round(
                        price_trend,
                        2
                    ),

                "previous_date":
                    previous_date,

                "historical_records":
                    int(
                        len(historical)
                    ),

                "historical_match":
                    True,

                "historical_basis":
                    "Product-level historical data"
            }

        # ----------------------------------------------------
        # PRODUCT DOES NOT EXIST
        #
        # IMPORTANT:
        # Use category history only.
        # Never select an unrelated product.
        # ----------------------------------------------------

        return cls.get_category_fallback(
            df,
            target_date,
            reference_price
        )

    # ========================================================
    # PRICE COMPATIBILITY
    # ========================================================

    @staticmethod
    def check_price_compatibility(
        historical_price: float,
        reference_price: float
    ) -> Dict[str, Any]:

        try:

            historical_price = float(
                historical_price
            )

            reference_price = float(
                reference_price
            )

        except (
            TypeError,
            ValueError
        ):

            return {
                "compatible": False,
                "ratio": None,
                "reason":
                    "Invalid price values."
            }

        if (
            historical_price <= 0
            or
            reference_price <= 0
        ):

            return {
                "compatible": False,
                "ratio": None,
                "reason":
                    "Price must be greater than zero."
            }

        ratio = (
            reference_price
            /
            historical_price
        )

        compatible = (
            0.25
            <= ratio
            <= 4.0
        )

        return {
            "compatible":
                compatible,

            "ratio":
                round(
                    ratio,
                    6
                ),

            "reason":
                (
                    "Prices are on a comparable scale."
                    if compatible
                    else
                    "Prices appear to use different "
                    "units, variants or scales."
                )
        }

    # ========================================================
    # FUSE PRICE DATA
    # ========================================================

    @classmethod
    def fuse_price_data(
        cls,
        product: str,
        product_type: str,
        year: int,
        month: int,
        current_price: Optional[float] = None,
        brand: Optional[str] = None,
        category: Optional[str] = None,
        subcategory: Optional[str] = None,
        merchant: Optional[str] = None,
        currency: str = "INR",
        user_data: Optional[Dict[str, Any]] = None,
        save_to_csv: bool = True
    ) -> Dict[str, Any]:

        user_data = (
            user_data
            if isinstance(
                user_data,
                dict
            )
            else {}
        )

        # ----------------------------------------------------
        # 1. CURRENT PRICE API FIRST
        # ----------------------------------------------------

        api_data = cls.get_api_data(
            product,
            product_type,
            brand
        )

        api_price = api_data.get(
            "api_price"
        )

        try:

            api_price = (
                float(api_price)
                if api_price is not None
                else None
            )

            if (
                api_price is not None
                and
                api_price <= 0
            ):
                api_price = None

        except (
            TypeError,
            ValueError
        ):

            api_price = None

        # ----------------------------------------------------
        # 2. REFERENCE PRICE
        # ----------------------------------------------------

        if api_price is not None:

            reference_price = (
                api_price
            )

            reference_source = (
                "Price API"
            )

        elif (
            current_price is not None
            and
            float(current_price) > 0
        ):

            reference_price = float(
                current_price
            )

            reference_source = (
                "User Input"
            )

        else:

            reference_price = None

            reference_source = (
                "Historical Dataset"
            )

        # ----------------------------------------------------
        # 3. HISTORICAL CONTEXT
        # ----------------------------------------------------

        historical = (
            cls.get_historical_summary(
                product=product,
                product_type=product_type,
                year=year,
                month=month,
                brand=brand,
                reference_price=
                    reference_price
            )
        )

        if reference_price is None:

            reference_price = float(
                historical[
                    "historical_price"
                ]
            )

        # ----------------------------------------------------
        # 4. PRODUCT MATCH STATUS
        # ----------------------------------------------------

        historical_match = bool(
            historical.get(
                "historical_match",
                False
            )
        )

        # ----------------------------------------------------
        # 5. CATEGORY / PRODUCT INFO
        # ----------------------------------------------------

        final_category = (
            category
            or
            (
                "Grocery"
                if cls.normalize_text(
                    product_type
                )
                == "grocery"
                else
                "Electronics"
            )
        )

        final_currency = (
            api_data.get(
                "currency"
            )
            or
            currency
            or
            "INR"
        )

        # ----------------------------------------------------
        # 6. BUILD FUSED RECORD
        # ----------------------------------------------------

        now = datetime.utcnow()

        fused_record = {

            "date":
                now.strftime(
                    "%Y-%m-%d"
                ),

            "user_id":
                user_data.get(
                    "user_id"
                ),

            "product_id":
                user_data.get(
                    "product_id"
                ),

            "product_name":
                product,

            "category":
                final_category,

            "subcategory":
                subcategory
                or
                user_data.get(
                    "subcategory"
                ),

            "brand":
                brand
                or
                user_data.get(
                    "brand"
                )
                or
                "Unknown",

            "merchant":
                merchant
                or
                user_data.get(
                    "merchant"
                )
                or
                "Unknown",

            "currency":
                final_currency,

            "price":
                round(
                    float(
                        reference_price
                    ),
                    2
                ),

            "previous_price":
                historical.get(
                    "previous_price"
                ),

            "price_lag2":
                historical.get(
                    "price_lag2"
                ),

            "price_lag3":
                historical.get(
                    "price_lag3"
                ),

            "rolling_mean":
                historical.get(
                    "rolling_mean"
                ),

            "rolling_median":
                historical.get(
                    "rolling_median"
                ),

            "price_change":
                historical.get(
                    "price_change"
                ),

            "price_change_percentage":
                historical.get(
                    "price_change_percentage"
                ),

            "price_ratio":
                historical.get(
                    "price_ratio"
                ),

            "price_trend":
                historical.get(
                    "price_trend"
                ),

            "discount":
                api_data.get(
                    "api_discount",
                    user_data.get(
                        "discount",
                        0.0
                    )
                ),

            "rating":
                user_data.get(
                    "rating",
                    0.0
                ),

            "quantity":
                user_data.get(
                    "quantity",
                    1
                ),

            "monthly_income":
                user_data.get(
                    "monthly_income",
                    0.0
                ),

            "monthly_expense":
                user_data.get(
                    "monthly_expense",
                    0.0
                ),

            "category_expense":
                user_data.get(
                    "category_expense",
                    0.0
                ),

            "previous_month_expense":
                user_data.get(
                    "previous_month_expense",
                    0.0
                ),

            "average_expense":
                user_data.get(
                    "average_expense",
                    0.0
                ),

            "purchase_frequency":
                user_data.get(
                    "purchase_frequency",
                    0.0
                ),

            "budget":
                user_data.get(
                    "budget",
                    0.0
                ),

            "remaining_budget":
                user_data.get(
                    "remaining_budget",
                    0.0
                ),

            "savings":
                user_data.get(
                    "savings",
                    0.0
                ),

            "inflation_rate":
                user_data.get(
                    "inflation_rate",
                    0.0
                ),

            "exchange_rate":
                user_data.get(
                    "exchange_rate",
                    0.0
                ),

            "temperature":
                user_data.get(
                    "temperature",
                    0.0
                ),

            "demand_index":
                user_data.get(
                    "demand_index",
                    0.0
                ),

            "market_trend":
                user_data.get(
                    "market_trend",
                    0.0
                ),

            "api_price":
                (
                    round(
                        api_price,
                        2
                    )
                    if api_price is not None
                    else np.nan
                ),

            "api_discount":
                api_data.get(
                    "api_discount",
                    0.0
                ),

            "month":
                int(month),

            "quarter":
                (
                    (
                        int(month)
                        - 1
                    )
                    // 3
                ) + 1,

            "day_of_week":
                int(
                    now.weekday()
                ),

            "is_weekend":
                int(
                    now.weekday() >= 5
                ),

            "is_festival":
                user_data.get(
                    "is_festival",
                    0
                ),

            "future_price":
                np.nan,

            "api_source":
                api_data.get(
                    "api_source"
                ),

            "data_source":
                (
                    "Price API + "
                    "Historical Dataset"
                    if (
                        api_price is not None
                        and
                        historical_match
                    )
                    else
                    "Price API + "
                    "Category Historical Dataset"
                    if api_price is not None
                    else
                    "Historical Dataset"
                ),

            "historical_match":
                historical_match
        }

        # ----------------------------------------------------
        # 7. SAVE
        # ----------------------------------------------------

        result = {

            "success":
                True,

            "product":
                product,

            "product_type":
                product_type,

            "category":
                final_category,

            "historical_match":
                historical_match,

            "historical_basis":
                historical.get(
                    "historical_basis"
                ),

            "reference_price":
                round(
                    reference_price,
                    2
                ),

            "reference_source":
                reference_source,

            "api_price":
                (
                    round(
                        api_price,
                        2
                    )
                    if api_price is not None
                    else None
                ),

            "historical_price":
                historical.get(
                    "historical_price"
                ),

            "previous_price":
                historical.get(
                    "previous_price"
                ),

            "price_lag2":
                historical.get(
                    "price_lag2"
                ),

            "price_lag3":
                historical.get(
                    "price_lag3"
                ),

            "rolling_mean":
                historical.get(
                    "rolling_mean"
                ),

            "rolling_median":
                historical.get(
                    "rolling_median"
                ),

            "price_change":
                historical.get(
                    "price_change"
                ),

            "price_change_percentage":
                historical.get(
                    "price_change_percentage"
                ),

            "price_ratio":
                historical.get(
                    "price_ratio"
                ),

            "price_trend":
                historical.get(
                    "price_trend"
                ),

            "historical_records":
                historical.get(
                    "historical_records",
                    0
                ),

            "api_source":
                api_data.get(
                    "api_source"
                ),

            "currency":
                final_currency,

            "fused_record":
                fused_record
        }

        if save_to_csv:

            try:

                result[
                    "fused_dataset"
                ] = cls.save_fused_record(
                    fused_record
                )

            except Exception as exc:

                result[
                    "fused_dataset_error"
                ] = str(exc)

        return result

    # ========================================================
    # SAVE ONE RECORD
    # ========================================================

    @classmethod
    def save_fused_record(
        cls,
        fused_record: Dict[str, Any],
        output_path: Optional[str] = None
    ) -> str:

        path = (
            Path(output_path)
            if output_path
            else FUSED_DATASET
        )

        path.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        row = {
            column:
                fused_record.get(
                    column,
                    np.nan
                )
            for column in FUSED_COLUMNS
        }

        new_df = pd.DataFrame(
            [row],
            columns=FUSED_COLUMNS
        )

        if path.exists():

            try:

                old_df = pd.read_csv(
                    path
                )

                for column in FUSED_COLUMNS:

                    if column not in old_df.columns:
                        old_df[column] = np.nan

                old_df = old_df[
                    FUSED_COLUMNS
                ]

                final_df = pd.concat(
                    [
                        old_df,
                        new_df
                    ],
                    ignore_index=True
                )

            except Exception:

                final_df = new_df

        else:

            final_df = new_df

        final_df.to_csv(
            path,
            index=False
        )

        return str(path)

    # ========================================================
    # SAVE MANY
    # ========================================================

    @classmethod
    def save_many_records(
        cls,
        records: List[Dict[str, Any]],
        output_path: Optional[str] = None
    ) -> str:

        path = (
            Path(output_path)
            if output_path
            else FUSED_DATASET
        )

        path.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        rows = [
            {
                column:
                    record.get(
                        column,
                        np.nan
                    )
                for column in FUSED_COLUMNS
            }
            for record in records
        ]

        new_df = pd.DataFrame(
            rows,
            columns=FUSED_COLUMNS
        )

        if path.exists():

            try:

                old_df = pd.read_csv(
                    path
                )

                for column in FUSED_COLUMNS:

                    if column not in old_df.columns:
                        old_df[column] = np.nan

                old_df = old_df[
                    FUSED_COLUMNS
                ]

                final_df = pd.concat(
                    [
                        old_df,
                        new_df
                    ],
                    ignore_index=True
                )

            except Exception:

                final_df = new_df

        else:

            final_df = new_df

        final_df.to_csv(
            path,
            index=False
        )

        return str(path)

    # ========================================================
    # PREDICTION FEATURES
    # ========================================================

    @classmethod
    def get_prediction_features(
        cls,
        fused_result: Dict[str, Any]
    ) -> Dict[str, Any]:

        fused = fused_result.get(
            "fused_record",
            {}
        )

        features = dict(
            fused
        )

        features.pop(
            "future_price",
            None
        )

        return features
