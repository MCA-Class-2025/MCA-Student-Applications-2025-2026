import os
import pandas as pd
from youtube_transcript_api import YouTubeTranscriptApi

def export_youtube_dataset(video_id):
    """
    Download a YouTube transcript and save it as a CSV dataset.
    Compatible with youtube-transcript-api v1.x
    """

    api = YouTubeTranscriptApi()

    # Fetch transcript
    transcript = api.fetch(video_id)

    # Convert transcript snippets into one text string
    text = " ".join([snippet.text for snippet in transcript])

    os.makedirs("datasets", exist_ok=True)

    df = pd.DataFrame([{
        "video_id": video_id,
        "title": "YouTube Video",
        "transcript": text
    }])

    df.to_csv("datasets/youtube_dataset.csv", index=False)

    print("YouTube dataset saved successfully.")

    return text

if __name__ == "__main__":
    text = export_youtube_dataset("dQw4w9WgXcQ")

    print(text[:500])