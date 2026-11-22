from services.gemini_service import (
    analyze_household_image
)

from services.fusion_service import (
    build_fusion_data
)

from services.final_reasoning_service import (
    generate_final_diagnosis
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
# STEP 1 — GEMINI IMAGE ANALYSIS
# =========================================================

print(
    "\nAnalyzing image..."
)


image_analysis = analyze_household_image(
    IMAGE_PATH
)


print(
    "\nImage analysis completed."
)


# =========================================================
# STEP 2 — BUILD FUSED DATA
# =========================================================

print(
    "\nBuilding fused data..."
)


fused_data = build_fusion_data(

    image_analysis,

    LOCATION
)


# =========================================================
# STEP 3 — FINAL GEMINI REASONING
# =========================================================

print(
    "\nGenerating final diagnosis..."
)


final_result = generate_final_diagnosis(
    fused_data
)


# =========================================================
# DISPLAY RESULT
# =========================================================

print(
    "\n"
    "=" * 60
)

print(
    "FINAL FIXAI DIAGNOSIS"
)

print(
    "=" * 60
)


for key, value in final_result.items():

    print(
        f"\n{key.upper()}:"
    )

    print(
        value
    )