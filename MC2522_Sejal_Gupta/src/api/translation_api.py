import requests
from urllib.parse import quote


MYMEMORY_URL = "https://api.mymemory.translated.net/get"


def translate_text(
    text,
    source_language="auto",
    target_language="en"
):
    """
    Translate text using MyMemory Translation API.

    Example:
        translate_text(
            "तुम पागल हो",
            source_language="hi",
            target_language="en"
        )
    """

    if not text or not text.strip():
        return ""

    # MyMemory needs an explicit source language.
    # For our moderation pipeline, we can detect common
    # languages ourselves or pass the known language.
    if source_language == "auto":
        source_language = "en"

    try:

        params = {
            "q": text,
            "langpair": f"{source_language}|{target_language}"
        }

        response = requests.get(
            MYMEMORY_URL,
            params=params,
            timeout=30
        )

        response.raise_for_status()

        result = response.json()

        translated_text = (
            result
            .get("responseData", {})
            .get("translatedText", "")
        )

        if not translated_text:
            raise RuntimeError(
                "MyMemory returned no translation."
            )

        return translated_text

    except requests.exceptions.RequestException as e:

        raise RuntimeError(
            f"Translation API request failed: {e}"
        )

    except Exception as e:

        raise RuntimeError(
            f"Translation failed: {e}"
        )