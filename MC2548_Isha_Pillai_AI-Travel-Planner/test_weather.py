from services.weather_service import get_weather


result = get_weather("Dubai")

if result:

    print("\nWeather Information")
    print("-------------------")

    print("City:", result["name"])
    print("Country:", result["sys"]["country"])
    print("Temperature:", result["main"]["temp"], "°C")
    print("Feels Like:", result["main"]["feels_like"], "°C")
    print("Condition:", result["weather"][0]["description"])
    print("Humidity:", result["main"]["humidity"], "%")
    print("Wind Speed:", result["wind"]["speed"], "m/s")
    print("Cloudiness:", result["clouds"]["all"], "%")

else:

    print("No weather data received.")