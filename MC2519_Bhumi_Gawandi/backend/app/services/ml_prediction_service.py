
from pathlib import Path
from typing import Optional, Dict, Any, List

import joblib
import numpy as np
import pandas as pd


# ============================================================
# PROJECT ROOT
# ============================================================

CURRENT_FILE = (
    Path(__file__)
    .resolve()
)


def find_project_root():

    candidates = [
        CURRENT_FILE.parent,
        *CURRENT_FILE.parents
    ]

    # --------------------------------------------------------
    # Find project root containing ml/
    # --------------------------------------------------------

    for directory in candidates:

        try:

            if (
                directory / "ml"
            ).is_dir():

                return directory.resolve()

        except Exception:

            continue

    # --------------------------------------------------------
    # Standard project fallback
    # --------------------------------------------------------

    if len(
        CURRENT_FILE.parents
    ) >= 3:

        return (
            CURRENT_FILE
            .parents[3]
            .resolve()
        )

    return (
        CURRENT_FILE
        .parent
        .resolve()
    )


PROJECT_ROOT = (
    find_project_root()
)


# ============================================================
# DIRECTORIES
# ============================================================

MODEL_DIRECTORY = (
    PROJECT_ROOT
    / "ml"
    / "models"
    / "saved"
)


DATASET_DIRECTORY = (
    PROJECT_ROOT
    / "ml"
    / "dataset"
    / "processed"
)


# ============================================================
# MODEL FILES
# ============================================================

GROCERY_MODEL_PATH = (
    MODEL_DIRECTORY
    / "grocery_best_model.pkl"
)


ELECTRONICS_MODEL_PATH = (
    MODEL_DIRECTORY
    / "electronics_best_model.pkl"
)


# ============================================================
# DATASET FILES
# ============================================================

GROCERY_DATASET_PATH = (
    DATASET_DIRECTORY
    / "grocery_price_history.csv"
)


ELECTRONICS_DATASET_PATH = (
    DATASET_DIRECTORY
    / "electronics_price_history.csv"
)


# ============================================================
# CONFIGURATION
# ============================================================

print()
print("=" * 70)
print("          PRICE PREDICTION ML SERVICE")
print("=" * 70)

print()
print("Project root:")
print(PROJECT_ROOT)

print()
print("Model directory:")
print(MODEL_DIRECTORY)

print()
print("Dataset directory:")
print(DATASET_DIRECTORY)

print()
print("Grocery model:")
print(GROCERY_MODEL_PATH)
print("Exists:", GROCERY_MODEL_PATH.exists())

print()
print("Electronics model:")
print(ELECTRONICS_MODEL_PATH)
print("Exists:", ELECTRONICS_MODEL_PATH.exists())

print()
print("Grocery dataset:")
print(GROCERY_DATASET_PATH)
print("Exists:", GROCERY_DATASET_PATH.exists())

print()
print("Electronics dataset:")
print(ELECTRONICS_DATASET_PATH)
print("Exists:", ELECTRONICS_DATASET_PATH.exists())

print("=" * 70)
print()


# ============================================================
# ML PREDICTION SERVICE
# ============================================================

class MLPredictionService:

    # ========================================================
    # VALIDATE FILES
    # ========================================================

    @staticmethod
    def validate_files():

        errors = []

        required_files = {

            "Grocery model":
                GROCERY_MODEL_PATH,

            "Electronics model":
                ELECTRONICS_MODEL_PATH,

            "Grocery dataset":
                GROCERY_DATASET_PATH,

            "Electronics dataset":
                ELECTRONICS_DATASET_PATH

        }

        for name, path in required_files.items():

            if not path.exists():

                errors.append(
                    f"{name} not found: {path}"
                )

        if errors:

            raise FileNotFoundError(
                "Price prediction files are missing:\n"
                +
                "\n".join(
                    errors
                )
            )

        return True


    # ========================================================
    # LOAD GROCERY MODEL
    # ========================================================

    @staticmethod
    def load_grocery_model():

        if not GROCERY_MODEL_PATH.exists():

            raise FileNotFoundError(
                "Grocery model not found: "
                f"{GROCERY_MODEL_PATH}"
            )

        try:

            model = joblib.load(
                GROCERY_MODEL_PATH
            )

        except Exception as error:

            raise ValueError(
                "Could not load grocery model: "
                f"{error}"
            )

        print(
            "Grocery ML model loaded."
        )

        return model


    # ========================================================
    # LOAD ELECTRONICS MODEL
    # ========================================================

    @staticmethod
    def load_electronics_model():

        if not ELECTRONICS_MODEL_PATH.exists():

            raise FileNotFoundError(
                "Electronics model not found: "
                f"{ELECTRONICS_MODEL_PATH}"
            )

        try:

            model = joblib.load(
                ELECTRONICS_MODEL_PATH
            )

        except Exception as error:

            raise ValueError(
                "Could not load electronics model: "
                f"{error}"
            )

        print(
            "Electronics ML model loaded."
        )

        return model


    # ========================================================
    # LOAD GROCERY DATASET
    # ========================================================

    @staticmethod
    def load_grocery_dataset():

        if not GROCERY_DATASET_PATH.exists():

            raise FileNotFoundError(
                "Grocery dataset not found: "
                f"{GROCERY_DATASET_PATH}"
            )

        df = pd.read_csv(
            GROCERY_DATASET_PATH,
            low_memory=False
        )

        if df.empty:

            raise ValueError(
                "Grocery dataset is empty."
            )

        return (
            MLPredictionService
            .prepare_dataset(
                df,
                "grocery"
            )
        )


    # ========================================================
    # LOAD ELECTRONICS DATASET
    # ========================================================

    @staticmethod
    def load_electronics_dataset():

        if not ELECTRONICS_DATASET_PATH.exists():

            raise FileNotFoundError(
                "Electronics dataset not found: "
                f"{ELECTRONICS_DATASET_PATH}"
            )

        df = pd.read_csv(
            ELECTRONICS_DATASET_PATH,
            low_memory=False
        )

        if df.empty:

            raise ValueError(
                "Electronics dataset is empty."
            )

        return (
            MLPredictionService
            .prepare_dataset(
                df,
                "electronics"
            )
        )


    # ========================================================
    # PREPARE DATASET
    # ========================================================

    @staticmethod
    def prepare_dataset(
        df,
        dataset_type
    ):

        df = df.copy()

        # ----------------------------------------------------
        # Required columns
        # ----------------------------------------------------

        required_columns = [
            "Date",
            "Product",
            "Price"
        ]

        missing = [

            column

            for column
            in required_columns

            if column not in df.columns

        ]

        if missing:

            raise ValueError(
                f"{dataset_type.capitalize()} dataset "
                f"is missing columns: {missing}. "
                f"Available columns: "
                f"{list(df.columns)}"
            )

        # ----------------------------------------------------
        # Date
        # ----------------------------------------------------

        df["Date"] = pd.to_datetime(
            df["Date"],
            errors="coerce",
            utc=True
        )

        try:

            df["Date"] = (
                df["Date"]
                .dt
                .tz_localize(None)
            )

        except Exception:

            pass

        # ----------------------------------------------------
        # Price
        # ----------------------------------------------------

        df["Price"] = pd.to_numeric(
            df["Price"],
            errors="coerce"
        )

        # ----------------------------------------------------
        # Remove invalid prices
        # ----------------------------------------------------

        df = df[
            df["Price"] > 0
        ].copy()

        # ----------------------------------------------------
        # Remove invalid dates
        # ----------------------------------------------------

        df = df[
            df["Date"].notna()
        ].copy()

        # ----------------------------------------------------
        # Product
        # ----------------------------------------------------

        df["Product"] = (
            df["Product"]
            .fillna("")
            .astype(str)
            .str.strip()
        )

        df = df[
            df["Product"] != ""
        ].copy()

        # ----------------------------------------------------
        # Sort
        # ----------------------------------------------------

        df = (
            df
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

        return df


    # ========================================================
    # NORMALIZE PRODUCT
    # ========================================================

    @staticmethod
    def normalize_product(
        product
    ):

        if product is None:

            return ""

        return (
            str(product)
            .strip()
            .lower()
        )


    # ========================================================
    # FIND PRODUCT
    # ========================================================

    @staticmethod
    def find_product_rows(
        df,
        product,
        brand=None,
        merchant=None
    ):

        if df.empty:

            return pd.DataFrame()

        search_product = (
            MLPredictionService
            .normalize_product(
                product
            )
        )

        if not search_product:

            return pd.DataFrame()

        normalized_products = (
            df["Product"]
            .fillna("")
            .astype(str)
            .str.strip()
            .str.lower()
        )

        # ----------------------------------------------------
        # Exact match
        # ----------------------------------------------------

        matches = df[
            normalized_products
            ==
            search_product
        ].copy()

        # ----------------------------------------------------
        # Starts with
        # ----------------------------------------------------

        if matches.empty:

            matches = df[
                normalized_products
                .str.startswith(
                    search_product,
                    na=False
                )
            ].copy()

        # ----------------------------------------------------
        # Contains
        # ----------------------------------------------------

        if matches.empty:

            matches = df[
                normalized_products
                .str.contains(
                    search_product,
                    regex=False,
                    na=False
                )
            ].copy()

        # ----------------------------------------------------
        # Word matching
        # ----------------------------------------------------

        if matches.empty:

            words = [

                word

                for word
                in search_product.split()

                if len(word) >= 2

            ]

            if words:

                mask = pd.Series(
                    True,
                    index=df.index
                )

                for word in words:

                    mask = (

                        mask
                        &
                        normalized_products
                        .str.contains(
                            word,
                            regex=False,
                            na=False
                        )

                    )

                matches = df[
                    mask
                ].copy()

        # ----------------------------------------------------
        # Brand filter
        # ----------------------------------------------------

        if (

            brand
            and
            "Brand" in matches.columns

        ):

            search_brand = (
                str(brand)
                .strip()
                .lower()
            )

            if search_brand not in [
                "",
                "unknown",
                "none",
                "null"
            ]:

                brand_values = (
                    matches["Brand"]
                    .fillna("")
                    .astype(str)
                    .str.strip()
                    .str.lower()
                )

                brand_matches = matches[
                    brand_values
                    .str.contains(
                        search_brand,
                        regex=False,
                        na=False
                    )
                ]

                if not brand_matches.empty:

                    matches = (
                        brand_matches
                    )


        # ----------------------------------------------------
        # Merchant filter
        # ----------------------------------------------------

        if (

            merchant
            and
            "Merchant" in matches.columns

        ):

            search_merchant = (
                str(merchant)
                .strip()
                .lower()
            )

            if search_merchant not in [
                "",
                "unknown",
                "none",
                "null"
            ]:

                merchant_values = (
                    matches["Merchant"]
                    .fillna("")
                    .astype(str)
                    .str.strip()
                    .str.lower()
                )

                merchant_matches = matches[
                    merchant_values
                    .str.contains(
                        search_merchant,
                        regex=False,
                        na=False
                    )
                ]

                if not merchant_matches.empty:

                    matches = (
                        merchant_matches
                    )

        return matches


    # ========================================================
    # HISTORICAL CONTEXT
    # ========================================================

    @staticmethod
    def get_historical_context(
        df,
        product,
        year,
        month,
        dataset_type,
        brand=None,
        merchant=None
    ):

        if df.empty:

            raise ValueError(
                "Historical dataset is empty."
            )

        # ----------------------------------------------------
        # Find product
        # ----------------------------------------------------

        matches = (
            MLPredictionService
            .find_product_rows(
                df,
                product,
                brand,
                merchant
            )
        )

        if matches.empty:

            available_products = (
                df["Product"]
                .dropna()
                .astype(str)
                .drop_duplicates()
                .head(20)
                .tolist()
            )

            raise ValueError(

                f"Product '{product}' "
                "not found in historical dataset. "
                f"Available examples: "
                f"{available_products}"

            )

        # ----------------------------------------------------
        # Sort chronologically
        # ----------------------------------------------------

        matches = (
            matches
            .sort_values(
                "Date"
            )
            .reset_index(
                drop=True
            )
        )

        # ----------------------------------------------------
        # Keep positive prices
        # ----------------------------------------------------

        matches["Price"] = pd.to_numeric(
            matches["Price"],
            errors="coerce"
        )

        matches = matches[
            matches["Price"] > 0
        ].copy()

        if matches.empty:

            raise ValueError(
                "No valid positive historical "
                "prices found for this product."
            )

        # ----------------------------------------------------
        # Last historical records
        # ----------------------------------------------------

        last_rows = (
            matches
            .tail(3)
            .copy()
        )

        prices = (
            last_rows["Price"]
            .astype(float)
            .tolist()
        )

        # ----------------------------------------------------
        # Previous price
        # ----------------------------------------------------

        previous_price = float(
            prices[-1]
        )

        # ----------------------------------------------------
        # Lag 2
        # ----------------------------------------------------

        price_lag2 = (

            float(
                prices[-2]
            )

            if len(prices) >= 2

            else previous_price

        )

        # ----------------------------------------------------
        # Lag 3
        # ----------------------------------------------------

        price_lag3 = (

            float(
                prices[-3]
            )

            if len(prices) >= 3

            else price_lag2

        )

        # ----------------------------------------------------
        # Rolling statistics
        # ----------------------------------------------------

        rolling_mean = float(
            np.mean(
                prices
            )
        )

        rolling_median = float(
            np.median(
                prices
            )
        )

        # ----------------------------------------------------
        # Historical percentage change
        # ----------------------------------------------------

        if price_lag2 != 0:

            historical_change_percent = (

                (
                    previous_price
                    -
                    price_lag2
                )
                /
                price_lag2

            ) * 100

        else:

            historical_change_percent = 0.0

        # ----------------------------------------------------
        # Overall historical change
        # ----------------------------------------------------

        if price_lag3 != 0:

            overall_change_percent = (

                (
                    previous_price
                    -
                    price_lag3
                )
                /
                price_lag3

            ) * 100

        else:

            overall_change_percent = 0.0

        # ----------------------------------------------------
        # Historical ratio
        # ----------------------------------------------------

        if price_lag2 != 0:

            historical_ratio = (

                previous_price
                /
                price_lag2

            )

        else:

            historical_ratio = 1.0

        # ----------------------------------------------------
        # Latest date
        # ----------------------------------------------------

        latest_date = (
            last_rows.iloc[-1]["Date"]
        )

        if pd.notna(
            latest_date
        ):

            previous_date = (
                latest_date
                .date()
                .isoformat()
            )

        else:

            previous_date = ""

        # ----------------------------------------------------
        # Matched product
        # ----------------------------------------------------

        matched_product = str(
            last_rows.iloc[-1]["Product"]
        )

        return {

            "matches":
                matches,

            "historical":
                matches,

            "last_rows":
                last_rows,

            "prices":
                prices,

            "previous_price":
                previous_price,

            "price_lag2":
                price_lag2,

            "price_lag3":
                price_lag3,

            "rolling_mean":
                rolling_mean,

            "rolling_median":
                rolling_median,

            "historical_change_percent":
                float(
                    historical_change_percent
                ),

            "overall_change_percent":
                float(
                    overall_change_percent
                ),

            "historical_ratio":
                float(
                    historical_ratio
                ),

            "previous_date":
                previous_date,

            "matched_product":
                matched_product

        }


    # ========================================================
    # BUILD MODEL INPUT
    #
    # This method creates ALL possible features first.
    # Then it uses feature_names_in_ from the saved model.
    #
    # This prevents feature-order and feature-mismatch errors.
    # ========================================================

    @staticmethod
    def build_features(
        current_price,
        context,
        product,
        year,
        month,
        category=None,
        brand=None,
        merchant=None,
        currency=None,
        model=None
    ):

        current_price = float(
            current_price
        )

        if current_price <= 0:

            raise ValueError(
                "Current price must be greater than zero."
            )

        previous_price = float(
            context.get(
                "previous_price",
                current_price
            )
        )

        price_lag2 = float(
            context.get(
                "price_lag2",
                previous_price
            )
        )

        price_lag3 = float(
            context.get(
                "price_lag3",
                price_lag2
            )
        )

        rolling_mean = float(
            context.get(
                "rolling_mean",
                previous_price
            )
        )

        rolling_median = float(
            context.get(
                "rolling_median",
                previous_price
            )
        )

        # ----------------------------------------------------
        # Historical percentage
        # ----------------------------------------------------

        historical_change_percent = float(
            context.get(
                "historical_change_percent",
                0.0
            )
        )

        # ----------------------------------------------------
        # Current price change
        # ----------------------------------------------------

        price_change = (

            current_price
            -
            previous_price

        )

        # ----------------------------------------------------
        # Current price percentage
        #
        # IMPORTANT:
        # We use historical movement as the signal rather
        # than comparing an INR current price directly against
        # a historical USD electronics price.
        # ----------------------------------------------------

        price_change_percent = (
            historical_change_percent
        )

        # ----------------------------------------------------
        # Price ratio
        # ----------------------------------------------------

        if price_lag2 != 0:

            price_ratio = (

                previous_price
                /
                price_lag2

            )

        else:

            price_ratio = 1.0

        # ----------------------------------------------------
        # Price trend
        # ----------------------------------------------------

        if price_lag2 != 0:

            price_trend = (

                previous_price
                -
                price_lag2

            )

        else:

            price_trend = 0.0

        # ----------------------------------------------------
        # Base row
        # ----------------------------------------------------

        row = {

            "Price":
                current_price,

            "PreviousPrice":
                previous_price,

            "PriceLag2":
                price_lag2,

            "PriceLag3":
                price_lag3,

            "RollingMean":
                rolling_mean,

            "RollingMedian":
                rolling_median,

            "PriceChange":
                price_change,

            "PriceTrend":
                price_trend,

            "Year":
                int(year),

            "Month":
                int(month),

            "Quarter":
                (
                    (
                        int(month)
                        - 1
                    )
                    // 3
                ) + 1,

            "PriceChangePercent":
                float(
                    price_change_percent
                ),

            "PriceRatio":
                float(
                    price_ratio
                ),

            "Product":
                str(
                    product
                ),

            "Category":
                str(
                    category
                    if category
                    else "Unknown"
                ),

            "Brand":
                str(
                    brand
                    if brand
                    else "Unknown"
                ),

            "Merchant":
                str(
                    merchant
                    if merchant
                    else "Unknown"
                ),

            "Currency":
                str(
                    currency
                    if currency
                    else "INR"
                )

        }

        # ====================================================
        # MODEL FEATURE NAMES
        # ====================================================

        if model is not None:

            expected_columns = getattr(
                model,
                "feature_names_in_",
                None
            )

            if expected_columns is not None:

                expected_columns = [

                    str(column)

                    for column
                    in expected_columns

                ]

                missing = [

                    column

                    for column
                    in expected_columns

                    if column not in row

                ]

                if missing:

                    raise ValueError(

                        "Unable to construct "
                        "model input. "

                        f"Missing features: "
                        f"{missing}. "

                        f"Available features: "
                        f"{list(row.keys())}"

                    )

                input_data = pd.DataFrame(
                    [
                        {
                            column:
                                row[column]

                            for column
                            in expected_columns
                        }
                    ]
                )

                print()
                print(
                    "MODEL EXPECTED FEATURES:"
                )

                print(
                    expected_columns
                )

                print(
                    "MODEL INPUT:"
                )

                print(
                    input_data.to_dict(
                        orient="records"
                    )
                )

                return input_data

        # ----------------------------------------------------
        # Fallback
        # ----------------------------------------------------

        return pd.DataFrame(
            [row]
        )


    # ========================================================
    # PREDICT RATIO
    #
    # IMPORTANT:
    #
    # Training target:
    #
    # FuturePriceRatio =
    # FuturePrice / Price
    #
    # If the saved model was trained using log target,
    # model output is converted using exp().
    #
    # If the model directly predicts a ratio, the value
    # is used directly.
    #
    # ========================================================

    @staticmethod
    def predict_ratio(
        model,
        input_data
    ):

        if model is None:

            raise ValueError(
                "ML model is not loaded."
            )

        if input_data is None:

            raise ValueError(
                "Model input is empty."
            )

        # ====================================================
        # FEATURE VALIDATION
        # ====================================================

        expected_columns = getattr(
            model,
            "feature_names_in_",
            None
        )

        if expected_columns is not None:

            expected_columns = [

                str(column)

                for column
                in expected_columns

            ]

            missing = [

                column

                for column
                in expected_columns

                if column not in input_data.columns

            ]

            if missing:

                raise ValueError(

                    "Model input columns are missing: "
                    f"{missing}. "

                    f"Available columns: "
                    f"{list(input_data.columns)}"

                )

            input_data = input_data[
                expected_columns
            ].copy()

        # ====================================================
        # MODEL PREDICTION
        # ====================================================

        try:

            prediction = model.predict(
                input_data
            )

        except Exception as exc:

            raise ValueError(

                "ML model prediction failed. "

                f"Input columns: "
                f"{list(input_data.columns)}. "

                f"Error: {exc}"

            ) from exc

        # ====================================================
        # CHECK OUTPUT
        # ====================================================

        if (

            prediction is None
            or
            len(prediction) == 0

        ):

            raise ValueError(
                "ML model returned no prediction."
            )

        raw_prediction = float(
            prediction[0]
        )

        print()
        print(
            "RAW ML MODEL OUTPUT:",
            raw_prediction
        )

        if not np.isfinite(
            raw_prediction
        ):

            raise ValueError(
                "ML model returned "
                "a non-finite prediction."
            )

        # ====================================================
        # DETERMINE MODEL TARGET FORMAT
        # ====================================================
        #
        # Your current training approach uses:
        #
        # FuturePriceRatio
        #
        # Some previous versions used:
        #
        # log(FuturePriceRatio)
        #
        # A negative direct ratio is impossible.
        # Therefore a negative value is treated as a log-space
        # prediction and converted using exp().
        #
        # ====================================================

        if raw_prediction <= 0:

            # ------------------------------------------------
            # Negative output cannot be a valid price ratio.
            # Convert from log-ratio space.
            # ------------------------------------------------

            ratio = float(
                np.exp(
                    raw_prediction
                )
            )

            print(
                "Negative raw output detected."
            )

            print(
                "Treating output as log(FuturePriceRatio)."
            )

        else:

            # ------------------------------------------------
            # Determine whether output looks like a ratio
            # or log-ratio.
            #
            # Values around 1 are normal direct ratios.
            #
            # Very small positive values can be valid ratios.
            #
            # Values between roughly -1 and +1 are also common
            # log-ratio outputs.
            #
            # The saved model metadata is checked first.
            # ------------------------------------------------

            target_name = ""

            for attribute in [

                "target_name_",
                "target_name",
                "target_column",
                "y_name"

            ]:

                value = getattr(
                    model,
                    attribute,
                    None
                )

                if value is not None:

                    target_name = (
                        str(value)
                        .lower()
                    )

                    break

            if (
                "log"
                in target_name
                and
                "ratio"
                in target_name
            ):

                ratio = float(
                    np.exp(
                        raw_prediction
                    )
                )

                print(
                    "Model target indicates "
                    "log ratio."
                )

            else:

                # ------------------------------------------------
                # Most current saved models are trained directly
                # on FuturePriceRatio.
                # ------------------------------------------------

                ratio = float(
                    raw_prediction
                )

        # ====================================================
        # FINAL VALIDATION
        # ====================================================

        if not np.isfinite(
            ratio
        ):

            raise ValueError(
                "ML model returned an invalid "
                "future price ratio."
            )

        if ratio <= 0:

            raise ValueError(

                "Unable to obtain a positive "
                f"prediction ratio from model output: "
                f"{raw_prediction}"

            )

        # ====================================================
        # SAFETY LIMIT
        #
        # Maximum one-step movement:
        #
        # 0.70 = -30%
        # 1.30 = +30%
        #
        # This protects the application from extreme model
        # outputs while preserving the ML prediction.
        # ====================================================

        unclipped_ratio = ratio

        ratio = float(
            np.clip(
                ratio,
                0.70,
                1.30
            )
        )

        print(
            "RAW RATIO:",
            unclipped_ratio
        )

        print(
            "SAFE RATIO:",
            ratio
        )

        return ratio


    # ========================================================
    # CALCULATE FUTURE PRICE
    # ========================================================

    @staticmethod
    def calculate_future_price(
        current_price,
        predicted_ratio
    ):

        current_price = float(
            current_price
        )

        predicted_ratio = float(
            predicted_ratio
        )

        if not np.isfinite(
            current_price
        ):

            raise ValueError(
                "Current price is invalid."
            )

        if current_price <= 0:

            raise ValueError(
                "Current price must be greater than zero."
            )

        if not np.isfinite(
            predicted_ratio
        ):

            raise ValueError(
                "Prediction ratio is invalid."
            )

        if predicted_ratio <= 0:

            raise ValueError(
                "Prediction ratio must be greater than zero."
            )

        future_price = (

            current_price
            *
            predicted_ratio

        )

        if not np.isfinite(
            future_price
        ):

            raise ValueError(
                "Future price calculation returned "
                "an invalid value."
            )

        return round(
            future_price,
            2
        )


    # ========================================================
    # BUILD RESULT
    # ========================================================

    @staticmethod
    def build_result(
        data,
        context,
        predicted_ratio,
        dataset_name,
        prediction_type,
        model_name
    ):

        current_price = float(
            data.current_price
        )

        # ----------------------------------------------------
        # Future price
        # ----------------------------------------------------

        future_price = (
            MLPredictionService
            .calculate_future_price(
                current_price,
                predicted_ratio
            )
        )

        # ----------------------------------------------------
        # Expected change
        # ----------------------------------------------------

        expected_change = (

            future_price
            -
            current_price

        )

        # ----------------------------------------------------
        # Expected change %
        # ----------------------------------------------------

        if current_price != 0:

            expected_change_percent = (

                expected_change
                /
                current_price

            ) * 100

        else:

            expected_change_percent = 0.0

        # ----------------------------------------------------
        # Price direction
        # ----------------------------------------------------

        if expected_change > 0:

            price_direction = (
                "Increase"
            )

        elif expected_change < 0:

            price_direction = (
                "Decrease"
            )

        else:

            price_direction = (
                "Stable"
            )

        # ----------------------------------------------------
        # Historical values
        # ----------------------------------------------------

        previous_price = float(
            context.get(
                "previous_price",
                current_price
            )
        )

        historical_trend = float(
            context.get(
                "historical_change_percent",
                0.0
            )
        )

        overall_trend = float(
            context.get(
                "overall_change_percent",
                0.0
            )
        )

        # ----------------------------------------------------
        # Result
        # ----------------------------------------------------

        result = {

            "success":
                True,

            "product_type":
                (
                    "Electronics"

                    if prediction_type
                    ==
                    "Future Electronics Price"

                    else
                    "Grocery"
                ),

            "dataset":
                dataset_name,

            "product":
                str(
                    data.product
                ),

            "matched_product":
                context.get(
                    "matched_product",
                    str(
                        data.product
                    )
                ),

            "historical_price":
                round(
                    previous_price,
                    2
                ),

            "previous_price":
                round(
                    previous_price,
                    2
                ),

            "previous_price_date":
                context.get(
                    "previous_date",
                    ""
                ),

            "historical_trend_percent":
                round(
                    historical_trend,
                    2
                ),

            "historical_overall_change_percent":
                round(
                    overall_trend,
                    2
                ),

            "current_price":
                round(
                    current_price,
                    2
                ),

            "predicted_ratio":
                round(
                    predicted_ratio,
                    6
                ),

            "predicted_future_price":
                future_price,

            "expected_change":
                round(
                    expected_change,
                    2
                ),

            "expected_change_percent":
                round(
                    expected_change_percent,
                    2
                ),

            "price_direction":
                price_direction,

            "model":
                model_name,

            "prediction_type":
                prediction_type,

            "currency":
                getattr(
                    data,
                    "currency",
                    "INR"
                ),

            "historical_records":
                int(
                    len(
                        context.get(
                            "matches",
                            []
                        )
                    )
                )

        }

        return result


    # ========================================================
    # GROCERY PREDICTION
    # ========================================================

    @staticmethod
    def predict_grocery(
        data
    ):

        # ----------------------------------------------------
        # Load model
        # ----------------------------------------------------

        model = (
            MLPredictionService
            .load_grocery_model()
        )

        # ----------------------------------------------------
        # Load dataset
        # ----------------------------------------------------

        dataset = (
            MLPredictionService
            .load_grocery_dataset()
        )

        # ----------------------------------------------------
        # Historical context
        # ----------------------------------------------------

        context = (

            MLPredictionService
            .get_historical_context(

                df=dataset,

                product=data.product,

                year=data.year,

                month=data.month,

                dataset_type="grocery"

            )

        )

        # ----------------------------------------------------
        # Build model features
        # ----------------------------------------------------

        input_data = (

            MLPredictionService
            .build_features(

                current_price=
                    data.current_price,

                context=
                    context,

                product=
                    data.product,

                year=
                    data.year,

                month=
                    data.month,

                model=
                    model

            )

        )

        # ----------------------------------------------------
        # Prediction
        # ----------------------------------------------------

        predicted_ratio = (

            MLPredictionService
            .predict_ratio(

                model,

                input_data

            )

        )

        # ----------------------------------------------------
        # Result
        # ----------------------------------------------------

        return (

            MLPredictionService
            .build_result(

                data=
                    data,

                context=
                    context,

                predicted_ratio=
                    predicted_ratio,

                dataset_name=
                    "Historical Grocery Dataset",

                prediction_type=
                    "Future Grocery Price",

                model_name=
                    "Gradient Boosting"

            )

        )


    # ========================================================
    # ELECTRONICS PREDICTION
    # ========================================================

    @staticmethod
    def predict_electronics(
        data
    ):

        # ----------------------------------------------------
        # Load model
        # ----------------------------------------------------

        model = (
            MLPredictionService
            .load_electronics_model()
        )

        # ----------------------------------------------------
        # Load dataset
        # ----------------------------------------------------

        dataset = (
            MLPredictionService
            .load_electronics_dataset()
        )

        # ----------------------------------------------------
        # Request values
        # ----------------------------------------------------

        category = getattr(
            data,
            "category",
            "Electronics"
        )

        brand = getattr(
            data,
            "brand",
            "Unknown"
        )

        merchant = getattr(
            data,
            "merchant",
            "Unknown"
        )

        currency = getattr(
            data,
            "currency",
            "USD"
        )

        # ----------------------------------------------------
        # Historical context
        # ----------------------------------------------------

        context = (

            MLPredictionService
            .get_historical_context(

                df=
                    dataset,

                product=
                    data.product,

                year=
                    data.year,

                month=
                    data.month,

                dataset_type=
                    "electronics",

                brand=
                    brand,

                merchant=
                    merchant

            )

        )

        # ----------------------------------------------------
        # Build features
        # ----------------------------------------------------

        input_data = (

            MLPredictionService
            .build_features(

                current_price=
                    data.current_price,

                context=
                    context,

                product=
                    data.product,

                year=
                    data.year,

                month=
                    data.month,

                category=
                    category,

                brand=
                    brand,

                merchant=
                    merchant,

                currency=
                    currency,

                model=
                    model

            )

        )

        # ----------------------------------------------------
        # Prediction
        # ----------------------------------------------------

        predicted_ratio = (

            MLPredictionService
            .predict_ratio(

                model,

                input_data

            )

        )

        # ----------------------------------------------------
        # Result
        # ----------------------------------------------------

        result = (

            MLPredictionService
            .build_result(

                data=
                    data,

                context=
                    context,

                predicted_ratio=
                    predicted_ratio,

                dataset_name=
                    "Datafiniti Electronics Dataset",

                prediction_type=
                    "Future Electronics Price",

                model_name=
                    "Gradient Boosting"

            )

        )

        # ----------------------------------------------------
        # Preserve electronics fields
        # ----------------------------------------------------

        result["category"] = (
            category
        )

        result["brand"] = (
            brand
        )

        result["merchant"] = (
            merchant
        )

        result["currency"] = (
            currency
        )

        return result