"""
Shared text-generation helper: Gemini first (with retry on
429/503), falling back to Groq's free API if Gemini's quota is
exhausted. Used by story.py for both story and scene generation.
"""

import time
import requests
from google import genai

from .config import GEMINI_API_KEY, GROQ_API_KEY, GROQ_API_URL, GROQ_MODEL
from .api_log import timed_api_call


def _call_groq(prompt: str) -> str:

    if not GROQ_API_KEY:
        raise RuntimeError(
            "GROQ_API_KEY is missing from .env -- add a free Groq "
            "API key (https://console.groq.com/keys) to enable the "
            "fallback for when Gemini's free quota runs out."
        )

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": GROQ_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.9,
    }

    with timed_api_call("Groq", GROQ_API_URL, prompt[:150]):

        response = requests.post(
            GROQ_API_URL, headers=headers, json=payload, timeout=60
        )

        if response.status_code == 401:
            raise RuntimeError("Groq authentication failed. Check GROQ_API_KEY.")

        if response.status_code == 429:
            raise RuntimeError("Groq's free tier rate limit was also reached.")

        if response.status_code >= 400:
            raise RuntimeError(
                f"Groq request failed {response.status_code}: {response.text}"
            )

        data = response.json()

        try:
            return data["choices"][0]["message"]["content"].strip()
        except (KeyError, IndexError, TypeError):
            raise RuntimeError(f"Groq returned an unexpected response: {data}")


def generate_text_with_ai(prompt: str, model: str = "gemini-3.5-flash") -> str:
    """Gemini first (3 retries on 429/503), Groq as fallback."""

    client = genai.Client(api_key=GEMINI_API_KEY)

    last_error = None

    for attempt in range(3):
        try:
            with timed_api_call(
                "Gemini", f"generate_content ({model})", prompt[:150]
            ):
                response = client.models.generate_content(
                    model=model, contents=prompt
                )
                return response.text.strip()

        except Exception as error:
            last_error = error
            error_text = str(error)

            if "429" not in error_text and "503" not in error_text:
                raise

            if attempt < 2:
                time.sleep(8 * (attempt + 1))

    try:
        return _call_groq(prompt)
    except Exception as groq_error:
        raise RuntimeError(
            f"Gemini failed ({last_error}) and the free Groq "
            f"fallback also failed ({groq_error})."
        )
