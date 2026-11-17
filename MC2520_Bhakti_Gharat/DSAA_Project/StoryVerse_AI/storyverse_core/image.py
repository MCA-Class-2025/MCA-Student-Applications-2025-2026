"""
Image captioning (BLIP) and free image generation (Pollinations.ai).
"""

from io import BytesIO
from functools import lru_cache

import requests
from PIL import Image
from transformers import BlipProcessor, BlipForConditionalGeneration

from .api_log import timed_api_call


@lru_cache(maxsize=1)
def _load_blip_model():
    processor = BlipProcessor.from_pretrained(
        "Salesforce/blip-image-captioning-base"
    )
    model = BlipForConditionalGeneration.from_pretrained(
        "Salesforce/blip-image-captioning-base"
    )
    return processor, model


def generate_caption(image: Image.Image) -> str:
    processor, model = _load_blip_model()

    inputs = processor(images=image, return_tensors="pt")
    output = model.generate(**inputs, max_new_tokens=50)

    return processor.decode(output[0], skip_special_tokens=True)


def generate_pollination_image(
    prompt: str, width: int = 1024, height: int = 1024
) -> Image.Image:

    encoded_prompt = requests.utils.quote(prompt)
    url = f"https://image.pollinations.ai/prompt/{encoded_prompt}"

    params = {"width": width, "height": height, "nologo": "true"}

    with timed_api_call("Pollinations", url, prompt[:150]):
        response = requests.get(url, params=params, timeout=60)
        response.raise_for_status()

        return Image.open(BytesIO(response.content)).convert("RGB")


SCENE_IMAGE_NEGATIVE_HINT = (
    "no text, no letters, no watermark, no signature, no logo, "
    "no captions, not blurry, not low quality, no extra limbs, "
    "no extra fingers, not deformed, not cropped, not duplicated"
)


def generate_scene_image(image_prompt: str) -> Image.Image:
    full_prompt = f"{image_prompt}, {SCENE_IMAGE_NEGATIVE_HINT}"
    return generate_pollination_image(full_prompt)
