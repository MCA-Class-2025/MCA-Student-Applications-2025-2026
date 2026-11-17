"""
Final video assembly: Ken Burns effect on scene images + narration
audio + emotion-based background music.
"""

import os
import random
import subprocess
import tempfile
import time
import gc

import numpy as np
import imageio_ffmpeg
from PIL import Image
from moviepy import (
    AudioFileClip, CompositeAudioClip, ImageClip, concatenate_videoclips,
)
from moviepy.audio.fx import AudioLoop

from .music import generate_background_music


def apply_ken_burns(pil_image, duration, video_size=(1280, 720), fps=24):

    zoom_margin = 1.25
    base_w = int(video_size[0] * zoom_margin)
    base_h = int(video_size[1] * zoom_margin)

    img_resized = pil_image.copy()
    img_resized.thumbnail((base_w, base_h), Image.LANCZOS)

    oversized_canvas = Image.new("RGB", (base_w, base_h), (0, 0, 0))
    offset = (
        (base_w - img_resized.width) // 2,
        (base_h - img_resized.height) // 2,
    )
    oversized_canvas.paste(img_resized, offset)

    frame_array = np.array(oversized_canvas)
    source_h, source_w = frame_array.shape[:2]
    target_w, target_h = video_size

    zoom_in = random.choice([True, False])
    pan_x = random.choice([-1, 0, 1])
    pan_y = random.choice([-1, 0, 1])

    start_scale = 1.0 if zoom_in else 1.15
    end_scale = 1.15 if zoom_in else 1.0

    def make_frame(t):
        progress = min(max(t / duration if duration > 0 else 0, 0), 1)
        scale = start_scale + (end_scale - start_scale) * progress

        crop_w = min(int(target_w * scale), source_w)
        crop_h = min(int(target_h * scale), source_h)

        max_x_offset = source_w - crop_w
        max_y_offset = source_h - crop_h

        x_shift = pan_x * max_x_offset / 2 * progress
        y_shift = pan_y * max_y_offset / 2 * progress

        x1 = int(max(0, min(max_x_offset, max_x_offset / 2 + x_shift)))
        y1 = int(max(0, min(max_y_offset, max_y_offset / 2 + y_shift)))

        cropped = frame_array[y1 : y1 + crop_h, x1 : x1 + crop_w]
        pil_frame = Image.fromarray(cropped).resize(
            (target_w, target_h), Image.LANCZOS
        )
        return np.array(pil_frame)

    clip = ImageClip(make_frame(0)).with_duration(duration)
    clip = clip.transform(lambda gf, t: make_frame(t))
    return clip.with_fps(fps)


def _get_accurate_audio_duration_and_clip(mp3_bytes, temp_dir):
    """Re-mux MP3 -> WAV so moviepy/ffmpeg reports the true duration."""

    mp3_path = os.path.join(temp_dir, "narration_source.mp3")
    wav_path = os.path.join(temp_dir, "narration_fixed.wav")

    with open(mp3_path, "wb") as mp3_file:
        mp3_file.write(mp3_bytes)

    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()

    subprocess.run(
        [ffmpeg_exe, "-y", "-i", mp3_path, "-ar", "44100", "-ac", "2", wav_path],
        check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )

    return AudioFileClip(wav_path), wav_path, mp3_path


def create_ai_video(
    scenes: list,
    scene_images: dict,
    full_audio_bytes: bytes,
    emotion: str = "joy",
    output_path: str = "storyverse_data/final_video.mp4",
    fps: int = 24,
    video_size=(1280, 720),
) -> str:
    """
    scene_images: {"scene_image_<n>": PIL.Image, ...}
    Returns the output video path.
    """

    clips = []
    audio_clip = None
    temp_dir_obj = None

    try:
        available_images = [
            (scene, scene_images[f"scene_image_{scene.get('scene_number')}"])
            for scene in scenes
            if f"scene_image_{scene.get('scene_number')}" in scene_images
        ]

        if not available_images:
            raise ValueError("No scene images available.")

        if not full_audio_bytes:
            raise ValueError("Full story audio is not available.")

        temp_dir_obj = tempfile.TemporaryDirectory()

        audio_clip, wav_path, mp3_path = _get_accurate_audio_duration_and_clip(
            full_audio_bytes, temp_dir_obj.name
        )

        total_audio_duration = audio_clip.duration
        scene_duration = total_audio_duration / len(available_images)

        for _, pil_image in available_images:
            clips.append(
                apply_ken_burns(
                    pil_image.convert("RGB"),
                    duration=scene_duration,
                    video_size=video_size,
                    fps=fps,
                )
            )

        final_video = concatenate_videoclips(clips, method="compose")
        final_video = final_video.with_audio(audio_clip)

        # Background music (best-effort; video still works without it)
        try:
            music_path = generate_background_music(
                emotion=emotion,
                duration=final_video.duration,
                output_path="storyverse_data/background_music.mp3",
            )

            music_clip = AudioFileClip(music_path)

            if music_clip.duration > final_video.duration:
                music_clip = music_clip.subclipped(0, final_video.duration)
            elif music_clip.duration < final_video.duration:
                music_clip = AudioLoop(duration=final_video.duration).apply(
                    music_clip
                )

            music_clip = music_clip.with_volume_scaled(0.12)

            final_audio = (
                CompositeAudioClip([final_video.audio, music_clip])
                if final_video.audio
                else music_clip
            )

            final_video = final_video.with_audio(final_audio)

        except Exception as music_error:
            print(f"Background music skipped: {music_error}")

        final_video.write_videofile(
            output_path, fps=fps, codec="libx264", audio_codec="aac", logger=None
        )
        final_video.close()

        return output_path

    finally:
        for clip in clips:
            try:
                clip.close()
            except Exception:
                pass

        if audio_clip:
            try:
                audio_clip.close()
            except Exception:
                pass

        gc.collect()
        time.sleep(0.5)

        if temp_dir_obj:
            for _ in range(3):
                try:
                    temp_dir_obj.cleanup()
                    break
                except PermissionError:
                    time.sleep(0.5)
                except Exception:
                    break
