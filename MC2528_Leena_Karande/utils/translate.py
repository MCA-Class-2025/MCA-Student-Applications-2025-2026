"""Translation helpers backed by the optional local Ollama model."""

from utils.llm import translate_local

LANGUAGES = {
    "English": "en-US", "Hindi": "hi-IN", "Marathi": "mr-IN", "Tamil": "ta-IN",
    "Spanish": "es-ES", "French": "fr-FR", "German": "de-DE", "Arabic": "ar-SA",
    "Chinese (Simplified)": "zh-CN", "Japanese": "ja-JP",
}


def translate_text(text: str, target_language: str) -> str:
    if not text or target_language in ("English", "", None):
        return text
    return translate_local(text, target_language)
