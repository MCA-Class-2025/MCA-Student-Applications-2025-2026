"""
Opens a Pixabay Music search page for each emotion folder used by
background_music/<emotion>/, one browser tab at a time (with a
short pause between each so your browser doesn't block popups).

Usage:
    python open_music_sources.py

Then for each tab: pick 1-3 tracks you like, click Download (MP3),
and save the file straight into the matching background_music/
subfolder next to app.py. No renaming needed.
"""

import time
import webbrowser

EMOTION_SEARCHES = {
    "joy": "happy upbeat",
    "sadness": "sad emotional piano",
    "love": "romantic warm",
    "anger": "intense dramatic",
    "fear": "tense suspense",
    "surprise": "playful adventure",
    "neutral": "calm ambient background",
}

BASE_URL = "https://pixabay.com/music/search/{query}/"


def main():
    for emotion, query in EMOTION_SEARCHES.items():
        url = BASE_URL.format(query=query.replace(" ", "%20"))
        print(f"Opening '{emotion}' -> {url}")
        webbrowser.open_new_tab(url)
        time.sleep(1.5)  # small gap so tabs open cleanly


if __name__ == "__main__":
    main()