"""
Nominatim / OpenStreetMap API Demo
DanceCompass AI

Purpose:
Convert a dance origin or region into geographical information.
"""

import re
import requests


NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"


def extract_geographic_query(location: str) -> str:
    """
    Extract the most useful geographic name from a dance origin string.

    Indian locations are made more specific by adding India.
    International locations are kept unchanged.
    """

    location = location.strip()

    # ---------------------------------------------------------
    # Known international geographic references
    # ---------------------------------------------------------
    international_keywords = [
        "italy",
        "cuba",
        "spain",
        "united states",
        "argentina",
        "egypt",
        "austria",
        "france",
        "russia",
        "brazil",
        "mexico",
        "colombia",
        "new york",
        "andalusia",
    ]

    if any(
        keyword in location.lower()
        for keyword in international_keywords
    ):
        return location

    # ---------------------------------------------------------
    # CASE 1: Region contains a specific location in brackets
    # Example:
    # "North India (Uttar Pradesh)"
    # -> "Uttar Pradesh, India"
    # ---------------------------------------------------------
    match = re.search(r"\(([^()]+)\)", location)

    if match:
        specific_location = match.group(1).strip()

        if "india" not in specific_location.lower():
            return f"{specific_location}, India"

        return specific_location

    # ---------------------------------------------------------
    # CASE 2: Location already contains India
    # ---------------------------------------------------------
    if "india" in location.lower():
        return location

    # ---------------------------------------------------------
    # CASE 3: Assume remaining dataset locations are Indian
    # ---------------------------------------------------------
    return f"{location}, India"


def geocode_location(location: str) -> dict:
    """
    Convert a textual dance origin/region into geographic information.

    The function:
    1. Extracts the specific geographic region.
    2. Searches Nominatim using the cleaned query.
    3. Validates that the returned result represents a geographic
       administrative area rather than an unrelated business/place.
    """

    geographic_query = extract_geographic_query(location)

    params = {
        "q": geographic_query,
        "format": "jsonv2",
        "addressdetails": 1,
        "limit": 5,
    }

    headers = {
        "User-Agent": "DanceCompass-AI/1.0"
    }

    try:

        response = requests.get(
            NOMINATIM_URL,
            params=params,
            headers=headers,
            timeout=10,
        )

        if response.status_code != 200:
            return {
                "location": location,
                "geographic_query": geographic_query,
                "found": False,
                "error": f"HTTP {response.status_code}",
            }

        results = response.json()

        if not results:
            return {
                "location": location,
                "geographic_query": geographic_query,
                "found": False,
                "error": "Location not found",
            }

        # ---------------------------------------------------------
        # Find the most appropriate geographic result
        # ---------------------------------------------------------

        valid_result = None

        for result in results:

            address = result.get("address", {})
            result_type = result.get("type", "").lower()
            result_class = result.get("class", "").lower()

            # Administrative/geographical result types
            valid_types = {
                "administrative",
                "state",
                "region",
                "county",
                "municipality",
                "city",
                "town",
                "village",
            }

            # Prefer administrative/geographical objects.
            if (
                result_type in valid_types
                or result_class == "boundary"
            ):
                valid_result = result
                break

        # If no administrative result was found,
        # don't blindly accept something like a mall.
        if valid_result is None:

            return {
                "location": location,
                "geographic_query": geographic_query,
                "found": False,
                "error": "No suitable geographic region found",
            }

        result = valid_result
        address = result.get("address", {})

        return {
            "location": location,
            "geographic_query": geographic_query,
            "found": True,

            "display_name": result.get("display_name"),

            "latitude": result.get("lat"),
            "longitude": result.get("lon"),

            "country": address.get("country"),
            "country_code": address.get("country_code"),

            "state": address.get("state"),
            "region": address.get("region"),

            "result_type": result.get("type"),
            "result_class": result.get("class"),
        }

    except requests.RequestException as e:

        return {
            "location": location,
            "geographic_query": geographic_query,
            "found": False,
            "error": str(e),
        }


def enrich_dance_origin(origin: str) -> dict:
    """
    Enrich a dance origin with geographical information.
    """

    return geocode_location(origin)


if __name__ == "__main__":

    origin = input("Enter dance origin/region: ")

    result = enrich_dance_origin(origin)

    print("\n--- Nominatim API Result ---")

    for key, value in result.items():
        print(f"{key}: {value}")