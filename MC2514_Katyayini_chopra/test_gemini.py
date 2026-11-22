from services.gemini_service import (
    analyze_household_image
)


# =========================================================
# TEST IMAGE
# =========================================================

IMAGE_PATH = "test_images/wall.jpg"


# =========================================================
# ANALYZE
# =========================================================

result = analyze_household_image(
    IMAGE_PATH
)


# =========================================================
# DISPLAY
# =========================================================

print(
    "\n===== GEMINI ANALYSIS ====="
)


for key, value in result.items():

    print(
        f"\n{key}: {value}"
    )