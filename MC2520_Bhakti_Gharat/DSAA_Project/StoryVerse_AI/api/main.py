"""
StoryVerse AI - Single Unified REST API

ONE endpoint runs the entire pipeline end-to-end:
  image caption OR weather lookup
    -> emotion detection
    -> story generation (Gemini + free Groq fallback)
    -> audio narration (Edge TTS)
    -> background music (MusicAPI + free stored-track fallback)
    -> [optional] scene storyboard + scene images (Pollinations)
    -> [optional] final video render
    -> dataset row logged

Because that whole chain is slow (video render especially), the
endpoint kicks it off as a background job and returns a job_id
immediately. Poll /jobs/{job_id} until status == "done", then
download whatever files the result links to.

Run locally:
    uvicorn api.main:app --reload

Interactive docs:
    http://localhost:8000/docs

Every request needs a header:
    X-API-Key: <your STORYVERSE_API_KEY from .env>
"""

import io
import uuid
import threading
import traceback
from typing import Optional

from fastapi import (
    FastAPI, UploadFile, File, Form, Header, HTTPException, Depends
)
from fastapi.responses import FileResponse
from PIL import Image
from moviepy import AudioFileClip

from storyverse_core.config import STORYVERSE_API_KEY, DATA_FOLDER
from storyverse_core.emotion import detect_emotion
from storyverse_core.image import generate_caption, generate_scene_image
from storyverse_core.story import (
    generate_story, generate_weather_story, generate_video_scenes,
)
from storyverse_core.weather import get_city_coordinates, get_weather_data
from storyverse_core.audio import generate_audio
from storyverse_core.music import generate_background_music
from storyverse_core.video import create_ai_video
from storyverse_core.dataset import log_story_to_excel, EXCEL_DATASET_FILE

app = FastAPI(
    title="StoryVerse AI API",
    description=(
        "One endpoint: send an image OR a city, get back a full "
        "AI story with narration, music, and (optionally) video."
    ),
    version="2.0.0",
)


# =================================
# AUTH
# =================================

def require_api_key(x_api_key: Optional[str] = Header(None)):
    if STORYVERSE_API_KEY and x_api_key != STORYVERSE_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid or missing X-API-Key.")
    return True


# =================================
# IN-MEMORY JOB STORE
# (swap for Redis/DB if you deploy with multiple worker processes)
# =================================

_jobs: dict = {}
_jobs_lock = threading.Lock()


def _new_job() -> str:
    job_id = str(uuid.uuid4())
    with _jobs_lock:
        _jobs[job_id] = {"status": "pending", "stage": "queued", "result": None, "error": None}
    return job_id


def _set_job(job_id: str, **fields):
    with _jobs_lock:
        _jobs[job_id].update(fields)


# =================================
# THE ENTIRE PIPELINE, ONE FUNCTION
# =================================

def _run_full_pipeline(
    job_id: str,
    image_bytes: Optional[bytes],
    city: Optional[str],
    language: str,
    create_video: bool,
):

    try:
        _set_job(job_id, status="running", stage="analyzing input")

        story_id = str(uuid.uuid4())

        # ---- Step 1: caption (image mode) OR weather (weather mode) ----

        if image_bytes:

            mode = "Image Upload"

            pil_image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
            caption = generate_caption(pil_image)

            _set_job(job_id, stage="detecting emotion")
            emotion_result = detect_emotion(caption)

            _set_job(job_id, stage="writing story")
            story = generate_story(caption, language, emotion_result["emotion"])

            source_prompt = caption
            city_name = ""
            weather_condition = ""
            temperature = ""

        elif city:

            mode = "Weather-Based"

            location = get_city_coordinates(city)
            weather = get_weather_data(location["latitude"], location["longitude"])

            _set_job(job_id, stage="writing story")
            story = generate_weather_story(
                location["name"], weather["description"],
                weather["temperature"], language,
            )

            _set_job(job_id, stage="detecting emotion")
            emotion_result = detect_emotion(story)

            source_prompt = f"{weather['description']} in {location['name']}"
            city_name = location["name"]
            weather_condition = weather["description"]
            temperature = weather["temperature"]

        else:
            raise ValueError("Provide either an image or a city.")

        detected_emotion = emotion_result["emotion"]
        emotion_score = emotion_result["score"]

        # ---- Step 2: audio narration ----

        _set_job(job_id, stage="generating audio narration")
        audio_bytes = generate_audio(story, language)

        audio_path = DATA_FOLDER / "audio" / f"{story_id}.mp3"
        audio_path.write_bytes(audio_bytes)

        audio_clip = AudioFileClip(str(audio_path))
        audio_duration = audio_clip.duration
        audio_clip.close()

        result = {
            "story_id": story_id,
            "mode": mode,
            "language": language,
            "source_prompt": source_prompt,
            "city": city_name,
            "weather_condition": weather_condition,
            "temperature": temperature,
            "detected_emotion": detected_emotion,
            "emotion_score": emotion_score,
            "story": story,
            "audio_download_url": f"/download/audio/{story_id}",
            "music_download_url": None,
            "scenes": None,
            "video_download_url": None,
        }

        # Log the story row right away so it's captured even if a
        # later step (music/video) fails.
        log_story_to_excel({
            "Story ID": story_id,
            "Mode": mode,
            "Title": story.splitlines()[0].strip("# *") or "AI Story",
            "Language": language,
            "Source / Prompt": source_prompt,
            "City": city_name,
            "Weather Condition": weather_condition,
            "Temperature (C)": temperature,
            "Story Text": story,
            "Detected Emotion": detected_emotion,
            "Emotion Confidence": round(emotion_score, 3),
            "Audio File Path": str(audio_path),
            "Background Music Added": "No",
            "Video Created": "No",
            "Video File Path": "",
        })

        # ---- Step 3: background music (best-effort, non-fatal) ----

        _set_job(job_id, stage="composing background music")

        try:
            music_path = DATA_FOLDER / f"music_{story_id}.mp3"
            generate_background_music(
                detected_emotion, audio_duration, str(music_path)
            )
            result["music_download_url"] = f"/download/music/{story_id}"

            log_story_to_excel({
                "Story ID": story_id, "Background Music Added": "Yes"
            })

        except Exception as music_error:
            print(f"Background music skipped: {music_error}")

        # ---- Step 4 (optional): scenes + images + video ----

        if create_video:

            _set_job(job_id, stage="writing storyboard scenes")
            scenes = generate_video_scenes(story, language, detected_emotion)
            result["scenes"] = scenes

            scene_images = {}

            for index, scene in enumerate(scenes, start=1):
                _set_job(
                    job_id,
                    stage=f"illustrating scene {index}/{len(scenes)}",
                )
                scene_number = scene.get("scene_number", index)
                image = generate_scene_image(scene.get("image_prompt", ""))
                scene_images[f"scene_image_{scene_number}"] = image

            _set_job(job_id, stage="rendering final video")

            video_path = DATA_FOLDER / f"video_{story_id}.mp4"

            create_ai_video(
                scenes, scene_images, audio_bytes,
                emotion=detected_emotion, output_path=str(video_path),
            )

            result["video_download_url"] = f"/download/video/{story_id}"

            log_story_to_excel({
                "Story ID": story_id,
                "Video Created": "Yes",
                "Video File Path": str(video_path),
            })

        _set_job(job_id, status="done", stage="complete", result=result)

    except Exception as error:
        traceback.print_exc()
        _set_job(job_id, status="failed", stage="failed", error=str(error))


# =================================
# THE ONE ENDPOINT
# =================================

@app.post("/generate", dependencies=[Depends(require_api_key)])
async def generate(
    image: Optional[UploadFile] = File(None),
    city: Optional[str] = Form(None),
    language: str = Form("English"),
    create_video: bool = Form(False),
):
    """
    Send EITHER an image file OR a city name (not both). Returns a
    job_id immediately - poll GET /jobs/{job_id} until status is
    "done", then use the download URLs in the result.
    """

    if not image and not city:
        raise HTTPException(
            status_code=400, detail="Provide either 'image' or 'city'."
        )

    image_bytes = await image.read() if image else None

    job_id = _new_job()

    thread = threading.Thread(
        target=_run_full_pipeline,
        args=(job_id, image_bytes, city, language, create_video),
        daemon=True,
    )
    thread.start()

    return {"job_id": job_id, "status_url": f"/jobs/{job_id}"}


@app.get("/jobs/{job_id}", dependencies=[Depends(require_api_key)])
def get_job(job_id: str):
    job = _jobs.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found.")
    return job


# =================================
# FILE DOWNLOADS
# =================================

@app.get("/download/audio/{story_id}", dependencies=[Depends(require_api_key)])
def download_audio(story_id: str):
    path = DATA_FOLDER / "audio" / f"{story_id}.mp3"
    if not path.exists():
        raise HTTPException(status_code=404, detail="Audio not found.")
    return FileResponse(path, media_type="audio/mpeg")


@app.get("/download/music/{story_id}", dependencies=[Depends(require_api_key)])
def download_music(story_id: str):
    path = DATA_FOLDER / f"music_{story_id}.mp3"
    if not path.exists():
        raise HTTPException(status_code=404, detail="Music not found.")
    return FileResponse(path, media_type="audio/mpeg")


@app.get("/download/video/{story_id}", dependencies=[Depends(require_api_key)])
def download_video(story_id: str):
    path = DATA_FOLDER / f"video_{story_id}.mp4"
    if not path.exists():
        raise HTTPException(status_code=404, detail="Video not found.")
    return FileResponse(path, media_type="video/mp4")


@app.get("/download/dataset", dependencies=[Depends(require_api_key)])
def download_dataset():
    if not EXCEL_DATASET_FILE.exists():
        raise HTTPException(status_code=404, detail="No dataset yet.")
    return FileResponse(
        EXCEL_DATASET_FILE,
        media_type=(
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        ),
        filename="storyverse_dataset.xlsx",
    )


@app.get("/health")
def health():
    return {"status": "ok"}
