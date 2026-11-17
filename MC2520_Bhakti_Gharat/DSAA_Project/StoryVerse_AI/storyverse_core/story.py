"""
Story + storyboard generation logic (no Streamlit dependency).
"""

import json
from .text_ai import generate_text_with_ai


def generate_story(
    image_caption: str, language: str, detected_emotion: str = "neutral"
) -> str:

    prompt = f"""
You are a creative children's story writer.

The image description below is in English:

"{image_caption}"

Detected emotion:

"{detected_emotion}"

Create one magical, child-friendly story in:
{language}

Rules:
- Write the title, complete story and moral only in {language}.
- Do not mix English with the selected language.
- Use simple and natural language.
- Generate around 200 words.
- Include a creative title and a short moral.
- Make the story's mood and events naturally reflect the detected emotion.
- Return only the story.
"""

    return generate_text_with_ai(prompt)


def generate_weather_story(
    city: str, weather_description: str, temperature: float, language: str
) -> str:

    prompt = f"""
You are a creative children's story writer.

Current weather in {city}:
- Condition: {weather_description}
- Temperature: {temperature} degrees Celsius

Create one magical, child-friendly story in:
{language}

Rules:
- The story must be inspired by the current weather condition and the city.
- Write the title, complete story and moral only in {language}.
- Do not mix English with the selected language.
- Use simple and natural language.
- Generate around 300 words.
- Include a creative title and a short moral.
- Return only the story.
"""

    return generate_text_with_ai(prompt)


def generate_video_scenes(
    story: str, language: str, emotion: str = None
) -> list:

    emotion_line = (
        f"Overall story emotion: {emotion}. Let the lighting, "
        f"color palette and mood of every image_prompt reflect "
        f"this emotion.\n"
        if emotion
        else ""
    )

    prompt = f"""
You are an AI storyboard artist preparing a shot list for an
illustrated story video. First read the ENTIRE story below and
mentally note the main character(s), the setting(s), and one
consistent art style that fits this story's mood.

Story:

{story}

{emotion_line}
Break the story into sequential scenes (each ~15-20 seconds
narrated). For EVERY scene return: scene_number, narration (in
{language}), and image_prompt (English, self-contained, structured
as [art style], [character description], [action], [setting],
[lighting/mood], under 60 words, no text/watermarks in the image,
character description and art style repeated identically in every
scene).

Return ONLY valid JSON:
[
    {{
        "scene_number": 1,
        "narration": "Scene narration in {language}",
        "image_prompt": "art style, character description, action, setting, lighting/mood"
    }}
]
"""

    scenes_text = generate_text_with_ai(prompt)

    scenes_text = scenes_text.replace("```json", "").replace("```", "").strip()

    json_start = scenes_text.find("[")
    json_end = scenes_text.rfind("]")

    if json_start == -1 or json_end == -1:
        raise ValueError("AI did not return valid scene JSON.")

    scenes = json.loads(scenes_text[json_start : json_end + 1])

    if not isinstance(scenes, list):
        raise ValueError("Video scenes must be returned as a list.")

    return scenes
