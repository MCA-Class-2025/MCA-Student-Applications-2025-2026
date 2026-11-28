from services.service_api_client import (
    find_services
)


print(
    "\n===== FIXAI MAHARASHTRA SERVICES =====\n"
)


# =========================================================
# ANDHERI WEST LOCATION
# =========================================================

latitude = 19.1172495
longitude = 72.833968


# =========================================================
# SEARCH
# =========================================================

services = find_services(

    service_type="wall_repair",

    city="Mumbai",

    latitude=latitude,

    longitude=longitude
)


# =========================================================
# DISPLAY
# =========================================================

print(
    f"Found {len(services)} services\n"
)


for service in services:

    print(
        f"Name: {service.get('name')}"
    )

    print(
        f"Type: {service.get('service_type')}"
    )

    print(
        f"Area: {service.get('area')}"
    )

    print(
        f"Rating: {service.get('rating')}"
    )

    print(
        f"Phone: {service.get('phone')}"
    )

    print(
        f"Experience: {service.get('experience')} years"
    )

    print(
        f"Price: ₹{service.get('price_range')}"
    )

    print(
        f"Distance: {service.get('distance_km', 'N/A')} km"
    )

    print(
        "----------------------"
    )