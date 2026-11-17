import os
import time
import requests
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv

# ============================================================
# CONFIGURATION
# ============================================================

YEAR = 2026
API_URL = "https://date.nager.at/api/v3/PublicHolidays"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")

REST_COUNTRIES_FILE = os.path.join(DATA_DIR, "rest_countries.csv")

HOLIDAYS_FILE = os.path.join(DATA_DIR, "nager_holidays.csv")
SUMMARY_FILE = os.path.join(DATA_DIR, "nager_holiday_summary.csv")
VALIDATION_FILE = os.path.join(DATA_DIR, "nager_validation.csv")

load_dotenv()


# ============================================================
# LOAD REST COUNTRIES
# ============================================================

if not os.path.exists(REST_COUNTRIES_FILE):
    raise FileNotFoundError(
        "rest_countries.csv was not found inside the data folder."
    )

countries = pd.read_csv(REST_COUNTRIES_FILE)

print("=" * 70)
print("NAGER.DATE PUBLIC HOLIDAY DATA COLLECTION")
print("=" * 70)

print(f"REST Countries records loaded: {len(countries)}")

required_columns = ["Country Name", "ISO Alpha-2", "ISO Alpha-3"]

for column in required_columns:
    if column not in countries.columns:
        raise ValueError(
            f"Required column '{column}' is missing from rest_countries.csv"
        )

# Keep only usable ISO-2 codes
countries["ISO Alpha-2"] = (
    countries["ISO Alpha-2"]
    .astype("string")
    .str.strip()
    .str.upper()
)

valid_countries = countries[
    countries["ISO Alpha-2"].notna()
    & (countries["ISO Alpha-2"].str.len() == 2)
].copy()

# Remove duplicate ISO-2 codes
valid_countries = valid_countries.drop_duplicates(
    subset=["ISO Alpha-2"]
)

print(f"Countries with valid ISO-2 codes: {len(valid_countries)}")


# ============================================================
# API COLLECTION
# ============================================================

all_holidays = []
api_failures = []

session = requests.Session()

headers = {
    "User-Agent": "Country-Intelligence-Project/1.0"
}

for index, row in valid_countries.iterrows():

    country_name = row["Country Name"]
    country_code = row["ISO Alpha-2"]

    url = f"{API_URL}/{YEAR}/{country_code}"

    try:
        response = session.get(
            url,
            headers=headers,
            timeout=30
        )

        if response.status_code == 200:

            data = response.json()

            if isinstance(data, list):

                for holiday in data:

                    all_holidays.append({
                        "Country Name": country_name,
                        "Country Code": country_code,
                        "Holiday Date": holiday.get("date"),
                        "Local Name": holiday.get("localName"),
                        "English Name": holiday.get("name"),
                        "Fixed": holiday.get("fixed"),
                        "Global": holiday.get("global"),
                        "Counties": (
                            ", ".join(holiday.get("counties", []))
                            if isinstance(holiday.get("counties"), list)
                            else holiday.get("counties")
                        ),
                        "Launch Year": holiday.get("launchYear"),
                        "Types": (
                            ", ".join(holiday.get("types", []))
                            if isinstance(holiday.get("types"), list)
                            else holiday.get("types")
                        )
                    })

                print(
                    f"[{index + 1}/{len(valid_countries)}] "
                    f"{country_name}: {len(data)} holidays"
                )

            else:
                api_failures.append({
                    "Country Name": country_name,
                    "Country Code": country_code,
                    "Status Code": response.status_code,
                    "Reason": "API response was not a list"
                })

        else:

            api_failures.append({
                "Country Name": country_name,
                "Country Code": country_code,
                "Status Code": response.status_code,
                "Reason": response.text[:200]
            })

            print(
                f"[{index + 1}/{len(valid_countries)}] "
                f"{country_name}: API status {response.status_code}"
            )

    except requests.RequestException as error:

        api_failures.append({
            "Country Name": country_name,
            "Country Code": country_code,
            "Status Code": None,
            "Reason": str(error)
        })

        print(
            f"[{index + 1}/{len(valid_countries)}] "
            f"{country_name}: request failed"
        )

    # Small delay to avoid unnecessarily aggressive requests
    time.sleep(0.05)


# ============================================================
# CREATE RAW HOLIDAY DATAFRAME
# ============================================================

holidays_df = pd.DataFrame(all_holidays)

if holidays_df.empty:

    print("\nNo holiday data was returned from Nager.Date.")

    holidays_df = pd.DataFrame(columns=[
        "Country Name",
        "Country Code",
        "Holiday Date",
        "Local Name",
        "English Name",
        "Fixed",
        "Global",
        "Counties",
        "Launch Year",
        "Types"
    ])

else:

    holidays_df["Holiday Date"] = pd.to_datetime(
        holidays_df["Holiday Date"],
        errors="coerce"
    )

    # Remove exact duplicate holiday records
    holidays_df = holidays_df.drop_duplicates(
        subset=[
            "Country Code",
            "Holiday Date",
            "English Name"
        ]
    )


# ============================================================
# SAVE RAW HOLIDAY DATA
# ============================================================

holidays_df.to_csv(
    HOLIDAYS_FILE,
    index=False,
    encoding="utf-8-sig"
)

print("\nRaw holiday data saved:")
print(HOLIDAYS_FILE)

print(f"Total holiday records: {len(holidays_df)}")


# ============================================================
# COUNTRY-LEVEL SUMMARY
# ============================================================

summary = valid_countries[
    [
        "Country Name",
        "ISO Alpha-2",
        "ISO Alpha-3"
    ]
].copy()

summary = summary.rename(
    columns={
        "ISO Alpha-2": "Country Code"
    }
)

# Convert holiday data to country-level information
if not holidays_df.empty:

    holiday_group = holidays_df.groupby(
        "Country Code"
    )

    holiday_counts = holiday_group.size().rename(
        "Public Holidays 2026"
    )

    summary = summary.merge(
        holiday_counts,
        on="Country Code",
        how="left"
    )

    # Collect holiday names
    holiday_names = holiday_group["English Name"].apply(
        lambda x: " | ".join(
            sorted(
                set(
                    str(value)
                    for value in x
                    if pd.notna(value)
                )
            )
        )
    ).rename("Holiday Names 2026")

    summary = summary.merge(
        holiday_names,
        on="Country Code",
        how="left"
    )

    # Collect holiday dates
    holiday_dates = holiday_group["Holiday Date"].apply(
        lambda x: " | ".join(
            sorted(
                set(
                    value.strftime("%Y-%m-%d")
                    for value in x
                    if pd.notna(value)
                )
            )
        )
    ).rename("Holiday Dates 2026")

    summary = summary.merge(
        holiday_dates,
        on="Country Code",
        how="left"
    )

else:

    summary["Public Holidays 2026"] = pd.NA
    summary["Holiday Names 2026"] = pd.NA
    summary["Holiday Dates 2026"] = pd.NA


# Countries without Nager data remain missing
summary["Public Holidays 2026"] = summary[
    "Public Holidays 2026"
].astype("Int64")


# ============================================================
# SAVE SUMMARY
# ============================================================

summary.to_csv(
    SUMMARY_FILE,
    index=False,
    encoding="utf-8-sig"
)

print("\nCountry-level holiday summary saved:")
print(SUMMARY_FILE)


# ============================================================
# VALIDATION
# ============================================================

validation = []

# Total countries
validation.append({
    "Validation": "Total Countries",
    "Value": len(summary),
    "Status": "INFO"
})

# Total holiday records
validation.append({
    "Validation": "Total Holiday Records",
    "Value": len(holidays_df),
    "Status": "INFO"
})

# Total columns
validation.append({
    "Validation": "Total Holiday Columns",
    "Value": len(holidays_df.columns),
    "Status": "INFO"
})

# Duplicate records
if not holidays_df.empty:

    duplicate_records = holidays_df.duplicated(
        subset=[
            "Country Code",
            "Holiday Date",
            "English Name"
        ]
    ).sum()

else:

    duplicate_records = 0

validation.append({
    "Validation": "Duplicate Holiday Records",
    "Value": int(duplicate_records),
    "Status": "PASS" if duplicate_records == 0 else "CHECK"
})

# Missing country codes
missing_country_codes = holidays_df[
    "Country Code"
].isna().sum()

validation.append({
    "Validation": "Missing Country Codes",
    "Value": int(missing_country_codes),
    "Status": "PASS" if missing_country_codes == 0 else "CHECK"
})

# Invalid dates
invalid_dates = holidays_df[
    "Holiday Date"
].isna().sum()

validation.append({
    "Validation": "Invalid Holiday Dates",
    "Value": int(invalid_dates),
    "Status": "PASS" if invalid_dates == 0 else "CHECK"
})

# Missing English holiday names
missing_names = holidays_df[
    "English Name"
].isna().sum()

validation.append({
    "Validation": "Missing English Holiday Names",
    "Value": int(missing_names),
    "Status": "PASS" if missing_names == 0 else "CHECK"
})

# Global field validation
if not holidays_df.empty:

    invalid_global = ~holidays_df["Global"].isin(
        [True, False]
    )

    invalid_global_count = invalid_global.sum()

else:

    invalid_global_count = 0

validation.append({
    "Validation": "Invalid Global Status",
    "Value": int(invalid_global_count),
    "Status": "PASS" if invalid_global_count == 0 else "CHECK"
})

# Countries with data
countries_with_data = (
    holidays_df["Country Code"].nunique()
    if not holidays_df.empty
    else 0
)

validation.append({
    "Validation": "Countries With Holiday Data",
    "Value": int(countries_with_data),
    "Status": "INFO"
})

# Countries without data
countries_without_data = (
    len(summary) - countries_with_data
)

validation.append({
    "Validation": "Countries Without Holiday Data",
    "Value": int(countries_without_data),
    "Status": "INFO"
})

# API failures
validation.append({
    "Validation": "API Failures",
    "Value": len(api_failures),
    "Status": "INFO"
})

# Coverage percentage
coverage = (
    countries_with_data / len(summary) * 100
    if len(summary) > 0
    else 0
)

validation.append({
    "Validation": "Holiday Country Coverage (%)",
    "Value": round(coverage, 2),
    "Status": "INFO"
})


validation_df = pd.DataFrame(validation)

validation_df.to_csv(
    VALIDATION_FILE,
    index=False,
    encoding="utf-8-sig"
)


# ============================================================
# DISPLAY RESULTS
# ============================================================

print("\n" + "=" * 70)
print("VALIDATION RESULTS")
print("=" * 70)

print(
    validation_df.to_string(index=False)
)

print("\n" + "=" * 70)
print("API FAILURES")
print("=" * 70)

if api_failures:

    failures_df = pd.DataFrame(api_failures)

    print(
        failures_df.to_string(index=False)
    )

else:

    print("No API failures.")


print("\n" + "=" * 70)
print("SAMPLE HOLIDAY DATA")
print("=" * 70)

if not holidays_df.empty:

    display_columns = [
        "Country Name",
        "Country Code",
        "Holiday Date",
        "English Name",
        "Global",
        "Types"
    ]

    print(
        holidays_df[
            display_columns
        ].head(15).to_string(index=False)
    )

print("\n" + "=" * 70)
print("SAMPLE COUNTRY SUMMARY")
print("=" * 70)

print(
    summary.head(10).to_string(index=False)
)

print("\nFiles created:")
print(f"1. {HOLIDAYS_FILE}")
print(f"2. {SUMMARY_FILE}")
print(f"3. {VALIDATION_FILE}")

print("\nStep 6 completed.")