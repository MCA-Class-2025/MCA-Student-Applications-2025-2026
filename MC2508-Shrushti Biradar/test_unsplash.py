from api.Unsplash_api import search_unsplash_photos


photos = search_unsplash_photos(
    "wedding decoration",
    5
)


print("Number of photos:", len(photos))


for photo in photos:

    print("-------------------------")

    print("Photographer:", photo["photographer"])

    print("Image:", photo["image_url"])

    print("Photo URL:", photo["photo_url"])