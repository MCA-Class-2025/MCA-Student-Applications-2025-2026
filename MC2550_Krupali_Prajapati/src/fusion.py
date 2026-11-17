import os
import requests
import pandas as pd

# ============================================================
# CONFIGURATION
# ============================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")

OUTPUT_FILE = os.path.join(
    DATA_DIR,
    "fused_country_intelligence.csv"
)

VALIDATION_FILE = os.path.join(
    DATA_DIR,
    "fusion_validation.csv"
)

WDI_URL = "https://api.worldbank.org/v2/country/all/indicator"

# WDI indicators used in the project
WDI_INDICATORS = {
    "Population": "SP.POP.TOTL",
    "GDP": "NY.GDP.MKTP.CD",
    "GDP per capita": "NY.GDP.PCAP.CD",
    "Life expectancy": "SP.DYN.LE00.IN",
    "Unemployment": "SL.UEM.TOTL.ZS",
    "Internet usage": "IT.NET.USER.ZS"
}


# ============================================================
# INPUT FILES
# ============================================================

REST_FILE = os.path.join(
    DATA_DIR,
    "rest_countries.csv"
)

WEATHER_FILE = os.path.join(
    DATA_DIR,
    "open_meteo_weather.csv"
)

FRANKFURTER_FILE = os.path.join(
    DATA_DIR,
    "frankfurter_rates.csv"
)

OPENAQ_FILE = os.path.join(
    DATA_DIR,
    "openaq_air_quality.csv"
)

NAGER_FILE = os.path.join(
    DATA_DIR,
    "nager_holiday_summary.csv"
)


# ============================================================
# HELPER FUNCTION
# ============================================================

def check_file(path, name):

    if not os.path.exists(path):

        raise FileNotFoundError(
            f"{name} was not found:\n{path}"
        )


# ============================================================
# START
# ============================================================

print("=" * 80)
print("COUNTRY INTELLIGENCE DATA FUSION")
print("=" * 80)


# ============================================================
# CHECK INPUT FILES
# ============================================================

check_file(
    REST_FILE,
    "REST Countries file"
)

check_file(
    WEATHER_FILE,
    "Open-Meteo file"
)

check_file(
    FRANKFURTER_FILE,
    "Frankfurter file"
)

check_file(
    OPENAQ_FILE,
    "OpenAQ file"
)

check_file(
    NAGER_FILE,
    "Nager.Date summary file"
)

print("\nAll external API files found.")


# ============================================================
# LOAD REST COUNTRIES
# ============================================================

rest = pd.read_csv(
    REST_FILE
)

print(
    f"\nREST Countries records: {len(rest)}"
)

required_rest_columns = [
    "Country Name",
    "ISO Alpha-2",
    "ISO Alpha-3"
]

for column in required_rest_columns:

    if column not in rest.columns:

        raise ValueError(
            f"Required REST Countries column "
            f"'{column}' is missing."
        )


# Standardize ISO codes
rest["ISO Alpha-2"] = (
    rest["ISO Alpha-2"]
    .astype("string")
    .str.strip()
    .str.upper()
)

rest["ISO Alpha-3"] = (
    rest["ISO Alpha-3"]
    .astype("string")
    .str.strip()
    .str.upper()
)


# Remove records without ISO-3
rest_valid_iso3 = rest[
    rest["ISO Alpha-3"].notna()
].copy()


# Remove duplicate ISO-3 records
rest_valid_iso3 = (
    rest_valid_iso3
    .drop_duplicates(
        subset=["ISO Alpha-3"],
        keep="first"
    )
)

print(
    f"REST Countries after duplicate handling: "
    f"{len(rest_valid_iso3)}"
)


# ============================================================
# WORLD BANK WDI FUNCTION
# ============================================================

def get_wdi_indicator(
    indicator_code,
    indicator_name
):

    print(
        f"\nDownloading WDI indicator: "
        f"{indicator_name} ({indicator_code})"
    )

    all_records = []

    page = 1

    while True:

        params = {
            "format": "json",
            "per_page": 1000,
            "page": page
        }

        url = (
            f"{WDI_URL}/"
            f"{indicator_code}"
        )

        response = requests.get(
            url,
            params=params,
            timeout=60
        )

        response.raise_for_status()

        data = response.json()

        if (
            not isinstance(data, list)
            or len(data) < 2
        ):
            break

        metadata = data[0]
        records = data[1]

        all_records.extend(records)

        total_pages = int(
            metadata.get(
                "pages",
                1
            )
        )

        if page >= total_pages:

            break

        page += 1

    if not all_records:

        raise ValueError(
            f"No WDI data returned for "
            f"{indicator_code}"
        )

    rows = []

    for record in all_records:

        country_code = (
            record.get(
                "countryiso3code"
            )
        )

        year = record.get(
            "date"
        )

        value = record.get(
            "value"
        )

        if (
            country_code
            and year
            and value is not None
        ):

            rows.append({
                "Country Code":
                    str(country_code)
                    .strip()
                    .upper(),

                "Year":
                    int(year),

                indicator_name:
                    value
            })

    df = pd.DataFrame(
        rows
    )

    if df.empty:

        raise ValueError(
            f"No usable WDI records for "
            f"{indicator_code}"
        )

    df = df.drop_duplicates(
        subset=[
            "Country Code",
            "Year"
        ],
        keep="first"
    )

    print(
        f"Usable records: {len(df)}"
    )

    return df


# ============================================================
# DOWNLOAD ALL WDI INDICATORS
# ============================================================

wdi = None

for (
    indicator_name,
    indicator_code
) in WDI_INDICATORS.items():

    indicator_df = get_wdi_indicator(
        indicator_code,
        indicator_name
    )

    if wdi is None:

        wdi = indicator_df

    else:

        wdi = wdi.merge(
            indicator_df,
            on=[
                "Country Code",
                "Year"
            ],
            how="outer"
        )


# ============================================================
# FILTER TO REAL COUNTRIES
# ============================================================

valid_iso3 = set(
    rest_valid_iso3[
        "ISO Alpha-3"
    ]
    .dropna()
    .astype(str)
)

wdi = wdi[
    wdi["Country Code"].isin(
        valid_iso3
    )
].copy()

print(
    f"\nWDI country/year records after "
    f"country filtering: {len(wdi)}"
)


# ============================================================
# SELECT WDI REFERENCE YEAR
# ============================================================

required_wdi_columns = list(
    WDI_INDICATORS.keys()
)

# Count complete country records for each year
year_quality = (
    wdi.groupby("Year")[
        required_wdi_columns
    ]
    .apply(
        lambda x:
        x.notna()
        .all(axis=1)
        .sum()
    )
    .sort_index(
        ascending=False
    )
)

reference_year = None

for (
    year,
    complete_count
) in year_quality.items():

    if complete_count > 0:

        reference_year = int(year)

        break


if reference_year is None:

    raise ValueError(
        "No year contains usable WDI data."
    )


print(
    f"Selected WDI reference year: "
    f"{reference_year}"
)


# ============================================================
# CREATE WDI SNAPSHOT
# ============================================================

wdi_snapshot = wdi[
    wdi["Year"] == reference_year
].copy()

wdi_snapshot = wdi_snapshot.rename(
    columns={
        "Year":
            "WDI Reference Year"
    }
)


# Add country name
wdi_snapshot = wdi_snapshot.merge(
    rest_valid_iso3[
        [
            "ISO Alpha-3",
            "Country Name"
        ]
    ],
    left_on="Country Code",
    right_on="ISO Alpha-3",
    how="left"
)

wdi_snapshot = wdi_snapshot.drop(
    columns=[
        "ISO Alpha-3"
    ]
)


# ============================================================
# LOAD OPEN-METEO
# ============================================================

weather = pd.read_csv(
    WEATHER_FILE
)

print(
    f"Open-Meteo records: "
    f"{len(weather)}"
)

weather["ISO Alpha-3"] = (
    weather["ISO Alpha-3"]
    .astype("string")
    .str.strip()
    .str.upper()
)

weather = weather.drop_duplicates(
    subset=["ISO Alpha-3"],
    keep="first"
)


# ============================================================
# LOAD FRANKFURTER
# ============================================================

frankfurter = pd.read_csv(
    FRANKFURTER_FILE
)

print(
    f"Frankfurter records: "
    f"{len(frankfurter)}"
)

frankfurter["ISO Alpha-3"] = (
    frankfurter["ISO Alpha-3"]
    .astype("string")
    .str.strip()
    .str.upper()
)

frankfurter = (
    frankfurter
    .drop_duplicates(
        subset=["ISO Alpha-3"],
        keep="first"
    )
)


# ============================================================
# LOAD OPENAQ
# ============================================================

openaq = pd.read_csv(
    OPENAQ_FILE
)

print(
    f"OpenAQ records: "
    f"{len(openaq)}"
)

openaq["ISO Alpha-2"] = (
    openaq["ISO Alpha-2"]
    .astype("string")
    .str.strip()
    .str.upper()
)

openaq = openaq.drop_duplicates(
    subset=["ISO Alpha-2"],
    keep="first"
)


# ============================================================
# LOAD NAGER.DATE
# ============================================================

nager = pd.read_csv(
    NAGER_FILE
)

print(
    f"Nager.Date records: "
    f"{len(nager)}"
)

nager["Country Code"] = (
    nager["Country Code"]
    .astype("string")
    .str.strip()
    .str.upper()
)

nager = nager.drop_duplicates(
    subset=["Country Code"],
    keep="first"
)


# ============================================================
# START FUSION
# ============================================================

fused = wdi_snapshot.copy()

print(
    "\nStarting data fusion..."
)


# ============================================================
# 1. JOIN REST COUNTRIES
# ============================================================

rest_columns = [
    "ISO Alpha-3",
    "ISO Alpha-2",
    "Official Name",
    "Capital",
    "Capital Latitude",
    "Capital Longitude",
    "Region",
    "Subregion",
    "Currency Code",
    "Currency Name",
    "Languages",
    "Area (km²)",
    "Borders",
    "Time Zones",
    "Latitude",
    "Longitude"
]

rest_join = rest_valid_iso3[
    [
        column
        for column in rest_columns
        if column in rest_valid_iso3.columns
    ]
].copy()

rest_join = rest_join.rename(
    columns={
        "ISO Alpha-3":
            "Country Code"
    }
)

fused = fused.merge(
    rest_join,
    on="Country Code",
    how="left",
    suffixes=(
        "",
        "_REST"
    )
)


# ============================================================
# 2. JOIN OPEN-METEO
# ============================================================

weather_columns = [
    "ISO Alpha-3",
    "Weather Observation Time",
    "Temperature (°C)",
    "Apparent Temperature (°C)",
    "Relative Humidity (%)",
    "Precipitation (mm)",
    "Wind Speed (km/h)",
    "Weather Code"
]

weather_join = weather[
    [
        column
        for column in weather_columns
        if column in weather.columns
    ]
].copy()

weather_join = weather_join.rename(
    columns={
        "ISO Alpha-3":
            "Country Code"
    }
)

fused = fused.merge(
    weather_join,
    on="Country Code",
    how="left",
    suffixes=(
        "",
        "_WEATHER"
    )
)


# ============================================================
# 3. JOIN FRANKFURTER
# ============================================================

frankfurter_columns = [
    "ISO Alpha-3",
    "Base Currency",
    "Currency Code",
    "Exchange Rate",
    "Rate Date"
]

frankfurter_join = frankfurter[
    [
        column
        for column in frankfurter_columns
        if column in frankfurter.columns
    ]
].copy()

# Rename ISO-3 to the WDI master key
frankfurter_join = frankfurter_join.rename(
    columns={
        "ISO Alpha-3":
            "Country Code",

        "Currency Code":
            "Frankfurter Currency Code"
    }
)

fused = fused.merge(
    frankfurter_join,
    on="Country Code",
    how="left",
    suffixes=(
        "",
        "_FRANKFURTER"
    )
)


# ============================================================
# 4. JOIN OPENAQ
# ============================================================

openaq_columns = [
    "ISO Alpha-2",
    "OpenAQ Location",
    "OpenAQ Latitude",
    "OpenAQ Longitude",
    "PM2.5",
    "PM2.5 Measurement Time",
    "PM10",
    "PM10 Measurement Time",
    "NO2",
    "NO2 Measurement Time",
    "O3",
    "O3 Measurement Time"
]

openaq_join = openaq[
    [
        column
        for column in openaq_columns
        if column in openaq.columns
    ]
].copy()

fused = fused.merge(
    openaq_join,
    on="ISO Alpha-2",
    how="left",
    suffixes=(
        "",
        "_OPENAQ"
    )
)


# ============================================================
# 5. JOIN NAGER.DATE
# ============================================================

nager_columns = [
    "Country Code",
    "Public Holidays 2026",
    "Holiday Names 2026",
    "Holiday Dates 2026"
]

nager_join = nager[
    [
        column
        for column in nager_columns
        if column in nager.columns
    ]
].copy()

# ------------------------------------------------------------
# IMPORTANT:
# Nager.Date uses ISO ALPHA-2 country codes.
#
# Example:
# Albania = AL
# Algeria = DZ
# Andorra = AD
#
# The fused dataset contains:
# Country Code = ISO Alpha-3
# ISO Alpha-2 = ISO Alpha-2
#
# Therefore Nager must be joined through ISO Alpha-2.
# ------------------------------------------------------------

nager_join = nager_join.rename(
    columns={
        "Country Code":
            "ISO Alpha-2"
    }
)

fused = fused.merge(
    nager_join,
    on="ISO Alpha-2",
    how="left",
    suffixes=(
        "",
        "_NAGER"
    )
)


# ============================================================
# REMOVE UNNECESSARY DUPLICATE COLUMNS
# ============================================================

duplicate_columns = []

for column in fused.columns:

    if (
        column.endswith("_REST")
        or column.endswith("_WEATHER")
        or column.endswith("_FRANKFURTER")
        or column.endswith("_OPENAQ")
        or column.endswith("_NAGER")
    ):

        duplicate_columns.append(
            column
        )

if duplicate_columns:

    fused = fused.drop(
        columns=duplicate_columns
    )


# ============================================================
# CONVERT NUMERIC COLUMNS
# ============================================================

numeric_columns = [
    "Population",
    "GDP",
    "GDP per capita",
    "Life expectancy",
    "Unemployment",
    "Internet usage",
    "Area (km²)",
    "Capital Latitude",
    "Capital Longitude",
    "Latitude",
    "Longitude",
    "Temperature (°C)",
    "Apparent Temperature (°C)",
    "Relative Humidity (%)",
    "Precipitation (mm)",
    "Wind Speed (km/h)",
    "Exchange Rate",
    "OpenAQ Latitude",
    "OpenAQ Longitude",
    "PM2.5",
    "PM10",
    "NO2",
    "O3",
    "Public Holidays 2026"
]

for column in numeric_columns:

    if column in fused.columns:

        fused[column] = pd.to_numeric(
            fused[column],
            errors="coerce"
        )


# ============================================================
# SORT DATA
# ============================================================

fused = (
    fused
    .sort_values(
        by="Country Name"
    )
    .reset_index(
        drop=True
    )
)


# ============================================================
# VALIDATION
# ============================================================

validation = []


def add_validation(
    name,
    value,
    status="INFO"
):

    validation.append({
        "Validation": name,
        "Value": value,
        "Status": status
    })


# ------------------------------------------------------------
# BASIC DATASET VALIDATION
# ------------------------------------------------------------

add_validation(
    "Final Country Records",
    len(fused)
)

add_validation(
    "Final Columns",
    len(fused.columns)
)


# ------------------------------------------------------------
# DUPLICATE COUNTRY CODES
# ------------------------------------------------------------

duplicate_country_codes = (
    fused["Country Code"]
    .duplicated()
    .sum()
)

add_validation(
    "Duplicate Country Codes",
    int(duplicate_country_codes),
    (
        "PASS"
        if duplicate_country_codes == 0
        else "CHECK"
    )
)


# ------------------------------------------------------------
# MISSING COUNTRY CODES
# ------------------------------------------------------------

missing_country_codes = (
    fused["Country Code"]
    .isna()
    .sum()
)

add_validation(
    "Missing Country Codes",
    int(missing_country_codes),
    (
        "PASS"
        if missing_country_codes == 0
        else "CHECK"
    )
)


# ------------------------------------------------------------
# WDI MISSING VALUES
# ------------------------------------------------------------

for column in required_wdi_columns:

    if column in fused.columns:

        missing = (
            fused[column]
            .isna()
            .sum()
        )

        add_validation(
            f"Missing WDI - {column}",
            int(missing),
            "INFO"
        )


# ------------------------------------------------------------
# REST COUNTRIES MATCHES
# ------------------------------------------------------------

rest_matches = (
    fused["ISO Alpha-2"]
    .notna()
    .sum()
)

add_validation(
    "REST Countries Matches",
    int(rest_matches),
    "INFO"
)


# ------------------------------------------------------------
# OPEN-METEO MATCHES
# ------------------------------------------------------------

if "Temperature (°C)" in fused.columns:

    weather_matches = (
        fused["Temperature (°C)"]
        .notna()
        .sum()
    )

else:

    weather_matches = 0

add_validation(
    "Open-Meteo Matches",
    int(weather_matches),
    "INFO"
)


# ------------------------------------------------------------
# FRANKFURTER MATCHES
# ------------------------------------------------------------

if "Exchange Rate" in fused.columns:

    frankfurter_matches = (
        fused["Exchange Rate"]
        .notna()
        .sum()
    )

else:

    frankfurter_matches = 0

add_validation(
    "Frankfurter Matches",
    int(frankfurter_matches),
    "INFO"
)


# ------------------------------------------------------------
# OPENAQ MATCHES
# ------------------------------------------------------------

if "PM2.5" in fused.columns:

    openaq_matches = (
        fused["PM2.5"]
        .notna()
        .sum()
    )

else:

    openaq_matches = 0

add_validation(
    "OpenAQ PM2.5 Matches",
    int(openaq_matches),
    "INFO"
)


# ------------------------------------------------------------
# NAGER MATCHES
# ------------------------------------------------------------

if "Public Holidays 2026" in fused.columns:

    nager_matches = (
        fused[
            "Public Holidays 2026"
        ]
        .notna()
        .sum()
    )

else:

    nager_matches = 0

add_validation(
    "Nager Holiday Matches",
    int(nager_matches),
    "INFO"
)


# ------------------------------------------------------------
# MISSING VALUES BY API
# ------------------------------------------------------------

api_columns = {

    "REST Countries": [
        "ISO Alpha-2",
        "Capital",
        "Currency Code"
    ],

    "Open-Meteo": [
        "Temperature (°C)"
    ],

    "Frankfurter": [
        "Exchange Rate"
    ],

    "OpenAQ": [
        "PM2.5"
    ],

    "Nager.Date": [
        "Public Holidays 2026"
    ]
}


for api_name, columns in api_columns.items():

    for column in columns:

        if column in fused.columns:

            missing = (
                fused[column]
                .isna()
                .sum()
            )

            add_validation(
                f"{api_name} Missing - {column}",
                int(missing),
                "INFO"
            )


# ============================================================
# SAVE FUSED DATASET
# ============================================================

fused.to_csv(
    OUTPUT_FILE,
    index=False,
    encoding="utf-8-sig"
)


# ============================================================
# SAVE VALIDATION
# ============================================================

validation_df = pd.DataFrame(
    validation
)

validation_df.to_csv(
    VALIDATION_FILE,
    index=False,
    encoding="utf-8-sig"
)


# ============================================================
# DISPLAY FINAL RESULTS
# ============================================================

print(
    "\n" + "=" * 80
)

print(
    "FUSION COMPLETED"
)

print(
    "=" * 80
)

print(
    f"Final dataset rows: "
    f"{len(fused)}"
)

print(
    f"Final dataset columns: "
    f"{len(fused.columns)}"
)

print(
    f"WDI reference year: "
    f"{reference_year}"
)

print(
    "\nFused dataset saved to:"
)

print(
    OUTPUT_FILE
)

print(
    "\nFusion validation saved to:"
)

print(
    VALIDATION_FILE
)


# ============================================================
# VALIDATION RESULTS
# ============================================================

print(
    "\n" + "=" * 80
)

print(
    "VALIDATION RESULTS"
)

print(
    "=" * 80
)

print(
    validation_df.to_string(
        index=False
    )
)


# ============================================================
# FINAL DATASET COLUMNS
# ============================================================

print(
    "\n" + "=" * 80
)

print(
    "FINAL DATASET COLUMNS"
)

print(
    "=" * 80
)

for index, column in enumerate(
    fused.columns,
    start=1
):

    print(
        f"{index:02d}. {column}"
    )


# ============================================================
# SAMPLE DATA
# ============================================================

print(
    "\n" + "=" * 80
)

print(
    "SAMPLE FUSED DATA"
)

print(
    "=" * 80
)


sample_columns = [
    "Country Name",
    "Country Code",
    "WDI Reference Year",
    "Population",
    "GDP",
    "GDP per capita",
    "Life expectancy",
    "Internet usage",
    "Capital",
    "Region",
    "Currency Code",
    "Temperature (°C)",
    "Exchange Rate",
    "PM2.5",
    "PM10",
    "Public Holidays 2026"
]


sample_columns = [
    column
    for column in sample_columns
    if column in fused.columns
]


print(
    fused[
        sample_columns
    ]
    .head(10)
    .to_string(
        index=False
    )
)


print(
    "\nStep 7 completed successfully."
)