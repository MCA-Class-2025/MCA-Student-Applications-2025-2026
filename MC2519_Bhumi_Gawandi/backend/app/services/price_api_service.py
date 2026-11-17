import os
import re
import requests

from datetime import datetime
from typing import Optional, Dict, Any


class PriceAPIService:

    """
    Price API service.

    Priority used by the project:
        1. External/current price API
        2. User supplied current price
        3. Historical project dataset

    This service never invents a price and never substitutes a
    different product when the requested product is missing.

    Configure these in .env:

        GROCERY_PRICE_API_URL=
        ELECTRONICS_PRICE_API_URL=
        PRICE_API_KEY=

    The external API can return common structures such as:

        {"price": 500}
        {"current_price": 500}
        {"data": {"price": 500}}
        {"product": {"price": 500}}
        [{"price": 500}]
    """

    GROCERY_API_URL = os.getenv(
        "GROCERY_PRICE_API_URL",
        ""
    )

    ELECTRONICS_API_URL = os.getenv(
        "ELECTRONICS_PRICE_API_URL",
        ""
    )

    API_KEY = os.getenv(
        "PRICE_API_KEY",
        ""
    )

    REQUEST_TIMEOUT = int(
        os.getenv(
            "PRICE_API_TIMEOUT",
            "10"
        )
    )

    # =========================================================
    # NORMALIZE PRODUCT
    # =========================================================

    @staticmethod
    def normalize_product(
        product: str
    ) -> str:

        if product is None:
            return ""

        text = str(product).strip()

        text = re.sub(
            r"\s+",
            " ",
            text
        )

        return text

    # =========================================================
    # GET API URL
    # =========================================================

    @classmethod
    def get_api_url(
        cls,
        product_type: str
    ) -> str:

        product_type = (
            str(product_type)
            .strip()
            .lower()
        )

        if product_type == "grocery":
            return cls.GROCERY_API_URL

        if product_type == "electronics":
            return cls.ELECTRONICS_API_URL

        raise ValueError(
            "product_type must be "
            "'grocery' or 'electronics'."
        )

    # =========================================================
    # BUILD REQUEST PARAMETERS
    # =========================================================

    @classmethod
    def build_params(
        cls,
        product: str,
        brand: Optional[str] = None
    ) -> Dict[str, Any]:

        params = {
            "product": cls.normalize_product(
                product
            )
        }

        if brand:
            params["brand"] = (
                cls.normalize_product(
                    brand
                )
            )

        if cls.API_KEY:
            params["api_key"] = cls.API_KEY

        return params

    # =========================================================
    # EXTRACT PRICE
    # =========================================================

    @staticmethod
    def extract_price(
        data: Any
    ) -> Optional[float]:

        if isinstance(data, dict):

            possible_keys = [
                "price",
                "current_price",
                "currentPrice",
                "sale_price",
                "salePrice",
                "latest_price",
                "latestPrice",
                "api_price",
                "amount",
                "value"
            ]

            for key in possible_keys:

                value = data.get(key)

                if value is None:
                    continue

                try:

                    if isinstance(
                        value,
                        str
                    ):

                        cleaned = (
                            value
                            .replace(
                                ",",
                                ""
                            )
                            .replace(
                                "₹",
                                ""
                            )
                            .replace(
                                "$",
                                ""
                            )
                            .strip()
                        )

                    else:

                        cleaned = value

                    price = float(cleaned)

                    if price > 0:
                        return price

                except (
                    TypeError,
                    ValueError
                ):
                    continue

            for key in [
                "data",
                "product",
                "result",
                "item",
                "offer",
                "offers"
            ]:

                nested = data.get(key)

                if nested is not None:

                    price = (
                        PriceAPIService
                        .extract_price(
                            nested
                        )
                    )

                    if price is not None:
                        return price

        if isinstance(data, list):

            for item in data:

                price = (
                    PriceAPIService
                    .extract_price(
                        item
                    )
                )

                if price is not None:
                    return price

        return None

    # =========================================================
    # EXTRACT DISCOUNT
    # =========================================================

    @staticmethod
    def extract_discount(
        data: Any
    ) -> float:

        if not isinstance(
            data,
            dict
        ):
            return 0.0

        possible_keys = [
            "discount",
            "discount_percent",
            "discountPercentage",
            "discount_percentages",
            "api_discount"
        ]

        for key in possible_keys:

            value = data.get(key)

            if value is None:
                continue

            try:
                return max(
                    0.0,
                    float(value)
                )
            except (
                TypeError,
                ValueError
            ):
                continue

        for key in [
            "data",
            "product",
            "result",
            "item"
        ]:

            nested = data.get(key)

            if nested is not None:

                return (
                    PriceAPIService
                    .extract_discount(
                        nested
                    )
                )

        return 0.0

    # =========================================================
    # EXTRACT PRODUCT NAME
    # =========================================================

    @staticmethod
    def extract_product(
        data: Any,
        default_product: str
    ) -> str:

        if isinstance(
            data,
            dict
        ):

            for key in [
                "matched_product",
                "product_name",
                "productName",
                "name",
                "title",
                "product"
            ]:

                value = data.get(key)

                if isinstance(
                    value,
                    str
                ) and value.strip():

                    return value.strip()

            for key in [
                "data",
                "result",
                "item"
            ]:

                nested = data.get(key)

                if isinstance(
                    nested,
                    dict
                ):

                    result = (
                        PriceAPIService
                        .extract_product(
                            nested,
                            default_product
                        )
                    )

                    if result != default_product:
                        return result

        return default_product

    # =========================================================
    # EXTRACT SOURCE
    # =========================================================

    @staticmethod
    def extract_source(
        data: Any,
        default_source: str
    ) -> str:

        if isinstance(
            data,
            dict
        ):

            for key in [
                "source",
                "api_source",
                "provider",
                "merchant",
                "seller"
            ]:

                value = data.get(key)

                if value:
                    return str(value)

            for key in [
                "data",
                "result",
                "product",
                "item"
            ]:

                nested = data.get(key)

                if nested is not None:

                    source = (
                        PriceAPIService
                        .extract_source(
                            nested,
                            default_source
                        )
                    )

                    if source != default_source:
                        return source

        return default_source

    # =========================================================
    # EXTRACT CURRENCY
    # =========================================================

    @staticmethod
    def extract_currency(
        data: Any,
        default_currency: str = "INR"
    ) -> str:

        if isinstance(
            data,
            dict
        ):

            for key in [
                "currency",
                "currency_code",
                "currencyCode"
            ]:

                value = data.get(key)

                if value:
                    return str(value).upper()

            for key in [
                "data",
                "result",
                "product",
                "item"
            ]:

                nested = data.get(key)

                if nested is not None:

                    currency = (
                        PriceAPIService
                        .extract_currency(
                            nested,
                            default_currency
                        )
                    )

                    if currency != default_currency:
                        return currency

        return default_currency

    # =========================================================
    # FETCH PRODUCT PRICE
    # =========================================================

    @classmethod
    def fetch_product_price(
        cls,
        product: str,
        product_type: str,
        brand: Optional[str] = None
    ) -> Dict[str, Any]:

        product = cls.normalize_product(
            product
        )

        if not product:
            raise ValueError(
                "Product name is required."
            )

        api_url = cls.get_api_url(
            product_type
        )

        now = datetime.utcnow().isoformat()

        if not api_url:

            return {
                "success": False,
                "available": False,
                "product": product,
                "api_price": None,
                "api_discount": 0.0,
                "api_source":
                    "No external price API configured",
                "api_date": now,
                "message":
                    (
                        "No external price API URL is "
                        "configured for this product type."
                    )
            }

        params = cls.build_params(
            product,
            brand
        )

        try:

            response = requests.get(
                api_url,
                params=params,
                timeout=cls.REQUEST_TIMEOUT
            )

            response.raise_for_status()

        except requests.RequestException as exc:

            print(
                "\n========== PRICE API ERROR =========="
            )
            print("URL:", api_url)
            print("Product:", product)
            print("Error:", exc)
            print(
                "====================================\n"
            )

            return {
                "success": False,
                "available": False,
                "product": product,
                "api_price": None,
                "api_discount": 0.0,
                "api_source":
                    "External Price API",
                "api_date": now,
                "message": str(exc)
            }

        try:

            data = response.json()

        except ValueError:

            return {
                "success": False,
                "available": False,
                "product": product,
                "api_price": None,
                "api_discount": 0.0,
                "api_source":
                    "External Price API",
                "api_date": now,
                "message":
                    "Price API returned invalid JSON."
            }

        price = cls.extract_price(data)

        discount = cls.extract_discount(
            data
        )

        source = cls.extract_source(
            data,
            "External Price API"
        )

        currency = cls.extract_currency(
            data,
            "INR"
        )

        matched_product = (
            cls.extract_product(
                data,
                product
            )
        )

        if price is None:

            return {
                "success": False,
                "available": False,
                "product": product,
                "matched_product":
                    matched_product,
                "api_price": None,
                "api_discount":
                    round(
                        discount,
                        2
                    ),
                "api_source": source,
                "api_date": now,
                "currency": currency,
                "raw_response": data,
                "message":
                    (
                        "The price API responded, "
                        "but no valid price was found."
                    )
            }

        return {
            "success": True,
            "available": True,
            "product": product,
            "matched_product":
                matched_product,
            "api_price":
                round(
                    price,
                    2
                ),
            "api_discount":
                round(
                    discount,
                    2
                ),
            "api_source": source,
            "api_date": now,
            "currency": currency
        }

    # =========================================================
    # GROCERY
    # =========================================================

    @classmethod
    def fetch_grocery_price(
        cls,
        product: str
    ) -> Dict[str, Any]:

        return cls.fetch_product_price(
            product=product,
            product_type="grocery"
        )

    # =========================================================
    # ELECTRONICS
    # =========================================================

    @classmethod
    def fetch_electronics_price(
        cls,
        product: str,
        brand: Optional[str] = None
    ) -> Dict[str, Any]:

        return cls.fetch_product_price(
            product=product,
            product_type="electronics",
            brand=brand
        )
