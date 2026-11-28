"""
Gemini wrapper for the Food Recognition Assistant.

Uses a Gemini Flash model for ALL AI features:
  - Image understanding (food captioning / recognition)
  - Text chat (nutrition Q&A, recipes, follow-ups)
  - Audio transcription (speech-to-text for voice questions)

Using one multimodal model for everything keeps the app simple and avoids
needing separate speech-recognition libraries that depend on system
binaries (which can get blocked by locked-down Windows security policies).

The model can be switched at runtime (see set_model / MODEL_OPTIONS below)
so if you hit a free-tier rate limit (HTTP 429) on one model, you can pick
a different one from the sidebar instead of waiting it out.

NOTE: This talks to Gemini directly over plain HTTPS (via `requests`)
instead of using the `google-generativeai` SDK. The SDK pulls in
grpc/cryptography/cffi, whose compiled DLLs get blocked by some
locked-down Windows machines (Application Control / WDAC policies).
Plain `requests` avoids that entirely and needs no extra permissions.

If a model ever returns a 404 "no longer available" or a 429 "limit: 0",
Google has retired that model ID. Check
https://ai.google.dev/gemini-api/docs/models for current model names and
update MODEL_OPTIONS below.
"""

import base64
import io

import requests

# Each of these has its own separate free-tier quota, so switching models
# in the sidebar effectively gives you a fresh rate-limit budget to try.
MODEL_OPTIONS = [
    "gemini-3.5-flash-lite",
    "gemini-3.6-flash",
    "gemini-3.5-flash",
    "gemini-2.5-flash",
    "gemini-2.5-flash-lite",
]

API_BASE = "https://generativelanguage.googleapis.com/v1beta/models"

_api_key = None
_model_name = MODEL_OPTIONS[0]


def configure_gemini(api_key: str) -> None:
    """Call once at app startup with the user's API key."""
    global _api_key
    _api_key = api_key


def set_model(model_name: str) -> None:
    """Switch which Gemini model subsequent calls use."""
    global _model_name
    _model_name = model_name


def get_model() -> str:
    return _model_name


def _endpoint() -> str:
    if not _api_key:
        raise RuntimeError("Gemini is not configured. Call configure_gemini(api_key) first.")
    return f"{API_BASE}/{_model_name}:generateContent?key={_api_key}"



def _call_gemini(parts: list, timeout: int = 120) -> str:
    payload = {"contents": [{"parts": parts}]}
    resp = requests.post(_endpoint(), json=payload, timeout=timeout)
    if resp.status_code != 200:
        raise RuntimeError(f"Gemini API error {resp.status_code}: {resp.text[:400]}")
    data = resp.json()
    try:
        return data["candidates"][0]["content"]["parts"][0]["text"].strip()
    except (KeyError, IndexError):
        raise RuntimeError(f"Unexpected Gemini response format: {data}")


def _pil_to_base64_jpeg(pil_image) -> str:
    """Resize large images before sending to reduce payload and avoid timeouts."""
    img = pil_image.convert("RGB")
    # Resize to max 800px on longest side — enough for food recognition
    max_size = 800
    w, h = img.size
    if max(w, h) > max_size:
        ratio = max_size / max(w, h)
        img = img.resize((int(w * ratio), int(h * ratio)))
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=75)
    return base64.b64encode(buf.getvalue()).decode("utf-8")


# ----------------------------------------------------------------------
# Food image analysis
# ----------------------------------------------------------------------
FOOD_ANALYSIS_PROMPT_TEMPLATE = """
You are a food recognition and nutrition expert.
Look at the image and identify the food/dish shown.

Respond ENTIRELY in {language} (translate every word, including the field
labels below, into {language} - do not leave any part in English unless
{language} IS English).

Use this exact Markdown structure (translate the bold labels too):

**Dish:** <name of the dish>
**Cuisine:** <cuisine type, if identifiable>
**Ingredients (likely):** <comma separated list>
**Estimated calories:** <approx kcal for one serving>
**Macros (approx per serving):** Protein: Xg | Carbs: Xg | Fat: Xg
**Health notes:** <1-2 short lines: healthy points or cautions, allergens if any>

Be concise and only state what you can reasonably infer from the image.
If the image does not contain food, say so clearly (in {language}) instead
of using the format above.
"""


def analyze_food_image(pil_image, language: str = "English") -> dict:
    """Send an image to Gemini and get back a structured food description
    written in the requested language."""
    image_b64 = _pil_to_base64_jpeg(pil_image)
    prompt = FOOD_ANALYSIS_PROMPT_TEMPLATE.format(language=language)
    parts = [
        {"text": prompt},
        {"inline_data": {"mime_type": "image/jpeg", "data": image_b64}},
    ]
    text = _call_gemini(parts)
    return {"raw_text": text}


# ----------------------------------------------------------------------
# Chat
# ----------------------------------------------------------------------
CHAT_SYSTEM_PROMPT_TEMPLATE = """
You are "Foodie", a friendly and knowledgeable food & nutrition assistant chatbot.
You help users understand the food they photographed, answer nutrition questions,
suggest recipes, healthier alternatives, and diet tips.
Keep answers short, clear, and conversational (2-5 sentences) unless the user
explicitly asks for more detail.

IMPORTANT: Always reply ENTIRELY in {language}, no matter what language the
user's message is written or spoken in. Translate everything into {language}.
"""


def chat_with_gemini(
    user_message: str,
    history: list | None = None,
    food_context: str = "",
    language: str = "English",
) -> str:
    """
    Simple stateless chat call: we build a single prompt containing
    system instructions + short rolling history + the food context
    from the last analyzed image (if any) + the new user message.
    """
    history = history or []

    text_parts = [CHAT_SYSTEM_PROMPT_TEMPLATE.format(language=language)]
    if food_context:
        text_parts.append(f"Context about the food the user uploaded earlier:\n{food_context}")

    # keep only the last 6 turns to stay fast + cheap on tokens
    for turn in history[-6:]:
        speaker = "User" if turn["role"] == "user" else "Assistant"
        text_parts.append(f"{speaker}: {turn['content']}")

    text_parts.append(f"User: {user_message}")
    prompt = "\n\n".join(text_parts)

    return _call_gemini([{"text": prompt}])


# ----------------------------------------------------------------------
# Speech-to-text via Gemini (no external binaries needed)
# ----------------------------------------------------------------------
TRANSCRIBE_PROMPT = """
Transcribe the spoken audio exactly as spoken, in its original language.
Output ONLY the raw transcription text - no quotation marks, no labels,
no commentary, no translation.
"""


def transcribe_audio(audio_bytes: bytes, mime_type: str = "audio/wav") -> str:
    """
    Sends recorded audio straight to Gemini and gets back a text transcript.
    Avoids SpeechRecognition's dependency on an external FLAC converter
    binary, which some locked-down Windows machines block.
    """
    audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")
    parts = [
        {"text": TRANSCRIBE_PROMPT},
        {"inline_data": {"mime_type": mime_type, "data": audio_b64}},
    ]
    return _call_gemini(parts)
