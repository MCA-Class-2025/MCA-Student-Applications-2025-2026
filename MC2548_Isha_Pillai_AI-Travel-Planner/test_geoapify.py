from services.geoapify_service import get_places


# Dubai coordinates
latitude = 25.1972
longitude = 55.2744

result = get_places(latitude, longitude)

if result:

    print("\nDubai Attractions")
    print("-----------------")

    for place in result.get("features", []):

        properties = place.get("properties", {})

        name = properties.get("name")

        if name:
            print(
                "Place:",
                name,
                "| Address:",
                properties.get("formatted", "N/A")
            )

else:
    print("No places data received.")