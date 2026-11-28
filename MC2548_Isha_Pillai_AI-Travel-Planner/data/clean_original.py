import pandas as pd


# -----------------------------------------
# 1. Read original dataset
# -----------------------------------------

input_file = "data/Travel details dataset.csv"

df = pd.read_csv(
    input_file,
    sep="\t"
)

print("Original records:", len(df))


# -----------------------------------------
# 2. Remove completely empty travel rows
# -----------------------------------------

data_columns = [
    "Destination",
    "Start date",
    "End date",
    "Duration (days)",
    "Traveler name",
    "Traveler age",
    "Traveler gender",
    "Traveler nationality",
    "Accommodation type",
    "Accommodation cost",
    "Transportation type",
    "Transportation cost"
]

df_clean = df.dropna(
    subset=data_columns,
    how="all"
).copy()


# -----------------------------------------
# 3. Remove rows without Trip ID
# -----------------------------------------

df_clean = df_clean[
    df_clean["Trip ID"].notna()
].copy()


# -----------------------------------------
# 4. Remove duplicate Trip IDs
# -----------------------------------------

df_clean = df_clean.drop_duplicates(
    subset=["Trip ID"],
    keep="first"
)


# -----------------------------------------
# 5. Handle missing transportation data
# -----------------------------------------
# Trip 83 has valid travel information,
# but transportation information is missing.
# We keep the trip and explicitly mark the
# unavailable information as "Unknown".

df_clean["Transportation type"] = (
    df_clean["Transportation type"]
    .fillna("Unknown")
)

df_clean["Transportation cost"] = (
    df_clean["Transportation cost"]
    .fillna("Unknown")
)


# -----------------------------------------
# 6. Save clean dataset
# -----------------------------------------

output_file = "data/clean_travel_data.csv"

df_clean.to_csv(
    output_file,
    index=False
)


# -----------------------------------------
# 7. Display results
# -----------------------------------------

print("\n----------------------------------")
print("Clean original dataset created!")
print("----------------------------------")

print(
    "Original records:",
    len(df)
)

print(
    "Clean records:",
    len(df_clean)
)

print(
    "Removed records:",
    len(df) - len(df_clean)
)

print("\nMissing values in clean dataset:")

print(
    df_clean.isnull().sum()
)

print("\nTrip 83 after cleaning:")

print(
    df_clean[
        df_clean["Trip ID"] == 83
    ].to_string(index=False)
)

print("\nFirst 5 records:")

print(
    df_clean.head().to_string(
        index=False
    )
)