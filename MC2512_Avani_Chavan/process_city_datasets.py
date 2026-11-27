from pathlib import Path
import pandas as pd


# ============================================================
# PROCESS DOWNLOADED CITY AIR-QUALITY DATASETS
# 12 CITIES
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "live_data"

OUTPUT_DIR.mkdir(exist_ok=True)

OUTPUT_FILE = OUTPUT_DIR / "city_historical_processed.csv"


print("=" * 80)
print("CITY AIR QUALITY DATA PROCESSING")
print("12-CITY CPCB / STATE PCB DATA")
print("=" * 80)


# ============================================================
# CITY FILE MAPPING
# ============================================================

CITY_FILES = {

    "Ahmedabad":
        "raw_data_hourly_chandkheda,_ahmedabad_-_iitm_1H.csv",

    "Bengaluru":
        "raw_data_hourly_bapuji_nagar,_bengaluru_-_kspcb_1H.csv",

    "Chennai":
        "raw_data_hourly_alandur_bus_depot,_chennai_-_cpcb_1H.csv",

    "Delhi":
        "raw_data_hourly_anand_vihar,_delhi_-_dpcc_1H.csv",

    "Hyderabad":
        "raw_data_hourly_bollaram_industrial_area,_hyderabad_-_tspcb_1H.csv",

    "Jaipur":
        "raw_data_hourly_adarsh_nagar,_jaipur_-_rspcb_1H.csv",

    "Kolkata":
        "raw_data_hourly_ballygunge,_kolkata_-_wbpcb_1H.csv",

    "Mumbai":
        "raw_data_hourly_bandra_kurla_complex,_mumbai_-_iitm_1H.csv",

    "Nagpur":
        "raw_data_hourly_ambazari,_nagpur_-_mpcb_1H.csv",

    "Nashik":
        "raw_data_hourly_gangapur_road,_nashik_-_mpcb_1H.csv",

    "Pune":
        "raw_data_hourly_dhankawadi,_pune_-_iitm_1H.csv",

    "Surat":
        "raw_data_hourly_katargam,_surat_-_nexteng_enviro_1H.csv",
}


# ============================================================
# REQUIRED COLUMNS
# ============================================================

REQUIRED_COLUMNS = [
    "Timestamp",
    "PM2.5 (µg/m³)",
    "PM10 (µg/m³)",
    "NO2 (µg/m³)",
    "NH3 (µg/m³)",
    "SO2 (µg/m³)",
    "CO (mg/m³)",
    "Ozone (µg/m³)",
    "AT (°C)",
    "RH (%)",
    "WS (m/s)",
    "WD (deg)",
]


# ============================================================
# PROCESS EACH CITY
# ============================================================

all_city_data = []


for city, filename in CITY_FILES.items():

    input_file = DATA_DIR / filename

    print("\n" + "-" * 80)
    print(f"PROCESSING: {city}")
    print("-" * 80)

    if not input_file.exists():

        print("ERROR: File not found:")
        print(input_file)

        continue

    print("File:", filename)

    try:

        df = pd.read_csv(
            input_file,
            low_memory=False,
            encoding="utf-8"
        )

    except UnicodeDecodeError:

        try:

            df = pd.read_csv(
                input_file,
                low_memory=False,
                encoding="utf-8-sig"
            )

        except Exception as e:

            print("ERROR while reading file:")
            print(e)

            continue

    except Exception as e:

        print("ERROR while reading file:")
        print(e)

        continue


    print("Original rows:", len(df))


    # --------------------------------------------------------
    # CLEAN COLUMN NAMES
    # --------------------------------------------------------

    df.columns = [
        str(c).strip()
        for c in df.columns
    ]


    # --------------------------------------------------------
    # CHECK REQUIRED COLUMNS
    # --------------------------------------------------------

    missing = [
        col
        for col in REQUIRED_COLUMNS
        if col not in df.columns
    ]

    if missing:

        print("Missing columns:")

        for col in missing:
            print("-", col)

        print("\nAvailable columns:")

        for col in df.columns:
            print("-", col)

        continue


    # --------------------------------------------------------
    # KEEP REQUIRED DATA
    # --------------------------------------------------------

    df = df[REQUIRED_COLUMNS].copy()


    # --------------------------------------------------------
    # ADD CITY
    # --------------------------------------------------------

    df.insert(
        0,
        "City",
        city
    )


    # --------------------------------------------------------
    # CONVERT TIMESTAMP
    # --------------------------------------------------------

    df["Timestamp"] = pd.to_datetime(
        df["Timestamp"],
        errors="coerce"
    )


    # --------------------------------------------------------
    # CONVERT NUMERIC COLUMNS
    # --------------------------------------------------------

    numeric_columns = [
        "PM2.5 (µg/m³)",
        "PM10 (µg/m³)",
        "NO2 (µg/m³)",
        "NH3 (µg/m³)",
        "SO2 (µg/m³)",
        "CO (mg/m³)",
        "Ozone (µg/m³)",
        "AT (°C)",
        "RH (%)",
        "WS (m/s)",
        "WD (deg)",
    ]


    for col in numeric_columns:

        df[col] = pd.to_numeric(
            df[col],
            errors="coerce"
        )


    # --------------------------------------------------------
    # REMOVE INVALID TIMESTAMP
    # --------------------------------------------------------

    before = len(df)

    df = df.dropna(
        subset=["Timestamp"]
    )

    removed = before - len(df)

    print(
        "Invalid timestamp rows removed:",
        removed
    )


    # --------------------------------------------------------
    # SORT
    # --------------------------------------------------------

    df = df.sort_values(
        "Timestamp"
    ).reset_index(drop=True)


    # --------------------------------------------------------
    # DISPLAY SUMMARY
    # --------------------------------------------------------

    print(
        "Processed rows:",
        len(df)
    )

    print(
        "Date range:",
        df["Timestamp"].min(),
        "to",
        df["Timestamp"].max()
    )

    print(
        "PM2.5 available:",
        df["PM2.5 (µg/m³)"].notna().sum()
    )

    all_city_data.append(df)


# ============================================================
# COMBINE ALL CITIES
# ============================================================

print("\n" + "=" * 80)
print("COMBINING CITY DATA")
print("=" * 80)


if not all_city_data:

    print("\nERROR: No city datasets were processed.")

    raise SystemExit(1)


combined_df = pd.concat(
    all_city_data,
    ignore_index=True
)


# ============================================================
# SORT COMBINED DATA
# ============================================================

combined_df = combined_df.sort_values(
    ["City", "Timestamp"]
).reset_index(drop=True)


# ============================================================
# SAVE
# ============================================================

combined_df.to_csv(
    OUTPUT_FILE,
    index=False,
    encoding="utf-8"
)


# ============================================================
# FINAL SUMMARY
# ============================================================

print("\n" + "=" * 80)
print("CITY DATA PROCESSING COMPLETE")
print("=" * 80)


print(
    "\nTotal rows:",
    len(combined_df)
)


print(
    "\nCities processed:",
    combined_df["City"].nunique()
)


print("\nCities:")

for city in sorted(combined_df["City"].unique()):

    print(
        "-",
        city
    )


print("\nRows by city:")

print(
    combined_df["City"]
    .value_counts()
    .sort_index()
    .to_string()
)


print("\nPM2.5 available by city:")

pm25_summary = (
    combined_df
    .groupby("City")["PM2.5 (µg/m³)"]
    .apply(lambda x: x.notna().sum())
    .sort_index()
)

print(
    pm25_summary.to_string()
)


print("\nColumns:")

for col in combined_df.columns:

    print(
        "-",
        col
    )


print("\nDate range:")

print(
    combined_df["Timestamp"].min(),
    "to",
    combined_df["Timestamp"].max()
)


print("\nSaved to:")

print(OUTPUT_FILE)


print("\n" + "=" * 80)
print("PROCESSING COMPLETE")
print("=" * 80)