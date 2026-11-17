"""
Text-to-speech narration using Edge TTS (free).
"""

import re
import time
import asyncio
from io import BytesIO

import edge_tts

from .config import VOICE_MAP
from .api_log import log_api_call


def clean_tts_text(text: str) -> str:
    text = re.sub(r"#+\s*", "", text)
    text = text.replace("**", "").replace("*", "")
    text = re.sub(r"[^\w\s.,!?।॥:;'\"-]", " ", text, flags=re.UNICODE)
    return re.sub(r"\s+", " ", text).strip()


def generate_audio(story: str, language: str) -> bytes:
    """Returns raw mp3 bytes for the given story text."""

    clean_story = clean_tts_text(story)
    selected_voice = VOICE_MAP.get(language, "en-US-AriaNeural")

    async def create_audio():
        audio_file = BytesIO()
        communicate = edge_tts.Communicate(text=clean_story, voice=selected_voice)

        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_file.write(chunk["data"])

        audio_file.seek(0)
        return audio_file.read()

    start_time = time.time()
    new_loop = asyncio.new_event_loop()

    try:
        asyncio.set_event_loop(new_loop)
        audio_bytes = new_loop.run_until_complete(create_audio())

        log_api_call(
            "Edge TTS", selected_voice, f"{language}, {len(clean_story)} chars",
            "success", time.time() - start_time,
        )

        return audio_bytes

    except Exception as error:
        log_api_call(
            "Edge TTS", selected_voice, f"{language}, {len(clean_story)} chars",
            "failed", time.time() - start_time, error=str(error),
        )
        raise

    finally:
        new_loop.close()
        asyncio.set_event_loop(None)
