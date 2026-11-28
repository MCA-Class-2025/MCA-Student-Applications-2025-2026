
from services.pexels_service import search_destination_image

image = search_destination_image("Singapore")

if image:
    print("Pexels API Working!")
    print("Photographer:", image["photographer"])
    print("Image URL:", image["image_url"])
    print("Pexels URL:", image["pexels_url"])
else:
    print("Image fetching failed.")
