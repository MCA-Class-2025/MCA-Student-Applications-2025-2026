import os
import json
from math import cos, radians
from subprocess import CalledProcessError, TimeoutExpired, run
from typing import Any
from urllib.parse import urlencode

import httpx


class ExternalApiError(RuntimeError):
    """Raised when an external health-information provider cannot be used."""


def _get_json(url: str, *, params: dict[str, Any]) -> dict[str, Any]:
    try:
        response = httpx.get(url, params=params, timeout=15.0)
        response.raise_for_status()
    except httpx.HTTPStatusError as error:
        raise ExternalApiError(
            f"The external service returned HTTP {error.response.status_code}."
        ) from error
    except httpx.RequestError as error:
        raise ExternalApiError("The external service is unavailable. Please try again later.") from error

    payload = response.json()
    if not isinstance(payload, dict):
        raise ExternalApiError("The external service returned an invalid response.")
    return payload


def search_foods(query: str, page_size: int) -> list[dict[str, Any]]:
    api_key = os.getenv("USDA_API_KEY")
    if not api_key:
        raise ExternalApiError("Food search is not configured. Add USDA_API_KEY to the backend environment.")

    payload = _get_json(
        "https://api.nal.usda.gov/fdc/v1/foods/search",
        params={"api_key": api_key, "query": query, "pageSize": page_size},
    )
    foods = payload.get("foods", [])
    if not isinstance(foods, list):
        raise ExternalApiError("The food service returned an invalid response.")
    return [
        {
            "name": food.get("description"),
            "brand": food.get("brandOwner"),
            "category": food.get("foodCategory"),
            "calories": next(
                (
                    nutrient.get("value")
                    for nutrient in food.get("foodNutrients", [])
                    if nutrient.get("nutrientName") == "Energy"
                ),
                None,
            ),
        }
        for food in foods
        if isinstance(food, dict)
    ]


def search_drug_labels(query: str, limit: int) -> list[dict[str, Any]]:
    try:
        response = httpx.get(
            "https://api.fda.gov/drug/label.json",
            params={"search": f"openfda.brand_name:{query}", "limit": limit},
            timeout=15.0,
        )
    except httpx.RequestError as error:
        raise ExternalApiError("The drug-label service is unavailable. Please try again later.") from error

    if response.status_code == 404:
        return []
    try:
        response.raise_for_status()
    except httpx.HTTPStatusError as error:
        raise ExternalApiError(
            f"The drug-label service returned HTTP {error.response.status_code}."
        ) from error

    payload = response.json()
    results = payload.get("results", []) if isinstance(payload, dict) else []
    if not isinstance(results, list):
        raise ExternalApiError("The drug-label service returned an invalid response.")
    return [
        {
            "brand_name": label.get("openfda", {}).get("brand_name", [None])[0],
            "generic_name": label.get("openfda", {}).get("generic_name", [None])[0],
            "purpose": label.get("purpose", [None])[0],
            "warnings": label.get("warnings", [None])[0],
        }
        for label in results
        if isinstance(label, dict)
    ]


def search_packaged_foods(query: str, limit: int) -> list[dict[str, Any]]:
    params = {
        "categories_tags_en": "-".join(query.lower().split()),
        "page_size": limit,
        "fields": "product_name,brands,nutrition_grades,nutriments",
    }
    try:
        response = run(
            [
                "curl.exe",
                "--fail",
                "--silent",
                "--show-error",
                "--connect-timeout",
                "5",
                "--max-time",
                "12",
                "--retry",
                "1",
                "--retry-delay",
                "1",
                "--header",
                "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) CardioCare-AI/0.1",
                f"https://world.openfoodfacts.org/api/v2/search?{urlencode(params, safe=',')}",
            ],
            capture_output=True,
            check=False,
            text=True,
            timeout=20,
        )
        if response.returncode != 0 or not response.stdout.strip():
            # If categories search returned nothing, return empty list gracefully
            return []
        payload = json.loads(response.stdout)
    except (CalledProcessError, TimeoutExpired, json.JSONDecodeError):
        # Gracefully return empty list when external service is rate-limited or unavailable
        return []

    products = payload.get("products", []) if isinstance(payload, dict) else []
    if not isinstance(products, list):
        return []
    return [
        {
            "name": product.get("product_name"),
            "brand": product.get("brands"),
            "nutrition_grade": product.get("nutrition_grades").upper()
            if isinstance(product.get("nutrition_grades"), str)
            else None,
            "calories": product.get("nutriments", {}).get("energy-kcal_100g")
            if isinstance(product.get("nutriments"), dict)
            else None,
            "sodium": product.get("nutriments", {}).get("sodium_100g")
            if isinstance(product.get("nutriments"), dict)
            else None,
            "saturated_fat": product.get("nutriments", {}).get("saturated-fat_100g")
            if isinstance(product.get("nutriments"), dict)
            else None,
        }
        for product in products
        if isinstance(product, dict) and isinstance(product.get("nutriments", {}), dict)
    ]


def find_nearby_care(latitude: float, longitude: float, radius: int) -> list[dict[str, Any]]:
    latitude_delta = radius / 111_000
    longitude_delta = radius / (111_000 * cos(radians(latitude)))
    viewbox = ",".join(
        str(value)
        for value in (
            longitude - longitude_delta,
            latitude + latitude_delta,
            longitude + longitude_delta,
            latitude - latitude_delta,
        )
    )
    try:
        response = httpx.get(
            "https://nominatim.openstreetmap.org/search",
            params={
                "q": "hospital",
                "format": "jsonv2",
                "limit": 10,
                "viewbox": viewbox,
                "bounded": 1,
            },
            headers={"User-Agent": "CardioCare AI nearby-care lookup"},
            timeout=15.0,
        )
        response.raise_for_status()
    except httpx.HTTPStatusError as error:
        raise ExternalApiError(f"The nearby-care service returned HTTP {error.response.status_code}.") from error
    except httpx.RequestError as error:
        raise ExternalApiError("The nearby-care service is unavailable. Please try again later.") from error

    places = response.json()
    if not isinstance(places, list):
        raise ExternalApiError("The nearby-care service returned an invalid response.")
    return [
        {
            "name": place.get("name") or str(place.get("display_name", "Healthcare service")).split(",")[0],
            "type": place.get("type"),
            "address": place.get("display_name"),
        }
        for place in places
        if isinstance(place, dict)
    ]
