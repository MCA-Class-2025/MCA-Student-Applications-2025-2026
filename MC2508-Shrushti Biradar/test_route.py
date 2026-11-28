from api.googleroute_api import get_route


print("=" * 50)
print("GOOGLE ROUTES API TEST")
print("=" * 50)


try:

    route = get_route(
        "Mumbai",
        "Juhu Beach, Mumbai"
    )


    print("\n✅ Route found!")

    print(
        "\nOrigin:",
        route["origin"]
    )

    print(
        "Destination:",
        route["destination"]
    )

    print(
        "Distance:",
        route["distance_km"],
        "km"
    )

    print(
        "Travel Time:",
        route["duration_text"]
    )


except Exception as e:

    print("\n❌ ERROR")

    print(e)