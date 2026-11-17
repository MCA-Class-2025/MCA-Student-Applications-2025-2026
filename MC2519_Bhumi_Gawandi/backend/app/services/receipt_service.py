import re

from datetime import datetime

import httpx

from app.config.settings import settings


# ============================================================
# OCR API CONFIGURATION
# ============================================================

OCR_API_URL = (
    "https://api.ocr.space/parse/image"
)


# ============================================================
# GET OCR API KEY
# ============================================================

def get_ocr_api_key():

    return settings.OCR_API_KEY.strip()


# ============================================================
# RECEIPT SERVICE
# ============================================================

class ReceiptService:

    # ========================================================
    # SCAN RECEIPT
    # ========================================================

    @staticmethod
    async def scan_receipt(
        file,
        user_id: str,
    ):

        # ----------------------------------------------------
        # GET OCR API KEY
        # ----------------------------------------------------

        ocr_api_key = (
            get_ocr_api_key()
        )

        print(
            "OCR API KEY FOUND:",
            bool(ocr_api_key)
        )

        if not ocr_api_key:

            return {
                "success": False,
                "message": (
                    "OCR_API_KEY is not configured "
                    "in the .env file."
                ),
            }

        # ----------------------------------------------------
        # CHECK FILE
        # ----------------------------------------------------

        if file is None:

            return {
                "success": False,
                "message": (
                    "No receipt file was uploaded."
                ),
            }

        # ----------------------------------------------------
        # READ FILE
        # ----------------------------------------------------

        try:

            contents = await file.read()

        except Exception as error:

            return {
                "success": False,
                "message": (
                    "Unable to read the uploaded receipt."
                ),
                "error": str(error),
            }

        if not contents:

            return {
                "success": False,
                "message": (
                    "The uploaded receipt is empty."
                ),
            }

        # ----------------------------------------------------
        # FILE INFORMATION
        # ----------------------------------------------------

        filename = (
            file.filename
            or "receipt.jpg"
        )

        content_type = (
            file.content_type
            or "image/jpeg"
        )

        # ----------------------------------------------------
        # ALLOWED FILE TYPES
        # ----------------------------------------------------

        allowed_types = {

            "image/jpeg",
            "image/jpg",
            "image/png",
            "image/webp",
            "application/pdf",

        }

        if content_type not in allowed_types:

            return {
                "success": False,
                "message": (
                    "Unsupported receipt format. "
                    "Please upload JPG, PNG, WEBP or PDF."
                ),
            }

        # ----------------------------------------------------
        # SEND RECEIPT TO OCR
        # ----------------------------------------------------

        try:

            async with httpx.AsyncClient(
                timeout=60
            ) as client:

                response = await client.post(

                    OCR_API_URL,

                    headers={
                        "apikey": ocr_api_key
                    },

                    files={
                        "file": (
                            filename,
                            contents,
                            content_type,
                        )
                    },

                    data={

                        "language": "eng",

                        "isOverlayRequired":
                            "false",

                        "isTable":
                            "true",

                        "OCREngine":
                            "2",

                        "scale":
                            "true",

                        "detectOrientation":
                            "true",

                    },

                )

        except httpx.TimeoutException:

            return {
                "success": False,
                "message": (
                    "OCR service took too long "
                    "to respond. Please try again."
                ),
            }

        except httpx.RequestError as error:

            print(
                "OCR CONNECTION ERROR:",
                error
            )

            return {
                "success": False,
                "message": (
                    "Unable to connect to OCR service."
                ),
                "error": str(error),
            }

        except Exception as error:

            print(
                "OCR UNKNOWN ERROR:",
                error
            )

            return {
                "success": False,
                "message": (
                    "An unexpected error occurred "
                    "while scanning the receipt."
                ),
                "error": str(error),
            }

        # ----------------------------------------------------
        # CHECK HTTP STATUS
        # ----------------------------------------------------

        if response.status_code != 200:

            print(
                "OCR HTTP STATUS:",
                response.status_code
            )

            return {
                "success": False,
                "message": (
                    "OCR service returned an error."
                ),
                "status_code":
                    response.status_code,
            }

        # ----------------------------------------------------
        # PARSE JSON RESPONSE
        # ----------------------------------------------------

        try:

            data = response.json()

        except ValueError:

            return {
                "success": False,
                "message": (
                    "Invalid response received "
                    "from OCR service."
                ),
            }

        # ----------------------------------------------------
        # CHECK OCR PROCESSING ERROR
        # ----------------------------------------------------

        if data.get(
            "IsErroredOnProcessing"
        ):

            error_message = (

                data.get(
                    "ErrorMessage"
                )

                or

                data.get(
                    "ErrorDetails"
                )

                or

                "OCR could not process the receipt."

            )

            if isinstance(
                error_message,
                list
            ):

                error_message = " ".join(

                    str(item)

                    for item
                    in error_message

                )

            return {
                "success": False,
                "message":
                    str(error_message),
            }

        # ----------------------------------------------------
        # GET PARSED RESULTS
        # ----------------------------------------------------

        parsed_results = (

            data.get(
                "ParsedResults",
                []
            )

        )

        if not parsed_results:

            return {
                "success": False,
                "message": (
                    "No text was found "
                    "in the receipt."
                ),
            }

        # ----------------------------------------------------
        # COMBINE OCR TEXT
        # ----------------------------------------------------

        raw_text_parts = []

        for result in parsed_results:

            parsed_text = (

                result.get(
                    "ParsedText",
                    ""
                )

            )

            if parsed_text:

                raw_text_parts.append(
                    parsed_text
                )

        raw_text = "\n".join(
            raw_text_parts
        ).strip()

        if not raw_text:

            return {
                "success": False,
                "message": (
                    "No readable text was detected "
                    "in the receipt."
                ),
            }

        # ----------------------------------------------------
        # EXTRACT RECEIPT DATA
        # ----------------------------------------------------

        extracted_data = (

            ReceiptService.extract_receipt_data(
                raw_text
            )

        )

        # ----------------------------------------------------
        # RETURN RESULT
        # ----------------------------------------------------

        return {

            "success": True,

            "message":
                "Receipt scanned successfully.",

            "merchant":
                extracted_data["merchant"],

            "amount":
                extracted_data["amount"],

            "date":
                extracted_data["date"],

            "category":
                extracted_data["category"],

            "payment_method":
                extracted_data["payment_method"],

            "raw_text":
                raw_text,

            "user_id":
                user_id,

        }


    # ========================================================
    # EXTRACT ALL RECEIPT DATA
    # ========================================================

    @staticmethod
    def extract_receipt_data(
        text: str
    ):

        lines = [

            line.strip()

            for line
            in text.splitlines()

            if line.strip()

        ]

        merchant = (
            ReceiptService.extract_merchant(
                lines
            )
        )

        amount = (
            ReceiptService.extract_amount(
                text
            )
        )

        receipt_date = (
            ReceiptService.extract_date(
                text
            )
        )

        category = (
            ReceiptService.detect_category(
                text
            )
        )

        payment_method = (
            ReceiptService.detect_payment_method(
                text
            )
        )

        return {

            "merchant":
                merchant,

            "amount":
                amount,

            "date":
                receipt_date,

            "category":
                category,

            "payment_method":
                payment_method,

        }


    # ========================================================
    # EXTRACT MERCHANT
    # ========================================================

    @staticmethod
    def extract_merchant(
        lines
    ):

        ignored_words = {

            "receipt",
            "invoice",
            "tax invoice",
            "sample receipt",
            "thank you",

        }

        for line in lines[:10]:

            clean = re.sub(
                r"[^A-Za-z0-9 &'.-]",
                "",
                line
            ).strip()

            if not clean:
                continue

            lower = clean.lower()

            if lower in ignored_words:
                continue

            if "receipt" in lower:
                continue

            if "invoice" in lower:
                continue

            if "date" in lower:
                continue

            if "total" in lower:
                continue

            if "amount" in lower:
                continue

            if re.search(
                r"\d{3,}",
                clean
            ):
                continue

            return clean[:100]

        return ""


    # ========================================================
    # EXTRACT AMOUNT
    # ========================================================

    @staticmethod
    def extract_amount(
        text
    ):

        # ----------------------------------------------------
        # NORMALIZE OCR TEXT
        # ----------------------------------------------------

        normalized_text = text.replace(
            "\t",
            " "
        )

        normalized_text = re.sub(
            r"\s+",
            " ",
            normalized_text
        )

        # ----------------------------------------------------
        # TOTAL PATTERN
        #
        # Supports:
        # TOTAL ₹ 837.00
        # TOTAL Rs 837.00
        # TOTAL INR 837.00
        # TOTAL $ 837.00
        # TOTAL USD 837.00
        # TOTAL 837.00
        # ----------------------------------------------------

        total_pattern = re.compile(

            r"(?:grand\s*total|"
            r"total\s*amount|"
            r"amount\s*payable|"
            r"net\s*amount|"
            r"\btotal\b)"

            r"\s*[:\-]?\s*"

            r"(?:₹|Rs\.?|INR|\$|USD)?"

            r"\s*"

            r"([0-9,]+"
            r"(?:\.[0-9]{1,2})?)",

            flags=re.IGNORECASE

        )

        matches = (
            total_pattern.findall(
                normalized_text
            )
        )

        if matches:

            try:

                amount = float(

                    matches[-1].replace(
                        ",",
                        ""
                    )

                )

                return round(
                    amount,
                    2
                )

            except ValueError:

                pass

        # ----------------------------------------------------
        # CURRENCY SYMBOL FALLBACK
        # ----------------------------------------------------

        currency_pattern = re.compile(

            r"(?:₹|Rs\.?|INR|\$|USD)"

            r"\s*"

            r"([0-9,]+"
            r"(?:\.[0-9]{1,2})?)",

            flags=re.IGNORECASE

        )

        currency_matches = (

            currency_pattern.findall(
                normalized_text
            )

        )

        if currency_matches:

            try:

                amount = float(

                    currency_matches[-1].replace(
                        ",",
                        ""
                    )

                )

                return round(
                    amount,
                    2
                )

            except ValueError:

                pass

        # ----------------------------------------------------
        # FALLBACK FOR PLAIN TOTAL
        # ----------------------------------------------------

        plain_amount_pattern = re.compile(

            r"\btotal\b"
            r"\s*"
            r"([0-9,]+"
            r"(?:\.[0-9]{1,2})?)",

            flags=re.IGNORECASE

        )

        plain_matches = (

            plain_amount_pattern.findall(
                normalized_text
            )

        )

        if plain_matches:

            try:

                amount = float(

                    plain_matches[-1].replace(
                        ",",
                        ""
                    )

                )

                return round(
                    amount,
                    2
                )

            except ValueError:

                pass

        return 0.0


    # ========================================================
    # EXTRACT DATE
    # ========================================================

    @staticmethod
    def extract_date(
        text
    ):

        patterns = [

            r"\b"
            r"(\d{1,2}"
            r"[/-]"
            r"\d{1,2}"
            r"[/-]"
            r"\d{2,4})"
            r"\b",

            r"\b"
            r"(\d{4}"
            r"[/-]"
            r"\d{1,2}"
            r"[/-]"
            r"\d{1,2})"
            r"\b",

            r"\b"
            r"(\d{1,2}"
            r"\s+"
            r"[A-Za-z]{3,9}"
            r"\s+"
            r"\d{2,4})"
            r"\b",

            r"\b"
            r"([A-Za-z]{3,9}"
            r"\s+"
            r"\d{1,2}"
            r",?"
            r"\s+"
            r"\d{2,4})"
            r"\b",

        ]

        formats = [

            "%d/%m/%Y",
            "%d-%m-%Y",

            "%d/%m/%y",
            "%d-%m-%y",

            "%Y/%m/%d",
            "%Y-%m-%d",

            "%d %B %Y",
            "%d %b %Y",

            "%B %d, %Y",
            "%B %d %Y",

            "%b %d, %Y",
            "%b %d %Y",

        ]

        for pattern in patterns:

            match = re.search(
                pattern,
                text
            )

            if not match:
                continue

            value = match.group(1)

            for date_format in formats:

                try:

                    parsed_date = (
                        datetime.strptime(
                            value,
                            date_format
                        )
                    )

                    return (
                        parsed_date.strftime(
                            "%Y-%m-%d"
                        )
                    )

                except ValueError:

                    continue

        return ""


    # ========================================================
    # DETECT CATEGORY
    # ========================================================

    @staticmethod
    def detect_category(
        text
    ):

        lower = text.lower()

        category_keywords = {

            "Food": [

                "restaurant",
                "pizza",
                "burger",
                "cafe",
                "coffee",
                "starbucks",
                "food",
                "meal",
                "dinner",
                "lunch",
                "swiggy",
                "zomato",

            ],

            "Groceries": [

                "grocery",
                "groceries",
                "dmart",
                "reliance fresh",
                "vegetables",
                "rice",
                "milk",
                "bread",
                "supermarket",

            ],

            "Shopping": [

                "amazon",
                "flipkart",
                "shopping",
                "fashion",
                "clothes",
                "shoes",
                "store",
                "mall",

            ],

            "Transport": [

                "uber",
                "ola",
                "taxi",
                "metro",
                "bus",
                "transport",
                "ride",

            ],

            "Fuel": [

                "petrol",
                "diesel",
                "fuel",
                "indian oil",
                "hp petrol",
                "bharat petroleum",

            ],

            "Healthcare": [

                "pharmacy",
                "medical",
                "medicine",
                "apollo",
                "hospital",
                "healthcare",

            ],

            "Entertainment": [

                "bookmyshow",
                "movie",
                "cinema",
                "entertainment",
                "ticket",

            ],

        }

        for category, keywords in (
            category_keywords.items()
        ):

            for keyword in keywords:

                if keyword in lower:

                    return category

        return "Other"


    # ========================================================
    # DETECT PAYMENT METHOD
    # ========================================================

    @staticmethod
    def detect_payment_method(
        text
    ):

        lower = text.lower()

        # ----------------------------------------------------
        # UPI
        # ----------------------------------------------------

        if any(

            value in lower

            for value in [

                "upi",
                "gpay",
                "google pay",
                "phonepe",
                "paytm",

            ]

        ):

            return "UPI"

        # ----------------------------------------------------
        # CARD
        # ----------------------------------------------------

        if any(

            value in lower

            for value in [

                "credit card",
                "debit card",
                "card",
                "visa",
                "mastercard",

            ]

        ):

            return "Card"

        # ----------------------------------------------------
        # CASH
        # ----------------------------------------------------

        if "cash" in lower:

            return "Cash"

        return ""