from services.aviationstack_service import get_flights
import pandas as pd


result = get_flights(
    dep_iata="BOM",
    arr_iata="DXB"
)

if result and "data" in result:

    flights = []

    for flight in result["data"]:

        flights.append({
            "Flight Date": flight.get("flight_date"),
            "Flight Status": flight.get("flight_status"),

            "Departure Airport": flight.get("departure", {}).get("airport"),
            "Departure IATA": flight.get("departure", {}).get("iata"),
            "Departure Terminal": flight.get("departure", {}).get("terminal"),
            "Departure Time": flight.get("departure", {}).get("scheduled"),

            "Arrival Airport": flight.get("arrival", {}).get("airport"),
            "Arrival IATA": flight.get("arrival", {}).get("iata"),
            "Arrival Terminal": flight.get("arrival", {}).get("terminal"),
            "Arrival Time": flight.get("arrival", {}).get("scheduled"),

            "Airline": flight.get("airline", {}).get("name"),
            "Airline IATA": flight.get("airline", {}).get("iata"),

            "Flight Number": flight.get("flight", {}).get("number"),
            "Flight IATA": flight.get("flight", {}).get("iata")
        })

    df = pd.DataFrame(flights)

    print("\nAviationstack Flight Data:\n")
    print(df.to_string(index=False))

    df.to_csv(
        "data/aviationstack_flights.csv",
        index=False
    )

    print("\n✅ Saved to data/aviationstack_flights.csv")

else:
    print("❌ No flight data received.")