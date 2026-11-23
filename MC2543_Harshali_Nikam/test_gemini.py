from gemini_client import generate_city_insight

city_data = {
    "city": "Mumbai",
    "country": "India",
    "population": 14000000,
    "gdp_usd": 400000000000,
    "urban_population_pct": 48.5,
    "currency": "INR",
    "timezone": "Asia/Kolkata"
}

print("\n===================================")
print("       CITYFUSION GEMINI TEST")
print("===================================\n")

result = generate_city_insight(city_data)

print(result)