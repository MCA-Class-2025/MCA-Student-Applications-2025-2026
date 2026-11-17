"""
Background music: tries MusicAPI first (if configured), falls back
to a locally stored, emotion-matched track from background_music/.
"""

import os
import random
import time
import requests
from moviepy import AudioFileClip
from moviepy.audio.fx import AudioLoop

from .config import MUSICAPI_KEY, BACKGROUND_MUSIC_FOLDER
from .api_log import timed_api_call, log_api_call

MUSICAPI_BASE_URL = "https://api.musicapi.ai/api/v1"

EMOTION_MUSIC_PROMPTS = {
    "joy": "instrumental, no vocals, cheerful playful children's "
           "background music, happy magical melody",
    "sadness": "instrumental, no vocals, soft emotional background "
               "music, gentle piano, warm strings",
    "love": "instrumental, no vocals, warm heartwarming background "
            "music, soft piano, gentle strings",
    "anger": "instrumental, no vocals, dramatic energetic cinematic "
             "background music, strong percussion",
    "fear": "instrumental, no vocals, mysterious suspenseful "
            "cinematic background music, dark ambient sound",
    "surprise": "instrumental, no vocals, magical exciting "
                "adventurous background music, playful melody",
}

BACKGROUND_MUSIC_EXTENSIONS = (".mp3", ".wav", ".m4a", ".ogg")


def _generate_via_musicapi(
    emotion: str, duration: float, output_path: str
) -> str:

    if not MUSICAPI_KEY:
        raise RuntimeError("MUSICAPI_KEY is missing from .env")

    prompt = EMOTION_MUSIC_PROMPTS.get(
        emotion,
        "instrumental, no vocals, calm gentle cinematic background "
        "music for a children's story",
    )

    music_duration = max(1, min(int(duration), 240))

    headers = {
        "Authorization": f"Bearer {MUSICAPI_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "task_type": "create_music",
        "mv": "Lyria 3 Pro",
        "sound": prompt,
        "lyrics": "",
        "length": music_duration,
        "title": f"StoryVerse {emotion} background music",
    }

    with timed_api_call(
        "MusicAPI", f"{MUSICAPI_BASE_URL}/producer/create", prompt[:150]
    ):
        response = requests.post(
            f"{MUSICAPI_BASE_URL}/producer/create",
            headers=headers, json=payload, timeout=60,
        )

        if response.status_code >= 400:
            raise RuntimeError(
                f"MusicAPI error {response.status_code}: {response.text}"
            )

        task_id = response.json().get("task_id")

        if not task_id:
            raise RuntimeError("MusicAPI did not return a task ID.")

    return _wait_for_musicapi(task_id, output_path)


def _wait_for_musicapi(task_id: str, output_path: str, timeout: int = 180) -> str:

    headers = {"Authorization": f"Bearer {MUSICAPI_KEY}"}
    start_time = time.time()

    while time.time() - start_time < timeout:

        time.sleep(7)

        poll_start = time.time()

        response = requests.get(
            f"{MUSICAPI_BASE_URL}/producer/task/{task_id}",
            headers=headers, timeout=60,
        )

        if response.status_code >= 400:
            log_api_call(
                "MusicAPI", f"{MUSICAPI_BASE_URL}/producer/task/{{id}}",
                task_id, "failed", time.time() - poll_start,
                error=f"{response.status_code}: {response.text}",
            )
            raise RuntimeError(
                f"MusicAPI status error {response.status_code}: "
                f"{response.text}"
            )

        songs = response.json().get("data", [])

        if not songs:
            continue

        song = songs[0]
        state = song.get("state")

        if state == "succeeded":

            log_api_call(
                "MusicAPI", f"{MUSICAPI_BASE_URL}/producer/task/{{id}}",
                task_id, "success", time.time() - poll_start,
            )

            audio_url = song.get("audio_url") or song.get("wav_url")

            if not audio_url:
                raise RuntimeError("MusicAPI returned no audio URL.")

            with timed_api_call("MusicAPI", audio_url, "download generated track"):
                music_response = requests.get(audio_url, timeout=120)
                music_response.raise_for_status()

                os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

                with open(output_path, "wb") as file:
                    file.write(music_response.content)

            return output_path

        if state == "failed":
            log_api_call(
                "MusicAPI", f"{MUSICAPI_BASE_URL}/producer/task/{{id}}",
                task_id, "failed", time.time() - poll_start,
                error="generation failed",
            )
            raise RuntimeError("MusicAPI music generation failed.")

    raise RuntimeError("MusicAPI music generation timed out.")


def _pick_stored_music_file(emotion: str):

    def _list_tracks(folder):
        if not folder.exists():
            return []
        return [
            f for f in folder.iterdir()
            if f.is_file() and f.suffix.lower() in BACKGROUND_MUSIC_EXTENSIONS
        ]

    emotion_folder = BACKGROUND_MUSIC_FOLDER / (emotion or "neutral").lower()
    candidates = _list_tracks(emotion_folder)

    if not candidates:
        candidates = _list_tracks(BACKGROUND_MUSIC_FOLDER / "neutral")

    return random.choice(candidates) if candidates else None


def _generate_from_stored_folder(
    emotion: str, duration: float, output_path: str
) -> str:

    start_time = time.time()

    music_file = _pick_stored_music_file(emotion)

    if music_file is None:
        emotion_folder = BACKGROUND_MUSIC_FOLDER / (emotion or "neutral").lower()

        log_api_call(
            "Local Stored Music", str(emotion_folder), emotion,
            "failed", time.time() - start_time,
            error="no stored music files found",
        )

        raise RuntimeError(
            f"No stored background music found for '{emotion}' (or "
            f"'neutral'). Add royalty-free files to '{emotion_folder}'."
        )

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    music_duration = max(1.0, min(float(duration), 240.0))

    source_clip = AudioFileClip(str(music_file))

    try:
        if source_clip.duration > music_duration:
            trimmed_clip = source_clip.subclipped(0, music_duration)
        elif source_clip.duration < music_duration:
            trimmed_clip = AudioLoop(duration=music_duration).apply(source_clip)
        else:
            trimmed_clip = source_clip

        trimmed_clip.write_audiofile(output_path, logger=None)

        if trimmed_clip is not source_clip:
            trimmed_clip.close()
    finally:
        source_clip.close()

    log_api_call(
        "Local Stored Music", str(music_file), emotion,
        "success", time.time() - start_time,
    )

    return output_path


def generate_background_music(
    emotion: str,
    duration: float,
    output_path: str = "storyverse_data/background_music.mp3",
) -> str:
    """MusicAPI first (if MUSICAPI_KEY is set), stored-folder fallback."""

    try:
        return _generate_via_musicapi(emotion, duration, output_path)

    except Exception as api_error:
        print(f"MusicAPI unavailable, using stored music: {api_error}")

        return _generate_from_stored_folder(emotion, duration, output_path)
