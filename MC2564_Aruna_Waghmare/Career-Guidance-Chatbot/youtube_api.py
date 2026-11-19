import requests


YOUTUBE_API_URL = "https://www.googleapis.com/youtube/v3/search"


def search_youtube(query, api_key, max_results=10):

    params = {
        "part": "snippet",
        "q": query,
        "type": "video",
        "maxResults": max_results,
        "key": api_key
    }

    try:

        response = requests.get(
            YOUTUBE_API_URL,
            params=params,
            timeout=15
        )

        if response.status_code == 400:

            return {
                "success": False,
                "message": "Invalid YouTube API key.",
                "videos": []
            }

        if response.status_code == 403:

            return {
                "success": False,
                "message": "YouTube API quota exceeded or API is not enabled.",
                "videos": []
            }

        if response.status_code != 200:

            return {
                "success": False,
                "message": f"YouTube API error: {response.status_code}",
                "videos": []
            }

        data = response.json()

        videos = []

        for item in data.get("items", []):

            video_id = item["id"]["videoId"]

            snippet = item["snippet"]

            videos.append({

                "title": snippet.get(
                    "title",
                    "Unknown Title"
                ),

                "description": snippet.get(
                    "description",
                    "No description available."
                ),

                "channel": snippet.get(
                    "channelTitle",
                    "Unknown Channel"
                ),

                "thumbnail": snippet.get(
                    "thumbnails",
                    {}
                ).get(
                    "medium",
                    {}
                ).get(
                    "url"
                ),

                "published": snippet.get(
                    "publishedAt",
                    ""
                ),

                "url":
                    f"https://www.youtube.com/watch?v={video_id}"
            })

        return {
            "success": True,
            "message": "Videos found successfully.",
            "videos": videos
        }

    except requests.exceptions.RequestException as e:

        return {
            "success": False,
            "message": str(e),
            "videos": []
        }