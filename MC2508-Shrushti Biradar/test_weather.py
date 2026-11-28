from api.Openweather_api import get_weather

print("\n===== WEATHER RESPONSE =====\n")

weather = get_weather("Mumbai")

print("City:", weather["city"])
print("Temperature:", weather["temperature"], "°C")
print("Feels Like:", weather["feels_like"], "°C")
print("Humidity:", weather["humidity"], "%")
print("Weather:", weather["description"])
print("Wind Speed:", weather["wind_speed"], "m/s")