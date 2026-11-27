from pathlib import Path
import pandas as pd

DATA_DIR = Path("data")
csv_files = list(DATA_DIR.glob("*.csv"))

if not csv_files:
    print("No CSV files found inside the data folder.")
    raise SystemExit


# Keywords for identifying columns
AIR_KEYWORDS = [
    "pm2.5",
    "pm25",
    "pm10",
    "aqi",
    "no2",
    "so2",
    "nh3",
    "ozone",
    "o3",
    "co"
]

TIME_KEYWORDS = [
    "date",
    "time",
    "timestamp",
    "last_update"
]

LOCATION_KEYWORDS = [
    "city",
    "station",
    "location",
    "state",
    "district"
]


for file in csv_files:

    print("\n" + "=" * 90)
    print("FILE:", file.name)
    print("=" * 90)

    try:
        df = pd.read_csv(file, low_memory=False)

    except Exception as e:
        print("ERROR READING FILE:", e)
        continue


    # ---------------------------------------------------------
    # BASIC INFORMATION
    # ---------------------------------------------------------

    print("\n1. DATASET SIZE")

    print("Rows:", len(df))
    print("Columns:", len(df.columns))


    # ---------------------------------------------------------
    # COLUMNS
    # ---------------------------------------------------------

    print("\n2. COLUMN NAMES")

    for col in df.columns:
        print("-", col)


    # ---------------------------------------------------------
    # FIRST 5 ROWS
    # ---------------------------------------------------------

    print("\n3. FIRST 5 ROWS")

    print(df.head().to_string(index=False))


    # ---------------------------------------------------------
    # MISSING VALUES
    # ---------------------------------------------------------

    print("\n4. MISSING VALUES")

    print(df.isnull().sum().to_string())


    # ---------------------------------------------------------
    # DATA TYPES
    # ---------------------------------------------------------

    print("\n5. DATA TYPES")

    print(df.dtypes.to_string())


    # ---------------------------------------------------------
    # LOCATION COLUMNS
    # ---------------------------------------------------------

    location_cols = []

    for col in df.columns:

        col_lower = col.lower().strip()

        if any(
            keyword in col_lower
            for keyword in LOCATION_KEYWORDS
        ):
            location_cols.append(col)


    print("\n6. LOCATION COLUMNS")

    if location_cols:

        print(location_cols)

        for col in location_cols:

            print(f"\nSample values from {col}:")

            values = (
                df[col]
                .dropna()
                .astype(str)
                .unique()
            )

            print(values[:20])

    else:

        print("No location columns found.")


    # ---------------------------------------------------------
    # AIR QUALITY COLUMNS
    # ---------------------------------------------------------

    air_cols = []

    for col in df.columns:

        col_lower = col.lower().strip()

        # Exact/clean matching instead of substring matching
        if (
            col_lower in AIR_KEYWORDS
            or any(
                col_lower.startswith(keyword)
                for keyword in AIR_KEYWORDS
            )
        ):
            air_cols.append(col)


    print("\n7. AIR QUALITY COLUMNS")

    if air_cols:
        print(air_cols)
    else:
        print("No air-quality columns detected.")


    # ---------------------------------------------------------
    # TIME COLUMNS
    # ---------------------------------------------------------

    time_cols = []

    for col in df.columns:

        col_lower = col.lower().strip()

        if any(
            keyword in col_lower
            for keyword in TIME_KEYWORDS
        ):
            time_cols.append(col)


    print("\n8. POSSIBLE TIME COLUMNS")

    if time_cols:

        print(time_cols)

        for col in time_cols:

            print(f"\nChecking time column: {col}")

            temp = pd.to_datetime(
                df[col],
                errors="coerce"
            )

            valid = temp.dropna()

            if len(valid) > 0:

                print("Minimum:", valid.min())
                print("Maximum:", valid.max())
                print("Valid timestamps:", len(valid))

                if len(valid) > 1:

                    differences = (
                        valid.sort_values()
                        .diff()
                        .dropna()
                    )

                    print(
                        "Most common time interval:"
                    )

                    print(
                        differences
                        .value_counts()
                        .head(5)
                    )

            else:

                print("Could not interpret as datetime.")


    # ---------------------------------------------------------
    # NUMERIC COLUMNS
    # ---------------------------------------------------------

    print("\n9. NUMERIC COLUMNS")

    numeric_cols = df.select_dtypes(
        include="number"
    ).columns.tolist()

    print(numeric_cols)


    # ---------------------------------------------------------
    # SUMMARY
    # ---------------------------------------------------------

    print("\n10. DATASET SUMMARY")

    print("File:", file.name)
    print("Rows:", len(df))
    print("Columns:", len(df.columns))
    print("Air-quality columns:", air_cols)
    print("Time columns:", time_cols)
    print("Location columns:", location_cols)


print("\n" + "=" * 90)
print("ALL DATASETS INSPECTED")
print("=" * 90)