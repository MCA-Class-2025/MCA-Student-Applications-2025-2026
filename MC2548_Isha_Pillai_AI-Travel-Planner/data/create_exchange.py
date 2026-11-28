import sys
import os

sys.path.append(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)

import pandas as pd
from services.exchange_service import convert_currency


# --------------------------------------------------
# 1. Read original travel dataset
# --------------------------------------------------

input_file = "data/Travel details dataset.csv"

df = pd.read_csv(
    input_file,
    sep="\t"
)


# --------------------------------------------------
# 2. Store exchange-rate records
# --------------------------------------------------

exchange_records = []


# --------------------------------------------------
# 3. Currency mapping
# --------------------------------------------------

currency_map = {

    # Countries
    "United Arab Emirates": "AED",
    "Thailand": "THB",
    "Indonesia": "IDR",
    "USA": "USD",
    "Japan": "JPY",
    "France": "EUR",
    "Australia": "AUD",
    "Brazil": "BRL",
    "Netherlands": "EUR",
    "Mexico": "MXN",
    "Spain": "EUR",
    "Hawaii": "USD",
    "Germany": "EUR",
    "Canada": "CAD",
    "United Kingdom": "GBP",
    "UK": "GBP",
    "Italy": "EUR",
    "Singapore": "SGD",
    "South Korea": "KRW",
    "China": "CNY",
    "India": "INR",
    "Morocco": "MAD",
    "Scotland": "GBP",
    "Greece": "EUR",
    "Egypt": "EGP",
    "South Africa": "ZAR",
    "SA": "ZAR",
    "New Zealand": "NZD",

    # Cities
    "Paris": "EUR",
    "Bali": "IDR",
    "London": "GBP",
    "Tokyo": "JPY",
    "New York": "USD",
    "Sydney": "AUD",
    "Rome": "EUR",
    "Bangkok": "THB",
    "Barcelona": "EUR",
    "Marrakech": "MAD",
    "Edinburgh": "GBP",
    "Cape Town": "ZAR",
    "Rio de Janeiro": "BRL",
    "Amsterdam": "EUR",
    "Phuket": "THB",
    "Dubai": "AED",
    "Seoul": "KRW",
    "Phnom Penh": "KHR",
    "Santorini": "EUR",
    "Athens": "EUR",
    "Auckland": "NZD",

    # Exact destination variants in the dataset
    "Sydney, AUS": "AUD",
    "Sydney, Aus": "AUD",
    "Bangkok, Thai": "THB",
    "Phuket, Thai": "THB"
}


# --------------------------------------------------
# 4. Process every trip
# --------------------------------------------------

for _, row in df.iterrows():

    trip_id = int(row["Trip ID"])

    destination = str(
        row["Destination"]
    ).strip()


    # --------------------------------------------------
    # 5. First check the complete destination
    # --------------------------------------------------

    target_currency = currency_map.get(
        destination
    )


    # --------------------------------------------------
    # 6. If not found, check country/region
    # --------------------------------------------------

    if target_currency is None:

        parts = destination.split(",")

        if len(parts) > 1:

            country = parts[-1].strip()

        else:

            country = destination

        target_currency = currency_map.get(
            country
        )


    # --------------------------------------------------
    # 7. Skip if currency cannot be identified
    # --------------------------------------------------

    if target_currency is None:

        print(
            f"Skipping Trip {trip_id} - "
            f"currency not mapped for {destination}"
        )

        continue


    # --------------------------------------------------
    # 8. Call Exchange Rate API
    # --------------------------------------------------

    print(
        f"Getting exchange rate for Trip {trip_id}: "
        f"INR -> {target_currency}"
    )


    result = convert_currency(
        "INR",
        target_currency,
        80000
    )


    # --------------------------------------------------
    # 9. Check API response
    # --------------------------------------------------

    if result is None:

        print(
            f"Skipping Trip {trip_id} - API failed"
        )

        continue


    if (
        "conversion_rate" not in result
        or "conversion_result" not in result
    ):

        print(
            f"Skipping Trip {trip_id} - "
            f"incomplete API data"
        )

        continue


    # --------------------------------------------------
    # 10. Add clean record
    # --------------------------------------------------

    exchange_records.append({

        # Primary Key
        "Exchange_ID": f"E{trip_id:03d}",

        # Foreign Key
        "Trip_ID": trip_id,

        "Destination": destination,

        "From_Currency": "INR",

        "To_Currency": target_currency,

        "Amount_INR": 80000,

        "Exchange_Rate": result[
            "conversion_rate"
        ],

        "Converted_Amount": result[
            "conversion_result"
        ]
    })


# --------------------------------------------------
# 11. Create DataFrame
# --------------------------------------------------

exchange_df = pd.DataFrame(
    exchange_records
)


# --------------------------------------------------
# 12. Remove duplicate Trip IDs
# --------------------------------------------------

exchange_df = exchange_df.drop_duplicates(
    subset=["Trip_ID"],
    keep="first"
)


# --------------------------------------------------
# 13. Remove NULL values
# --------------------------------------------------

exchange_df = exchange_df.dropna()


# --------------------------------------------------
# 14. Remove empty string values
# --------------------------------------------------

for column in exchange_df.columns:

    exchange_df = exchange_df[
        exchange_df[column]
        .astype(str)
        .str.strip()
        .ne("")
    ]


# --------------------------------------------------
# 15. Save clean Exchange Rate dataset
# --------------------------------------------------

output_file = "data/exchange_rates.csv"

exchange_df.to_csv(
    output_file,
    index=False
)


# --------------------------------------------------
# 16. Display results
# --------------------------------------------------

print("\n--------------------------------")
print("Clean exchange_rates.csv created!")
print("--------------------------------")

print(
    "Number of records:",
    len(exchange_df)
)

print("\nColumns:")

print(
    list(exchange_df.columns)
)

print("\nExchange Rate Data:")

print(
    exchange_df.to_string(
        index=False
    )
)