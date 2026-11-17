import whisper
import tempfile
import os


model = whisper.load_model("base")


def speech_to_text(audio_bytes):

    temp_file = tempfile.NamedTemporaryFile(
        delete=False,
        suffix=".wav"
    )

    temp_file.write(audio_bytes)
    temp_file.close()


    try:
        result = model.transcribe(
            temp_file.name
        )

        text = result["text"]

        return text.strip()


    except Exception as e:

        print("Whisper Error:", e)
        return ""


    finally:

        os.remove(temp_file.name)
