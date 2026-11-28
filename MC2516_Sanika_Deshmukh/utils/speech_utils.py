"""
Text-to-Speech utility for the Food Recognition Assistant.

Speech-to-Text is now handled by Gemini directly (see gemini_utils.transcribe_audio)
so this file no longer depends on SpeechRecognition / external FLAC binaries,
which some locked-down Windows machines block.

Text-to-Speech uses gTTS (Google Text-to-Speech) - free, needs internet,
supports dozens of languages via a language code (e.g. "en", "hi", "es").
"""

import io
from gtts import gTTS


def text_to_speech_bytes(text: str, lang: str = "en") -> bytes:
    """Converts text into MP3 audio bytes using gTTS in the given language."""
    tts = gTTS(text=text, lang=lang)
    buf = io.BytesIO()
    tts.write_to_fp(buf)
    buf.seek(0)
    return buf.read()
