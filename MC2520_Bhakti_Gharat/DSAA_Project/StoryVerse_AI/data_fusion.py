import pandas as pd

# ==========================================
# 1. LOAD CSV FILES
# ==========================================

emotion_df = pd.read_csv("emotion_dataset.csv")
api_df = pd.read_csv("api_calls.csv")

print("Emotion Dataset Shape:", emotion_df.shape)
print("API Calls Dataset Shape:", api_df.shape)

print("\nEmotion Dataset Columns:")
print(emotion_df.columns.tolist())

print("\nAPI Calls Columns:")
print(api_df.columns.tolist())


# ==========================================
# 2. CLEAN COLUMN NAMES
# ==========================================

emotion_df.columns = (
    emotion_df.columns
    .str.strip()
    .str.lower()
    .str.replace(" ", "_")
)

api_df.columns = (
    api_df.columns
    .str.strip()
    .str.lower()
    .str.replace(" ", "_")
)


# ==========================================
# 3. CHECK EMOTION COLUMN
# ==========================================

if "emotion" not in emotion_df.columns:
    raise ValueError(
        "Emotion dataset does not contain an 'emotion' column."
    )

if "emotion" not in api_df.columns:
    raise ValueError(
        "API Calls CSV does not contain an 'emotion' column."
    )


# ==========================================
# 4. NORMALIZE EMOTION VALUES
# ==========================================

emotion_df["emotion"] = (
    emotion_df["emotion"]
    .astype(str)
    .str.strip()
    .str.lower()
)

api_df["emotion"] = (
    api_df["emotion"]
    .astype(str)
    .str.strip()
    .str.lower()
)


# ==========================================
# 5. FUSE / MERGE DATA
# ==========================================

fused_df = pd.merge(
    emotion_df,
    api_df,
    on="emotion",
    how="inner",
    suffixes=("_dataset", "_api")
)


# ==========================================
# 6. REMOVE DUPLICATES
# ==========================================

fused_df = fused_df.drop_duplicates()


# ==========================================
# 7. SAVE FUSED DATASET
# ==========================================

fused_df.to_csv(
    "storyverse_fused_dataset.csv",
    index=False
)


# ==========================================
# 8. DISPLAY RESULTS
# ==========================================

print("\n===================================")
print("DATA FUSION COMPLETED")
print("===================================")

print("Original Emotion Dataset:",
      emotion_df.shape)

print("Original API Dataset:",
      api_df.shape)

print("Fused Dataset:",
      fused_df.shape)

print("\nFused Columns:")
print(fused_df.columns.tolist())

print("\nFirst 5 Fused Records:")
print(fused_df.head())

print("\nFused Dataset saved as:")
print("storyverse_fused_dataset.csv")