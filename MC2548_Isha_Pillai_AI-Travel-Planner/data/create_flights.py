import pandas as pd

# Read raw Aviationstack data
input_file = "data/aviationstack_flights.csv"

df = pd.read_csv(input_file)

# Keep only the useful fields
clean_df = df[
    [
        "Flight Date",
        "Flight Status",
        "Departure IATA",
        "Arrival IATA",
        "Departure Time",
        "Arrival Time",
        "Airline",
        "Airline IATA",
        "Flight Number",
        "Flight IATA"
    ]
].copy()

# Remove rows where important flight information is missing
required_columns = [
    "Flight Date",
    "Flight Status",
    "Departure IATA",
    "Arrival IATA",
    "Airline",
    "Flight Number",
    "Flight IATA"
]

clean_df = clean_df.dropna(subset=required_columns)

# Remove empty strings too
clean_df = clean_df[
    clean_df[required_columns]
    .astype(str)
    .apply(lambda x: x.str.strip().ne("").all(), axis=1)
]

# Create Primary Key
clean_df.insert(
    0,
    "Flight_ID",
    [f"F{i:03d}" for i in range(1, len(clean_df) + 1)]
)

# Trip ID 10 = United Arab Emirates / Dubai
# This is the Foreign Key connecting the API data to the original dataset.
clean_df.insert(1, "Trip_ID", 10)

# Rename columns
clean_df = clean_df.rename(columns={
    "Flight Date": "Flight_Date",
    "Flight Status": "Flight_Status",
    "Departure IATA": "Departure_IATA",
    "Arrival IATA": "Arrival_IATA",
    "Departure Time": "Departure_Time",
    "Arrival Time": "Arrival_Time",
    "Airline IATA": "Airline_IATA",
    "Flight Number": "Flight_Number",
    "Flight IATA": "Flight_IATA"
})

# Save clean file
output_file = "data/flights.csv"
clean_df.to_csv(output_file, index=False)

print("Clean flights.csv created successfully!")
print("Number of records:", len(clean_df))
print("\nColumns:")
print(list(clean_df.columns))
print("\nFirst 5 records:")
print(clean_df.head())