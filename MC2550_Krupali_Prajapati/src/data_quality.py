import os
import pandas as pd
import numpy as np


# ============================================================
# CONFIGURATION
# ============================================================

INPUT_FILE = os.path.join(
    "data",
    "fused_country_intelligence.csv"
)

OUTPUT_DIR = os.path.join(
    "data",
    "quality_outputs"
)

os.makedirs(OUTPUT_DIR, exist_ok=True)


# ============================================================
# LOAD DATA
# ============================================================

print("=" * 70)
print("PART D - DATA QUALITY ASSESSMENT")
print("=" * 70)

df = pd.read_csv(INPUT_FILE)

print(f"\nDataset loaded successfully.")
print(f"Records   : {df.shape[0]}")
print(f"Attributes: {df.shape[1]}")


# ============================================================
# 1. STRUCTURAL QUALITY CHECKS
# ============================================================

print("\n" + "=" * 70)
print("1. STRUCTURAL QUALITY CHECKS")
print("=" * 70)

structural_results = []

# Dimensions
structural_results.append({
    "Check": "Number of Records",
    "Result": df.shape[0],
    "Status": "PASS"
})

structural_results.append({
    "Check": "Number of Attributes",
    "Result": df.shape[1],
    "Status": "PASS"
})

# Duplicate rows
duplicate_rows = int(df.duplicated().sum())

structural_results.append({
    "Check": "Duplicate Complete Rows",
    "Result": duplicate_rows,
    "Status": "PASS" if duplicate_rows == 0 else "CHECK"
})

# Country Code missing
missing_country_code = int(df["Country Code"].isna().sum())

structural_results.append({
    "Check": "Missing Country Codes",
    "Result": missing_country_code,
    "Status": "PASS" if missing_country_code == 0 else "CHECK"
})

# Country Code duplicates
duplicate_country_codes = int(
    df["Country Code"].duplicated().sum()
)

structural_results.append({
    "Check": "Duplicate Country Codes",
    "Result": duplicate_country_codes,
    "Status": "PASS" if duplicate_country_codes == 0 else "CHECK"
})

structural_df = pd.DataFrame(structural_results)

print(structural_df.to_string(index=False))

structural_df.to_csv(
    os.path.join(OUTPUT_DIR, "structural_checks.csv"),
    index=False
)


# ============================================================
# 2. DATA TYPES AND UNIQUE VALUES
# ============================================================

print("\n" + "=" * 70)
print("2. DATA TYPES AND UNIQUE VALUES")
print("=" * 70)

data_types_unique = pd.DataFrame({
    "Attribute": df.columns,
    "Data Type": [str(df[col].dtype) for col in df.columns],
    "Unique Values": [df[col].nunique(dropna=True) for col in df.columns],
    "Missing Values": [df[col].isna().sum() for col in df.columns]
})

print(data_types_unique.to_string(index=False))

data_types_unique.to_csv(
    os.path.join(OUTPUT_DIR, "data_types_unique.csv"),
    index=False
)


# ============================================================
# 3. MISSING VALUE ANALYSIS
# ============================================================

print("\n" + "=" * 70)
print("3. MISSING VALUE ANALYSIS")
print("=" * 70)

missing_values = pd.DataFrame({
    "Attribute": df.columns,
    "Missing Count": df.isna().sum(),
    "Missing Percentage": (
        df.isna().mean() * 100
    ).round(2)
})

missing_values = missing_values.sort_values(
    by="Missing Count",
    ascending=False
)

print(missing_values.to_string(index=False))

missing_values.to_csv(
    os.path.join(OUTPUT_DIR, "missing_values.csv"),
    index=False
)

max_missing = missing_values.iloc[0]

print(
    f"\nAttribute with maximum missing values: "
    f"{max_missing['Attribute']} "
    f"({int(max_missing['Missing Count'])} missing, "
    f"{max_missing['Missing Percentage']:.2f}%)"
)


# ============================================================
# 4. CATEGORICAL / IDENTIFIER CONSISTENCY
# ============================================================

print("\n" + "=" * 70)
print("4. CATEGORICAL AND IDENTIFIER CONSISTENCY")
print("=" * 70)

consistency_results = []


def add_consistency_check(
    attribute,
    check,
    invalid_count,
    details
):
    consistency_results.append({
        "Attribute": attribute,
        "Check": check,
        "Invalid Count": invalid_count,
        "Details": details
    })


# ------------------------------------------------------------
# Country Code
# ------------------------------------------------------------

country_code = df["Country Code"].dropna().astype(str)

invalid_country_code = (
    ~country_code.str.fullmatch(r"[A-Z]{3}")
).sum()

add_consistency_check(
    "Country Code",
    "ISO Alpha-3 format",
    int(invalid_country_code),
    "Must contain exactly three uppercase letters"
)


# ------------------------------------------------------------
# ISO Alpha-2
# ------------------------------------------------------------

iso2 = df["ISO Alpha-2"].dropna().astype(str)

invalid_iso2 = (
    ~iso2.str.fullmatch(r"[A-Z]{2}")
).sum()

add_consistency_check(
    "ISO Alpha-2",
    "ISO Alpha-2 format",
    int(invalid_iso2),
    "Must contain exactly two uppercase letters"
)


# ------------------------------------------------------------
# Currency Code
# ------------------------------------------------------------

currency = df["Currency Code"].dropna().astype(str)

invalid_currency = (
    ~currency.str.fullmatch(r"[A-Z]{3}(,\s*[A-Z]{3})*")
).sum()

add_consistency_check(
    "Currency Code",
    "Currency code format",
    int(invalid_currency),
    "Currency codes should contain three uppercase letters"
)


# ------------------------------------------------------------
# Country Name whitespace
# ------------------------------------------------------------

country_names = df["Country Name"].dropna().astype(str)

whitespace_errors = (
    country_names != country_names.str.strip()
).sum()

add_consistency_check(
    "Country Name",
    "Leading/trailing whitespace",
    int(whitespace_errors),
    "Country names should not contain leading/trailing spaces"
)


# ------------------------------------------------------------
# Region missing
# ------------------------------------------------------------

region_missing = int(df["Region"].isna().sum())

add_consistency_check(
    "Region",
    "Missing category",
    region_missing,
    "Region should be populated where source data provides it"
)


# ------------------------------------------------------------
# Subregion missing
# ------------------------------------------------------------

subregion_missing = int(df["Subregion"].isna().sum())

add_consistency_check(
    "Subregion",
    "Missing category",
    subregion_missing,
    "Subregion may be unavailable for some records"
)


# ------------------------------------------------------------
# Geographic latitude
# ------------------------------------------------------------

lat = pd.to_numeric(
    df["Latitude"],
    errors="coerce"
)

invalid_lat = (
    lat.notna() &
    ((lat < -90) | (lat > 90))
).sum()

add_consistency_check(
    "Latitude",
    "Valid geographic range",
    int(invalid_lat),
    "Valid range is -90 to +90 degrees"
)


# ------------------------------------------------------------
# Geographic longitude
# ------------------------------------------------------------

lon = pd.to_numeric(
    df["Longitude"],
    errors="coerce"
)

invalid_lon = (
    lon.notna() &
    ((lon < -180) | (lon > 180))
).sum()

add_consistency_check(
    "Longitude",
    "Valid geographic range",
    int(invalid_lon),
    "Valid range is -180 to +180 degrees"
)


# ------------------------------------------------------------
# Capital latitude
# ------------------------------------------------------------

capital_lat = pd.to_numeric(
    df["Capital Latitude"],
    errors="coerce"
)

invalid_capital_lat = (
    capital_lat.notna() &
    ((capital_lat < -90) | (capital_lat > 90))
).sum()

add_consistency_check(
    "Capital Latitude",
    "Valid geographic range",
    int(invalid_capital_lat),
    "Valid range is -90 to +90 degrees"
)


# ------------------------------------------------------------
# Capital longitude
# ------------------------------------------------------------

capital_lon = pd.to_numeric(
    df["Capital Longitude"],
    errors="coerce"
)

invalid_capital_lon = (
    capital_lon.notna() &
    ((capital_lon < -180) | (capital_lon > 180))
).sum()

add_consistency_check(
    "Capital Longitude",
    "Valid geographic range",
    int(invalid_capital_lon),
    "Valid range is -180 to +180 degrees"
)


# ------------------------------------------------------------
# Currency consistency
# ------------------------------------------------------------

currency_a = (
    df["Currency Code"]
    .fillna("")
    .astype(str)
    .str.split(",")
    .str[0]
    .str.strip()
)

currency_b = (
    df["Frankfurter Currency Code"]
    .fillna("")
    .astype(str)
    .str.strip()
)

currency_conflicts = (
    (currency_a != "") &
    (currency_b != "") &
    (currency_a != currency_b)
).sum()

add_consistency_check(
    "Currency",
    "Currency Code vs Frankfurter Currency Code",
    int(currency_conflicts),
    "Compared the primary country currency with the Frankfurter currency code"
)


# Save consistency results
consistency_df = pd.DataFrame(consistency_results)

print(consistency_df.to_string(index=False))

consistency_df.to_csv(
    os.path.join(OUTPUT_DIR, "consistency_checks.csv"),
    index=False
)


# ============================================================
# 5. NUMERICAL VALIDITY
# ============================================================

print("\n" + "=" * 70)
print("5. NUMERICAL VALIDITY CHECKS")
print("=" * 70)

numerical_rules = {

    "Population": (
        lambda x: x < 0,
        "Population cannot be negative"
    ),

    "GDP": (
        lambda x: x < 0,
        "GDP cannot be negative"
    ),

    "GDP per capita": (
        lambda x: x < 0,
        "GDP per capita cannot be negative"
    ),

    "Life expectancy": (
        lambda x: (x < 0) | (x > 100),
        "Expected range: 0 to 100 years"
    ),

    "Unemployment": (
        lambda x: (x < 0) | (x > 100),
        "Expected percentage range: 0 to 100"
    ),

    "Internet usage": (
        lambda x: (x < 0) | (x > 100),
        "Expected percentage range: 0 to 100"
    ),

    "Area (km²)": (
        lambda x: x < 0,
        "Area cannot be negative"
    ),

    "Relative Humidity (%)": (
        lambda x: (x < 0) | (x > 100),
        "Expected percentage range: 0 to 100"
    ),

    "Precipitation (mm)": (
        lambda x: x < 0,
        "Precipitation cannot be negative"
    ),

    "Wind Speed (km/h)": (
        lambda x: x < 0,
        "Wind speed cannot be negative"
    ),

    "Exchange Rate": (
        lambda x: x <= 0,
        "Exchange rate must be positive"
    ),

    "PM2.5": (
        lambda x: x < 0,
        "Air-quality concentration cannot be negative"
    ),

    "PM10": (
        lambda x: x < 0,
        "Air-quality concentration cannot be negative"
    ),

    "NO2": (
        lambda x: x < 0,
        "Air-quality concentration cannot be negative"
    ),

    "O3": (
        lambda x: x < 0,
        "Air-quality concentration cannot be negative"
    ),

    "Public Holidays 2026": (
        lambda x: x < 0,
        "Holiday count cannot be negative"
    )
}


numerical_results = []

for column, (rule, explanation) in numerical_rules.items():

    values = pd.to_numeric(
        df[column],
        errors="coerce"
    )

    invalid_mask = (
        values.notna() &
        rule(values)
    )

    invalid_count = int(invalid_mask.sum())

    numerical_results.append({
        "Attribute": column,
        "Invalid Values": invalid_count,
        "Status": "PASS" if invalid_count == 0 else "CHECK",
        "Validation Rule": explanation
    })

    if invalid_count > 0:
        print(
            f"{column}: {invalid_count} invalid value(s)"
        )

numerical_df = pd.DataFrame(numerical_results)

print("\n" + numerical_df.to_string(index=False))

numerical_df.to_csv(
    os.path.join(OUTPUT_DIR, "numerical_validity.csv"),
    index=False
)


# ============================================================
# 6. DATE / TIME CONSISTENCY
# ============================================================

print("\n" + "=" * 70)
print("6. DATE / TIME CONSISTENCY")
print("=" * 70)

date_columns = [
    "Weather Observation Time",
    "Rate Date",
    "PM2.5 Measurement Time",
    "PM10 Measurement Time",
    "NO2 Measurement Time",
    "O3 Measurement Time"
]

date_results = []

for column in date_columns:

    values = df[column]

    parsed = pd.to_datetime(
        values,
        errors="coerce",
        utc=True
    )

    invalid_dates = (
        values.notna() &
        parsed.isna()
    ).sum()

    date_results.append({
        "Attribute": column,
        "Non-Missing Values": int(values.notna().sum()),
        "Invalid Dates": int(invalid_dates),
        "Status": (
            "PASS"
            if invalid_dates == 0
            else "CHECK"
        )
    })

# Holiday dates
holiday_values = df["Holiday Dates 2026"]

invalid_holiday_dates = 0
non_2026_holiday_dates = 0

for value in holiday_values.dropna():

    dates = str(value).split("|")

    for date_value in dates:

        date_value = date_value.strip()

        if not date_value:
            continue

        parsed_date = pd.to_datetime(
            date_value,
            errors="coerce"
        )

        if pd.isna(parsed_date):

            invalid_holiday_dates += 1

        elif parsed_date.year != 2026:

            non_2026_holiday_dates += 1


date_results.append({
    "Attribute": "Holiday Dates 2026",
    "Non-Missing Values": int(holiday_values.notna().sum()),
    "Invalid Dates": invalid_holiday_dates,
    "Status": (
        "PASS"
        if invalid_holiday_dates == 0
        else "CHECK"
    )
})

date_df = pd.DataFrame(date_results)

print(date_df.to_string(index=False))

print(
    f"\nHoliday dates outside 2026: "
    f"{non_2026_holiday_dates}"
)

date_df.to_csv(
    os.path.join(OUTPUT_DIR, "date_time_checks.csv"),
    index=False
)


# ============================================================
# 7. IQR OUTLIER DETECTION
# ============================================================

print("\n" + "=" * 70)
print("7. IQR OUTLIER DETECTION")
print("=" * 70)

outlier_columns = [
    "Population",
    "GDP",
    "GDP per capita",
    "Life expectancy",
    "Unemployment",
    "Internet usage",
    "Area (km²)",
    "Temperature (°C)",
    "Relative Humidity (%)",
    "Precipitation (mm)",
    "Wind Speed (km/h)",
    "Exchange Rate",
    "PM2.5",
    "PM10",
    "NO2",
    "O3",
    "Public Holidays 2026"
]

outlier_results = []

for column in outlier_columns:

    values = pd.to_numeric(
        df[column],
        errors="coerce"
    ).dropna()

    if len(values) < 4:
        continue

    q1 = values.quantile(0.25)
    q3 = values.quantile(0.75)

    iqr = q3 - q1

    lower_bound = q1 - 1.5 * iqr
    upper_bound = q3 + 1.5 * iqr

    outlier_mask = (
        (values < lower_bound) |
        (values > upper_bound)
    )

    outlier_count = int(outlier_mask.sum())

    outlier_results.append({
        "Attribute": column,
        "Q1": round(q1, 4),
        "Q3": round(q3, 4),
        "IQR": round(iqr, 4),
        "Lower Bound": round(lower_bound, 4),
        "Upper Bound": round(upper_bound, 4),
        "Outlier Count": outlier_count,
        "Outlier Percentage": round(
            (outlier_count / len(values)) * 100,
            2
        )
    })

    print(
        f"{column}: {outlier_count} outlier(s)"
    )


outlier_df = pd.DataFrame(outlier_results)

print("\n" + outlier_df.to_string(index=False))

outlier_df.to_csv(
    os.path.join(OUTPUT_DIR, "iqr_outliers.csv"),
    index=False
)


# ============================================================
# 8. OUTLIER INTERPRETATION
# ============================================================

print("\n" + "=" * 70)
print("8. OUTLIER INTERPRETATION")
print("=" * 70)

print("""
IQR outliers are treated as statistical observations requiring
investigation, not automatically as data errors.

Large population, GDP, GDP per capita and area values may represent
genuine differences between countries and are therefore retained.

Air-quality observations are checked separately for physically
invalid negative values. Negative pollutant concentrations are
treated as invalid source values and should be handled as missing
during subsequent analysis.

Valid statistical outliers are retained because removing them would
distort genuine country-level variation.
""")


# ============================================================
# 9. FINAL SUMMARY
# ============================================================

print("\n" + "=" * 70)
print("PART D COMPLETED")
print("=" * 70)

print(f"""
Dataset:
    Records              : {df.shape[0]}
    Attributes           : {df.shape[1]}

Structural quality:
    Duplicate rows       : {duplicate_rows}
    Duplicate Country ID : {duplicate_country_codes}
    Missing Country ID   : {missing_country_code}

Maximum missing attribute:
    {max_missing['Attribute']}
    Missing values       : {int(max_missing['Missing Count'])}
    Missing percentage    : {max_missing['Missing Percentage']:.2f}%

Output directory:
    {OUTPUT_DIR}

Generated files:
    1. structural_checks.csv
    2. data_types_unique.csv
    3. missing_values.csv
    4. consistency_checks.csv
    5. numerical_validity.csv
    6. date_time_checks.csv
    7. iqr_outliers.csv
""")

print("=" * 70)
print("All Part D quality reports have been generated.")
print("=" * 70)