import os
import requests
from dotenv import load_dotenv

load_dotenv()

PIXABAY_API_KEY = os.getenv("PIXABAY_API_KEY")

print("=" * 70)
print("TESTING PIXABAY")
print("=" * 70)

if not PIXABAY_API_KEY:
    print("✗ PIXABAY_API_KEY NOT FOUND")
    exit()

print("✓ Pixabay API key found")

query = "industrial interior design"

url = "https://pixabay.com/api/"

params = {
    "key": PIXABAY_API_KEY,
    "q": query,
    "image_type": "photo",
    "orientation": "horizontal",
    "safesearch": "true",
    "per_page": 3
}

try:

    response = requests.get(
        url,
        params=params,
        timeout=30
    )

    print()
    print("HTTP STATUS:", response.status_code)

    response.raise_for_status()

    data = response.json()

    hits = data.get("hits", [])

    if not hits:
        print("✗ No images found")
        exit()

    print()
    print("✓ PIXABAY WORKING")
    print()
    print("Images found:", len(hits))
    print()

    for i, image in enumerate(hits, 1):

        print(f"Image {i}:")
        print(image.get("webformatURL"))
        print()

except Exception as e:

    print()
    print("✗ PIXABAY FAILED")
    print("Error:", e)