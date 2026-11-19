from gtts import gTTS
import tempfile
import uuid
import os

def text_to_speech(text):

    filename = f"{uuid.uuid4()}.mp3"

    audio_path = os.path.join(
        tempfile.gettempdir(),
        filename
    )

    tts = gTTS(
        text=text,
        lang="en",
        slow=False
    )

    tts.save(audio_path)

    return audio_path