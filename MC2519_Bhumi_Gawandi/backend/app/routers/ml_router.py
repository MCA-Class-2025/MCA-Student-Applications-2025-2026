from pathlib import Path
from datetime import date

import joblib
import pandas as pd

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.ml_prediction_service import (
    MLPredictionService
)


# ============================================================
# ROUTER
# ============================================================

router = APIRouter(
    prefix="/api/v1/ml",
    tags=["Machine Learning"]
)


# ============================================================
# PROJECT PATHS
# ============================================================

PROJECT_ROOT = (
    Path(__file__)
    .resolve()
    .parents[3]
)

ML_MODELS_PATH = (
    PROJECT_ROOT
    / "ml"
    / "models"
)

ML_DATASET_PATH = (
    PROJECT_ROOT
    / "ml"
    / "dataset"
)

PROCESSED_DATASET_PATH = (
    ML_DATASET_PATH
    / "processed"
)


# ============================================================
# EXISTING MODEL FILES
# ============================================================

ANOMALY_MODEL_PATH = (
    ML_MODELS_PATH
    / "anomaly_model.pkl"
)

FORECAST_MODEL_PATH = (
    ML_MODELS_PATH
    / "expense_forecast_model.pkl"
)

MONTHLY_DATASET_PATH = (
    ML_DATASET_PATH
    / "monthly_expenses.csv"
)


# ============================================================
# PRICE DATASETS
# ============================================================

GROCERY_PRICE_DATASET = (
    PROCESSED_DATASET_PATH
    / "grocery_price_history.csv"
)

ELECTRONICS_PRICE_DATASET = (
    PROCESSED_DATASET_PATH
    / "electronics_price_history.csv"
)


# ============================================================
# LOAD EXISTING ANOMALY MODEL
# ============================================================

anomaly_model = None

try:

    anomaly_model = joblib.load(
        ANOMALY_MODEL_PATH
    )

    print(
        "Anomaly model loaded successfully."
    )

except Exception as error:

    print(
        "Anomaly model error:",
        error
    )


# ============================================================
# LOAD EXISTING EXPENSE FORECAST MODEL
# ============================================================

forecast_model = None

try:

    forecast_model = joblib.load(
        FORECAST_MODEL_PATH
    )

    print(
        "Forecast model loaded successfully."
    )

except Exception as error:

    print(
        "Forecast model error:",
        error
    )


# ============================================================
# EXISTING EXPENSE ANALYSIS REQUEST
# ============================================================

class ExpenseAnalysisRequest(BaseModel):

    amount: float = Field(
        ...,
        gt=0
    )

    category: str = Field(
        ...,
        min_length=1
    )

    transaction_date: date


# ============================================================
# GROCERY PRICE PREDICTION REQUEST
#
# current_price is OPTIONAL now.
#
# If frontend sends it, it is ignored for the actual
# prediction price.
#
# Backend obtains the latest price from the project
# Price API dataset.
# ============================================================

class GroceryPricePredictionRequest(BaseModel):

    product: str = Field(
        ...,
        min_length=1
    )

    current_price: float | None = Field(
        default=None,
        gt=0
    )

    year: int = Field(
        ...,
        ge=1900
    )

    month: int = Field(
        ...,
        ge=1,
        le=12
    )

    quarter: int = Field(
        ...,
        ge=1,
        le=4
    )


# ============================================================
# ELECTRONICS PRICE PREDICTION REQUEST
# ============================================================

class ElectronicsPricePredictionRequest(BaseModel):

    product: str = Field(
        ...,
        min_length=1
    )

    category: str = "Electronics"

    brand: str = "Unknown"

    merchant: str = "Unknown"

    currency: str = "USD"

    current_price: float | None = Field(
        default=None,
        gt=0
    )

    year: int = Field(
        ...,
        ge=1900
    )

    month: int = Field(
        ...,
        ge=1,
        le=12
    )

    quarter: int = Field(
        ...,
        ge=1,
        le=4
    )


# ============================================================
# PRICE API DATA LOADER
#
# This is used internally by the ML endpoint.
#
# The frontend does NOT decide the actual prediction price.
# The backend gets it from the project's price dataset.
# ============================================================

def load_price_dataset(
    category: str
) -> pd.DataFrame:

    category = (
        category
        .strip()
        .lower()
    )

    if category == "grocery":

        file_path = (
            GROCERY_PRICE_DATASET
        )

    elif category == "electronics":

        file_path = (
            ELECTRONICS_PRICE_DATASET
        )

    else:

        raise HTTPException(
            status_code=400,
            detail=(
                "Category must be "
                "'grocery' or "
                "'electronics'."
            )
        )

    if not file_path.exists():

        raise HTTPException(
            status_code=404,
            detail=(
                f"Price dataset not found: "
                f"{file_path}"
            )
        )

    try:

        df = pd.read_csv(
            file_path,
            low_memory=False
        )

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=(
                "Could not read price dataset: "
                f"{error}"
            )
        )

    if df.empty:

        raise HTTPException(
            status_code=404,
            detail="Price dataset is empty."
        )

    return df


# ============================================================
# NORMALIZE PRODUCT
# ============================================================

def normalize_product(
    value: str
) -> str:

    return (
        str(value)
        .strip()
        .lower()
    )


# ============================================================
# GET API CURRENT PRICE
#
# This is the important new part.
#
# The ML prediction uses the current price returned by
# the project's Price API data source.
# ============================================================

def get_api_current_price(
    category: str,
    product: str,
    brand: str | None = None
):

    df = load_price_dataset(
        category
    )

    if "Product" not in df.columns:

        raise HTTPException(
            status_code=500,
            detail=(
                "Product column is missing "
                "from price dataset."
            )
        )

    if "Price" not in df.columns:

        raise HTTPException(
            status_code=500,
            detail=(
                "Price column is missing "
                "from price dataset."
            )
        )

    # --------------------------------------------------------
    # Normalize
    # --------------------------------------------------------

    df = df.copy()

    df["_product_normalized"] = (
        df["Product"]
        .fillna("")
        .astype(str)
        .str.strip()
        .str.lower()
    )

    search_product = normalize_product(
        product
    )

    # --------------------------------------------------------
    # Exact product match
    # --------------------------------------------------------

    matches = df[
        df["_product_normalized"]
        ==
        search_product
    ].copy()

    # --------------------------------------------------------
    # Starts-with match
    # --------------------------------------------------------

    if matches.empty:

        matches = df[
            df["_product_normalized"]
            .str.startswith(
                search_product,
                na=False
            )
        ].copy()

    # --------------------------------------------------------
    # Contains match
    # --------------------------------------------------------

    if matches.empty:

        matches = df[
            df["_product_normalized"]
            .str.contains(
                search_product,
                regex=False,
                na=False
            )
        ].copy()

    # --------------------------------------------------------
    # Electronics brand filtering
    # --------------------------------------------------------

    if (

        category.lower()
        == "electronics"

        and brand

        and brand.lower()
        not in [
            "",
            "unknown",
            "none",
            "null"
        ]

        and "Brand" in matches.columns

    ):

        brand_search = normalize_product(
            brand
        )

        brand_matches = matches[
            matches["Brand"]
            .fillna("")
            .astype(str)
            .str.strip()
            .str.lower()
            .str.contains(
                brand_search,
                regex=False,
                na=False
            )
        ]

        if not brand_matches.empty:

            matches = (
                brand_matches
            )

    # --------------------------------------------------------
    # Product not found
    # --------------------------------------------------------

    if matches.empty:

        examples = (
            df["Product"]
            .dropna()
            .astype(str)
            .drop_duplicates()
            .head(20)
            .tolist()
        )

        raise HTTPException(
            status_code=404,
            detail={
                "message":
                    (
                        f"Product '{product}' "
                        "was not found."
                    ),

                "category":
                    category,

                "available_products":
                    examples
            }
        )

    # --------------------------------------------------------
    # Convert price
    # --------------------------------------------------------

    matches["_price_numeric"] = (
        pd.to_numeric(
            matches["Price"],
            errors="coerce"
        )
    )

    matches = matches[
        matches["_price_numeric"] > 0
    ].copy()

    if matches.empty:

        raise HTTPException(
            status_code=404,
            detail=(
                "No valid price found "
                "for this product."
            )
        )

    # --------------------------------------------------------
    # Sort by date
    # --------------------------------------------------------

    if "Date" in matches.columns:

        matches["_date"] = (
            pd.to_datetime(
                matches["Date"],
                errors="coerce",
                utc=True
            )
        )

        try:

            matches["_date"] = (
                matches["_date"]
                .dt
                .tz_localize(None)
            )

        except Exception:

            pass

        valid_dates = matches[
            matches["_date"].notna()
        ]

        if not valid_dates.empty:

            matches = (
                valid_dates
                .sort_values(
                    "_date"
                )
            )

    # --------------------------------------------------------
    # Latest record
    # --------------------------------------------------------

    latest = (
        matches.iloc[-1]
    )

    current_price = float(
        latest["_price_numeric"]
    )

    # --------------------------------------------------------
    # Previous price
    # --------------------------------------------------------

    if len(matches) >= 2:

        previous_price = float(
            matches
            .iloc[-2]
            ["_price_numeric"]
        )

    else:

        previous_price = (
            current_price
        )

    # --------------------------------------------------------
    # API date
    # --------------------------------------------------------

    api_date = ""

    if "Date" in matches.columns:

        value = latest.get(
            "Date"
        )

        if pd.notna(value):

            api_date = str(
                value
            )

    # --------------------------------------------------------
    # API brand
    # --------------------------------------------------------

    matched_brand = (
        brand
        if brand
        else "Unknown"
    )

    if "Brand" in latest.index:

        value = latest.get(
            "Brand"
        )

        if pd.notna(value):

            matched_brand = str(
                value
            )

    # --------------------------------------------------------
    # Merchant
    # --------------------------------------------------------

    merchant = "Unknown"

    if "Merchant" in latest.index:

        value = latest.get(
            "Merchant"
        )

        if pd.notna(value):

            merchant = str(
                value
            )

    # --------------------------------------------------------
    # Currency
    # --------------------------------------------------------

    currency = "INR"

    if "Currency" in latest.index:

        value = latest.get(
            "Currency"
        )

        if pd.notna(value):

            currency = str(
                value
            )

    # --------------------------------------------------------
    # Price change
    # --------------------------------------------------------

    price_change = (
        current_price
        -
        previous_price
    )

    if previous_price != 0:

        price_change_percent = (

            price_change
            /
            previous_price

        ) * 100

    else:

        price_change_percent = 0.0

    # --------------------------------------------------------
    # Return API information
    # --------------------------------------------------------

    return {

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

        "price_change":
            round(
                price_change,
                2
            ),

        "price_change_percentage":
            round(
                price_change_percent,
                2
            ),

        "matched_product":
            str(
                latest["Product"]
            ),

        "brand":
            matched_brand,

        "merchant":
            merchant,

        "currency":
            currency,

        "date":
            api_date,

        "historical_records":
            int(
                len(matches)
            ),

        "source":
            "Own Project Price API",

        "dataset":
            (
                "grocery_price_history.csv"
                if category.lower()
                == "grocery"

                else
                "electronics_price_history.csv"
            )

    }


# ============================================================
# UPDATE REQUEST CURRENT PRICE
#
# We create a copy so that the original request structure
# remains unchanged.
# ============================================================

def update_request_price(
    request,
    api_price
):

    try:

        # Pydantic v2

        updated = request.model_copy(
            update={
                "current_price":
                    api_price
            }
        )

        return updated

    except AttributeError:

        # Pydantic v1

        updated = request.copy(
            update={
                "current_price":
                    api_price
            }
        )

        return updated


# ============================================================
# API 1
# EXISTING ANOMALY ANALYSIS
#
# DO NOT CHANGE THIS API.
# ============================================================

@router.post(
    "/analyze",
    summary="Analyze Expense"
)
async def analyze_expense(
    expense: ExpenseAnalysisRequest
):

    try:

        if anomaly_model is None:

            raise HTTPException(
                status_code=500,
                detail=(
                    "Anomaly model "
                    "is not loaded."
                )
            )

        transaction_date = (
            expense.transaction_date
        )

        day_of_week = (
            transaction_date.weekday()
        )

        is_weekend = (
            1
            if day_of_week >= 5
            else 0
        )

        input_data = pd.DataFrame([
            {

                "Amount":
                    float(
                        expense.amount
                    ),

                "Year":
                    transaction_date.year,

                "Month":
                    transaction_date.month,

                "DayOfWeek":
                    day_of_week,

                "IsWeekend":
                    is_weekend,

                "TypeEncoded":
                    0
            }
        ])

        prediction = (
            anomaly_model
            .predict(
                input_data
            )[0]
        )

        anomaly_score = (
            anomaly_model
            .decision_function(
                input_data
            )[0]
        )

        prediction = int(
            prediction
        )

        anomaly_score = float(
            anomaly_score
        )

        is_anomaly = (
            prediction == -1
        )

        if is_anomaly:

            status = "Anomaly"

            message = (
                "Unusual expense detected"
            )

        else:

            status = "Normal"

            message = (
                "Expense appears normal"
            )

        return {

            "success":
                True,

            "data": {

                "amount":
                    float(
                        expense.amount
                    ),

                "category":
                    expense.category,

                "date":
                    str(
                        transaction_date
                    ),

                "status":
                    status,

                "is_anomaly":
                    is_anomaly,

                "anomaly_score":
                    round(
                        anomaly_score,
                        6
                    ),

                "message":
                    message
            }
        }

    except HTTPException:

        raise

    except Exception as error:

        print(
            "ANALYZE ERROR:",
            repr(error)
        )

        raise HTTPException(
            status_code=500,
            detail=str(error)
        )


# ============================================================
# API 2
# EXISTING MONTHLY EXPENSE FORECAST
#
# DO NOT CHANGE THIS API.
# ============================================================

@router.get(
    "/forecast",
    summary="Forecast Expense"
)
async def forecast_expense():

    try:

        if forecast_model is None:

            raise HTTPException(
                status_code=500,
                detail=(
                    "Forecast model "
                    "is not loaded."
                )
            )

        if not MONTHLY_DATASET_PATH.exists():

            raise HTTPException(
                status_code=404,
                detail=(
                    "monthly_expenses.csv "
                    "not found."
                )
            )

        df = pd.read_csv(
            MONTHLY_DATASET_PATH
        )

        if df.empty:

            raise HTTPException(
                status_code=404,
                detail=(
                    "Monthly dataset "
                    "is empty."
                )
            )

        df = (
            df.sort_values(
                "YearMonth"
            )
            .reset_index(
                drop=True
            )
        )

        if len(df) < 3:

            raise HTTPException(
                status_code=400,
                detail=(
                    "At least 3 months "
                    "are required."
                )
            )

        latest = df.iloc[-1]

        previous_expense = float(
            latest["Total_Expense"]
        )

        previous_income = float(
            latest["Total_Income"]
        )

        previous_transaction_count = int(
            latest["Transaction_Count"]
        )

        rolling_average = float(
            df["Total_Expense"]
            .tail(3)
            .mean()
        )

        latest_date = pd.to_datetime(
            latest["YearMonth"]
        )

        next_month_date = (
            latest_date
            + pd.DateOffset(
                months=1
            )
        )

        next_year = int(
            next_month_date.year
        )

        next_month = int(
            next_month_date.month
        )

        input_data = pd.DataFrame([
            {

                "Year":
                    next_year,

                "Month":
                    next_month,

                "Previous_Expense":
                    previous_expense,

                "Previous_Income":
                    previous_income,

                "Previous_Transaction_Count":
                    previous_transaction_count,

                "Expense_Rolling_Average":
                    rolling_average
            }
        ])

        prediction = (
            forecast_model
            .predict(
                input_data
            )[0]
        )

        predicted_expense = max(
            0.0,
            float(
                prediction
            )
        )

        difference = (
            predicted_expense
            - previous_expense
        )

        percentage_change = 0

        if previous_expense > 0:

            percentage_change = (
                difference
                / previous_expense
            ) * 100

        return {

            "success":
                True,

            "data": {

                "forecast_month":
                    f"{next_year}-{next_month:02d}",

                "predicted_expense":
                    round(
                        predicted_expense,
                        2
                    ),

                "previous_month_expense":
                    round(
                        previous_expense,
                        2
                    ),

                "three_month_average":
                    round(
                        rolling_average,
                        2
                    ),

                "difference_from_previous_month":
                    round(
                        difference,
                        2
                    ),

                "percentage_change":
                    round(
                        percentage_change,
                        2
                    )
            }
        }

    except HTTPException:

        raise

    except Exception as error:

        print(
            "FORECAST ERROR:",
            repr(error)
        )

        raise HTTPException(
            status_code=500,
            detail=str(error)
        )


# ============================================================
# API 3
# GROCERY PRICE PREDICTION
#
# POST:
#
# /api/v1/ml/price-forecast/grocery
# ============================================================

@router.post(
    "/price-forecast/grocery",
    summary="Predict Future Grocery Price"
)
async def predict_grocery_price(
    request: GroceryPricePredictionRequest
):

    try:

        # ====================================================
        # STEP 1
        # GET CURRENT PRICE FROM OWN PRICE API
        # ====================================================

        api_data = get_api_current_price(

            category="grocery",

            product=request.product

        )

        print()
        print(
            "========== GROCERY PRICE API =========="
        )

        print(
            "Requested product:",
            request.product
        )

        print(
            "Matched product:",
            api_data["matched_product"]
        )

        print(
            "API current price:",
            api_data["current_price"]
        )

        print(
            "API previous price:",
            api_data["previous_price"]
        )

        print(
            "API source:",
            api_data["source"]
        )

        print(
            "========================================"
        )

        # ====================================================
        # STEP 2
        # UPDATE REQUEST WITH API PRICE
        # ====================================================

        prediction_request = (
            update_request_price(

                request,

                api_data[
                    "current_price"
                ]

            )
        )

        # ====================================================
        # STEP 3
        # ML PREDICTION
        # ====================================================

        result = (
            MLPredictionService
            .predict_grocery(
                prediction_request
            )
        )

        # ====================================================
        # STEP 4
        # ADD PRICE API INFORMATION
        # ====================================================

        result["price_api"] = {

            "enabled":
                True,

            "source":
                api_data[
                    "source"
                ],

            "dataset":
                api_data[
                    "dataset"
                ],

            "requested_product":
                request.product,

            "matched_product":
                api_data[
                    "matched_product"
                ],

            "current_price":
                api_data[
                    "current_price"
                ],

            "previous_price":
                api_data[
                    "previous_price"
                ],

            "price_change":
                api_data[
                    "price_change"
                ],

            "price_change_percentage":
                api_data[
                    "price_change_percentage"
                ],

            "date":
                api_data[
                    "date"
                ]

        }

        # ====================================================
        # IMPORTANT
        #
        # Clearly identify the predicted value.
        # ====================================================

        result["prediction_source"] = (
            "Own Project Price API + "
            "Historical Dataset + "
            "Machine Learning Model"
        )

        result["prediction_note"] = (
            "The current price is obtained "
            "from the project's Price API. "
            "The future price is calculated "
            "by the trained ML model."
        )

        return result

    except HTTPException:

        raise

    except FileNotFoundError as error:

        raise HTTPException(
            status_code=404,
            detail=str(error)
        )

    except ValueError as error:

        raise HTTPException(
            status_code=400,
            detail=str(error)
        )

    except Exception as error:

        print(
            "GROCERY PRICE PREDICTION ERROR:",
            repr(error)
        )

        raise HTTPException(
            status_code=500,
            detail=str(error)
        )


# ============================================================
# API 4
# ELECTRONICS PRICE PREDICTION
#
# POST:
#
# /api/v1/ml/price-forecast/electronics
# ============================================================

@router.post(
    "/price-forecast/electronics",
    summary="Predict Future Electronics Price"
)
async def predict_electronics_price(
    request: ElectronicsPricePredictionRequest
):

    try:

        # ====================================================
        # STEP 1
        # GET CURRENT PRICE FROM OWN PRICE API
        # ====================================================

        api_data = get_api_current_price(

            category="electronics",

            product=request.product,

            brand=request.brand

        )

        print()
        print(
            "======= ELECTRONICS PRICE API ======="
        )

        print(
            "Requested product:",
            request.product
        )

        print(
            "Requested brand:",
            request.brand
        )

        print(
            "Matched product:",
            api_data["matched_product"]
        )

        print(
            "Matched brand:",
            api_data["brand"]
        )

        print(
            "API current price:",
            api_data["current_price"]
        )

        print(
            "API previous price:",
            api_data["previous_price"]
        )

        print(
            "API currency:",
            api_data["currency"]
        )

        print(
            "======================================"
        )

        # ====================================================
        # STEP 2
        # UPDATE REQUEST WITH API PRICE
        # ====================================================

        prediction_request = (
            update_request_price(

                request,

                api_data[
                    "current_price"
                ]

            )
        )

        # ====================================================
        # ALSO USE API BRAND / MERCHANT / CURRENCY
        # ====================================================

        try:

            prediction_request = (
                prediction_request
                .model_copy(
                    update={

                        "brand":
                            api_data[
                                "brand"
                            ],

                        "merchant":
                            api_data[
                                "merchant"
                            ],

                        "currency":
                            api_data[
                                "currency"
                            ]

                    }
                )
            )

        except AttributeError:

            prediction_request = (
                prediction_request
                .copy(
                    update={

                        "brand":
                            api_data[
                                "brand"
                            ],

                        "merchant":
                            api_data[
                                "merchant"
                            ],

                        "currency":
                            api_data[
                                "currency"
                            ]

                    }
                )
            )

        # ====================================================
        # STEP 3
        # ML PREDICTION
        # ====================================================

        result = (
            MLPredictionService
            .predict_electronics(
                prediction_request
            )
        )

        # ====================================================
        # STEP 4
        # ADD PRICE API INFORMATION
        # ====================================================

        result["price_api"] = {

            "enabled":
                True,

            "source":
                api_data[
                    "source"
                ],

            "dataset":
                api_data[
                    "dataset"
                ],

            "requested_product":
                request.product,

            "matched_product":
                api_data[
                    "matched_product"
                ],

            "requested_brand":
                request.brand,

            "matched_brand":
                api_data[
                    "brand"
                ],

            "current_price":
                api_data[
                    "current_price"
                ],

            "previous_price":
                api_data[
                    "previous_price"
                ],

            "price_change":
                api_data[
                    "price_change"
                ],

            "price_change_percentage":
                api_data[
                    "price_change_percentage"
                ],

            "currency":
                api_data[
                    "currency"
                ],

            "merchant":
                api_data[
                    "merchant"
                ],

            "date":
                api_data[
                    "date"
                ]

        }

        # ====================================================
        # IMPORTANT
        # ====================================================

        result["prediction_source"] = (
            "Own Project Price API + "
            "Historical Dataset + "
            "Machine Learning Model"
        )

        result["prediction_note"] = (
            "The current price is obtained "
            "from the project's Price API. "
            "The future price is calculated "
            "by the trained ML model."
        )

        return result

    except HTTPException:

        raise

    except FileNotFoundError as error:

        raise HTTPException(
            status_code=404,
            detail=str(error)
        )

    except ValueError as error:

        raise HTTPException(
            status_code=400,
            detail=str(error)
        )

    except Exception as error:

        print(
            "ELECTRONICS PRICE PREDICTION ERROR:",
            repr(error)
        )

        raise HTTPException(
            status_code=500,
            detail=str(error)
        )