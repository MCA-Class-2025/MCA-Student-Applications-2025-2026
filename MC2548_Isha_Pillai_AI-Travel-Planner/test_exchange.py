from services.exchange_service import convert_currency


result = convert_currency(
    "INR",
    "AED",
    80000
)

if result:

    print("\nCurrency Conversion")
    print("-------------------")

    print("From: INR")
    print("To: AED")
    print("Amount: ₹80,000")
    print("Exchange Rate:", result["conversion_rate"])
    print("Converted Amount:", result["conversion_result"], "AED")

else:
    print("No currency data received.")