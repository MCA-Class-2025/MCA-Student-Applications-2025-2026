import os
import time
import requests
from dotenv import load_dotenv

load_dotenv()

HF_TOKEN = os.getenv("HF_TOKEN")

API_URL = "https://api-inference.huggingface.co/models/black-forest-labs/FLUX.1-schnell"

headers = {
    "Authorization": f"Bearer {HF_TOKEN}"
}

def generate_ai_image(room, style, budget, description):

    prompt = f"""
    Photorealistic {style} {room} interior design.

    Budget: ₹{budget}

    Requirements:
    {description}

    Luxury furniture,
    modern lighting,
    wooden flooring,
    elegant wall design,
    ultra realistic,
    8k,
    interior photography
    """

    response = requests.post(
        API_URL,
        headers=headers,
        json={"inputs": prompt},
        timeout=300
    )

    if response.status_code == 200:

        filename = f"generated_{int(time.time())}.png"

        os.makedirs("generated", exist_ok=True)

        filepath = os.path.join("generated", filename)

        with open(filepath, "wb") as f:
            f.write(response.content)

        return filepath

    else:

        raise Exception(
            f"Image generation failed:\n{response.text}"
        )