import os
import pandas as pd
from PIL import Image
from dotenv import load_dotenv
from google import genai

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def export_gemini_dataset(image_path):
    image = Image.open(image_path)

    prompt = (
        "Extract all visible text from this image and explain any diagrams, "
        "flowcharts, handwritten notes, tables, and visual elements in detail."
    )

    response = client.models.generate_content(
        model="models/gemini-3.5-flash",
        contents=[prompt, image]
    )

    os.makedirs("datasets", exist_ok=True)

    df = pd.DataFrame([{
        "image_name": os.path.basename(image_path),
        "analysis": response.text
    }])

    df.to_csv("datasets/gemini_dataset.csv", index=False)

    print("Gemini dataset saved successfully.")

    return response.text

if __name__ == "__main__":
    result = export_gemini_dataset("sample_image.png")
    print(result[:500])