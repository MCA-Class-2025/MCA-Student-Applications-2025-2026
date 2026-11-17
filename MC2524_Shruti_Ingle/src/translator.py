from deep_translator import GoogleTranslator

LANGUAGES = {
    "English": "en",
    "Hindi": "hi",
    "Marathi": "mr",
    "Gujarati": "gu",
    "Tamil": "ta",
    "Telugu": "te",
    "Kannada": "kn",
    "Bengali": "bn",
}

def translate_text(text, target_language):
    if target_language == "English":
        return text
    try:
        return GoogleTranslator(
            source="auto",
            target=LANGUAGES[target_language]
        ).translate(text)
    except Exception:
        return text