import requests


API_URL = "http://127.0.0.1:8000"


def find_services(
    service_type=None,
    city=None,
    latitude=None,
    longitude=None
):

    # Use nearby search when coordinates are available
    if latitude is not None and longitude is not None:

        params = {
            "latitude": latitude,
            "longitude": longitude,
            "radius_km": 25,
            "limit": 10
        }

        if service_type:
            params["service_type"] = service_type

        response = requests.get(
            f"{API_URL}/professionals/nearby",
            params=params,
            timeout=10
        )

    else:

        params = {}

        if service_type:
            params["service_type"] = service_type

        if city:
            params["city"] = city

        response = requests.get(
            f"{API_URL}/professionals",
            params=params,
            timeout=10
        )

    response.raise_for_status()

    result = response.json()

    return result.get(
        "professionals",
        []
    )