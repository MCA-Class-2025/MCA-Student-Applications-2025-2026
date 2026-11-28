import os
import base64
import requests
from dotenv import load_dotenv

load_dotenv()

VISION_API_KEY = os.getenv("VISION_API_KEY")

VISION_URL = "https://vision.googleapis.com/v1/images:annotate"


def detect_safe_search(image_bytes):
    """
    Analyze an image using Google Cloud Vision SafeSearch API.

    Returns likelihoods for:
    - Adult
    - Medical
    - Spoof
    - Violence
    - Racy
    """

    if not VISION_API_KEY:
        return {
            "success": False,
            "error": "VISION_API_KEY not found in .env"
        }

    try:
        # Convert image bytes to Base64
        encoded_image = base64.b64encode(image_bytes).decode("utf-8")

        payload = {
            "requests": [
                {
                    "image": {
                        "content": encoded_image
                    },
                    "features": [
                        {
                            "type": "SAFE_SEARCH_DETECTION"
                        }
                    ]
                }
            ]
        }

        response = requests.post(
            f"{VISION_URL}?key={VISION_API_KEY}",
            json=payload,
            timeout=30
        )

        response.raise_for_status()

        data = response.json()

        # Check API errors
        if "error" in data:
            return {
                "success": False,
                "error": data["error"].get("message", "Vision API error")
            }

        annotation = data["responses"][0].get(
            "safeSearchAnnotation", {}
        )

        result = {
            "adult": annotation.get("adult", "UNKNOWN"),
            "medical": annotation.get("medical", "UNKNOWN"),
            "spoof": annotation.get("spoof", "UNKNOWN"),
            "violence": annotation.get("violence", "UNKNOWN"),
            "racy": annotation.get("racy", "UNKNOWN")
        }

        return {
            "success": True,
            "result": result
        }

    except requests.exceptions.RequestException as e:
        return {
            "success": False,
            "error": str(e)
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }