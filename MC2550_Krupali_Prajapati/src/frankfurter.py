import time
from pathlib import Path

import pandas as pd
import requests


# ============================================================
# FRANKFURTER CURRENCY EXCHANGE API
# ============================================================

BASE_DIR = Path(__file__).parent

DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

INPUT_FILE = DATA_DIR / "rest_countries.csv"

OUTPUT_FILE = DATA_DIR / "frankfurter_rates.csv"

VALIDATION_FILE = DATA_DIR / "frankfurter_validation.csv"

API_URL = "https://api.frankfurter.dev/v2/rates"


# ============================================================
# LOAD REST COUNTRIES DATA
# ============================================================

def load_country_data():

    if not INPUT_FILE.exists():

        raise FileNotFoundError(
            f"\nCould not find:\n{INPUT_FILE}\n\n"
            "Please run rest_countries.py first."
        )

    df = pd.read_csv(INPUT_FILE)

    print(
        f"\nREST Countries records loaded: {len(df)}"
    )

    return df


# ============================================================
# EXTRACT FIRST CURRENCY
# ============================================================

def extract_currency_code(value):

    if pd.isna(value):
        return None

    value = str(value).strip()

    if not value:
        return None

    # Some countries may have multiple currencies.
    # For this project we use the first currency.
    currency = value.split(",")[0].strip()

    if not currency:
        return None

    return currency.upper()


# ============================================================
# GET ALL FRANKFURTER RATES
# ============================================================

def get_all_rates():

    print(
        "\nRequesting exchange rates from Frankfurter..."
    )

    print(
        "Base currency: EUR"
    )

    params = {
        "base": "EUR"
    }

    response = requests.get(
        API_URL,
        params=params,
        timeout=60
    )

    if response.status_code != 200:

        print("\nFRANKFURTER API ERROR")
        print("-" * 50)
        print("Status code:", response.status_code)
        print("Response:", response.text[:1000])

    response.raise_for_status()

    data = response.json()

    # v2 returns a list of rate records.
    if not isinstance(data, list):

        raise ValueError(
            "Unexpected Frankfurter API response format. "
            "Expected a list of rate records."
        )

    print(
        f"Rate records received from API: {len(data)}"
    )

    return data


# ============================================================
# CREATE RATE LOOKUP
# ============================================================

def create_rate_lookup(rate_records):

    lookup = {}

    for record in rate_records:

        if not isinstance(record, dict):
            continue

        quote = record.get("quote")

        rate = record.get("rate")

        date = record.get("date")

        base = record.get(
            "base",
            "EUR"
        )

        if quote and rate is not None:

            lookup[quote.upper()] = {

                "Exchange Rate":
                    rate,

                "Base Currency":
                    base,

                "Quote Currency":
                    quote.upper(),

                "Rate Date":
                    date,

                "API Status":
                    "Success"
            }

    # EUR to EUR is always 1.
    lookup["EUR"] = {

        "Exchange Rate":
            1.0,

        "Base Currency":
            "EUR",

        "Quote Currency":
            "EUR",

        "Rate Date":
            None,

        "API Status":
            "Success"
    }

    return lookup


# ============================================================
# ATTACH RATES TO COUNTRIES
# ============================================================

def build_country_rate_dataset(
    countries_df,
    rate_lookup
):

    records = []

    matched = 0

    unavailable = 0

    missing_currency = 0

    total = len(countries_df)

    print(
        "\nMatching currencies with country records..."
    )

    for index, row in countries_df.iterrows():

        country_name = row[
            "Country Name"
        ]

        iso3 = row[
            "ISO Alpha-3"
        ]

        original_currency = row[
            "Currency Code"
        ]

        currency = extract_currency_code(
            original_currency
        )

        record = {

            "Country Name":
                country_name,

            "ISO Alpha-3":
                iso3,

            "Currency Code":
                currency
        }

        # ----------------------------------------------------
        # No currency available
        # ----------------------------------------------------

        if not currency:

            record.update({

                "Exchange Rate":
                    None,

                "Base Currency":
                    "EUR",

                "Quote Currency":
                    None,

                "Rate Date":
                    None,

                "API Status":
                    "Missing Currency"
            })

            missing_currency += 1

            records.append(record)

            continue

        # ----------------------------------------------------
        # Currency available in Frankfurter
        # ----------------------------------------------------

        if currency in rate_lookup:

            record.update(
                rate_lookup[currency]
            )

            matched += 1

        # ----------------------------------------------------
        # Currency not supported by Frankfurter
        # ----------------------------------------------------

        else:

            record.update({

                "Exchange Rate":
                    None,

                "Base Currency":
                    "EUR",

                "Quote Currency":
                    currency,

                "Rate Date":
                    None,

                "API Status":
                    "Currency Not Available"
            })

            unavailable += 1

        records.append(record)

    print(
        "\nCurrency matching completed."
    )

    print(
        "Total countries:",
        total
    )

    print(
        "Currencies matched:",
        matched
    )

    print(
        "Currencies unavailable:",
        unavailable
    )

    print(
        "Countries without currency:",
        missing_currency
    )

    return pd.DataFrame(records)


# ============================================================
# VALIDATION
# ============================================================

def validate_exchange_rates(df):

    validation = []

    # --------------------------------------------------------
    # Basic dataset information
    # --------------------------------------------------------

    validation.append({

        "Check":
            "Total Country Records",

        "Value":
            len(df),

        "Status":
            "INFO"
    })

    validation.append({

        "Check":
            "Total Columns",

        "Value":
            len(df.columns),

        "Status":
            "INFO"
    })

    # --------------------------------------------------------
    # Duplicate countries
    # --------------------------------------------------------

    duplicate_countries = int(
        df["Country Name"]
        .duplicated()
        .sum()
    )

    validation.append({

        "Check":
            "Duplicate Country Records",

        "Value":
            duplicate_countries,

        "Status":
            "PASS"
            if duplicate_countries == 0
            else "WARNING"
    })

    # --------------------------------------------------------
    # Duplicate ISO codes
    # --------------------------------------------------------

    duplicate_iso3 = int(
        df["ISO Alpha-3"]
        .dropna()
        .duplicated()
        .sum()
    )

    validation.append({

        "Check":
            "Duplicate ISO Alpha-3 Codes",

        "Value":
            duplicate_iso3,

        "Status":
            "PASS"
            if duplicate_iso3 == 0
            else "WARNING"
    })

    # --------------------------------------------------------
    # Missing currency codes
    # --------------------------------------------------------

    missing_currency = int(
        df["Currency Code"]
        .isna()
        .sum()
    )

    validation.append({

        "Check":
            "Missing Currency Codes",

        "Value":
            missing_currency,

        "Status":
            "PASS"
            if missing_currency == 0
            else "INFO"
    })

    # --------------------------------------------------------
    # Successful matches
    # --------------------------------------------------------

    successful = int(
        (
            df["API Status"]
            == "Success"
        ).sum()
    )

    validation.append({

        "Check":
            "Successful Exchange Rate Matches",

        "Value":
            successful,

        "Status":
            "PASS"
            if successful > 0
            else "FAIL"
    })

    # --------------------------------------------------------
    # Unsupported currencies
    # --------------------------------------------------------

    unavailable = int(
        (
            df["API Status"]
            == "Currency Not Available"
        ).sum()
    )

    validation.append({

        "Check":
            "Currencies Not Available",

        "Value":
            unavailable,

        "Status":
            "INFO"
    })

    # --------------------------------------------------------
    # Missing exchange rates
    # --------------------------------------------------------

    missing_rates = int(
        df["Exchange Rate"]
        .isna()
        .sum()
    )

    validation.append({

        "Check":
            "Missing Exchange Rates",

        "Value":
            missing_rates,

        "Status":
            "INFO"
            if missing_rates > 0
            else "PASS"
    })

    # --------------------------------------------------------
    # Non-positive rates
    # --------------------------------------------------------

    rates = pd.to_numeric(
        df["Exchange Rate"],
        errors="coerce"
    )

    invalid_rates = int(
        (
            rates <= 0
        )
        .fillna(False)
        .sum()
    )

    validation.append({

        "Check":
            "Non-positive Exchange Rates",

        "Value":
            invalid_rates,

        "Status":
            "PASS"
            if invalid_rates == 0
            else "WARNING"
    })

    # --------------------------------------------------------
    # Base currency validation
    # --------------------------------------------------------

    incorrect_base = int(
        (
            df["Base Currency"]
            .notna()
            &
            (
                df["Base Currency"]
                != "EUR"
            )
        ).sum()
    )

    validation.append({

        "Check":
            "Incorrect Base Currency",

        "Value":
            incorrect_base,

        "Status":
            "PASS"
            if incorrect_base == 0
            else "WARNING"
    })

    # --------------------------------------------------------
    # Rate date availability
    # --------------------------------------------------------

    missing_date = int(
        df["Rate Date"]
        .isna()
        .sum()
    )

    validation.append({

        "Check":
            "Missing Rate Date",

        "Value":
            missing_date,

        "Status":
            "INFO"
    })

    return pd.DataFrame(
        validation
    )


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 60)
    print(
        "FRANKFURTER CURRENCY API DATA COLLECTION"
    )
    print("=" * 60)

    # --------------------------------------------------------
    # Load country data
    # --------------------------------------------------------

    countries_df = load_country_data()

    # --------------------------------------------------------
    # Get all rates in one API request
    # --------------------------------------------------------

    rate_records = get_all_rates()

    # --------------------------------------------------------
    # Create lookup
    # --------------------------------------------------------

    rate_lookup = create_rate_lookup(
        rate_records
    )

    print(
        f"Usable currency rates: {len(rate_lookup)}"
    )

    # --------------------------------------------------------
    # Match rates to countries
    # --------------------------------------------------------

    rates_df = build_country_rate_dataset(
        countries_df,
        rate_lookup
    )

    # --------------------------------------------------------
    # Validate
    # --------------------------------------------------------

    print(
        "\nValidating exchange-rate data..."
    )

    validation_df = validate_exchange_rates(
        rates_df
    )

    print(
        "\nVALIDATION RESULTS"
    )

    print("=" * 60)

    print(
        validation_df.to_string(
            index=False
        )
    )

    # --------------------------------------------------------
    # Save dataset
    # --------------------------------------------------------

    rates_df.to_csv(
        OUTPUT_FILE,
        index=False,
        encoding="utf-8"
    )

    # --------------------------------------------------------
    # Save validation report
    # --------------------------------------------------------

    validation_df.to_csv(
        VALIDATION_FILE,
        index=False,
        encoding="utf-8"
    )

    # --------------------------------------------------------
    # Display sample
    # --------------------------------------------------------

    print(
        "\nFirst 10 exchange-rate records"
    )

    print("=" * 60)

    print(
        rates_df.head(10).to_string(
            index=False
        )
    )

    # --------------------------------------------------------
    # Completion
    # --------------------------------------------------------

    print(
        "\n" + "=" * 60
    )

    print(
        "FRANKFURTER STEP COMPLETED"
    )

    print(
        "=" * 60
    )

    print(
        "\nExchange-rate dataset:"
    )

    print(
        OUTPUT_FILE
    )

    print(
        "\nValidation report:"
    )

    print(
        VALIDATION_FILE
    )


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":

    try:

        main()

    except requests.exceptions.RequestException as error:

        print(
            "\nAPI/NETWORK ERROR"
        )

        print("-" * 40)

        print(error)

    except Exception as error:

        print(
            "\nPROGRAM ERROR"
        )

        print("-" * 40)

        print(
            type(error).__name__,
            ":",
            error
        )