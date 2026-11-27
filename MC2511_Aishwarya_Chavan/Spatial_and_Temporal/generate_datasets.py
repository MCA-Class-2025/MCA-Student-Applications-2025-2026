
import pandas as pd
import numpy as np
from pathlib import Path

# Output folder
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "datasets"
DATA_DIR.mkdir(exist_ok=True)

np.random.seed(42)

# ---------------- SPATIAL DATASET ----------------

locations = [
    ("Area_A", 18.5204, 73.8567),
    ("Area_B", 18.5314, 73.8446),
    ("Area_C", 18.5074, 73.8077),
    ("Area_D", 18.5679, 73.9143),
    ("Area_E", 18.4575, 73.8677),
    ("Area_F", 18.5913, 73.7389),
    ("Area_G", 18.6298, 73.7997),
    ("Area_H", 18.4890, 73.8320)
]

spatial_data = []

for i in range(200):
    area, lat, lon = locations[i % len(locations)]

    spatial_data.append({
        "Record_ID": f"SP{i+1:03d}",
        "Location": area,
        "Latitude": round(lat + np.random.normal(0, 0.002), 6),
        "Longitude": round(lon + np.random.normal(0, 0.002), 6),
        "Category": np.random.choice(["Low", "Medium", "High"]),
        "Event_Count": np.random.randint(5, 101),
        "Activity_Score": round(np.random.uniform(10, 100), 2)
    })

spatial_df = pd.DataFrame(spatial_data)
spatial_df.to_csv(DATA_DIR / "Spatial_Dataset.csv", index=False)

# ---------------- TEMPORAL DATASET ----------------

timestamps = pd.date_range(
    start="2026-01-01",
    periods=30 * 24,
    freq="h"
)

temporal_data = []

for i, timestamp in enumerate(timestamps):
    hour = timestamp.hour
    rush_hour = hour in [8, 9, 17, 18, 19]

    metric = (
        35
        + (28 if rush_hour else 0)
        + 10 * np.sin(2 * np.pi * hour / 24)
        + np.random.normal(0, 7)
    )

    temporal_data.append({
        "Record_ID": f"TM{i+1:04d}",
        "Timestamp": timestamp,
        "Date": timestamp.strftime("%Y-%m-%d"),
        "Hour": hour,
        "Day": timestamp.day_name(),
        "Metric_Value": round(max(0, metric), 2),
        "Event_Count": np.random.randint(5, 51),
        "Time_Category": (
            "Peak" if rush_hour else "Off-Peak"
        )
    })

temporal_df = pd.DataFrame(temporal_data)
temporal_df.to_csv(DATA_DIR / "Temporal_Dataset.csv", index=False)

# ---------------- OUTPUT ----------------

print("DATASETS GENERATED SUCCESSFULLY!")
print("--------------------------------")
print("Spatial Dataset Shape:", spatial_df.shape)
print("Temporal Dataset Shape:", temporal_df.shape)
print("Spatial file: datasets/Spatial_Dataset.csv")
print("Temporal file: datasets/Temporal_Dataset.csv")

print("\nSpatial Dataset Preview:")
print(spatial_df.head())

print("\nTemporal Dataset Preview:")
print(temporal_df.head())
