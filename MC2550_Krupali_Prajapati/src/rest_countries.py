import os
import time
from pathlib import Path

import pandas as pd
import requests
from dotenv import load_dotenv


# ============================================================
# REST COUNTRIES API - COUNTRY DATA COLLECTION
# ============================================================

# Load variables from .env
load_dotenv()

API_KEY = os.getenv("REST_COUNTRIES_API_KEY")

BASE_URL = "https://api.restcountries.com/countries/v5"

# Project folders
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"

DATA_DIR.mkdir(exist_ok=True)

OUTPUT_FILE = DATA_DIR / "rest_countries.csv"
VALIDATION_FILE = DATA_DIR / "rest_countries_validation.csv"


# ============================================================
# API CONFIGURATION
# ============================================================

# We only request fields that are useful for our project.
#
# This makes the API response smaller and keeps the resulting
# dataset focused on country intelligence.

RESPONSE_FIELDS = ",".join([
    "names.common",
    "names.official",
    "codes.alpha_2",
    "codes.alpha_3",
    "capitals",
    "region",
    "subregion",
    "currencies",
    "languages",
    "area.kilometers",
    "borders",
    "timezones",
    "coordinates.lat",
    "coordinates.lng",
    "population"
])


# ============================================================
# CHECK API KEY
# ============================================================

def check_api_key():

    if not API_KEY:

        raise ValueError(
            "\nREST_COUNTRIES_API_KEY was not found.\n\n"
            "Make sure your .env file contains:\n\n"
            "REST_COUNTRIES_API_KEY=YOUR_API_KEY\n"
        )

    # Prevent accidentally using the demo key
    if API_KEY == "rc_live_demo":

        raise ValueError(
            "\nThe demo key is not suitable for collecting "
            "the complete country dataset.\n\n"
            "Please put your real REST Countries API key "
            "inside the .env file.\n"
        )


# ============================================================
# GET ONE PAGE FROM API
# ============================================================

def get_page(offset=0, limit=100):

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Accept": "application/json"
    }

    params = {
        "limit": limit,
        "offset": offset,
        "response_fields": RESPONSE_FIELDS
    }

    response = requests.get(
        BASE_URL,
        headers=headers,
        params=params,
        timeout=60
    )

    # Helpful error message
    if response.status_code != 200:

        print("\nAPI ERROR")
        print("-" * 40)
        print("Status code:", response.status_code)
        print("Response:", response.text[:1000])

    response.raise_for_status()

    result = response.json()

    return result


# ============================================================
# COLLECT ALL COUNTRIES
# ============================================================

def get_countries():

    check_api_key()

    all_countries = []

    offset = 0
    limit = 100

    print("\nStarting REST Countries API collection...")
    print("Maximum records per request:", limit)

    while True:

        print(
            f"\nRequesting records "
            f"{offset + 1} to {offset + limit}..."
        )

        result = get_page(
            offset=offset,
            limit=limit
        )

        # ----------------------------------------------------
        # Validate basic response structure
        # ----------------------------------------------------

        if "data" not in result:

            raise ValueError(
                "API response does not contain 'data'."
            )

        data = result["data"]

        if "objects" not in data:

            raise ValueError(
                "API response does not contain "
                "'data.objects'."
            )

        objects = data["objects"]

        # ----------------------------------------------------
        # Add records
        # ----------------------------------------------------

        all_countries.extend(objects)

        print(
            f"Records received in this request: "
            f"{len(objects)}"
        )

        # ----------------------------------------------------
        # Read pagination metadata
        # ----------------------------------------------------

        meta = data.get("meta", {})

        total = meta.get("total")

        more = meta.get("more")

        print("Total according to API:", total)
        print("More records available:", more)

        # ----------------------------------------------------
        # Stop when API says there are no more records
        # ----------------------------------------------------

        if not more:

            break

        # Safety check
        if not objects:

            break

        offset += len(objects)

        time.sleep(0.2)

    print("\nCollection completed.")
    print(
        "Total API records collected:",
        len(all_countries)
    )

    return all_countries


# ============================================================
# SAFE VALUE HELPERS
# ============================================================

def safe_string(value):

    if value is None:
        return None

    if isinstance(value, str):
        return value

    return str(value)


# ============================================================
# COUNTRY NAME
# ============================================================

def get_common_name(country):

    names = country.get("names", {})

    if isinstance(names, dict):

        return names.get("common")

    return None


def get_official_name(country):

    names = country.get("names", {})

    if isinstance(names, dict):

        return names.get("official")

    return None


# ============================================================
# ISO CODES
# ============================================================

def get_alpha2(country):

    codes = country.get("codes", {})

    if isinstance(codes, dict):

        return codes.get("alpha_2")

    return None


def get_alpha3(country):

    codes = country.get("codes", {})

    if isinstance(codes, dict):

        return codes.get("alpha_3")

    return None


# ============================================================
# CAPITAL
# ============================================================

def get_capital(country):

    capitals = country.get("capitals", [])

    if not isinstance(capitals, list):

        return None

    if len(capitals) == 0:

        return None

    names = []

    for capital in capitals:

        if isinstance(capital, dict):

            name = capital.get("name")

            if name:
                names.append(str(name))

        elif isinstance(capital, str):

            names.append(capital)

    if names:

        return ", ".join(names)

    return None


def get_capital_latitude(country):

    capitals = country.get("capitals", [])

    if not isinstance(capitals, list):

        return None

    for capital in capitals:

        if isinstance(capital, dict):

            coordinates = capital.get(
                "coordinates",
                {}
            )

            if isinstance(coordinates, dict):

                latitude = coordinates.get("lat")

                if latitude is not None:

                    return latitude

    return None


def get_capital_longitude(country):

    capitals = country.get("capitals", [])

    if not isinstance(capitals, list):

        return None

    for capital in capitals:

        if isinstance(capital, dict):

            coordinates = capital.get(
                "coordinates",
                {}
            )

            if isinstance(coordinates, dict):

                longitude = coordinates.get("lng")

                if longitude is not None:

                    return longitude

    return None


# ============================================================
# CURRENCY
# ============================================================

def get_currencies(country):

    currencies = country.get(
        "currencies",
        {}
    )

    # Current documented format
    if isinstance(currencies, dict):

        codes = []

        for code in currencies.keys():

            if code:

                codes.append(str(code))

        if codes:

            return ", ".join(codes)

    # Additional protection if API returns a list
    elif isinstance(currencies, list):

        codes = []

        for item in currencies:

            if isinstance(item, str):

                codes.append(item)

            elif isinstance(item, dict):

                code = (
                    item.get("code")
                    or item.get("currency_code")
                    or item.get("iso_code")
                )

                if code:

                    codes.append(str(code))

        if codes:

            return ", ".join(codes)

    return None


def get_currency_names(country):

    currencies = country.get(
        "currencies",
        {}
    )

    names = []

    # Dictionary format
    if isinstance(currencies, dict):

        for code, details in currencies.items():

            if isinstance(details, dict):

                name = details.get("name")

                if name:

                    names.append(str(name))

            elif isinstance(details, str):

                names.append(details)

    # List format
    elif isinstance(currencies, list):

        for item in currencies:

            if isinstance(item, dict):

                name = (
                    item.get("name")
                    or item.get("currency_name")
                )

                if name:

                    names.append(str(name))

            elif isinstance(item, str):

                names.append(item)

    if names:

        return ", ".join(names)

    return None


# ============================================================
# LANGUAGES
# ============================================================

def get_languages(country):

    languages = country.get(
        "languages",
        []
    )

    names = []

    # Current API may represent languages as
    # a list of objects.
    if isinstance(languages, list):

        for language in languages:

            if isinstance(language, dict):

                name = (
                    language.get("name")
                    or language.get("english")
                    or language.get("common")
                )

                if name:

                    names.append(str(name))

            elif isinstance(language, str):

                names.append(language)

    # Protection for dictionary format
    elif isinstance(languages, dict):

        for key, value in languages.items():

            if isinstance(value, str):

                names.append(value)

            elif isinstance(value, dict):

                name = (
                    value.get("name")
                    or value.get("english")
                )

                if name:

                    names.append(str(name))

    if names:

        return ", ".join(names)

    return None


# ============================================================
# BORDERS
# ============================================================

def get_borders(country):

    borders = country.get(
        "borders",
        []
    )

    if not borders:

        return None

    if isinstance(borders, list):

        return ", ".join(
            str(border)
            for border in borders
        )

    return str(borders)


# ============================================================
# TIME ZONES
# ============================================================

def get_timezones(country):

    timezones = country.get(
        "timezones",
        []
    )

    if not timezones:

        return None

    if isinstance(timezones, list):

        return ", ".join(
            str(zone)
            for zone in timezones
        )

    return str(timezones)


# ============================================================
# COUNTRY COORDINATES
# ============================================================

def get_latitude(country):

    coordinates = country.get(
        "coordinates",
        {}
    )

    if isinstance(coordinates, dict):

        return coordinates.get("lat")

    return None


def get_longitude(country):

    coordinates = country.get(
        "coordinates",
        {}
    )

    if isinstance(coordinates, dict):

        return coordinates.get("lng")

    return None


# ============================================================
# CONVERT API DATA TO DATAFRAME
# ============================================================

def convert_to_dataframe(countries):

    rows = []

    for country in countries:

        row = {

            "Country Name":
                get_common_name(country),

            "Official Name":
                get_official_name(country),

            "ISO Alpha-2":
                get_alpha2(country),

            "ISO Alpha-3":
                get_alpha3(country),

            "Capital":
                get_capital(country),

            "Capital Latitude":
                get_capital_latitude(country),

            "Capital Longitude":
                get_capital_longitude(country),

            "Region":
                country.get("region"),

            "Subregion":
                country.get("subregion"),

            "Currency Code":
                get_currencies(country),

            "Currency Name":
                get_currency_names(country),

            "Languages":
                get_languages(country),

            "Area (km²)":
                country.get("area", {}).get(
                    "kilometers"
                )
                if isinstance(
                    country.get("area", {}),
                    dict
                )
                else country.get("area"),

            "Borders":
                get_borders(country),

            "Time Zones":
                get_timezones(country),

            "Latitude":
                get_latitude(country),

            "Longitude":
                get_longitude(country),

            "Population":
                country.get("population")
        }

        rows.append(row)

    df = pd.DataFrame(rows)

    return df


# ============================================================
# DATA VALIDATION
# ============================================================

def validate_data(df):

    validation_rows = []

    total_records = len(df)

    # --------------------------------------------------------
    # General dataset information
    # --------------------------------------------------------

    validation_rows.append({
        "Check": "Total Records",
        "Value": total_records,
        "Status": "INFO"
    })

    validation_rows.append({
        "Check": "Total Columns",
        "Value": len(df.columns),
        "Status": "INFO"
    })

    # --------------------------------------------------------
    # Duplicate rows
    # --------------------------------------------------------

    duplicate_rows = int(
        df.duplicated().sum()
    )

    validation_rows.append({
        "Check": "Duplicate Rows",
        "Value": duplicate_rows,
        "Status":
            "PASS"
            if duplicate_rows == 0
            else "WARNING"
    })

    # --------------------------------------------------------
    # Duplicate ISO-3 codes
    # --------------------------------------------------------

    duplicate_iso3 = int(
        df["ISO Alpha-3"]
        .dropna()
        .duplicated()
        .sum()
    )

    validation_rows.append({
        "Check": "Duplicate ISO Alpha-3 Codes",
        "Value": duplicate_iso3,
        "Status":
            "PASS"
            if duplicate_iso3 == 0
            else "WARNING"
    })

    # --------------------------------------------------------
    # Missing country names
    # --------------------------------------------------------

    missing_names = int(
        df["Country Name"].isna().sum()
    )

    validation_rows.append({
        "Check": "Missing Country Names",
        "Value": missing_names,
        "Status":
            "PASS"
            if missing_names == 0
            else "WARNING"
    })

    # --------------------------------------------------------
    # Missing ISO-3
    # --------------------------------------------------------

    missing_iso3 = int(
        df["ISO Alpha-3"].isna().sum()
    )

    validation_rows.append({
        "Check": "Missing ISO Alpha-3",
        "Value": missing_iso3,
        "Status":
            "PASS"
            if missing_iso3 == 0
            else "WARNING"
    })

    # --------------------------------------------------------
    # Missing capital
    # --------------------------------------------------------

    missing_capital = int(
        df["Capital"].isna().sum()
    )

    validation_rows.append({
        "Check": "Missing Capital",
        "Value": missing_capital,
        "Status":
            "INFO"
            if missing_capital > 0
            else "PASS"
    })

    # --------------------------------------------------------
    # Missing currency
    # --------------------------------------------------------

    missing_currency = int(
        df["Currency Code"].isna().sum()
    )

    validation_rows.append({
        "Check": "Missing Currency",
        "Value": missing_currency,
        "Status":
            "INFO"
            if missing_currency > 0
            else "PASS"
    })

    # --------------------------------------------------------
    # Missing region
    # --------------------------------------------------------

    missing_region = int(
        df["Region"].isna().sum()
    )

    validation_rows.append({
        "Check": "Missing Region",
        "Value": missing_region,
        "Status":
            "INFO"
            if missing_region > 0
            else "PASS"
    })

    # --------------------------------------------------------
    # Missing languages
    # --------------------------------------------------------

    missing_languages = int(
        df["Languages"].isna().sum()
    )

    validation_rows.append({
        "Check": "Missing Languages",
        "Value": missing_languages,
        "Status":
            "INFO"
            if missing_languages > 0
            else "PASS"
    })

    # --------------------------------------------------------
    # Missing coordinates
    # --------------------------------------------------------

    missing_latitude = int(
        df["Latitude"].isna().sum()
    )

    missing_longitude = int(
        df["Longitude"].isna().sum()
    )

    validation_rows.append({
        "Check": "Missing Latitude",
        "Value": missing_latitude,
        "Status":
            "INFO"
            if missing_latitude > 0
            else "PASS"
    })

    validation_rows.append({
        "Check": "Missing Longitude",
        "Value": missing_longitude,
        "Status":
            "INFO"
            if missing_longitude > 0
            else "PASS"
    })

    # --------------------------------------------------------
    # Validation dataframe
    # --------------------------------------------------------

    validation_df = pd.DataFrame(
        validation_rows
    )

    return validation_df


# ============================================================
# MAIN PROGRAM
# ============================================================

def main():

    print("=" * 60)
    print("REST COUNTRIES API DATA COLLECTION")
    print("=" * 60)

    # --------------------------------------------------------
    # Collect data
    # --------------------------------------------------------

    countries = get_countries()

    # --------------------------------------------------------
    # Convert to dataframe
    # --------------------------------------------------------

    print("\nConverting API response to dataframe...")

    df = convert_to_dataframe(
        countries
    )

    print(
        "\nDataframe created successfully."
    )

    print(
        "Rows:",
        len(df)
    )

    print(
        "Columns:",
        len(df.columns)
    )

    # --------------------------------------------------------
    # Validate
    # --------------------------------------------------------

    print("\nValidating API data...")

    validation_df = validate_data(df)

    print("\nVALIDATION RESULTS")
    print("=" * 60)

    print(
        validation_df.to_string(
            index=False
        )
    )

    # --------------------------------------------------------
    # Save country dataset
    # --------------------------------------------------------

    df.to_csv(
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

    print("\nFirst 10 records")
    print("=" * 60)

    print(
        df.head(10).to_string(
            index=False
        )
    )

    # --------------------------------------------------------
    # Final information
    # --------------------------------------------------------

    print("\n" + "=" * 60)
    print("REST COUNTRIES API STEP COMPLETED")
    print("=" * 60)

    print(
        "\nCountry dataset:"
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

    except requests.exceptions.HTTPError as error:

        print("\nHTTP ERROR")
        print("-" * 40)
        print(error)
        print(
            "\nCheck that your REST Countries API key "
            "is valid and active."
        )

    except requests.exceptions.RequestException as error:

        print("\nNETWORK/API ERROR")
        print("-" * 40)
        print(error)

    except Exception as error:

        print("\nPROGRAM ERROR")
        print("-" * 40)
        print(type(error).__name__ + ":", error)