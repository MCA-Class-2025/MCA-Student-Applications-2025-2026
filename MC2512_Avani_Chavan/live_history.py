from pathlib import Path
import pandas as pd


# ============================================================
# CONFIGURATION
# ============================================================

LIVE_FILE = Path(
    "live_data/live_air_quality_processed.csv"
)

HISTORY_FILE = Path(
    "live_data/pm25_history.csv"
)


# ============================================================
# HEADER
# ============================================================

print("=" * 80)
print("AIR QUALITY - LIVE PM2.5 HISTORY")
print("=" * 80)


# ============================================================
# CHECK LIVE FILE
# ============================================================

if not LIVE_FILE.exists():
    raise FileNotFoundError(
        f"Live air quality file not found:\n{LIVE_FILE}"
    )


# ============================================================
# LOAD LIVE DATA
# ============================================================

print()
print("Loading latest CPCB live data...")

live_df = pd.read_csv(LIVE_FILE)

print(
    f"Live records found: {len(live_df)}"
)


if live_df.empty:
    raise ValueError(
        "Live air quality file contains no records."
    )


print()
print("Live columns:")

for column in live_df.columns:
    print(f"- {column}")


# ============================================================
# REQUIRED COLUMNS
# ============================================================

required_columns = [
    "city",
    "last_update",
    "PM2.5 (µg/m³)"
]


missing_columns = [
    column
    for column in required_columns
    if column not in live_df.columns
]


if missing_columns:

    raise ValueError(
        "Required columns missing from live data:\n"
        + "\n".join(
            f"- {column}"
            for column in missing_columns
        )
    )


# ============================================================
# CREATE HISTORY DATA
# ============================================================

history_new = live_df[
    [
        "city",
        "last_update",
        "PM2.5 (µg/m³)"
    ]
].copy()


# ============================================================
# STANDARDIZE COLUMN NAMES
# ============================================================

history_new = history_new.rename(
    columns={
        "city": "City",
        "last_update": "Timestamp"
    }
)


# ============================================================
# CLEAN CITY
# ============================================================

history_new["City"] = (
    history_new["City"]
    .astype(str)
    .str.strip()
)


# ============================================================
# PARSE TIMESTAMP
# ============================================================

history_new["Timestamp"] = pd.to_datetime(
    history_new["Timestamp"],
    errors="coerce",
    utc=True
)


# ============================================================
# PM2.5 NUMERIC
# ============================================================

history_new["PM2.5 (µg/m³)"] = pd.to_numeric(
    history_new["PM2.5 (µg/m³)"],
    errors="coerce"
)


# ============================================================
# REMOVE INVALID DATA
# ============================================================

before = len(history_new)

history_new = history_new.dropna(
    subset=[
        "City",
        "Timestamp",
        "PM2.5 (µg/m³)"
    ]
)

removed = before - len(history_new)

print()
print(
    f"Invalid records removed: {removed}"
)


# ============================================================
# KEEP ONLY MUMBAI AND PUNE
# ============================================================

history_new = history_new[
    history_new["City"]
    .str.lower()
    .isin(
        [
            "mumbai",
            "pune"
        ]
    )
].copy()


if history_new.empty:

    raise ValueError(
        "No valid Mumbai or Pune PM2.5 records found."
    )


# ============================================================
# CITY-LEVEL AGGREGATION
# ============================================================
#
# Multiple stations may report PM2.5 for the same city
# and timestamp.
#
# Median is used instead of zero-filling missing values.
# ============================================================

history_new = (
    history_new
    .groupby(
        [
            "City",
            "Timestamp"
        ],
        as_index=False
    )[
        "PM2.5 (µg/m³)"
    ]
    .median()
)


# ============================================================
# LOAD EXISTING HISTORY
# ============================================================

if HISTORY_FILE.exists():

    print()
    print("Existing PM2.5 history found.")

    history_old = pd.read_csv(
        HISTORY_FILE
    )

    if not history_old.empty:

        # Handle old column naming if necessary
        if "city" in history_old.columns:
            history_old = history_old.rename(
                columns={
                    "city": "City"
                }
            )

        if "last_update" in history_old.columns:
            history_old = history_old.rename(
                columns={
                    "last_update": "Timestamp"
                }
            )

        history_old["City"] = (
            history_old["City"]
            .astype(str)
            .str.strip()
        )

        history_old["Timestamp"] = pd.to_datetime(
            history_old["Timestamp"],
            errors="coerce",
            utc=True
        )

        history_old["PM2.5 (µg/m³)"] = pd.to_numeric(
            history_old["PM2.5 (µg/m³)"],
            errors="coerce"
        )

        history_old = history_old.dropna(
            subset=[
                "City",
                "Timestamp",
                "PM2.5 (µg/m³)"
            ]
        )

    else:

        history_old = pd.DataFrame(
            columns=[
                "City",
                "Timestamp",
                "PM2.5 (µg/m³)"
            ]
        )

else:

    print()
    print(
        "No existing PM2.5 history found."
    )

    print(
        "Creating new history file..."
    )

    history_old = pd.DataFrame(
        columns=[
            "City",
            "Timestamp",
            "PM2.5 (µg/m³)"
        ]
    )


# ============================================================
# COMBINE OLD + NEW
# ============================================================

history = pd.concat(
    [
        history_old,
        history_new
    ],
    ignore_index=True
)


# ============================================================
# KEEP ONLY MUMBAI AND PUNE
# ============================================================

history = history[
    history["City"]
    .astype(str)
    .str.lower()
    .isin(
        [
            "mumbai",
            "pune"
        ]
    )
].copy()


# ============================================================
# SORT
# ============================================================

history = history.sort_values(
    [
        "City",
        "Timestamp"
    ]
).reset_index(
    drop=True
)


# ============================================================
# REMOVE DUPLICATES
# ============================================================

history = (
    history
    .drop_duplicates(
        subset=[
            "City",
            "Timestamp"
        ],
        keep="last"
    )
    .reset_index(drop=True)
)


# ============================================================
# SAVE
# ============================================================

HISTORY_FILE.parent.mkdir(
    parents=True,
    exist_ok=True
)

history.to_csv(
    HISTORY_FILE,
    index=False
)


# ============================================================
# DISPLAY SUMMARY
# ============================================================

print()
print("=" * 80)
print("LIVE PM2.5 HISTORY UPDATED")
print("=" * 80)

print()
print(
    f"Total history records: {len(history)}"
)


print()
print("Records by city:")

print(
    history["City"]
    .value_counts()
    .to_string()
)


# ============================================================
# LATEST OBSERVATION
# ============================================================

print()
print("Latest observation for each city:")

for city in ["Mumbai", "Pune"]:

    city_df = history[
        history["City"]
        .str.lower()
        == city.lower()
    ].sort_values(
        "Timestamp"
    )

    if city_df.empty:
        print()
        print(
            f"{city}: No data"
        )
        continue

    latest = city_df.iloc[-1]

    print()
    print("-" * 80)

    print(
        f"City: {city}"
    )

    print(
        f"Timestamp: {latest['Timestamp']}"
    )

    print(
        f"PM2.5: "
        f"{latest['PM2.5 (µg/m³)']:.2f} µg/m³"
    )


# ============================================================
# LAG AVAILABILITY
# ============================================================

print()
print("=" * 80)
print("LAG DATA AVAILABILITY")
print("=" * 80)


for city in ["Mumbai", "Pune"]:

    city_df = history[
        history["City"]
        .str.lower()
        == city.lower()
    ].sort_values(
        "Timestamp"
    )

    count = len(city_df)

    print()
    print(
        f"{city}: {count} observations"
    )

    print(
        f"  Lag 1   : "
        f"{'YES' if count >= 1 else 'NO'}"
    )

    print(
        f"  Lag 4   : "
        f"{'YES' if count >= 4 else 'NO'}"
    )

    print(
        f"  Lag 8   : "
        f"{'YES' if count >= 8 else 'NO'}"
    )

    print(
        f"  Lag 96  : "
        f"{'YES' if count >= 96 else 'NO'}"
    )

    print(
        f"  Lag 672 : "
        f"{'YES' if count >= 672 else 'NO'}"
    )


# ============================================================
# FINAL
# ============================================================

print()
print("=" * 80)
print("HISTORY PROCESSING COMPLETE")
print("=" * 80)

print()
print("Saved:")
print(HISTORY_FILE)

print("=" * 80)