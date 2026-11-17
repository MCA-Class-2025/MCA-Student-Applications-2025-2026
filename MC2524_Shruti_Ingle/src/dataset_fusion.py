import os
import json
import pandas as pd

DATASET_DIR = "datasets"

def safe_read(path):
    """
    Safely read a CSV file. If the file is missing or empty,
    return an empty DataFrame.
    """

    if not os.path.exists(path):
        return pd.DataFrame()

    try:
        return pd.read_csv(path)
    except pd.errors.EmptyDataError:
        return pd.DataFrame()

def fuse_datasets():
    drive = safe_read(os.path.join(DATASET_DIR, "google_drive_dataset.csv"))
    github = safe_read(os.path.join(DATASET_DIR, "github_dataset.csv"))
    youtube = safe_read(os.path.join(DATASET_DIR, "youtube_dataset.csv"))
    gemini = safe_read(os.path.join(DATASET_DIR, "gemini_dataset.csv"))
    duck = safe_read(os.path.join(DATASET_DIR, "duckduckgo_dataset.csv"))

    fused = []

    # Google Drive
    for _, row in drive.iterrows():
        fused.append({
            "source_type": "Google Drive",
            "title": row.get("name", ""),
            "content": row.get("mimeType", ""),
            "url": "",
            "language": "",
            "modified_time": row.get("modifiedTime", ""),
            "metadata": json.dumps(row.to_dict())
        })

    # GitHub
    for _, row in github.iterrows():
        fused.append({
            "source_type": "GitHub",
            "title": row.get("repo_name", ""),
            "content": row.get("description", ""),
            "url": row.get("url", ""),
            "language": row.get("language", ""),
            "modified_time": row.get("updated_at", ""),
            "metadata": json.dumps(row.to_dict())
        })

    # YouTube
    for _, row in youtube.iterrows():
        fused.append({
            "source_type": "YouTube",
            "title": row.get("title", ""),
            "content": row.get("transcript", ""),
            "url": f"https://www.youtube.com/watch?v={row.get('video_id', '')}",
            "language": "",
            "modified_time": "",
            "metadata": json.dumps(row.to_dict())
        })

    # Gemini
    for _, row in gemini.iterrows():
        fused.append({
            "source_type": "Gemini Vision",
            "title": row.get("image_name", ""),
            "content": row.get("analysis", ""),
            "url": "",
            "language": "",
            "modified_time": "",
            "metadata": json.dumps(row.to_dict())
        })

    # DuckDuckGo
    for _, row in duck.iterrows():
        fused.append({
            "source_type": "DuckDuckGo",
            "title": row.get("title", ""),
            "content": row.get("snippet", ""),
            "url": row.get("url", ""),
            "language": "",
            "modified_time": "",
            "metadata": json.dumps(row.to_dict())
        })

    fused_df = pd.DataFrame(fused)

    output = os.path.join(DATASET_DIR, "fused_knowledge_dataset.csv")
    fused_df.to_csv(output, index=False)

    print(f"Fused dataset created: {output}")
    print(f"Total records: {len(fused_df)}")

    return fused_df

if __name__ == "__main__":
    fuse_datasets()