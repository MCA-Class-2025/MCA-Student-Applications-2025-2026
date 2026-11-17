import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st
import os
import streamlit as st
import re
import json
import pickle
import time
import edge_tts
import asyncio
import requests
import subprocess
import imageio_ffmpeg
from io import BytesIO
from datetime import datetime
from PIL import Image
from dotenv import load_dotenv
from pathlib import Path
from transformers import (
    BlipProcessor,
    BlipForConditionalGeneration,
    pipeline
)
from google import genai
from google import genai

from moviepy.audio.io.AudioFileClip import AudioFileClip
from moviepy.audio.AudioClip import CompositeAudioClip
from moviepy.video.VideoClip import ImageClip
from moviepy.video.compositing.CompositeVideoClip import concatenate_videoclips
from moviepy.audio.fx import AudioLoop
import tempfile
import numpy as np
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Font

# =================================
# LOAD ENVIRONMENT VARIABLES
# =================================

load_dotenv()

GEMINI_API_KEY = os.getenv(
    "GEMINI_API_KEY"
)
MOTAPI_KEY = os.getenv(
    "MOTAPI_KEY"
)

# =================================
# GROQ CONFIGURATION (free fallback
# for when Gemini's free quota runs out)
# =================================

GROQ_API_KEY = os.getenv(
    "GROQ_API_KEY"
)

GROQ_API_URL = (
    "https://api.groq.com/openai/v1/chat/completions"
)

GROQ_MODEL = "llama-3.3-70b-versatile"


def _call_groq(prompt):
    """
    Sends `prompt` to Groq's free, OpenAI-compatible chat API and
    returns the plain text response. Get a free key at
    https://console.groq.com/keys (no credit card required).
    Used ONLY as a fallback when Gemini's free quota is exhausted --
    it does not change any existing Gemini call logic.
    """

    if not GROQ_API_KEY:

        raise RuntimeError(
            "GROQ_API_KEY is missing from .env -- add a free Groq "
            "API key (https://console.groq.com/keys) to enable the "
            "fallback for when Gemini's free quota runs out."
        )

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": GROQ_MODEL,
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.9
    }

    response = requests.post(
        GROQ_API_URL,
        headers=headers,
        json=payload,
        timeout=60
    )

    if response.status_code == 401:

        raise RuntimeError(
            "Groq authentication failed. Check your GROQ_API_KEY."
        )

    if response.status_code == 429:

        raise RuntimeError(
            "Groq's free tier rate limit was also reached. "
            "Please wait a bit and try again."
        )

    if response.status_code >= 400:

        raise RuntimeError(
            f"Groq request failed {response.status_code}: "
            f"{response.text}"
        )

    data = response.json()

    try:
        return data["choices"][0]["message"]["content"].strip()

    except (KeyError, IndexError, TypeError):

        raise RuntimeError(
            f"Groq returned an unexpected response: {data}"
        )

# =================================
# MUSICAPI CONFIGURATION
# =================================

MUSICAPI_KEY = os.getenv(
    "MUSICAPI_KEY"
)

MUSICAPI_BASE_URL = (
    "https://api.musicapi.ai/api/v1"
)
# =================================
# PERMANENT STORY STORAGE
# =================================

DATA_FOLDER = Path("storyverse_data")

STORIES_FILE = (
    DATA_FOLDER /
    "stories.json"
)

AUDIO_FOLDER = (
    DATA_FOLDER /
    "audio"
)

DATA_FOLDER.mkdir(
    exist_ok=True
)

AUDIO_FOLDER.mkdir(
    exist_ok=True
)


def load_saved_stories():

    if not STORIES_FILE.exists():

        return []

    try:

        with open(

            STORIES_FILE,

            "r",

            encoding="utf-8"

        ) as file:

            stories = json.load(
                file
            )

        return stories

    except Exception:

        return []


def save_stories_to_file(
    stories
):

    with open(

        STORIES_FILE,

        "w",

        encoding="utf-8"

    ) as file:

        json.dump(

            stories,

            file,

            ensure_ascii=False,

            indent=4

        )


# =================================
# EXCEL DATASET LOGGING
# =================================
# Builds a single growing .xlsx dataset out of everything generated
# in BOTH Image Story Mode and Weather Story Mode: the story text,
# its detected emotion, audio/music/video file paths, etc.
# Each story gets ONE row, identified by "Story ID". The row is
# created as soon as the story + audio are saved, then UPDATED in
# place (looked up by Story ID) as background music and video get
# added later in the flow -- so the dataset never ends up with
# duplicate rows for the same story.

EXCEL_DATASET_FILE = DATA_FOLDER / "storyverse_dataset.xlsx"

EXCEL_COLUMNS = [
    "Story ID",             # 1
    "Timestamp",             # 2
    "Mode",                  # 3  Image Upload / Weather-Based
    "Title",                 # 4
    "Language",               # 5
    "Source / Prompt",       # 6  image caption OR weather description
    "City",                  # 7  weather mode only
    "Weather Condition",     # 8  weather mode only
    "Temperature (C)",       # 9  weather mode only
    "Story Text",            # 10
    "Detected Emotion",      # 11
    "Emotion Confidence",    # 12
    "Audio File Path",       # 13
    "Background Music Added",# 14  Yes / No
    "Video Created",         # 15  Yes / No
    "Video File Path"        # 16
]


def log_story_to_excel(record):
    """
    Create or update one row of the StoryVerse Excel dataset.

    `record` is a dict of {column_name: value}. It MUST include
    "Story ID". If a row with that Story ID already exists, only the
    columns present in `record` are overwritten (everything else on
    that row is left untouched) -- this is what lets us fill in
    "Background Music Added" and "Video File Path" later, on a
    separate Streamlit rerun, without creating a second row for the
    same story. If no row with that Story ID exists yet, a new one
    is appended (missing columns are left blank, "Timestamp" is
    filled in automatically).
    """

   

    story_id = record.get("Story ID")

    if not story_id:
        # Can't create or find a row without an identifier
        return False

    DATA_FOLDER.mkdir(parents=True, exist_ok=True)

    if EXCEL_DATASET_FILE.exists():

        workbook = load_workbook(EXCEL_DATASET_FILE)
        sheet = workbook.active

    else:

        workbook = Workbook()
        sheet = workbook.active
        sheet.title = "StoryVerse Dataset"

        sheet.append(EXCEL_COLUMNS)

        for header_cell in sheet[1]:
            header_cell.font = Font(bold=True)

    # Look for an existing row with this Story ID in column 1
    target_row = None

    for row_index in range(2, sheet.max_row + 1):

        if sheet.cell(row=row_index, column=1).value == story_id:
            target_row = row_index
            break

    if target_row is None:

        record.setdefault(
            "Timestamp",
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )

        sheet.append(
            [record.get(column, "") for column in EXCEL_COLUMNS]
        )

    else:

        for col_index, column in enumerate(EXCEL_COLUMNS, start=1):

            if column in record:

                sheet.cell(
                    row=target_row,
                    column=col_index,
                    value=record[column]
                )

    # Rough column autofit so the file is readable on open
    for col_index, column in enumerate(EXCEL_COLUMNS, start=1):

        column_letter = sheet.cell(
            row=1,
            column=col_index
        ).column_letter

        sheet.column_dimensions[column_letter].width = max(
            14,
            min(60, len(column) + 6)
        )

    workbook.save(EXCEL_DATASET_FILE)

    return True


def save_audio_file(
    audio_bytes,
    story_id
):

    audio_path = (

        AUDIO_FOLDER /

        f"{story_id}.mp3"

    )

    with open(

        audio_path,

        "wb"

    ) as audio_file:

        audio_file.write(
            audio_bytes
        )

    return str(
        audio_path
    )


def load_audio_file(
    audio_path
):

    if not audio_path:

        return None

    if not os.path.exists(
        audio_path
    ):

        return None

    with open(

        audio_path,

        "rb"

    ) as audio_file:

        return audio_file.read()

# =================================
# EMOTION → BACKGROUND MUSIC
# =================================

EMOTION_MUSIC_PROMPTS = {

    "joy":
        "instrumental, no vocals, cheerful playful "
        "children's background music, happy magical "
        "melody, light piano, gentle percussion",

    "sadness":
        "instrumental, no vocals, soft emotional "
        "background music, gentle piano, warm strings, "
        "calm and touching atmosphere",

    "love":
        "instrumental, no vocals, warm heartwarming "
        "background music, soft piano, gentle strings, "
        "peaceful and beautiful melody",

    "anger":
        "instrumental, no vocals, dramatic energetic "
        "cinematic background music, strong percussion, "
        "powerful rhythm, intense atmosphere",

    "fear":
        "instrumental, no vocals, mysterious suspenseful "
        "cinematic background music, dark ambient sound, "
        "soft tension and eerie atmosphere",

    "surprise":
        "instrumental, no vocals, magical exciting "
        "adventurous background music, playful melody, "
        "uplifting orchestral elements"
    
}

# =================================
# GENERATE BACKGROUND MUSIC
# =================================

def _generate_background_music_via_api(
    emotion,
    duration,
    output_path="storyverse_data/background_music.mp3"
):

    if not MUSICAPI_KEY:

        raise RuntimeError(
            "MUSICAPI_KEY is missing from .env"
        )

    prompt = EMOTION_MUSIC_PROMPTS.get(
        emotion,
        (
            "instrumental, no vocals, calm gentle "
            "cinematic background music for a "
            "children's story"
        )
    )

    # Producer API supports 1–240 seconds.
    music_duration = max(
        1,
        min(
            int(duration),
            240
        )
    )

    headers = {
        "Authorization":
            f"Bearer {MUSICAPI_KEY}",

        "Content-Type":
            "application/json"
    }

    payload = {

        "task_type":
            "create_music",

        "mv":
            "Lyria 3 Pro",

        "sound":
            prompt,

        "lyrics":
            "",

        "length":
            music_duration,

        "title":
            f"StoryVerse {emotion} background music"
    }

    try:

        response = requests.post(

            f"{MUSICAPI_BASE_URL}/producer/create",

            headers=headers,

            json=payload,

            timeout=60
        )

        if response.status_code == 401:

            raise RuntimeError(
                "MusicAPI authentication failed. "
                "Check your MUSICAPI_KEY."
            )

        if response.status_code == 403:

            raise RuntimeError(
                "MusicAPI access denied or "
                "insufficient credits."
            )

        if response.status_code == 429:

            raise RuntimeError(
                "MusicAPI rate limit reached. "
                "Please try again later."
            )

        if response.status_code >= 400:

            raise RuntimeError(
                f"MusicAPI error "
                f"{response.status_code}: "
                f"{response.text}"
            )

        data = response.json()

        task_id = data.get(
            "task_id"
        )

        if not task_id:

            raise RuntimeError(
                f"MusicAPI did not return a "
                f"task ID: {data}"
            )

        return wait_for_music_generation(
            task_id,
            output_path
        )

    except requests.exceptions.Timeout:

        raise RuntimeError(
            "MusicAPI request timed out."
        )

    except requests.exceptions.ConnectionError:

        raise RuntimeError(
            "Could not connect to MusicAPI. "
            "Check your internet connection."
        )

    except requests.exceptions.RequestException as e:

        raise RuntimeError(
            f"MusicAPI request failed: {e}"
        )
# =================================
# WAIT FOR MUSIC GENERATION
# =================================

def wait_for_music_generation(
    task_id,
    output_path,
    timeout=180
):

    headers = {
        "Authorization":
            f"Bearer {MUSICAPI_KEY}"
    }

    start_time = time.time()

    while (
        time.time() - start_time
        < timeout
    ):

        time.sleep(7)

        try:

            response = requests.get(

                f"{MUSICAPI_BASE_URL}"
                f"/producer/task/{task_id}",

                headers=headers,

                timeout=60
            )

            if response.status_code == 401:

                raise RuntimeError(
                    "MusicAPI authentication failed "
                    "while checking task status."
                )

            if response.status_code == 404:

                raise RuntimeError(
                    "MusicAPI task was not found."
                )

            if response.status_code == 429:

                time.sleep(10)

                continue

            if response.status_code >= 400:

                raise RuntimeError(
                    f"MusicAPI status error "
                    f"{response.status_code}: "
                    f"{response.text}"
                )

            data = response.json()

            songs = data.get(
                "data",
                []
            )

            if not songs:

                continue

            song = songs[0]

            state = song.get(
                "state"
            )

            # -----------------------------
            # MUSIC READY
            # -----------------------------

            if state == "succeeded":

                audio_url = song.get(
                    "audio_url"
                )

                if not audio_url:

                    audio_url = song.get(
                        "wav_url"
                    )

                if not audio_url:

                    raise RuntimeError(
                        "MusicAPI completed the "
                        "task but returned no "
                        "audio URL."
                    )

                return download_music_file(
                    audio_url,
                    output_path
                )

            # -----------------------------
            # MUSIC FAILED
            # -----------------------------

            if state == "failed":

                raise RuntimeError(
                    "MusicAPI music generation failed."
                )

            # Otherwise:
            # pending/running → keep polling

        except requests.exceptions.Timeout:

            continue

        except requests.exceptions.RequestException as e:

            raise RuntimeError(
                f"MusicAPI polling failed: {e}"
            )

    raise RuntimeError(
        "MusicAPI music generation timed out."
    )

# =================================
# DOWNLOAD GENERATED MUSIC
# =================================

def download_music_file(
    audio_url,
    output_path
):

    try:

        os.makedirs(
            os.path.dirname(
                output_path
            ),
            exist_ok=True
        )

        response = requests.get(
            audio_url,
            timeout=120
        )

        response.raise_for_status()

        with open(
            output_path,
            "wb"
        ) as file:

            file.write(
                response.content
            )

        if not os.path.exists(
            output_path
        ):

            raise RuntimeError(
                "Music file was not created."
            )

        if os.path.getsize(
            output_path
        ) == 0:

            raise RuntimeError(
                "Generated music file is empty."
            )

        return output_path

    except requests.exceptions.Timeout:

        raise RuntimeError(
            "Music download timed out."
        )

    except requests.exceptions.RequestException as e:

        raise RuntimeError(
            f"Could not download generated "
            f"music: {e}"
        )


# =================================
# STORED MUSIC FALLBACK
# (used when MusicAPI is not working)
# =================================
# Drop your own royalty-free .mp3/.wav files into the matching
# emotion subfolder below. If MusicAPI fails for any reason
# (missing key, no credits, rate limit, network issue, etc.),
# generate_background_music() automatically falls back to picking
# one of these stored tracks instead of failing outright.
#
#   background_music/
#       joy/        <- your joyful/happy tracks
#       sadness/    <- your sad/gentle tracks
#       love/       <- your warm/romantic tracks
#       anger/      <- your intense/dramatic tracks
#       fear/       <- your tense/suspenseful tracks
#       surprise/   <- your playful/adventurous tracks
#       neutral/    <- general fallback track (used if a specific
#                      emotion folder is empty, or the emotion isn't
#                      one of the folders above)
#
# Supported file types: .mp3, .wav, .m4a, .ogg

BACKGROUND_MUSIC_FOLDER = Path("background_music")

for _emotion_name in (
    "joy", "sadness", "love", "anger", "fear", "surprise", "neutral"
):
    (BACKGROUND_MUSIC_FOLDER / _emotion_name).mkdir(
        parents=True, exist_ok=True
    )

BACKGROUND_MUSIC_EXTENSIONS = (".mp3", ".wav", ".m4a", ".ogg")


def _pick_stored_music_file(emotion):
    """
    Randomly picks a stored music file matching `emotion` from
    background_music/<emotion>/. Falls back to
    background_music/neutral/ if that folder is empty or the
    emotion has no matching folder. Returns a Path, or None if
    nothing usable is found anywhere.
    """

    import random

    def _list_tracks(folder):
        if not folder.exists():
            return []
        return [
            f for f in folder.iterdir()
            if f.is_file()
            and f.suffix.lower() in BACKGROUND_MUSIC_EXTENSIONS
        ]

    emotion_folder = (
        BACKGROUND_MUSIC_FOLDER / (emotion or "neutral").lower()
    )

    candidates = _list_tracks(emotion_folder)

    if not candidates:
        candidates = _list_tracks(BACKGROUND_MUSIC_FOLDER / "neutral")

    if not candidates:
        return None

    return random.choice(candidates)


def _generate_background_music_from_stored_folder(
    emotion,
    duration,
    output_path="storyverse_data/background_music.mp3"
):
    """
    Picks a pre-stored royalty-free music file matching `emotion`
    from the local background_music/ folder, trims it (or loops it
    if it's shorter than needed) to match `duration`, and writes the
    result to `output_path`. No API call required.
    """

    music_file = _pick_stored_music_file(emotion)

    if music_file is None:

        emotion_folder = (
            BACKGROUND_MUSIC_FOLDER / (emotion or "neutral").lower()
        )

        raise RuntimeError(
            f"No stored background music files found for "
            f"'{emotion}' (or 'neutral'). Add a few royalty-free "
            f".mp3 files to '{emotion_folder}' (or "
            f"'{BACKGROUND_MUSIC_FOLDER / 'neutral'}')."
        )

    os.makedirs(
        os.path.dirname(output_path) or ".",
        exist_ok=True
    )

    music_duration = max(1.0, min(float(duration), 240.0))

    source_clip = AudioFileClip(str(music_file))

    try:

        if source_clip.duration > music_duration:

            trimmed_clip = source_clip.subclipped(0, music_duration)

        elif source_clip.duration < music_duration:

            trimmed_clip = AudioLoop(
                duration=music_duration
            ).apply(source_clip)

        else:

            trimmed_clip = source_clip

        trimmed_clip.write_audiofile(output_path, logger=None)

        if trimmed_clip is not source_clip:
            trimmed_clip.close()

    finally:

        source_clip.close()

    if not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
        raise RuntimeError("Background music file was not created.")

    return output_path


def generate_background_music(
    emotion,
    duration,
    output_path="storyverse_data/background_music.mp3"
):
    """
    Tries MusicAPI first (existing logic, unchanged). If that fails
    for ANY reason -- missing key, no credits, rate limit, network
    error, etc. -- automatically falls back to a stored music file
    matching the detected emotion instead of failing outright.
    """

    try:

        return _generate_background_music_via_api(
            emotion,
            duration,
            output_path
        )

    except Exception as api_error:

        print(
            f"MusicAPI failed, falling back to stored music: "
            f"{api_error}"
        )

        try:

            return _generate_background_music_from_stored_folder(
                emotion,
                duration,
                output_path
            )

        except Exception as fallback_error:

            raise RuntimeError(
                f"MusicAPI failed ({api_error}) and the stored "
                f"music fallback also failed ({fallback_error})."
            )


# =================================
# ADD EMOTION-BASED BACKGROUND MUSIC
# TO NARRATION AUDIO (NO VIDEO NEEDED)
# =================================
# Used by BOTH Image Story Mode and Weather Story Mode so a user
# gets emotion-matched background music even when they only want
# the audio narration (i.e. "No - Generate Story Only").

def add_background_music_to_audio(
    narration_bytes,
    emotion,
    output_path="storyverse_data/narration_with_music.mp3"
):

    if not narration_bytes:
        return None

    temp_dir_obj = tempfile.TemporaryDirectory()

    narration_clip = None
    music_clip = None
    mixed_clip = None

    try:

        os.makedirs(
            os.path.dirname(output_path),
            exist_ok=True
        )

        narration_path = os.path.join(
            temp_dir_obj.name,
            "narration.mp3"
        )

        with open(narration_path, "wb") as narration_file:
            narration_file.write(narration_bytes)

        narration_clip = AudioFileClip(narration_path)
        narration_duration = narration_clip.duration

        music_path = generate_background_music(
            emotion=emotion,
            duration=narration_duration,
            output_path=os.path.join(
                temp_dir_obj.name,
                "bg_music.mp3"
            )
        )

        if not music_path or not os.path.exists(music_path):
            return None

        music_clip = AudioFileClip(music_path)

        # Match music duration to narration duration
        if music_clip.duration > narration_duration:

            music_clip = music_clip.subclipped(
                0,
                narration_duration
            )

        elif music_clip.duration < narration_duration:

            music_clip = AudioLoop(
                duration=narration_duration
            ).apply(music_clip)

        # Keep background music quiet so narration stays clear
        music_clip = music_clip.with_volume_scaled(0.12)

        mixed_clip = CompositeAudioClip(
            [narration_clip, music_clip]
        )

        mixed_clip.write_audiofile(
            output_path,
            logger=None
        )

        with open(output_path, "rb") as mixed_file:
            return mixed_file.read()

    except Exception as mix_error:

        print(f"Background music mixing error: {mix_error}")
        # Re-raise so the caller's try/except can show the real
        # error to the user (st.caption) instead of a generic
        # "could not be generated" message with no detail.
        raise

    finally:

        for clip in (narration_clip, music_clip, mixed_clip):

            if clip:

                try:
                    clip.close()

                except Exception:
                    pass

        import gc
        gc.collect()
        time.sleep(0.3)

        try:
            temp_dir_obj.cleanup()

        except Exception:
            pass


# =================================
# STREAMLIT PAGE CONFIGURATION
# =================================

st.set_page_config(
    page_title="StoryVerse AI",
    page_icon="🎨",
    layout="wide",
    initial_sidebar_state="collapsed"
)
# =================================
# SESSION STATE
# =================================

if "generated_scenes" not in st.session_state:
    st.session_state.generated_scenes = []

if "scene_images" not in st.session_state:
    st.session_state.scene_images = {}

if "video_generated" not in st.session_state:
    st.session_state.video_generated = False

if "final_video_path" not in st.session_state:
    st.session_state["final_video_path"] = None

if "weather_scene_images" not in st.session_state:
    st.session_state["weather_scene_images"] = {}

if "weather_final_video_path" not in st.session_state:
    st.session_state["weather_final_video_path"] = None

if "weatherstory_result" not in st.session_state:
    st.session_state["weatherstory_result"] = None
# =================================
# INITIALIZE SAVED STORIES
# =================================

# =================================
# LOAD STORIES PERMANENTLY
# =================================

if "my_stories" not in st.session_state:

    st.session_state[
        "my_stories"
    ] = load_saved_stories()
# =================================
# INITIALIZE THEME
# =================================

if "theme" not in st.session_state:
    st.session_state["theme"] = "Dark"


# =================================
# APPLY LIGHT / DARK THEME
# =================================

if st.session_state["theme"] == "Dark":

    theme_css = """
    <style>

    /* =================================
   RECENT STORIES FIX
================================= */

.recent-card {

    background:
    var(--secondary-background-color);

    border:
    1px solid
    rgba(
        130,
        130,
        130,
        0.20
    );

    border-radius:
    22px;

    padding:
    25px;

    margin-top:
    20px;

    min-height:
    520px;

    color:
    var(--text-color);

    box-shadow:
    0 7px 25px
    rgba(
        0,
        0,
        0,
        0.07
    );
}


.recent-card h2 {

    color:
    var(--text-color);

    margin-top:
    0;

    margin-bottom:
    22px;
}


.recent-story {

    padding:
    16px 8px;

    margin-bottom:
    10px;

    border-bottom:
    1px solid
    rgba(
        130,
        130,
        130,
        0.18
    );
}


.recent-title {

    color:
    var(--text-color);

    font-size:
    17px;

    font-weight:
    700;

    line-height:
    1.5;

    word-break:
    break-word;
}


.recent-language {

    color:
    var(--text-color);

    opacity:
    0.65;

    font-size:
    14px;

    margin-top:
    8px;
}


.empty-story {

    color:
    var(--text-color);

    opacity:
    0.65;

    text-align:
    center;

    padding:
    60px 10px;
}
    .stApp {
        background-color: #111827;
        color: #f9fafb;
    }

    [data-testid="stSidebar"] {
        background-color: #1f2937;
        border-right: 1px solid #374151;
    }

    .main-title {
        color: #f9fafb;
    }

    .main-subtitle {
        color: #d1d5db;
    }

    .dashboard-card,
    .story-card,
    .recent-card,
    .output-card {
        background-color: #1f2937;
        border: 1px solid #374151;
    }

    .card-number {
        color: #f9fafb;
    }

    .card-text {
        color: #d1d5db;
    }

    </style>
    """

else:

    theme_css = """
    <style>

    .stApp {
        background-color: #f6f7fb;
        color: #171717;
    }

    [data-testid="stSidebar"] {
        background-color: #ffffff;
        border-right: 1px solid #e5e7eb;
    }

    .main-title {
        color: #171717;
    }

    .main-subtitle {
        color: #5f6368;
    }

    .dashboard-card,
    .story-card,
    .recent-card,
    .output-card {
        background-color: #ffffff;
        border: 1px solid #e5e7eb;
    }

    .card-number {
        color: #171717;
    }

    .card-text {
        color: #5f6368;
    }

    </style>
    """


st.markdown(
    theme_css,
    unsafe_allow_html=True
)
# =================================
# PROFESSIONAL DASHBOARD CSS
# =================================

st.markdown("""
<style>

/* Hide Streamlit default menu */

#MainMenu {
    visibility: hidden;
}

footer {
    visibility: hidden;
}


/* Main application */

.stApp {
    background:
    var(--background-color);
}


/* Main content */

.block-container {

    max-width:
    1300px;

    padding-top:
    2.5rem;

    padding-bottom:
    3rem;
}


/* Sidebar */

[data-testid="stSidebar"] {

    background:
    var(
        --secondary-background-color
    );

    border-right:
    1px solid
    rgba(
        130,
        130,
        130,
        0.20
    );
}


/* Logo */

.logo-title {

    font-size:
    30px;

    font-weight:
    750;

    color:
    #6546d8;

    text-align:
    center;

    padding:
    18px 0;
}


/* Main heading */

.main-title {

    font-size:
    46px;

    font-weight:
    750;

    color:
    var(--text-color);

    margin-bottom:
    5px;
}


/* Subtitle */

.main-subtitle {

    font-size:
    19px;

    color:
    var(--text-color);

    opacity:
    0.65;

    margin-bottom:
    30px;
}


/* Dashboard cards */

.dashboard-card {

    background:
    var(
        --secondary-background-color
    );

    border:
    1px solid
    rgba(
        130,
        130,
        130,
        0.20
    );

    border-radius:
    20px;

    padding:
    23px;

    min-height:
    145px;

    margin-bottom:
    18px;

    box-shadow:
    0 7px 25px
    rgba(
        0,
        0,
        0,
        0.08
    );

    transition:
    0.3s;
}


.dashboard-card:hover {

    transform:
    translateY(-4px);

    box-shadow:
    0 12px 30px
    rgba(
        90,
        60,
        210,
        0.18
    );
}


/* Card icon */

.card-icon {

    font-size:
    31px;

    margin-bottom:
    12px;
}


/* Card title */

.card-number {

    font-size:
    29px;

    font-weight:
    750;

    color:
    var(--text-color);
}


/* Card description */

.card-text {

    font-size:
    15px;

    color:
    var(--text-color);

    opacity:
    0.65;

    margin-top:
    5px;
}


/* Story form */

.story-card {

    background:
    var(
        --secondary-background-color
    );

    border:
    1px solid
    rgba(
        130,
        130,
        130,
        0.20
    );

    border-radius:
    22px;

    padding:
    30px;

    margin-top:
    20px;

    box-shadow:
    0 7px 25px
    rgba(
        0,
        0,
        0,
        0.07
    );
}


/* Recent stories */

.recent-card {

    background:
    var(
        --secondary-background-color
    );

    border:
    1px solid
    rgba(
        130,
        130,
        130,
        0.20
    );

    border-radius:
    22px;

    padding:
    25px;

    margin-top:
    20px;

    min-height:
    520px;

    box-shadow:
    0 7px 25px
    rgba(
        0,
        0,
        0,
        0.07
    );
}


/* Recent story item */

.recent-story {

    padding:
    15px 5px;

    border-bottom:
    1px solid
    rgba(
        130,
        130,
        130,
        0.15
    );
}


/* Output card */

.output-card {

    background:
    var(
        --secondary-background-color
    );

    border:
    1px solid
    rgba(
        130,
        130,
        130,
        0.20
    );

    border-radius:
    20px;

    padding:
    28px;

    margin-top:
    25px;

    box-shadow:
    0 7px 25px
    rgba(
        0,
        0,
        0,
        0.07
    );
}


/* Main button */

.stButton > button {

    background:
    linear-gradient(
        90deg,
        #5b35d5,
        #7b48e6
    );

    color:
    white;

    border:
    none;

    border-radius:
    11px;

    min-height:
    52px;

    font-size:
    17px;

    font-weight:
    650;
}


/* Mobile */

@media (max-width: 768px) {

    .block-container {
        padding-left: 0.75rem !important;
        padding-right: 0.75rem !important;
        padding-top: 1rem !important;
        padding-bottom: 1.5rem !important;
    }

    .main-title {
        font-size: 28px !important;
        line-height: 1.15 !important;
    }

    .main-subtitle {
        font-size: 14px !important;
        margin-bottom: 16px !important;
    }

    .dashboard-card,
    .story-card,
    .recent-card,
    .output-card {
        padding: 16px !important;
        border-radius: 16px !important;
        min-height: auto !important;
        margin-bottom: 12px !important;
    }

    .card-number {
        font-size: 22px !important;
    }

    .card-text {
        font-size: 13px !important;
    }

    .stButton > button {
        width: 100% !important;
        min-height: 44px !important;
        font-size: 15px !important;
    }

    div[data-testid="column"] {
        min-width: 100% !important;
        width: 100% !important;
        flex: 1 1 100% !important;
    }

    div[data-testid="stHorizontalBlock"] {
        display: block !important;
    }

    [data-testid="stSidebar"] {
        width: 85vw !important;
        max-width: 320px !important;
    }

    .recent-card {
        min-height: auto !important;
    }
}
/* =================================
   MOBILE SIDEBAR BACKGROUND FIX
================================= */

[data-testid="stSidebar"] {

    background-color: #1f2937 !important;

    opacity: 1 !important;

    border-right:
    1px solid #374151;

    z-index: 999999 !important;
}


/* Sidebar inner content */

[data-testid="stSidebarContent"] {

    background-color: #1f2937 !important;

    min-height: 100vh;

}


/* Mobile sidebar */

@media (max-width: 768px) {

    [data-testid="stSidebar"] {

        background-color:
        #1f2937 !important;

        width:
        300px !important;

    }

}  
</style>
""", unsafe_allow_html=True)


# =================================
# LOAD BLIP MODEL
# =================================
@st.cache_resource
def load_blip_model():

    processor = (
        BlipProcessor
        .from_pretrained(
            "Salesforce/"
            "blip-image-captioning-base"
        )
    )

    model = (
        BlipForConditionalGeneration
        .from_pretrained(
            "Salesforce/"
            "blip-image-captioning-base"
        )
    )

    return processor, model


processor, model = (
    load_blip_model()
)

# =================================
# LOAD TRAINED DATA SCIENCE
# EMOTION MODEL
# =================================

EMOTION_MODEL_PATH = (
    "emotion_model/emotion_model.pkl"
)

TFIDF_PATH = (
    "emotion_model/tfidf_vectorizer.pkl"
)


@st.cache_resource
def load_trained_emotion_model():

    with open(
        EMOTION_MODEL_PATH,
        "rb"
    ) as file:

        emotion_model = pickle.load(
            file
        )

    with open(
        TFIDF_PATH,
        "rb"
    ) as file:

        tfidf_vectorizer = pickle.load(
            file
        )

    return (
        emotion_model,
        tfidf_vectorizer
    )


emotion_model, tfidf_vectorizer = (
    load_trained_emotion_model()
)

# =================================
# EMOTION LABEL MAPPING
# =================================

EMOTION_LABELS = {
    0: "sadness",
    1: "joy",
    2: "love",
    3: "anger",
    4: "fear",
    5: "surprise"
}
# =================================
# GENERATE IMAGE CAPTION
# =================================

def generate_caption(image):

    inputs = processor(
        images=image,
        return_tensors="pt"
    )

    output = model.generate(
        **inputs,
        max_new_tokens=50
    )

    caption = processor.decode(
        output[0],
        skip_special_tokens=True
    )

    return caption
# =================================
# EMOTION DETECTION API
# =================================


# =================================
# DETECT EMOTION USING
# TRAINED DATA SCIENCE MODEL
# =================================

def detect_emotion(text):

    if not text or not text.strip():

        return {
            "emotion": "neutral",
            "score": 0.0
        }

    # Convert caption into TF-IDF features
    text_vector = tfidf_vectorizer.transform(
        [text]
    )

    # Predict numeric label
    predicted_label = emotion_model.predict(
        text_vector
    )[0]

    # Get confidence
    probabilities = emotion_model.predict_proba(
        text_vector
    )[0]

    confidence = max(
        probabilities
    )

    # Convert numeric label to emotion name
    emotion = EMOTION_LABELS.get(
        int(predicted_label),
        "neutral"
    )

    return {
        "emotion": emotion,
        "score": float(confidence)
    }
# =================================
# GET WEATHER DATA
# =================================

def get_weather(city):

    weather_api_key = os.getenv(
        "OPENWEATHER_API_KEY"
    )

    if not weather_api_key:
        raise ValueError(
            "OPENWEATHER_API_KEY was not found in .env"
        )

    url = (
        "https://api.openweathermap.org/data/2.5/weather"
    )

    params = {
        "q": city,
        "appid": weather_api_key,
        "units": "metric"
    }

    response = requests.get(
        url,
        params=params,
        timeout=20
    )

    if response.status_code != 200:

        raise Exception(
            f"Weather API error "
            f"{response.status_code}: "
            f"{response.text}"
        )

    data = response.json()

    weather_data = {

        "city": data["name"],

        "country": data["sys"]["country"],

        "temperature": data["main"]["temp"],

        "feels_like": data["main"]["feels_like"],

        "humidity": data["main"]["humidity"],

        "description":
            data["weather"][0]["description"],

        "main":
            data["weather"][0]["main"],

        "wind_speed":
            data["wind"]["speed"]

    }

    return weather_data
# =================================
# TRANSLATE IMAGE CAPTION
# =================================

def translate_caption(
    caption,
    language
):

    # API call is intentionally avoided here.
    # BLIP produces an English caption, and Gemini will use it
    # directly while generating the story in the selected language.
    return caption

def show_data_science_dashboard():

    st.title("📊 StoryVerse AI - Data Science Dashboard")

    st.markdown(
        """
        This dashboard presents the Data Science implementation of
        StoryVerse AI including dataset analysis, statistical analysis,
        relationships between variables, and multivariate analysis.
        """
    )

    # ==========================================================
    # LOAD DATASET
    # ==========================================================

    dataset_path = "storyverse_data/storyverse_dataset.xlsx"

    if not os.path.exists(dataset_path):

        st.error(
            "Dataset not found: storyverse_data/storyverse_dataset.xlsx"
        )
        return

    try:
        df = pd.read_excel(dataset_path)

    except Exception as e:

        st.error(f"Unable to load dataset: {e}")
        return

    # Clean column names
    df.columns = (
        df.columns
        .astype(str)
        .str.strip()
        .str.lower()
        .str.replace(" ", "_")
        .str.replace("-", "_")
    )

    # ==========================================================
    # DATASET OVERVIEW
    # ==========================================================

    st.subheader("📌 Dataset Overview")

    total_records = len(df)
    total_columns = len(df.columns)

    numerical_columns = df.select_dtypes(
        include=np.number
    ).columns.tolist()

    categorical_columns = df.select_dtypes(
        include=["object", "category", "bool"]
    ).columns.tolist()

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "Total Records",
        total_records
    )

    col2.metric(
        "Total Columns",
        total_columns
    )

    col3.metric(
        "Numerical Columns",
        len(numerical_columns)
    )

    col4.metric(
        "Categorical Columns",
        len(categorical_columns)
    )

    # ==========================================================
    # DATA PREVIEW
    # ==========================================================

    with st.expander("🔍 View Dataset"):

        st.dataframe(
            df,
            use_container_width=True,
            height=250
        )

    # ==========================================================
    # UNIVARIATE ANALYSIS
    # ==========================================================

    st.subheader("1️⃣ Univariate Analysis")

    if numerical_columns:

        st.markdown(
            "### Statistical Summary"
        )

        stats = pd.DataFrame(
            index=numerical_columns
        )

        stats["Mean"] = df[numerical_columns].mean()
        stats["Median"] = df[numerical_columns].median()
        stats["Std Dev"] = df[numerical_columns].std()
        stats["Minimum"] = df[numerical_columns].min()
        stats["Q1"] = df[numerical_columns].quantile(0.25)
        stats["Q3"] = df[numerical_columns].quantile(0.75)
        stats["Maximum"] = df[numerical_columns].max()

        st.dataframe(
            stats.round(2),
            use_container_width=True
        )

        # Select variable
        selected_column = st.selectbox(
            "Select numerical variable",
            numerical_columns
        )

        col1, col2 = st.columns(2)

        # Histogram
        with col1:

            fig, ax = plt.subplots()

            ax.hist(
                df[selected_column].dropna(),
                bins=15,
                edgecolor="black"
            )

            ax.set_title(
                f"Distribution of {selected_column}"
            )

            ax.set_xlabel(
                selected_column
            )

            ax.set_ylabel(
                "Frequency"
            )

            st.pyplot(
                fig,
                use_container_width=True
            )

            plt.close(fig)

        # Boxplot
        with col2:

            fig, ax = plt.subplots()

            ax.boxplot(
                df[selected_column].dropna(),
                vert=False
            )

            ax.set_title(
                f"Boxplot of {selected_column}"
            )

            ax.set_xlabel(
                selected_column
            )

            st.pyplot(
                fig,
                use_container_width=True
            )

            plt.close(fig)

    # ==========================================================
    # CATEGORICAL ANALYSIS
    # ==========================================================

    if categorical_columns:

        st.markdown(
            "### Categorical Distribution"
        )

        selected_category = st.selectbox(
            "Select categorical variable",
            categorical_columns
        )

        category_counts = (
            df[selected_category]
            .astype(str)
            .value_counts()
            .head(10)
        )

        fig, ax = plt.subplots()

        category_counts.plot(
            kind="bar",
            ax=ax
        )

        ax.set_title(
            f"{selected_category} Distribution"
        )

        ax.set_xlabel(
            selected_category
        )

        ax.set_ylabel(
            "Count"
        )

        plt.xticks(
            rotation=45,
            ha="right"
        )

        plt.tight_layout()

        st.pyplot(
            fig,
            use_container_width=True
        )

        plt.close(fig)

    # ==========================================================
    # BIVARIATE ANALYSIS
    # ==========================================================

    st.subheader("2️⃣ Bivariate Analysis")

    if len(numerical_columns) >= 2:

        col1, col2 = st.columns(2)

        with col1:

            x_variable = st.selectbox(
                "X Variable",
                numerical_columns,
                key="bivariate_x"
            )

        with col2:

            y_variable = st.selectbox(
                "Y Variable",
                numerical_columns,
                index=min(
                    1,
                    len(numerical_columns) - 1
                ),
                key="bivariate_y"
            )

        correlation = df[
            [x_variable, y_variable]
        ].corr().iloc[0, 1]

        st.metric(
            "Correlation",
            f"{correlation:.3f}"
        )

        if correlation > 0:
            relationship = "Positive relationship"
        elif correlation < 0:
            relationship = "Negative relationship"
        else:
            relationship = "No relationship"

        st.info(
            f"Relationship: **{relationship}**"
        )

        fig, ax = plt.subplots()

        ax.scatter(
            df[x_variable],
            df[y_variable],
            alpha=0.6
        )

        ax.set_xlabel(
            x_variable
        )

        ax.set_ylabel(
            y_variable
        )

        ax.set_title(
            f"{x_variable} vs {y_variable}"
        )

        ax.grid(
            alpha=0.3
        )

        st.pyplot(
            fig,
            use_container_width=True
        )

        plt.close(fig)

    # ==========================================================
    # MULTIVARIATE ANALYSIS
    # ==========================================================

    st.subheader("3️⃣ Multivariate Analysis")

    if len(numerical_columns) >= 2:

        correlation_matrix = df[
            numerical_columns
        ].corr()

        st.markdown(
            "### Correlation Heatmap"
        )

        fig, ax = plt.subplots(
            figsize=(10, 6)
        )

        sns.heatmap(
            correlation_matrix,
            annot=True,
            fmt=".2f",
            cmap="coolwarm",
            ax=ax
        )

        ax.set_title(
            "Correlation Heatmap"
        )

        plt.tight_layout()

        st.pyplot(
            fig,
            use_container_width=True
        )

        plt.close(fig)

    # ==========================================================
    # MISSING VALUES
    # ==========================================================

    st.subheader("🔎 Data Quality")

    missing_values = df.isnull().sum()

    missing_values = (
        missing_values[
            missing_values > 0
        ]
        .sort_values(
            ascending=False
        )
    )

    if len(missing_values) == 0:

        st.success(
            "✓ No missing values found."
        )

    else:

        st.dataframe(
            missing_values.rename(
                "Missing Values"
            ),
            use_container_width=True
        )

    # ==========================================================
    # DUPLICATES
    # ==========================================================

    duplicate_count = df.duplicated().sum()

    if duplicate_count == 0:

        st.success(
            "✓ No duplicate records found."
        )

    else:

        st.warning(
            f"{duplicate_count} duplicate records found."
        )

    # ==========================================================
    # FINAL SUMMARY
    # ==========================================================

    st.subheader("📈 Data Science Summary")

    st.markdown(
        f"""
        **Dataset:** StoryVerse AI Dataset

        **Records:** {total_records}

        **Features:** {total_columns}

        **Numerical Features:** {len(numerical_columns)}

        **Categorical Features:** {len(categorical_columns)}

        **Analysis Performed:**

        ✓ Univariate Analysis  
        ✓ Mean, Median, Standard Deviation  
        ✓ Minimum, Maximum and Quartiles  
        ✓ Histogram  
        ✓ Boxplot  
        ✓ Bar Chart  
        ✓ Bivariate Analysis  
        ✓ Correlation Analysis  
        ✓ Scatter Plot  
        ✓ Multivariate Analysis  
        ✓ Correlation Heatmap  
        ✓ Missing Value Analysis  
        ✓ Duplicate Detection
        """
    )
# =================================
# GENERATE STORY
# =================================

def generate_story(
    image_caption,
    language,
    detected_emotion="neutral"
):

    client = genai.Client(
        api_key=GEMINI_API_KEY
    )

    prompt = f"""
You are a creative children's story writer.

The image description below is in English:

"{image_caption}"

Detected emotion:

"{detected_emotion}"


Create one magical, child-friendly story in:
{language}

Rules:
- Write the title, complete story and moral only in {language}.
- Do not translate or display the image description separately.
- Do not mix English with the selected language.
- Use simple and natural language.
- Generate around 200 words.
- Include a creative title and a short moral.
- Make the story's mood and events naturally reflect the detected emotion.
- Return only the story.

This single request replaces the separate caption-translation request
to reduce Gemini API usage.
"""

    last_error = None

    for attempt in range(3):

        try:

            response = (
                client.models
                .generate_content(
                    model="gemini-3.5-flash",
                    contents=prompt
                )
            )

            return response.text.strip()

        except Exception as error:

            last_error = error
            error_text = str(error)

            if "429" not in error_text and "503" not in error_text:
                raise

            if attempt < 2:
                time.sleep(8 * (attempt + 1))

    # Gemini's free quota is exhausted after retries -- fall back
    # to Groq's free API instead of failing outright.
    try:
        return _call_groq(prompt)
    except Exception as groq_error:
        raise RuntimeError(
            f"Gemini failed ({last_error}) and the free Groq "
            f"fallback also failed ({groq_error})."
        )


# =================================
# GENERATE VIDEO SCENES
# =================================

def generate_video_scenes(
    story,
    language,
    emotion=None
):

    client = genai.Client(
        api_key=GEMINI_API_KEY
    )

    emotion_line = (
        f"Overall story emotion: {emotion}. Let the lighting, "
        f"color palette and mood of every image_prompt reflect "
        f"this emotion.\n"
        if emotion else ""
    )

    prompt = f"""
You are an AI storyboard artist preparing a shot list for an
illustrated story video. First read the ENTIRE story below and
mentally note:
- The main character(s): species/type, age, exact physical
  appearance (colors, clothing, distinguishing features).
- The setting(s) the story takes place in.
- One consistent art style that fits this story's mood (for
  example: "warm, colorful children's storybook illustration,
  digital painting").

Story:

{story}

{emotion_line}
Now break the story into sequential scenes, one per key story beat
(each scene is narrated in roughly 15-20 seconds). For EVERY scene
return exactly these three fields:

1. scene_number — sequential integer starting at 1
2. narration — the portion of the story for this scene, written in
   {language}, short and natural to read aloud
3. image_prompt — a single, self-contained English text-to-image
   prompt for THIS scene ONLY

STRICT RULES for image_prompt — each one is sent to an AI image
model independently, with NO memory of the other scenes, so every
prompt must be fully self-contained and specific:

- Start every image_prompt with the SAME fixed art-style phrase you
  chose above, so all scenes visually belong to one book. Reuse that
  exact phrase, word for word, in every scene.
- Re-state the main character's full physical description (species,
  age, colors, clothing, distinguishing features) in EVERY
  image_prompt, exactly the same way each time. Never shorten it to
  just a name after scene 1 — the image model does not know names.
- Describe ONLY what is actually happening in that scene's
  narration: the specific action, the specific setting, and objects
  explicitly mentioned in the story. Do NOT invent characters,
  props, or locations that are not part of the story.
- Structure each image_prompt as a comma-separated descriptive
  phrase, in this order: [art style], [character description],
  [action], [setting], [lighting / time of day / mood]. Not a full
  sentence — a dense visual description.
- Avoid vague filler words like "a scene", "something happens", "a
  nice picture", "beautiful image" — every word must describe
  something concretely visible.
- No text, letters, numbers, watermarks, logos, or captions inside
  the image itself.
- Keep each image_prompt under 60 words.
- Keep the character's appearance and the art style identical across
  every scene — only the action, setting and mood should change.

Return ONLY valid JSON, no commentary before or after it, in exactly
this shape:

[
    {{
        "scene_number": 1,
        "narration": "Scene narration in {language}",
        "image_prompt": "art style, character description, action, setting, lighting/mood"
    }}
]
"""

    last_error = None

    for attempt in range(3):

        try:

            response = (
                client.models
                .generate_content(
                    model="gemini-3.5-flash",
                    contents=prompt
                )
            )

            scenes_text = (
                response.text
                .strip()
            )

            break

        except Exception as error:

            last_error = error
            error_text = str(error)

            if "429" not in error_text and "503" not in error_text:
                raise

            if attempt < 2:
                time.sleep(8 * (attempt + 1))

    else:
        # Gemini's free quota is exhausted after retries -- fall
        # back to Groq's free API instead of failing outright.
        try:
            scenes_text = _call_groq(prompt)
        except Exception as groq_error:
            raise RuntimeError(
                f"Gemini failed ({last_error}) and the free Groq "
                f"fallback also failed ({groq_error})."
            )

    # Remove Markdown code fences
    scenes_text = (
        scenes_text
        .replace(
            "```json",
            ""
        )
        .replace(
            "```",
            ""
        )
        .strip()
    )

    # Extract the JSON array if Gemini
    # adds text before or after it.
    json_start = scenes_text.find("[")
    json_end = scenes_text.rfind("]")

    if (
        json_start == -1
        or json_end == -1
    ):

        raise ValueError(
            "Gemini did not return "
            "valid scene JSON."
        )

    scenes = json.loads(
        scenes_text[
            json_start:
            json_end + 1
        ]
    )

    if not isinstance(
        scenes,
        list
    ):

        raise ValueError(
            "Video scenes must be "
            "returned as a list."
        )

    return scenes
# =================================
# GENERATE SCENE IMAGE (Pollinations.ai - free, no key needed)
# =================================
# Hugging Face's SDXL endpoint now requires a paid plan (402 Payment
# Required), so scene images are generated with Pollinations.ai
# instead — same free, keyless service already used for the weather
# story's main image below. Pollinations has no separate
# negative_prompt field, so the "avoid these" guidance is appended
# straight into the prompt text.

SCENE_IMAGE_NEGATIVE_HINT = (
    "no text, no letters, no watermark, no signature, no logo, "
    "no captions, not blurry, not low quality, no extra limbs, "
    "no extra fingers, not deformed, not cropped, not duplicated"
)


def generate_scene_image(image_prompt):

    full_prompt = f"{image_prompt}, {SCENE_IMAGE_NEGATIVE_HINT}"

    return generate_pollination_image(full_prompt)

# =================================
# WEATHER LOOKUP (Open-Meteo - free, no key needed)
# =================================

WEATHER_CODE_MAP = {
    0: "clear sky",
    1: "mainly clear",
    2: "partly cloudy",
    3: "overcast",
    45: "fog",
    48: "depositing rime fog",
    51: "light drizzle",
    53: "moderate drizzle",
    55: "dense drizzle",
    61: "slight rain",
    63: "moderate rain",
    65: "heavy rain",
    66: "light freezing rain",
    67: "heavy freezing rain",
    71: "slight snow fall",
    73: "moderate snow fall",
    75: "heavy snow fall",
    77: "snow grains",
    80: "slight rain showers",
    81: "moderate rain showers",
    82: "violent rain showers",
    85: "slight snow showers",
    86: "heavy snow showers",
    95: "thunderstorm",
    96: "thunderstorm with slight hail",
    99: "thunderstorm with heavy hail"
}


def get_city_coordinates(city_name):

    url = "https://geocoding-api.open-meteo.com/v1/search"

    params = {"name": city_name, "count": 1}

    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()

    data = response.json()
    results = data.get("results")

    if not results:
        raise ValueError(f"City '{city_name}' was not found.")

    first = results[0]

    return {
        "latitude": first["latitude"],
        "longitude": first["longitude"],
        "name": first.get("name", city_name),
        "country": first.get("country", "")
    }


def get_weather_data(latitude, longitude):

    url = "https://api.open-meteo.com/v1/forecast"

    params = {
        "latitude": latitude,
        "longitude": longitude,
        "current_weather": True
    }

    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()

    data = response.json()
    current = data.get("current_weather", {})
    weather_code = current.get("weathercode", 0)

    description = WEATHER_CODE_MAP.get(weather_code, "unknown weather")

    return {
        "temperature": current.get("temperature"),
        "windspeed": current.get("windspeed"),
        "weathercode": weather_code,
        "description": description
    }


# =================================
# IMAGE GENERATION USING POLLINATIONS API
# =================================

def generate_pollination_image(prompt, width=1024, height=1024):

    encoded_prompt = requests.utils.quote(prompt)

    url = f"https://image.pollinations.ai/prompt/{encoded_prompt}"

    params = {
        "width": width,
        "height": height,
        "nologo": "true"
    }

    response = requests.get(url, params=params, timeout=60)
    response.raise_for_status()

    image = Image.open(BytesIO(response.content)).convert("RGB")

    return image


def build_weather_image_prompt(city, weather_description, temperature):

    return (
        f"A beautiful artistic storybook illustration of {city} "
        f"experiencing {weather_description} weather at {temperature} "
        f"degrees Celsius, vibrant colors, magical children's book "
        f"illustration style, highly detailed"
    )


# =================================
# GENERATE STORY FROM WEATHER
# =================================

def generate_weather_story(city, weather_description, temperature, language):

    client = genai.Client(api_key=GEMINI_API_KEY)

    prompt = f"""
You are a creative children's story writer.

Current weather in {city}:
- Condition: {weather_description}
- Temperature: {temperature} degrees Celsius

Create one magical, child-friendly story in:
{language}

Rules:
- The story must be inspired by the current weather condition and the city.
- Write the title, complete story and moral only in {language}.
- Do not mix English with the selected language.
- Use simple and natural language.
- Generate around 300 words.
- Include a creative title and a short moral.
- Return only the story.
"""

    last_error = None

    for attempt in range(3):

        try:

            response = client.models.generate_content(
                model="gemini-3.5-flash",
                contents=prompt
            )

            return response.text.strip()

        except Exception as error:

            last_error = error
            error_text = str(error)

            if "429" not in error_text and "503" not in error_text:
                raise

            if attempt < 2:
                time.sleep(8 * (attempt + 1))

    # Gemini's free quota is exhausted after retries -- fall back
    # to Groq's free API instead of failing outright.
    try:
        return _call_groq(prompt)
    except Exception as groq_error:
        raise RuntimeError(
            f"Gemini failed ({last_error}) and the free Groq "
            f"fallback also failed ({groq_error})."
        )
# =================================
# GENERATE AI VIDEO FROM SCENES
# =================================

VOICE_MAP = {
    "English": "en-US-AriaNeural",
    "Hindi (हिंदी)": "hi-IN-SwaraNeural",
    "Marathi (मराठी)": "mr-IN-AarohiNeural"
}


def generate_scene_audio(narration_text, language):
    """Generate narration audio for a single scene using Edge TTS.
    Returns raw mp3 bytes."""

    clean_text = clean_tts_text(narration_text)
    selected_voice = VOICE_MAP.get(language, "en-US-AriaNeural")

    async def create_audio():
        audio_bytes = BytesIO()
        communicate = edge_tts.Communicate(
            text=clean_text,
            voice=selected_voice
        )
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_bytes.write(chunk["data"])
        audio_bytes.seek(0)
        return audio_bytes.read()

    new_loop = asyncio.new_event_loop()
    try:
        asyncio.set_event_loop(new_loop)
        audio_data = new_loop.run_until_complete(create_audio())
    finally:
        new_loop.close()
        asyncio.set_event_loop(None)

    return audio_data


# =================================
# KEN BURNS EFFECT HELPER
# =================================

import random

def apply_ken_burns(pil_image, duration, video_size=(1280, 720), fps=24):
    """
    Takes a static PIL image and returns a moviepy ImageClip with a
    slow zoom + pan effect applied over its duration, giving the
    illusion of motion instead of a static frame.
    """

    # Prepare a slightly oversized base frame so we have room to pan/zoom
    zoom_margin = 1.25  # base image is 25% larger than target canvas
    base_w = int(video_size[0] * zoom_margin)
    base_h = int(video_size[1] * zoom_margin)

    img_resized = pil_image.copy()
    img_resized.thumbnail((base_w, base_h), Image.LANCZOS)

    # Paste onto oversized black canvas so aspect ratio is preserved
    oversized_canvas = Image.new("RGB", (base_w, base_h), (0, 0, 0))
    offset = (
        (base_w - img_resized.width) // 2,
        (base_h - img_resized.height) // 2
    )
    oversized_canvas.paste(img_resized, offset)

    frame_array = np.array(oversized_canvas)
    source_h, source_w = frame_array.shape[:2]

    target_w, target_h = video_size

    # Randomize direction each scene so the video doesn't feel repetitive
    zoom_in = random.choice([True, False])
    pan_x = random.choice([-1, 0, 1])   # left, none, right
    pan_y = random.choice([-1, 0, 1])   # up, none, down

    start_scale = 1.0 if zoom_in else 1.15
    end_scale = 1.15 if zoom_in else 1.0

    def make_frame(t):
        progress = t / duration if duration > 0 else 0
        progress = min(max(progress, 0), 1)

        scale = start_scale + (end_scale - start_scale) * progress

        crop_w = int(target_w * scale)
        crop_h = int(target_h * scale)

        crop_w = min(crop_w, source_w)
        crop_h = min(crop_h, source_h)

        max_x_offset = source_w - crop_w
        max_y_offset = source_h - crop_h

        x_center = max_x_offset / 2
        y_center = max_y_offset / 2

        x_shift = pan_x * max_x_offset / 2 * progress
        y_shift = pan_y * max_y_offset / 2 * progress

        x1 = int(max(0, min(max_x_offset, x_center + x_shift)))
        y1 = int(max(0, min(max_y_offset, y_center + y_shift)))

        cropped = frame_array[y1:y1 + crop_h, x1:x1 + crop_w]

        pil_frame = Image.fromarray(cropped).resize(
            (target_w, target_h), Image.LANCZOS
        )

        return np.array(pil_frame)

    clip = ImageClip(make_frame(0)).with_duration(duration)
    clip = clip.transform(lambda gf, t: make_frame(t))
    clip = clip.with_fps(fps)

    return clip


# =================================
# GENERATE AI VIDEO FROM SCENES
# =================================

def _get_accurate_audio_duration_and_clip(mp3_bytes, temp_dir):
    """
    Edge-TTS produces MP3 data without a proper VBR/Xing header.
    ffmpeg (which moviepy relies on) frequently mis-estimates the
    duration of such files - often reporting a duration far SHORTER
    than the real audio. That mismatch is what causes the final
    video/audio to get cut off early even though the narration file
    itself plays fully in a normal media player.

    Fix: re-mux the MP3 into a WAV file first. WAV headers store an
    exact sample count, so moviepy/ffmpeg always reports the correct
    duration for it. We then build the video around that accurate
    duration and load the audio track from the WAV file.

    Returns (audio_clip, wav_path, mp3_path).
    """

    mp3_path = os.path.join(temp_dir, "narration_source.mp3")
    wav_path = os.path.join(temp_dir, "narration_fixed.wav")

    with open(mp3_path, "wb") as mp3_file:
        mp3_file.write(mp3_bytes)

    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()

    subprocess.run(
        [
            ffmpeg_exe,
            "-y",
            "-i", mp3_path,
            "-ar", "44100",
            "-ac", "2",
            wav_path
        ],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

    audio_clip = AudioFileClip(wav_path)

    return audio_clip, wav_path, mp3_path


def create_ai_video(
    scenes,
    scene_images,
    language,
    output_path="storyverse_data/final_video.mp4",
    fps=24,
    video_size=(1280, 720),
    full_audio_bytes=None,
    emotion=None
):
    """
    Creates final video using generated scene images and
    the complete story audio.

    The total video duration will match the full story audio.
    Scene images are distributed across the complete audio duration.
    """

    clips = []
    audio_clip = None
    temp_dir_obj = None

    try:

        # ==========================================
        # COLLECT AVAILABLE SCENE IMAGES
        # ==========================================

        available_images = []

        for scene in scenes:

            scene_number = scene.get(
                "scene_number"
            )

            image_key = (
                f"scene_image_{scene_number}"
            )

            if image_key in scene_images:

                available_images.append(
                    (
                        scene,
                        scene_images[image_key]
                    )
                )

        if not available_images:

            raise ValueError(
                "No scene images available. "
                "Generate at least one scene image "
                "before creating the video."
            )

        # ==========================================
        # CHECK FULL AUDIO
        # ==========================================

        if not full_audio_bytes:

            raise ValueError(
                "Full story audio is not available."
            )

        # ==========================================
        # SAVE FULL AUDIO + FIX DURATION METADATA
        # ==========================================
        # (see _get_accurate_audio_duration_and_clip for why this
        #  step exists - it is the actual fix for the "video is way
        #  shorter than the audio" bug)

        temp_dir_obj = tempfile.TemporaryDirectory()

        audio_clip, wav_path, mp3_path = (
            _get_accurate_audio_duration_and_clip(
                full_audio_bytes,
                temp_dir_obj.name
            )
        )

        total_audio_duration = (
            audio_clip.duration
        )

        # ==========================================
        # DISTRIBUTE AUDIO DURATION
        # ==========================================

        number_of_scenes = len(
            available_images
        )

        scene_duration = (
            total_audio_duration
            / number_of_scenes
        )

        # ==========================================
        # CREATE SCENE CLIPS
        # ==========================================

        for scene, pil_image in available_images:

            image_clip = apply_ken_burns(
                pil_image.convert("RGB"),
                duration=scene_duration,
                video_size=video_size,
                fps=fps
            )

            clips.append(
                image_clip
            )

        # ==========================================
        # COMBINE SCENE IMAGES
        # ==========================================

        final_video = concatenate_videoclips(
            clips,
            method="compose"
        )

        # ==========================================
        # ATTACH STORY NARRATION TO THE VIDEO
        # ==========================================
        # This was the missing step causing videos with no audio:
        # `audio_clip` (the narration) was only ever used to compute
        # scene durations above, and was never actually attached to
        # `final_video`. Attach it now, before the background music
        # step, so `final_video.audio` below correctly detects the
        # narration and mixes both tracks together.

        final_video = final_video.with_audio(
            audio_clip
        )

        # =================================
        # GENERATE EMOTION-BASED
        # BACKGROUND MUSIC
        # =================================

        music_path = None
        music_clip = None

        try:

            # Prefer the emotion explicitly passed in by the caller
            # (each story mode detects its own emotion). Fall back to
            # session state / "joy" only if nothing was passed, so
            # Weather Story videos never silently reuse an emotion
            # left over from Image Story mode (or vice versa).
            detected_emotion = (
                emotion
                or st.session_state.get(
                    "detected_emotion",
                    "joy"
                )
            )

            st.info(
                f"🎵 Generating "
                f"{detected_emotion} background music..."
            )

            music_path = generate_background_music(

                emotion=detected_emotion,

                duration=final_video.duration,

                output_path=(
                    "storyverse_data/"
                    "background_music.mp3"
                )
            )

            if (
                music_path
                and os.path.exists(music_path)
            ):

                music_clip = AudioFileClip(
                    music_path
                )

                # Match music duration to video
                if music_clip.duration > final_video.duration:

                    music_clip = (
                        music_clip
                        .subclipped(
                            0,
                            final_video.duration
                        )
                    )

                elif music_clip.duration < final_video.duration:

                    # If generated music is shorter,
                    # loop it to cover the complete video.
                    music_clip = AudioLoop(
                        duration=final_video.duration
                    ).apply(
                        music_clip
                    )

                # Make background music quieter
                music_clip = (
                    music_clip
                    .with_volume_scaled(
                        0.12
                    )
                )

                # Combine narration + background music
                if final_video.audio:

                    final_audio = CompositeAudioClip(
                        [
                            final_video.audio,
                            music_clip
                        ]
                    )

                else:

                    final_audio = music_clip

                final_video = final_video.with_audio(
                    final_audio
                )

                st.success(
                    "🎵 Emotion-based background music "
                    "added to the video."
                )

        except Exception as music_error:

            st.warning(
                "Background music could not be generated. "
                "The video will be created with narration only."
            )

            print(
                f"MusicAPI error: {music_error}"
            )


        # =================================
        # WRITE FINAL VIDEO
        # =================================

        final_video.write_videofile(
            output_path,
            fps=fps,
            codec="libx264",
            audio_codec="aac",
            logger=None
        )
        final_video.close()

        return output_path

    finally:

        # ==========================================
        # CLOSE VIDEO CLIPS
        # ==========================================

        for clip in clips:

            try:
                clip.close()

            except Exception:
                pass

        # ==========================================
        # CLOSE AUDIO
        # ==========================================

        if audio_clip:

            try:
                audio_clip.close()

            except Exception:
                pass

        # ==========================================
        # CLEAN MEMORY
        # ==========================================

        import gc

        gc.collect()

        time.sleep(0.5)

        # ==========================================
        # DELETE TEMP AUDIO FILES
        # ==========================================

        if temp_dir_obj:

            for attempt in range(3):

                try:

                    temp_dir_obj.cleanup()

                    break

                except PermissionError:

                    time.sleep(0.5)

                except Exception:

                    break
# =================================
# GENERATE AUDIO
# =================================

def clean_tts_text(text):

    # Remove Markdown symbols
    text = re.sub(r'#+\s*', '', text)
    text = text.replace("**", "")
    text = text.replace("*", "")

    # Remove emojis and unsupported symbols,
    # while keeping English, Hindi and Marathi text
    text = re.sub(
        r'[^\w\s.,!?।॥:;\'"-]',
        ' ',
        text,
        flags=re.UNICODE
    )

    # Remove repeated spaces
    text = re.sub(r'\s+', ' ', text)

    return text.strip()


def split_text_for_tts(text, max_length=2500):

    sentences = re.split(
        r'(?<=[.!?।॥])\s+',
        text
    )

    chunks = []
    current_chunk = ""

    for sentence in sentences:

        sentence = sentence.strip()

        if not sentence:
            continue

        if (
            len(current_chunk)
            + len(sentence)
            + 1
            <= max_length
        ):

            current_chunk += (
                sentence + " "
            )

        else:

            if current_chunk.strip():

                chunks.append(
                    current_chunk.strip()
                )

            current_chunk = (
                sentence + " "
            )

    if current_chunk.strip():

        chunks.append(
            current_chunk.strip()
        )

    return chunks


# =================================
# GENERATE AUDIO USING EDGE TTS
# =================================

def generate_audio(
    story,
    language
):

    # Remove Markdown symbols
    clean_story = re.sub(
        r'#+\s*',
        '',
        story
    )

    clean_story = clean_story.replace(
        "**",
        ""
    )

    clean_story = clean_story.replace(
        "*",
        ""
    )

    # Remove extra spaces
    clean_story = re.sub(
        r'\s+',
        ' ',
        clean_story
    ).strip()


    # Select voice
    voices = {

        "English":
        "en-US-AriaNeural",

        "Hindi (हिंदी)":
        "hi-IN-SwaraNeural",

        "Marathi (मराठी)":
        "mr-IN-AarohiNeural"

    }


    selected_voice = voices[
        language
    ]


    async def create_audio():

        audio_file = BytesIO()

        communicate = (
            edge_tts.Communicate(

                text=clean_story,

                voice=selected_voice

            )
        )

        async for chunk in (
            communicate.stream()
        ):

            if (
                chunk["type"]
                == "audio"
            ):

                audio_file.write(
                    chunk["data"]
                )

        audio_file.seek(
            0
        )

        return audio_file


    # Run Edge TTS in a dedicated event loop.
    # This avoids Streamlit's existing-loop errors.
    new_loop = asyncio.new_event_loop()

    try:

        asyncio.set_event_loop(
            new_loop
        )

        audio_file = (
            new_loop.run_until_complete(
                create_audio()
            )
        )

    finally:

        new_loop.close()

        asyncio.set_event_loop(
            None
        )


    return audio_file
    # Initialize My Stories
    if "my_stories" not in st.session_state:
        st.session_state.my_stories = []


    # Save Story button
    if st.button(
        "💾 Save Story and Audio",
        use_container_width=True
    ):

        audio_bytes = audio_file.getvalue()

        st.session_state.my_stories.append({
            "title": "My AI Story",
            "language": language,
            "story": story,
            "caption": translated_caption,
            "audio": audio_bytes
        })

        st.success(
            "Story and audio saved in My Stories! 🎉"
        )
# =================================
# SESSION STATE
# =================================

if "scene_images" not in st.session_state:

    st.session_state[
        "scene_images"
    ] = {}


if "generated_scenes" not in st.session_state:

    st.session_state[
        "generated_scenes"
    ] = []


if "video_generated" not in st.session_state:

    st.session_state[
        "video_generated"
    ] = False

# =================================
# SESSION CACHE
# =================================

if "storyverse_result" not in st.session_state:

    st.session_state.storyverse_result = None

# =================================
# SESSION STATE FOR MY STORIES
# =================================

if "saved_stories" not in st.session_state:
    st.session_state.saved_stories = []

# =================================
# THEME SESSION STATE
# =================================

if "theme" not in st.session_state:

    st.session_state.theme = "Light"

# =================================
# SIDEBAR
# =================================

with st.sidebar:

    st.markdown(
        """
<div class="logo-title">
🎨 StoryVerse AI
</div>
        """,
        unsafe_allow_html=True
    )

    st.divider()

    page = st.radio(
        "Navigation",
        [
            "🏠 Home",
            "✍️ Create Story",
            "🌦️ Weather Story",
            "📚 My Stories",
            "📊 Dataset",
            "🧪 Data Science Dashboard",
            "⭐ Favorites",
            "⚙️ Settings",
            "ℹ️ About"
        ],
        label_visibility="collapsed"
        )

    st.divider()

    # =================================
    # DATASET DOWNLOAD (Excel)
    # =================================
    # Every story generated in either mode logs a row here, so this
    # single .xlsx grows into a dataset of everything the app made.

    if EXCEL_DATASET_FILE.exists():

        with open(EXCEL_DATASET_FILE, "rb") as dataset_file:
            dataset_bytes = dataset_file.read()

        st.download_button(
            label="📊 Download Dataset (Excel)",
            data=dataset_bytes,
            file_name="storyverse_dataset.xlsx",
            mime=(
                "application/vnd.openxmlformats-officedocument"
                ".spreadsheetml.sheet"
            ),
            use_container_width=True,
            key="sidebar_dataset_download"
        )

    else:

        st.caption(
            "📊 No dataset rows yet -- generate a story to "
            "start building it."
        )

    st.divider()

    st.subheader(
        "About StoryVerse AI"
    )

    st.write(
        """
StoryVerse AI creates
magical stories from images
using Artificial Intelligence.

Upload an image and
let the magic begin! ✨
        """
    )


# =================================
# HOME / CREATE STORY PAGE
# =================================

if page in [

    "🏠 Home",

    "✍️ Create Story"

]:

    st.markdown(
        """
<div class="main-title">
🎨 StoryVerse AI
</div>
        """,
        unsafe_allow_html=True
    )

    st.markdown(
        """
<div class="main-subtitle">
Turn Your Images into
Magical Stories ✨
</div>
        """,
        unsafe_allow_html=True
    )


    # =============================
    # DASHBOARD CARDS - ROW 1
    # =============================

    card1, card2, card3 = (
        st.columns(
            [1.25, 1, 1]
        )
    )


    with card1:

        st.markdown(
            """
<div class="dashboard-card">

<div class="card-icon">
📖
</div>

<div class="card-number">
AI Stories
</div>

<div class="card-text">

Create magical stories
from uploaded images.

</div>

</div>
            """,
            unsafe_allow_html=True
        )


    with card2:

        st.markdown(
            """
<div class="dashboard-card">

<div class="card-icon">
🌐
</div>

<div class="card-number">
3 Languages
</div>

<div class="card-text">

English • Hindi • Marathi

</div>

</div>
            """,
            unsafe_allow_html=True
        )


    with card3:

        st.markdown(
            """
<div class="dashboard-card">

<div class="card-icon">
🎙️
</div>

<div class="card-number">
Audio
</div>

<div class="card-text">

Listen to your story.

</div>

</div>
            """,
            unsafe_allow_html=True
        )


    # =============================
    # DASHBOARD CARDS - ROW 2
    # =============================

    video_col, info_col = (
        st.columns(
            [1, 2.25]
        )
    )


    with video_col:

        st.markdown(
            """
<div class="dashboard-card">

<div class="card-icon">
🎬
</div>

<div class="card-number">
AI Video
</div>

<div class="card-text">

Optional storyboard.

</div>

</div>
            """,
            unsafe_allow_html=True
        )


    with info_col:

        st.markdown(
            """
<div class="dashboard-card">

<div class="card-icon">
✨
</div>

<div class="card-number">
Create Your Story
</div>

<div class="card-text">

Select language,
upload an image and let
StoryVerse AI create
your magical story.

</div>

</div>
            """,
            unsafe_allow_html=True
        )


    # =============================
    # MAIN FORM + RECENT STORIES
    # =============================

    main_col, recent_col = (
        st.columns(
            [2.2, 1]
        )
    )


    # =============================
    # CREATE STORY FORM
    # =============================

    with main_col:

        st.markdown(
            '<div class="story-card">',
            unsafe_allow_html=True
        )

        st.subheader(
            "✨ Create a New Story"
        )

        st.write(
            """
Choose a language,
upload an image and let
AI create a magical story.
            """
        )

        language = st.selectbox(

            "🌐 Choose Story Language",

            [

                "English",

                "Hindi (हिंदी)",

                "Marathi (मराठी)"

            ]

        )

        # =================================
        # IMAGE UPLOAD
        # =================================
        # This page is for Image Story Mode only.
        # Weather-based story creation lives on its own
        # "🌦️ Weather Story" page (see sidebar).

        uploaded_image = (
            st.file_uploader(

                "🖼️ Upload Your Image",

                type=[
                    "jpg",
                    "jpeg",
                    "png"
                ]

            )
        )

        create_video = st.radio(

            "🎬 Do you want to "
            "create a video?",

            [

                "No - Generate Story Only",

                "Yes - Create Full "
                "AI Story Video"

            ]

        )

        generate_button = (
            st.button(

                "✨ Generate "
                "Magical Story",

                use_container_width=True

            )
        )

        st.markdown(
            '</div>',
            unsafe_allow_html=True
        )


    # =================================Recent stories
    with recent_col:

        st.subheader(
            "🕘 Recent Stories"
        )

        saved_stories = (
            st.session_state.get(
                "my_stories",
                []
            )
        )

        recent_stories = (
            saved_stories[-2:]
        )

        recent_stories = (
            recent_stories[::-1]
        )

        if not recent_stories:

            st.info(
                "📚 No stories created yet."
            )

            st.caption(
                "Generate your first magical "
                "story and it will appear here."
            )

        else:

            for story_data in recent_stories:

                story_title = (
                    story_data.get(
                        "title",
                        "My AI Story"
                    )
                )

                story_language = (
                    story_data.get(
                        "language",
                        "English"
                    )
                )

                story_title = (
                    story_title
                    .replace("**", "")
                    .replace("#", "")
                    .strip()
                )

                st.markdown(
                    f"### 📖 {story_title}"
                )

                st.caption(
                    f"🌐 {story_language}"
                )

                st.divider()
    # =============================
    # GENERATE STORY
    # =============================

    if (
    generate_button
    or
    st.session_state.storyverse_result
    is not None
    ):

        if uploaded_image is None:

            st.warning(
                "Please upload "
                "an image first."
            )

        elif not GEMINI_API_KEY:

            st.error(
                "Gemini API key "
                "was not found."
            )

        else:

            image = (
                Image.open(
                    uploaded_image
                )
                .convert(
                    "RGB"
                )
            )

            st.image(

                image,

                caption=
                "Uploaded Image",

                use_container_width=
                True

            )

            try:

                # Only run the full analysis + story generation
                # pipeline on a genuine NEW "Generate" click, or the
                # very first time this image is processed. This is
                # the actual fix for "every scene generation changes
                # the whole process" -- Streamlit reruns this ENTIRE
                # script on every button click anywhere on the page
                # (including a single scene's "Generate Image"
                # button), and this block used to call Gemini again
                # unconditionally on every one of those reruns.
                # Since Gemini's output isn't deterministic, that
                # produced a brand NEW story (and therefore new,
                # mismatched scenes) every single click, wiping out
                # any scene images already generated for the old
                # story. Caching the result here means the story
                # (and later, its scenes) are generated once and
                # reused for the rest of the session.

                if (
                    generate_button
                    or st.session_state.storyverse_result is None
                ):

                    with st.spinner(
                        "AI is analyzing your image..."
                    ):

                        english_caption = generate_caption(
                            image
                        )

                    translated_caption = english_caption

                    # =================================
                    # EMOTION DETECTION
                    # =================================

                    with st.spinner(
                        "🎭 Detecting image emotion..."
                    ):

                        emotion_result = detect_emotion(
                            english_caption
                        )

                    detected_emotion = (
                        emotion_result["emotion"]
                    )

                    emotion_score = (
                        emotion_result["score"]
                    )

                    # =================================
                    # GENERATE EMOTION-AWARE STORY
                    # =================================

                    with st.spinner(
                        "Gemini is creating your story..."
                    ):

                        story = generate_story(
                            translated_caption,
                            language,
                            detected_emotion
                        )

                    # Save story only once
                    if (
                        "last_saved_story"
                        not in st.session_state
                        or st.session_state.last_saved_story
                        != story
                    ):

                        story_data = {
                            "title": "Generated Story",
                            "story": story,
                            "language": language,
                            "caption": translated_caption
                        }

                        st.session_state.saved_stories.append(
                            story_data
                        )

                        st.session_state.last_saved_story = story

                    st.session_state.storyverse_result = {

                        "story": story,

                        "caption": translated_caption,

                        "language": language,

                        "emotion": detected_emotion,

                        "emotion_score": emotion_score,

                        "scenes": None,

                        "create_video": create_video,

                        "audio_bytes": None

                    }

                # Everything below now reads from the CACHED result
                # instead of re-generating, so scene/video buttons
                # further down the page no longer trigger a fresh
                # (and different) story.

                cached_result = st.session_state.storyverse_result

                story = cached_result["story"]
                translated_caption = cached_result["caption"]
                detected_emotion = cached_result["emotion"]
                emotion_score = cached_result["emotion_score"]

                st.session_state[
                    "detected_emotion"
                ] = detected_emotion

                # =================================
                # DISPLAY EMOTION
                # =================================

                emotion_icons = {

                    "joy": "😊",

                    "sadness": "😢",

                    "anger": "😡",

                    "fear": "😨",

                    "surprise": "😲",

                    "disgust": "🤢",

                    "anticipation": "🤩",

                    "trust": "🤝",

                    "neutral": "😐"
                }

                emotion_icon = emotion_icons.get(
                    detected_emotion.lower(),
                    "🎭"
                )


                st.success(
                    f"{emotion_icon} Detected Emotion: "
                    f"{detected_emotion.title()}"
                )


                st.success(
                    "Your story is ready! 🎉"
                )


                st.markdown(
                    '<div class="output-card">',
                    unsafe_allow_html=True
                )


                st.subheader(
                    f"🖼️ Image Description "
                    f"({language})"
                )

                st.write(
                    translated_caption
                )

                st.subheader(
                    "🎭 Detected Emotion"
                )

                st.write(
                    f"{emotion_icon} "
                    f"{detected_emotion.title()}"
                )

                st.caption(
                    f"Emotion confidence/intensity: "
                    f"{emotion_score:.2f}"
                )

                st.subheader(
                    "📖 Generated Story"
                )

                st.write(
                    story
                )


                st.download_button(

                    label=
                    "⬇️ Download Story",

                    data=story,

                    file_name=
                    "storyverse_story.txt",

                    mime=
                    "text/plain",

                    use_container_width=True

                )


                # =====================
                # AUDIO
                # =====================
                # Cached the same way as the story above -- only
                # generated once per story, then reused on every
                # later rerun (e.g. clicking a scene image button)
                # instead of calling Edge TTS again each time.

                try:

                    if cached_result.get("audio_bytes") is None:

                        with st.spinner(
                            "Creating audio..."
                        ):

                            audio_file = (
                                generate_audio(

                                    story,

                                    language

                                )
                            )

                        cached_result["audio_bytes"] = (
                            audio_file.getvalue()
                        )

                    audio_bytes = cached_result["audio_bytes"]

                    st.subheader(
                        "🎙️ Listen to "
                        "Your Story"
                    )

                    st.audio(
                        audio_bytes,
                        format="audio/mp3"
                    )

                    # =================================
                    # SAVE STORY AND AUDIO
                    # =================================

                    # Get title from first line
                    clean_title = re.sub(
                        r"^[#*\s]+",
                        "",
                        story.splitlines()[0]
                    ).strip()

                    if not clean_title:

                        clean_title = "My AI Story"


                    new_story = {

                        "title": clean_title,

                        "language": language,

                        "caption": translated_caption,

                        "story": story,

                        "audio": audio_bytes

                    }


                    # Prevent duplicate saving
                    already_saved = any(

                        saved_story["story"] == story

                        for saved_story

                        in st.session_state["my_stories"]

                    )


                    if not already_saved:

                        import uuid

                        story_id = str(
                            uuid.uuid4()
                        )

                        audio_path = (
                            save_audio_file(

                                audio_bytes,

                                story_id

                            )
                        )

                        new_story[
                            "id"
                        ] = story_id

                        new_story[
                            "audio_path"
                        ] = audio_path

                       
                        new_story.pop(
                            "audio",
                            None
                        )

                        st.session_state[
                            "my_stories"
                        ].append(
                            new_story
                        )

                        # Save stories permanently

                        save_stories_to_file(

                            st.session_state[
                                "my_stories"
                            ]

                        )

                        st.success(
                            "💾 Story and audio saved "
                            "permanently!"
                        )

                        st.session_state[
                            "current_story_id"
                        ] = story_id

                        try:

                            log_story_to_excel({
                                "Story ID": story_id,
                                "Mode": "Image Upload",
                                "Title": clean_title,
                                "Language": language,
                                "Source / Prompt": translated_caption,
                                "Story Text": story,
                                "Detected Emotion": detected_emotion,
                                "Emotion Confidence": round(
                                    emotion_score, 3
                                ),
                                "Audio File Path": audio_path,
                                "Background Music Added": "No",
                                "Video Created": "No",
                                "Video File Path": ""
                            })

                        except Exception as excel_error:

                            st.caption(
                                f"Dataset logging skipped: "
                                f"{excel_error}"
                            )

                    # =================================
                    # BACKGROUND MUSIC (AUDIO-ONLY PATH)
                    # =================================
                    # Adds emotion-matched background music even
                    # when the user did not choose to create a video.
                    # Also cached in `cached_result` so this doesn't
                    # get re-composed (and re-logged) on every rerun.

                    try:

                        if "story_with_music" not in cached_result:

                            with st.spinner(
                                f"🎵 Composing {detected_emotion} "
                                f"background music..."
                            ):

                                cached_result["story_with_music"] = (
                                    add_background_music_to_audio(
                                        audio_bytes,
                                        detected_emotion,
                                        output_path=(
                                            "storyverse_data/"
                                            "image_narration_with_music.mp3"
                                        )
                                    )
                                )

                            try:

                                log_story_to_excel({
                                    "Story ID": st.session_state.get(
                                        "current_story_id"
                                    ),
                                    "Background Music Added":
                                        "Yes"
                                        if cached_result["story_with_music"]
                                        else "No"
                                })

                            except Exception:
                                pass

                        story_with_music = cached_result["story_with_music"]

                        if story_with_music:

                            st.subheader(
                                "🎶 Story with Background Music"
                            )

                            st.audio(
                                story_with_music,
                                format="audio/mp3"
                            )

                            st.download_button(
                                label=
                                "⬇️ Download Story with Music",
                                data=story_with_music,
                                file_name=
                                "storyverse_story_with_music.mp3",
                                mime="audio/mpeg",
                                use_container_width=True,
                                key="image_music_download"
                            )

                        else:

                            st.info(
                                "Background music could not be "
                                "generated right now."
                            )

                    except Exception as music_error:

                        st.warning(
                            "Background music could not be "
                            "added to the narration."
                        )

                        st.caption(
                            f"Music details: {music_error}"
                        )

                except Exception as audio_error:

                    st.warning(
                        "Story was generated, "
                        "but audio could not "
                        "be created right now."
                    )

                    st.caption(
                        f"TTS details: "
                        f"{audio_error}"
                    )


                # =====================
                # VIDEO SCENES
                # =====================

                if create_video == (
                    "Yes - Create Full "
                    "AI Story Video"
                ):

                    cached_result = (
                        st.session_state.get(
                            "storyverse_result"
                        )
                    )

                    if (
                        cached_result
                        and
                        cached_result.get("scenes")
                    ):

                        scenes = (
                            cached_result["scenes"]
                        )

                    else:

                        with st.spinner(
                            "Creating AI video scenes..."
                        ):

                            scenes = (
                                generate_video_scenes(
                                    story,
                                    language,
                                    emotion=detected_emotion
                                )
                            )

                        if cached_result:

                            cached_result["scenes"] = (
                                scenes
                            )

                        st.session_state[
                            "generated_scenes"
                        ] = scenes

                        st.session_state[
                            "video_generated"
                        ] = True

                        st.success(
                            "Video scenes created successfully!"
                        )


                    st.subheader(
                        "🎬 AI Video Storyboard"
                    )

                    for index, scene in enumerate(scenes, start=1):

                        scene_number = scene.get("scene_number", index)
                        narration = scene.get("narration", "Narration not available.")
                        image_prompt = scene.get("image_prompt", "Image prompt not available.")

                        st.markdown(f"### 🎞️ Scene {scene_number}")
                        st.write("🎙️ Narration: " + narration)
                        st.write("🖼️ Image Prompt: " + image_prompt)

                        image_key = f"scene_image_{scene_number}"

                        if st.button(
                            f"🎨 Generate Scene {scene_number} Image",
                            key=f"generate_image_{scene_number}",
                            use_container_width=True
                        ):
                            try:
                                with st.spinner(f"Creating image for Scene {scene_number}..."):
                                    generated_image = generate_scene_image(image_prompt)
                                    st.session_state["scene_images"][image_key] = generated_image
                                st.success(f"Scene {scene_number} image created!")
                            except Exception as error:
                                st.error(f"Scene {scene_number} image could not be generated.")
                                st.caption(str(error))

                        if image_key in st.session_state["scene_images"]:
                            st.image(
                                st.session_state["scene_images"][image_key],
                                caption=f"AI Generated Image for Scene {scene_number}",
                                use_container_width=True
                            )

                    # ===================================================
                    # THIS BLOCK IS NOW OUTSIDE THE FOR LOOP - runs once
                    # after all scenes are listed, not after each image
                    # ===================================================

                    st.markdown("---")
                    st.divider()
                    st.markdown("### 🎬 Create Final AI Video")

                    total_scenes = len(scenes)
                    images_done = sum(
                        1 for scene in scenes
                        if f"scene_image_{scene.get('scene_number')}" in st.session_state["scene_images"]
                    )

                    st.caption(f"Images generated: {images_done} / {total_scenes}")

                    images_ready = images_done > 0
                    all_images_ready = images_done == total_scenes

                    if not all_images_ready:
                        st.info(
                            "You can generate the video with the images you have so far, "
                            "or generate the remaining scene images first for a complete video."
                        )

                    if st.button(
                        "🎬 Generate AI Video",
                        use_container_width=True,
                        disabled=not images_ready
                    ):
                        try:
                            with st.spinner(
                                "Rendering your AI video... this can take a minute or two."
                            ):
                                video_path = create_ai_video(
                                    scenes,
                                    st.session_state.scene_images,
                                    language,
                                    full_audio_bytes=audio_bytes,
                                    emotion=detected_emotion
                                )

                            st.session_state["video_generated"] = True
                            st.session_state["final_video_path"] = video_path

                            st.success("🎉 AI video created successfully!")

                            try:
                                log_story_to_excel({
                                    "Story ID": st.session_state.get(
                                        "current_story_id"
                                    ),
                                    "Video Created": "Yes",
                                    "Video File Path": video_path
                                })
                            except Exception:
                                pass

                        except Exception as error:
                            st.error("Video generation failed.")
                            st.caption(str(error))

                    if (
                        st.session_state.get("final_video_path")
                        and os.path.exists(st.session_state["final_video_path"])
                    ):
                        st.video(st.session_state["final_video_path"])

                        with open(st.session_state["final_video_path"], "rb") as video_file:
                            st.download_button(
                                label="⬇️ Download AI Video",
                                data=video_file.read(),
                                file_name="storyverse_ai_video.mp4",
                                mime="video/mp4",
                                use_container_width=True,
                                key="download_final_video"
                            )
                        


                st.markdown(
                    '</div>',
                    unsafe_allow_html=True
                )


            except Exception as error:

                error_text = str(error)

                if "429" in error_text:

                    st.error(
                        "Gemini free quota is currently exhausted. "
                        "Please wait for the retry time shown by Gemini "
                        "and then click Generate again."
                    )

                    st.caption(
                        "The app now uses fewer Gemini requests: "
                        "caption translation was merged into story generation."
                    )

                elif "503" in error_text:

                    st.warning(
                        "Gemini is temporarily busy. "
                        "Please try again after a short time."
                    )

                else:

                    st.error(
                        f"An error occurred: "
                        f"{error}"
                    )

    
# =================================
# OTHER PAGES
# =================================
elif page == "🌦️ Weather Story":

    st.markdown(
        """
        <div class="main-title">
        🌦️ Weather Story
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown(
        """
        <div class="main-subtitle">
        Enter a city and let real-time weather inspire a magical AI story
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown('<div class="story-card">', unsafe_allow_html=True)

    st.subheader("🌍 Choose Your City")

    weather_language = st.selectbox(
        "🌐 Choose Story Language",
        ["English", "Hindi (हिंदी)", "Marathi (मराठी)"],
        key="weather_language_select"
    )

    city_name = st.text_input(
        "🏙️ Enter City Name",
        placeholder="e.g. Mumbai, London, Tokyo"
    )

    weather_create_video = st.radio(
        "🎬 Do you want to create a video?",
        ["No - Generate Story Only", "Yes - Create Full AI Story Video"],
        key="weather_video_radio"
    )

    weather_generate_button = st.button(
        "🌦️ Generate Weather Story",
        use_container_width=True,
        key="weather_generate_button"
    )

    st.markdown('</div>', unsafe_allow_html=True)

    if (
        weather_generate_button
        or st.session_state.weatherstory_result is not None
    ):

        if not city_name or not city_name.strip():

            st.warning("Please enter a city name first.")

        elif not GEMINI_API_KEY:

            st.error("Gemini API key was not found.")

        else:

            try:

                # Only fetch fresh weather/reset story on a genuine
                # new button click - NOT on reruns from scene buttons
                if weather_generate_button:

                    with st.spinner("Fetching city location..."):

                        location = get_city_coordinates(city_name.strip())

                    with st.spinner("Fetching current weather..."):

                        weather = get_weather_data(
                            location["latitude"],
                            location["longitude"]
                        )

                    st.session_state.weatherstory_result = {
                        "city": location["name"],
                        "country": location["country"],
                        "weather": weather,
                        "language": weather_language,
                        "story": None,
                        "scenes": None,
                        "create_video": weather_create_video,
                        "main_image": None
                    }

                result = st.session_state.weatherstory_result

                city_display = result["city"]
                country_display = result["country"]
                weather = result["weather"]

                st.markdown('<div class="output-card">', unsafe_allow_html=True)

                st.subheader(f"📍 {city_display}, {country_display}")

                weather_col1, weather_col2 = st.columns(2)

                with weather_col1:
                    st.metric("🌡️ Temperature", f"{weather['temperature']}°C")

                with weather_col2:
                    st.metric("☁️ Condition", weather['description'].title())

                # =====================
                # MAIN WEATHER IMAGE (Pollinations)
                # =====================

                if result.get("main_image") is None:

                    with st.spinner("Painting the weather scene..."):

                        weather_image_prompt = build_weather_image_prompt(
                            city_display,
                            weather["description"],
                            weather["temperature"]
                        )

                        result["main_image"] = generate_pollination_image(
                            weather_image_prompt
                        )

                st.image(
                    result["main_image"],
                    caption=f"AI Visualization of {city_display}'s Weather",
                    use_container_width=True
                )

                # =====================
                # STORY GENERATION
                # =====================

                if result.get("story") is None:

                    with st.spinner("Gemini is writing your weather story..."):

                        result["story"] = generate_weather_story(
                            city_display,
                            weather["description"],
                            weather["temperature"],
                            weather_language
                        )

                story = result["story"]

                st.subheader("📖 Generated Story")
                st.write(story)

                st.download_button(
                    label="⬇️ Download Story",
                    data=story,
                    file_name="weather_story.txt",
                    mime="text/plain",
                    use_container_width=True,
                    key="weather_story_download"
                )

                # =====================
                # EMOTION DETECTION
                # =====================
                # Weather Story Mode has no image caption, so the
                # emotion is detected from the generated story text.

                if result.get("emotion") is None:

                    with st.spinner("🎭 Detecting story emotion..."):

                        weather_emotion_result = detect_emotion(story)

                    result["emotion"] = weather_emotion_result["emotion"]
                    result["emotion_score"] = weather_emotion_result["score"]

                detected_weather_emotion = result["emotion"]
                weather_emotion_score = result.get("emotion_score", 0)

                weather_emotion_icons = {
                    "joy": "😊",
                    "sadness": "😢",
                    "anger": "😡",
                    "fear": "😨",
                    "surprise": "😲",
                    "disgust": "🤢",
                    "anticipation": "🤩",
                    "trust": "🤝",
                    "neutral": "😐"
                }

                weather_emotion_icon = weather_emotion_icons.get(
                    detected_weather_emotion.lower(),
                    "🎭"
                )

                st.subheader("🎭 Detected Emotion")

                st.write(
                    f"{weather_emotion_icon} "
                    f"{detected_weather_emotion.title()}"
                )

                st.caption(
                    f"Emotion confidence/intensity: "
                    f"{weather_emotion_score:.2f}"
                )

                # =====================
                # AUDIO
                # =====================

                try:

                    with st.spinner("Creating audio..."):

                        weather_audio_file = generate_audio(
                            story,
                            weather_language
                        )

                    st.subheader("🎙️ Listen to Your Story")

                    st.audio(weather_audio_file, format="audio/mp3")

                    weather_audio_bytes = weather_audio_file.getvalue()

                    clean_title = re.sub(
                        r"^[#*\s]+",
                        "",
                        story.splitlines()[0]
                    ).strip()

                    if not clean_title:
                        clean_title = f"Weather Story - {city_display}"

                    already_saved = any(
                        saved_story["story"] == story
                        for saved_story in st.session_state["my_stories"]
                    )

                    if not already_saved:

                        import uuid
                        story_id = str(uuid.uuid4())

                        audio_path = save_audio_file(
                            weather_audio_bytes,
                            story_id
                        )

                        weather_new_story = {
                            "id": story_id,
                            "title": clean_title,
                            "language": weather_language,
                            "caption": f"{weather['description']} in {city_display}",
                            "story": story,
                            "audio_path": audio_path
                        }

                        st.session_state["my_stories"].append(weather_new_story)

                        save_stories_to_file(st.session_state["my_stories"])

                        st.success("💾 Story and audio saved permanently!")

                        st.session_state["current_weather_story_id"] = story_id

                        try:

                            log_story_to_excel({
                                "Story ID": story_id,
                                "Mode": "Weather-Based",
                                "Title": clean_title,
                                "Language": weather_language,
                                "Source / Prompt":
                                    f"{weather['description']} "
                                    f"in {city_display}",
                                "City": city_display,
                                "Weather Condition":
                                    weather["description"],
                                "Temperature (C)": weather["temperature"],
                                "Story Text": story,
                                "Detected Emotion": detected_weather_emotion,
                                "Emotion Confidence": round(
                                    weather_emotion_score, 3
                                ),
                                "Audio File Path": audio_path,
                                "Background Music Added": "No",
                                "Video Created": "No",
                                "Video File Path": ""
                            })

                        except Exception as excel_error:

                            st.caption(
                                f"Dataset logging skipped: "
                                f"{excel_error}"
                            )

                    # =================================
                    # BACKGROUND MUSIC (AUDIO-ONLY PATH)
                    # =================================
                    # Adds emotion-matched background music even
                    # when the user did not choose to create a video.

                    try:

                        with st.spinner(
                            f"🎵 Composing {detected_weather_emotion} "
                            f"background music..."
                        ):

                            weather_story_with_music = (
                                add_background_music_to_audio(
                                    weather_audio_bytes,
                                    detected_weather_emotion,
                                    output_path=(
                                        "storyverse_data/"
                                        "weather_narration_with_music.mp3"
                                    )
                                )
                            )

                        try:

                            log_story_to_excel({
                                "Story ID": st.session_state.get(
                                    "current_weather_story_id"
                                ),
                                "Background Music Added":
                                    "Yes" if weather_story_with_music
                                    else "No"
                            })

                        except Exception:
                            pass

                        if weather_story_with_music:

                            st.subheader(
                                "🎶 Story with Background Music"
                            )

                            st.audio(
                                weather_story_with_music,
                                format="audio/mp3"
                            )

                            st.download_button(
                                label=
                                "⬇️ Download Story with Music",
                                data=weather_story_with_music,
                                file_name=
                                "weather_story_with_music.mp3",
                                mime="audio/mpeg",
                                use_container_width=True,
                                key="weather_music_download"
                            )

                        else:

                            st.info(
                                "Background music could not be "
                                "generated right now."
                            )

                    except Exception as music_error:

                        st.warning(
                            "Background music could not be "
                            "added to the narration."
                        )

                        st.caption(
                            f"Music details: {music_error}"
                        )

                except Exception as audio_error:

                    st.warning(
                        "Story was generated, but audio could not "
                        "be created right now."
                    )
                    st.caption(f"TTS details: {audio_error}")

                # =====================
                # VIDEO SCENES
                # =====================

                if weather_create_video == "Yes - Create Full AI Story Video":

                    if result.get("scenes"):

                        scenes = result["scenes"]

                    else:

                        with st.spinner("Creating AI video scenes..."):

                            scenes = generate_video_scenes(
                                story,
                                weather_language,
                                emotion=result.get("emotion")
                            )

                        result["scenes"] = scenes

                        st.success("Video scenes created successfully!")

                    st.subheader("🎬 AI Video Storyboard")

                    for index, scene in enumerate(scenes, start=1):

                        scene_number = scene.get("scene_number", index)
                        narration = scene.get(
                            "narration", "Narration not available."
                        )
                        image_prompt = scene.get(
                            "image_prompt", "Image prompt not available."
                        )

                        st.markdown(f"### 🎞️ Scene {scene_number}")
                        st.write("🎙️ Narration: " + narration)
                        st.write("🖼️ Image Prompt: " + image_prompt)

                        image_key = f"weather_scene_image_{scene_number}"

                        if st.button(
                            f"🎨 Generate Scene {scene_number} Image",
                            key=f"weather_generate_image_{scene_number}",
                            use_container_width=True
                        ):
                            try:
                                with st.spinner(
                                    f"Creating image for Scene {scene_number}..."
                                ):
                                    generated_image = generate_pollination_image(
                                        image_prompt
                                    )

                                    st.session_state["weather_scene_images"][
                                        image_key
                                    ] = generated_image

                                st.success(f"Scene {scene_number} image created!")

                            except Exception as error:
                                st.error(
                                    f"Scene {scene_number} image could not "
                                    f"be generated."
                                )
                                st.caption(str(error))

                        if image_key in st.session_state["weather_scene_images"]:
                            st.image(
                                st.session_state["weather_scene_images"][image_key],
                                caption=f"AI Generated Image for Scene {scene_number}",
                                use_container_width=True
                            )

                    st.markdown("---")
                    st.divider()
                    st.markdown("### 🎬 Create Final AI Video")

                    total_scenes = len(scenes)
                    images_done = sum(
                        1 for scene in scenes
                        if f"weather_scene_image_{scene.get('scene_number')}"
                        in st.session_state["weather_scene_images"]
                    )

                    st.caption(f"Images generated: {images_done} / {total_scenes}")

                    images_ready = images_done > 0

                    if images_done < total_scenes:
                        st.info(
                            "You can generate the video with the images "
                            "you have so far, or generate the remaining "
                            "scene images first for a complete video."
                        )

                    if st.button(
                        "🎬 Generate AI Video",
                        use_container_width=True,
                        disabled=not images_ready,
                        key="weather_generate_video_button"
                    ):
                        try:
                            with st.spinner(
                                "Rendering your AI video... this can "
                                "take a minute or two."
                            ):
                                # create_ai_video expects keys shaped
                                # scene_image_{number} - remap here
                                remapped_images = {
                                    f"scene_image_{scene.get('scene_number')}":
                                    st.session_state["weather_scene_images"][
                                        f"weather_scene_image_{scene.get('scene_number')}"
                                    ]
                                    for scene in scenes
                                    if f"weather_scene_image_{scene.get('scene_number')}"
                                    in st.session_state["weather_scene_images"]
                                }

                                video_path = create_ai_video(
                                    scenes=scenes,
                                    scene_images=remapped_images,
                                    language=weather_language,
                                    output_path=
                                    "storyverse_data/weather_final_video.mp4",
                                    full_audio_bytes=weather_audio_bytes,
                                    emotion=result.get(
                                        "emotion", "joy"
                                    )
                                )

                            st.session_state["weather_final_video_path"] = video_path

                            st.success("🎉 AI video created successfully!")

                            try:
                                log_story_to_excel({
                                    "Story ID": st.session_state.get(
                                        "current_weather_story_id"
                                    ),
                                    "Video Created": "Yes",
                                    "Video File Path": video_path
                                })
                            except Exception:
                                pass

                        except Exception as error:
                            st.error("Video generation failed.")
                            st.caption(str(error))

                    if (
                        st.session_state.get("weather_final_video_path")
                        and os.path.exists(
                            st.session_state["weather_final_video_path"]
                        )
                    ):
                        st.video(st.session_state["weather_final_video_path"])

                        with open(
                            st.session_state["weather_final_video_path"], "rb"
                        ) as video_file:
                            st.download_button(
                                label="⬇️ Download AI Video",
                                data=video_file.read(),
                                file_name="weather_story_video.mp4",
                                mime="video/mp4",
                                use_container_width=True,
                                key="weather_download_final_video"
                            )

                st.markdown('</div>', unsafe_allow_html=True)

            except Exception as error:

                error_text = str(error)

                if "429" in error_text:
                    st.error(
                        "Gemini free quota is currently exhausted. "
                        "Please wait and try again."
                    )
                elif "503" in error_text:
                    st.warning(
                        "Gemini is temporarily busy. Please try again "
                        "after a short time."
                    )
                else:
                    st.error(f"An error occurred: {error}")

# =================================
# DATASET PAGE
# =================================

elif page == "📊 Dataset":

    st.markdown(
        """
        <div class="main-title">
        📊 StoryVerse Dataset
        </div>
        """,
        unsafe_allow_html=True
    )

    st.write(
        "Every story generated in Image Story Mode or Weather "
        "Story Mode logs one row here — story text, detected "
        "emotion, and the audio/music/video files produced for it."
    )

    if not EXCEL_DATASET_FILE.exists():

        st.info(
            "📊 No dataset rows yet — generate a story to "
            "start building it."
        )

    else:

        import pandas as pd

        try:

            dataset_df = pd.read_excel(EXCEL_DATASET_FILE)

        except Exception as read_error:

            st.error("Could not read the dataset file.")
            st.caption(str(read_error))

        else:

            stat_col1, stat_col2, stat_col3 = st.columns(3)

            with stat_col1:
                st.metric("Total Stories", len(dataset_df))

            with stat_col2:
                st.metric(
                    "With Background Music",
                    int(
                        (dataset_df["Background Music Added"] == "Yes")
                        .sum()
                    ) if "Background Music Added" in dataset_df
                    else 0
                )

            with stat_col3:
                st.metric(
                    "With Video",
                    int(
                        (dataset_df["Video Created"] == "Yes")
                        .sum()
                    ) if "Video Created" in dataset_df
                    else 0
                )

            st.divider()

            mode_options = ["All Modes"]

            if "Mode" in dataset_df:
                mode_options += sorted(
                    dataset_df["Mode"].dropna().unique().tolist()
                )

            selected_mode = st.selectbox(
                "Filter by Mode",
                mode_options
            )

            filtered_df = (
                dataset_df
                if selected_mode == "All Modes"
                else dataset_df[dataset_df["Mode"] == selected_mode]
            )

            st.dataframe(
                filtered_df,
                use_container_width=True,
                hide_index=True
            )

            st.divider()

            with open(EXCEL_DATASET_FILE, "rb") as dataset_file:
                dataset_bytes = dataset_file.read()

            st.download_button(
                label="⬇️ Download Full Dataset (Excel)",
                data=dataset_bytes,
                file_name="storyverse_dataset.xlsx",
                mime=(
                    "application/vnd.openxmlformats-officedocument"
                    ".spreadsheetml.sheet"
                ),
                use_container_width=True,
                key="dataset_page_download"
            )

elif page == "🧪 Data Science Dashboard":
    show_data_science_dashboard()
# =================================
# MY STORIES PAGE
# =================================

elif page == "📚 My Stories":

    st.markdown(
        """
        <div class="main-title">
        📚 My Stories
        </div>
        """,
        unsafe_allow_html=True
    )


    st.markdown(
        """
        <div class="main-subtitle">
        View, listen to and download
        your saved AI stories
        </div>
        """,
        unsafe_allow_html=True
    )


    if len(
        st.session_state["my_stories"]
    ) == 0:

        st.info(
            "No stories saved yet. "
            "Generate a new story "
            "from the Home page."
        )


    else:

        # Newest story first
        all_stories = (
            st.session_state[
                "my_stories"
            ][::-1]
        )


        for index, saved_story in enumerate(
            all_stories
        ):

            title = saved_story.get(
                "title",
                f"AI Story {index + 1}"
            )

            story_language = (
                saved_story.get(
                    "language",
                    "English"
                )
            )


            with st.expander(

                f"📖 {title} "
                f"— {story_language}",

                expanded=(
                    index == 0
                )

            ):


                st.subheader(
                    "🖼️ Image Description"
                )

                st.write(
                    saved_story.get(
                        "caption",
                        "Description not available."
                    )
                )


                st.subheader(
                    "📖 Story"
                )

                st.write(
                    saved_story.get(
                        "story",
                        ""
                    )
                )


                st.subheader(
                    "🎙️ Audio Narration"
                )

                saved_audio = (
                    load_audio_file(

                        saved_story.get(
                            "audio_path"
                        )

                    )
                )


                if saved_audio:

                    st.audio(

                        saved_audio,

                        format=
                        "audio/mp3"

                    )

                else:

                    st.warning(

                        "Audio is not "
                        "available."

                    )


                download_col1, download_col2 = (
                    st.columns(2)
                )


                with download_col1:

                    st.download_button(

                        label=
                        "⬇️ Download Story",

                        data=
                        saved_story[
                            "story"
                        ],

                        file_name=
                        f"story_{index + 1}.txt",

                        mime=
                        "text/plain",

                        key=
                        f"story_download_"
                        f"{index}"

                    )


                with download_col2:

                    saved_audio = (
                    load_audio_file(

                        saved_story.get(
                            "audio_path"
                        )

                    )
                )


                if saved_audio:

                    st.download_button(

                        label=
                        "⬇️ Download Audio",

                        data=
                        saved_audio,

                        file_name=
                        f"story_audio_"
                        f"{index + 1}.mp3",

                        mime=
                        "audio/mpeg",

                        key=
                        f"audio_download_"
                        f"{index}"

                    )


                if st.button(

                    "🗑️ Delete Story",

                    key=
                    f"delete_story_"
                    f"{index}",

                    use_container_width=
                    True

                ):

                    # Convert displayed index
                    # to original index

                    original_index = (

                        len(
                            st.session_state[
                                "my_stories"
                            ]
                        )

                        - 1

                        - index

                    )


                    deleted_story = (

                        st.session_state[
                            "my_stories"
                        ].pop(
                            original_index
                        )

                    )


                    # Delete audio file

                    deleted_audio_path = (

                        deleted_story.get(
                            "audio_path"
                        )

                    )


                    if (

                        deleted_audio_path

                        and

                        os.path.exists(
                            deleted_audio_path
                        )

                    ):

                        os.remove(
                            deleted_audio_path
                        )


                    # Update stories.json

                    save_stories_to_file(

                        st.session_state[
                            "my_stories"
                        ]

                    )


                    st.success(
                        "Story deleted permanently."
                    )


                    st.rerun()

elif page == "⭐ Favorites":

    st.title(
        "⭐ Favorites"
    )

    st.info(
        "Favorite stories will "
        "appear here."
    )


# =================================
# SETTINGS PAGE
# =================================

elif page == "⚙️ Settings":

    st.markdown(
        """
        <div class="main-title">
        ⚙️ Settings
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown(
        """
        <div class="main-subtitle">
        Customize your StoryVerse AI experience
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown(
        """
        <div class="story-card">
        """,
        unsafe_allow_html=True
    )

    st.subheader(
        "🎨 Appearance"
    )

    st.write(
        "Choose your preferred theme."
    )

    selected_theme = st.radio(

        "Select Theme",

        [
            "☀️ Light Mode",
            "🌙 Dark Mode"
        ],

        index=(
            0
            if
            st.session_state.theme
            == "Light"
            else
            1
        )
    )

    if selected_theme == "☀️ Light Mode":

        new_theme = "Light"

    else:

        new_theme = "Dark"


    if st.button(

        "💾 Apply Theme",

        use_container_width=True

    ):

        st.session_state.theme = (
            new_theme
        )

        st.rerun()


    st.markdown(
        """
        </div>
        """,
        unsafe_allow_html=True
    )


    st.markdown(
        """
        <div class="story-card">
        """,
        unsafe_allow_html=True
    )

    st.subheader(
        "ℹ️ Application Settings"
    )

    st.write(
        "StoryVerse AI uses:"
    )

    st.write(
        """
        🤖 Gemini AI for story generation

        🖼️ BLIP for image captioning

        🎙️ Edge TTS for audio narration

        🎬 AI storyboard for video scenes
        """
    )

    st.markdown(
        """
        </div>
        """,
        unsafe_allow_html=True
    )

elif page == "ℹ️ About":

    st.title(
        "ℹ️ About StoryVerse AI"
    )

    st.write(
       """

            📖 About StoryVerse AI ✨

           
               StoryVerse AI is where imagination meets
                Artificial Intelligence! 🚀
           
                Turn your ideas and images into beautiful, engaging stories
                with the power of AI.
            
                🤖 AI-Powered
                🌍 Multilingual
                🎨 Creative Stories
                🔊 AI Audio
          
                Made with ❤️ using
                Python, Streamlit, Gemini AI, BLIP, and gTTS
            
                ✨ Developed by Bhakti Gharat
        """
           
    )
    st.markdown(
        """
        ### 🔗 GitHub Repository

        View the complete source code here:

        [👉 Open StoryVerse AI on GitHub](https://github.com/your-username/StoryVerse-AI)
        """
        )