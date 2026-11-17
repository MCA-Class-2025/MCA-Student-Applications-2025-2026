from gtts import gTTS
import tempfile
import os

def text_to_audio(text):
    if not text:
        return None

    tts = gTTS(text=text, lang="en")

    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
    tts.save(temp_file.name)

    return temp_file.name