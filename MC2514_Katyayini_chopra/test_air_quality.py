from services.air_quality_service import get_air_quality


# =========================================================
# MUMBAI
# =========================================================

latitude = 19.0760
longitude = 72.8777


# =========================================================
# GET AIR QUALITY
# =========================================================

air_quality = get_air_quality(

    latitude,

    longitude
)


# =========================================================
# DISPLAY
# =========================================================

print(
    "\n===== MUMBAI AIR QUALITY ====="
)


for key, value in air_quality.items():

    print(
        f"{key}: {value}"
    )
    