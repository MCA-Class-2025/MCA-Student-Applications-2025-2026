import os
import requests
from dotenv import load_dotenv

load_dotenv()

YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

BASE_URL = "https://www.googleapis.com/youtube/v3/search"


def search_movie_trailer(movie_title):

    if not YOUTUBE_API_KEY:
        print("YouTube API key not found.")
        return None

    params = {
        "part": "snippet",
        "q": f"{movie_title} official trailer",
        "type": "video",
        "maxResults": 1,
        "key": YOUTUBE_API_KEY
    }

    try:
        response = requests.get(
            BASE_URL,
            params=params,
            timeout=10
        )

        response.raise_for_status()

        data = response.json()

        results = data.get("items", [])

        if not results:
            print("Trailer not found.")
            return None

        video = results[0]

        video_id = video["id"]["videoId"]

        return {
            "video_id": video_id,
            "title": video["snippet"]["title"],
            "channel": video["snippet"]["channelTitle"],
            "thumbnail": video["snippet"]["thumbnails"]["high"]["url"],
            "youtube_url": f"https://www.youtube.com/watch?v={video_id}"
        }

    except requests.RequestException as e:
        print("YouTube API Error:", e)
        return None