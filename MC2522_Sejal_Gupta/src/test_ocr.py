from api.ocr_api import extract_text_from_image

image_path = "test_image.png"

with open(image_path, "rb") as image:
    text = extract_text_from_image(image)

print("\n========== OCR RESULT ==========\n")
print(text)