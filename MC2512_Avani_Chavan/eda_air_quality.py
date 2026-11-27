from pathlib import Path
import pandas as pd


# ---------------------------------------------------------
# CLEANED DATA FOLDER
# ---------------------------------------------------------

CLEANED_DIR = Path("cleaned_data")


# ---------------------------------------------------------
# FILES
# ---------------------------------------------------------

files = [
    CLEANED_DIR / "mumbai_cleaned.csv",
    CLEANED_DIR / "pune_cleaned.csv"
]


# ---------------------------------------------------------
# TARGET
# ---------------------------------------------------------

TARGET = "PM2.5 (µg/m³)"


# ---------------------------------------------------------
# PROCESS EACH DATASET
# ---------------------------------------------------------

for file in files:

    print("\n" + "=" * 90)
    print("EDA:", file.name)
    print("=" * 90)

    if not file.exists():

        print(
            "File not found:",
            file
        )

        print(
            "Run clean_air_quality_data.py first."
        )

        continue


    # -----------------------------------------------------
    # READ DATA
    # -----------------------------------------------------

    df = pd.read_csv(
        file,
        low_memory=False
    )


    # -----------------------------------------------------
    # DATASET SIZE
    # -----------------------------------------------------

    print("\n1. DATASET SIZE")

    print(
        "Rows:",
        len(df)
    )

    print(
        "Columns:",
        len(df.columns)
    )


    # -----------------------------------------------------
    # DATE RANGE
    # -----------------------------------------------------

    print("\n2. DATE RANGE")

    df["Timestamp"] = pd.to_datetime(
        df["Timestamp"],
        errors="coerce",
        utc=True
    )

    print(
        "Start:",
        df["Timestamp"].min()
    )

    print(
        "End:",
        df["Timestamp"].max()
    )


    # -----------------------------------------------------
    # MISSING VALUES
    # -----------------------------------------------------

    print("\n3. MISSING VALUES")

    missing = df.isnull().sum()

    missing_percentage = (
        missing / len(df) * 100
    ).round(2)

    missing_table = pd.DataFrame({

        "Missing": missing,

        "Percentage": missing_percentage

    })

    print(
        missing_table.to_string()
    )


    # -----------------------------------------------------
    # PM2.5 STATISTICS
    # -----------------------------------------------------

    print("\n4. PM2.5 STATISTICS")

    if TARGET in df.columns:

        print(
            df[TARGET]
            .describe()
            .round(2)
            .to_string()
        )

    else:

        print(
            "PM2.5 column not found."
        )


    # -----------------------------------------------------
    # POLLUTANT STATISTICS
    # -----------------------------------------------------

    print("\n5. POLLUTANT STATISTICS")

    pollutant_columns = [

        "PM2.5 (µg/m³)",

        "PM10 (µg/m³)",

        "NO2 (µg/m³)",

        "NH3 (µg/m³)",

        "SO2 (µg/m³)",

        "CO (mg/m³)",

        "Ozone (µg/m³)"

    ]


    available_pollutants = [

        column

        for column in pollutant_columns

        if column in df.columns

    ]


    if available_pollutants:

        print(

            df[available_pollutants]

            .describe()

            .round(2)

            .to_string()

        )


    # -----------------------------------------------------
    # WEATHER STATISTICS
    # -----------------------------------------------------

    print("\n6. WEATHER STATISTICS")

    weather_columns = [

        "AT (°C)",

        "RH (%)",

        "WS (m/s)",

        "WD (deg)",

        "RF (mm)",

        "SR (W/mt2)"

    ]


    available_weather = [

        column

        for column in weather_columns

        if column in df.columns

    ]


    if available_weather:

        print(

            df[available_weather]

            .describe()

            .round(2)

            .to_string()

        )


    # -----------------------------------------------------
    # DUPLICATE TIMESTAMPS
    # -----------------------------------------------------

    print("\n7. DUPLICATE TIMESTAMPS")

    duplicate_count = df[
        "Timestamp"
    ].duplicated().sum()

    print(
        "Duplicate timestamps:",
        duplicate_count
    )


    # -----------------------------------------------------
    # PM2.5 AVAILABLE RECORDS
    # -----------------------------------------------------

    print("\n8. PM2.5 AVAILABLE RECORDS")

    if TARGET in df.columns:

        available_pm25 = (
            df[TARGET]
            .notna()
            .sum()
        )

        missing_pm25 = (
            df[TARGET]
            .isna()
            .sum()
        )

        print(
            "Available:",
            available_pm25
        )

        print(
            "Missing:",
            missing_pm25
        )


        # -------------------------------------------------
        # PM2.5 PERCENTILES
        # -------------------------------------------------

        print(
            "\nPM2.5 percentiles:"
        )

        percentiles = (

            df[TARGET]

            .quantile([

                0.01,

                0.05,

                0.25,

                0.50,

                0.75,

                0.95,

                0.99

            ])

            .round(2)

        )

        print(
            percentiles.to_string()
        )


    # -----------------------------------------------------
    # REQUIRED FEATURES CHECK
    # -----------------------------------------------------

    print(
        "\n9. DATASET READY CHECK"
    )


    required_columns = [

        "Timestamp",

        "PM2.5 (µg/m³)",

        "PM10 (µg/m³)",

        "NO2 (µg/m³)",

        "SO2 (µg/m³)",

        "CO (mg/m³)",

        "Ozone (µg/m³)",

        "AT (°C)",

        "RH (%)",

        "WS (m/s)"

    ]


    for column in required_columns:

        if column in df.columns:

            print(
                "YES -",
                column
            )

        else:

            print(
                "NO  -",
                column
            )


# ---------------------------------------------------------
# COMPLETE
# ---------------------------------------------------------

print("\n" + "=" * 90)

print(
    "EDA COMPLETE"
)

print(
    "=" * 90
)