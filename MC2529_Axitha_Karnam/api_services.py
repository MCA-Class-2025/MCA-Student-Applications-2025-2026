import requests


# ============================================================
# FRANKFURTER EXCHANGE RATE API
# ============================================================

BASE_URL = "https://api.frankfurter.dev/v2"


def get_exchange_rate(from_currency, to_currency):
    """
    Get the latest exchange rate between two currencies.

    Example:
        USD -> INR
        EUR -> INR
    """

    from_currency = from_currency.upper()
    to_currency = to_currency.upper()

    # Same currency
    if from_currency == to_currency:
        return {
            "success": True,
            "rate": 1.0,
            "date": "Same currency",
            "from": from_currency,
            "to": to_currency
        }

    url = (
        f"{BASE_URL}/rate/"
        f"{from_currency}/"
        f"{to_currency}"
    )

    try:

        response = requests.get(
            url,
            timeout=10
        )

        response.raise_for_status()

        data = response.json()

        return {
            "success": True,
            "rate": data["rate"],
            "date": data["date"],
            "from": data["base"],
            "to": data["quote"]
        }

    except requests.exceptions.RequestException as error:

        return {
            "success": False,
            "error": str(error)
        }

    except (KeyError, ValueError):

        return {
            "success": False,
            "error": "Invalid response received from exchange rate API."
        }


# ============================================================
# CURRENCY CONVERSION
# ============================================================

def convert_currency(
    amount,
    from_currency,
    to_currency
):
    """
    Convert an amount from one currency to another.
    """

    result = get_exchange_rate(
        from_currency,
        to_currency
    )

    if not result["success"]:

        return result

    converted_amount = (
        float(amount) *
        float(result["rate"])
    )

    return {
        "success": True,
        "original_amount": float(amount),
        "converted_amount": converted_amount,
        "rate": result["rate"],
        "date": result["date"],
        "from": result["from"],
        "to": result["to"]
    }