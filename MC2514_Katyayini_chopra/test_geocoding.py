from services.geocoding_service import geocode_location


location = geocode_location(
    "Andheri West, Mumbai, Maharashtra, India"
)


print("\n===== GEOCODING RESULT =====")

print(
    "Location:",
    location["display_name"]
)

print(
    "Latitude:",
    location["latitude"]
)

print(
    "Longitude:",
    location["longitude"]
)