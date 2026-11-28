from api.Googleplaces_api import search_places

places = search_places(
    "Mumbai",
    "restaurants"
)

print("\n===== PLACES RESPONSE =====\n")

for place in places[:5]:
    print("Name:", place.get("displayName", {}).get("text"))
    print("Address:", place.get("formattedAddress"))
    print("Rating:", place.get("rating"))
    print("Map:", place.get("googleMapsUri"))
    print("-----------------------------")