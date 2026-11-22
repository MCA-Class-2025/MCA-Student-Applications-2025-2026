import os

from dotenv import load_dotenv
from elevenlabs.client import ElevenLabs


# =========================================================
# LOAD ENVIRONMENT VARIABLES
# =========================================================

load_dotenv()

ELEVENLABS_API_KEY = os.getenv(
    "ELEVENLABS_API_KEY"
)


# =========================================================
# CHECK API KEY
# =========================================================

if not ELEVENLABS_API_KEY:

    raise ValueError(
        "ELEVENLABS_API_KEY is not configured in .env"
    )


# =========================================================
# ELEVENLABS CLIENT
# =========================================================

client = ElevenLabs(
    api_key=ELEVENLABS_API_KEY
)


# =========================================================
# TEXT TO SPEECH
# =========================================================

def text_to_speech(
    text,
    output_file="output/fixai_result.mp3"
):

    # -----------------------------------------------------
    # GENERATE AUDIO
    # -----------------------------------------------------

    audio = client.text_to_speech.convert(

        text=text,

        voice_id="JBFqnCBsd6RMkjVDRZzb",

        model_id="eleven_flash_v2_5",

        output_format="mp3_44100_128"
    )


    # -----------------------------------------------------
    # CREATE OUTPUT DIRECTORY
    # -----------------------------------------------------

    output_directory = os.path.dirname(
        output_file
    )

    if output_directory:

        os.makedirs(
            output_directory,
            exist_ok=True
        )


    # -----------------------------------------------------
    # SAVE AUDIO
    # -----------------------------------------------------

    with open(
        output_file,
        "wb"
    ) as file:

        for chunk in audio:

            if chunk:

                file.write(chunk)


    return output_file