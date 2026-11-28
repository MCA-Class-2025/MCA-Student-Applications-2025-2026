from services.defect_service import (
    search_defects
)

from services.weather_service import (
    get_weather_summary
)

from services.air_quality_service import (
    get_air_quality
)

from services.geocoding_service import (
    geocode_location
)

from services.service_api_client import (
    find_services
)


# =========================================================
# BUILD FUSED DATA
# =========================================================

def build_fusion_data(

    image_analysis,

    location

):

    # =====================================================
    # 1. GEMINI / LLM ANALYSIS
    # =====================================================

    issue = image_analysis.get(
        "issue",
        ""
    )

    category = image_analysis.get(
        "category",
        ""
    )

    recommended_service = image_analysis.get(
        "recommended_service",
        ""
    )


    # =====================================================
    # 2. GEOCODING
    # =====================================================

    coordinates = geocode_location(
        location
    )


    if not coordinates:

        raise ValueError(
            "Could not find the specified location."
        )


    latitude = coordinates[
        "latitude"
    ]

    longitude = coordinates[
        "longitude"
    ]


    # =====================================================
    # 3. WEATHER
    # =====================================================

    weather = get_weather_summary(

        latitude,

        longitude
    )


    # =====================================================
    # 4. AIR QUALITY
    # =====================================================

    try:

        air_quality = get_air_quality(

            latitude,

            longitude
        )

    except Exception as e:

        print(
            f"Air quality API unavailable: {e}"
        )

        air_quality = {

            "status":
                "temporarily_unavailable",

            "message":
                "Air quality data is temporarily unavailable."
        }


    # =====================================================
    # 5. DEFECT KNOWLEDGE
    # =====================================================

    defect_knowledge = search_defects(

        defect=issue

    )


    # If exact issue doesn't match,
    # try category.

    if not defect_knowledge:

        defect_knowledge = search_defects(

            defect=category
        )


    # =====================================================
    # 6. YOUR OWN SERVICES API
    # =====================================================

    try:

        local_services = find_services(

            service_type=recommended_service,

            latitude=latitude,

            longitude=longitude
        )

    except Exception as e:

        print(
            f"Professional API unavailable: {e}"
        )

        local_services = []


    # =====================================================
    # 7. FINAL FUSED OBJECT
    # =====================================================

    fused_data = {

        "image_analysis":
            image_analysis,

        "location": {

            "address":
                location,

            "latitude":
                latitude,

            "longitude":
                longitude
        },

        "weather":
            weather,

        "air_quality":
            air_quality,

        "defect_knowledge":
            defect_knowledge,

        "local_services":
            local_services

    }


    # =====================================================
    # RETURN
    # =====================================================

    return fused_data
