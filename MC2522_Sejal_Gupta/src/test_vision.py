from api.vision_api import detect_safe_search


IMAGE_PATH = "test_image.png"


with open(IMAGE_PATH, "rb") as image_file:
    image_bytes = image_file.read()


result = detect_safe_search(image_bytes)


print("\n===== GOOGLE VISION SAFESEARCH RESULT =====\n")

if result["success"]:

    print("Adult   :", result["result"]["adult"])
    print("Medical :", result["result"]["medical"])
    print("Spoof   :", result["result"]["spoof"])
    print("Violence:", result["result"]["violence"])
    print("Racy    :", result["result"]["racy"])

else:

    print("ERROR:", result["error"])