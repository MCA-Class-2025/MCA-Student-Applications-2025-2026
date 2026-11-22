from services.weather_service import get_weather_summary


# Mumbai coordinates

latitude = 19.0760
longitude = 72.8777


weather = get_weather_summary(
    latitude,
    longitude
)


print("\n===== MUMBAI WEATHER =====")

for key, value in weather.items():

    print(
        f"{key}: {value}"
    )