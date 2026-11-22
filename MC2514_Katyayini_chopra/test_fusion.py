from services.gemini_service import (
    analyze_household_image
)

from services.fusion_service import (
    build_fusion_data
)


# =========================================================
# IMAGE
# =========================================================

IMAGE_PATH = (
    "test_images/wall.jpg"
)


# =========================================================
# LOCATION
# =========================================================

LOCATION = (
    "Andheri West, Mumbai, Maharashtra, India"
)


# =========================================================
# GEMINI
# =========================================================

print(
    "\nAnalyzing image..."
)


image_analysis = (
    analyze_household_image(
        IMAGE_PATH
    )
)


print(
    "\nGemini result:"
)

print(
    image_analysis
)


# =========================================================
# FUSION
# =========================================================

print(
    "\nBuilding fused data..."
)


fused_data = build_fusion_data(

    image_analysis,

    LOCATION
)


# =========================================================
# DISPLAY
# =========================================================

print(
    "\n===== FUSED DATA ====="
)


print(
    "\nIMAGE ANALYSIS:"
)

print(
    fused_data[
        "image_analysis"
    ]
)


print(
    "\nLOCATION:"
)

print(
    fused_data[
        "location"
    ]
)


print(
    "\nWEATHER:"
)

print(
    fused_data[
        "weather"
    ]
)


print(
    "\nAIR QUALITY:"
)

print(
    fused_data[
        "air_quality"
    ]
)


print(
    "\nDEFECT KNOWLEDGE:"
)

print(
    fused_data[
        "defect_knowledge"
    ]
)
print("\nLOCAL SERVICES:")
print(fused_data["local_services"])