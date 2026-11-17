from pathlib import Path

import pandas as pd
from sklearn.model_selection import train_test_split


# ============================================================
# PROJECT PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

SOURCE_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "train.csv"
)

OUTPUT_DIR = (
    PROJECT_ROOT
    / "data"
    / "indicbert"
)

TRAIN_FILE = OUTPUT_DIR / "train.csv"
VALIDATION_FILE = OUTPUT_DIR / "validation.csv"


# ============================================================
# SETTINGS
# ============================================================

RANDOM_STATE = 42

# CPU-friendly first experiment.
# These are maximum TOTAL records per language.
MAX_ENGLISH = 16000
MAX_HINDI = 10000
MAX_MARATHI = 1132


# ============================================================
# CREATE OUTPUT DIRECTORY
# ============================================================

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# ============================================================
# LOAD DATA
# ============================================================

print("\n==============================================")
print(" INDICBERT DATA PREPARATION")
print("==============================================")

print("\nLoading dataset...")

df = pd.read_csv(
    SOURCE_FILE
)

print(
    "Original records:",
    len(df)
)


# ============================================================
# REQUIRED COLUMNS
# ============================================================

required_columns = [
    "text",
    "language",
    "label"
]

missing_columns = [
    column
    for column in required_columns
    if column not in df.columns
]

if missing_columns:

    raise ValueError(
        f"Missing columns: {missing_columns}"
    )


# ============================================================
# CLEAN DATA
# ============================================================

df = df[
    required_columns
].copy()

df["text"] = (
    df["text"]
    .fillna("")
    .astype(str)
    .str.strip()
)

df["language"] = (
    df["language"]
    .fillna("")
    .astype(str)
    .str.strip()
)

df["label"] = (
    df["label"]
    .fillna("")
    .astype(str)
    .str.strip()
)


# Remove empty text

df = df[
    df["text"].str.len() > 0
].copy()


# Keep only supported languages

df = df[
    df["language"].isin(
        [
            "English",
            "Hindi",
            "Marathi"
        ]
    )
].copy()


# Keep only the two labels

df = df[
    df["label"].isin(
        [
            "Fake",
            "Real"
        ]
    )
].copy()


# ============================================================
# DISPLAY ORIGINAL DISTRIBUTION
# ============================================================

print("\nOriginal distribution:")

print(
    df.groupby(
        [
            "language",
            "label"
        ]
    ).size()
)


# ============================================================
# BALANCED LANGUAGE SUBSETS
# ============================================================

def create_language_subset(
    data,
    language,
    maximum
):

    language_df = data[
        data["language"] == language
    ].copy()

    fake_df = language_df[
        language_df["label"] == "Fake"
    ]

    real_df = language_df[
        language_df["label"] == "Real"
    ]

    # Equal number from both classes

    n = min(
        len(fake_df),
        len(real_df)
    )

    # Apply maximum total records

    max_per_class = maximum // 2

    n = min(
        n,
        max_per_class
    )

    fake_sample = fake_df.sample(
        n=n,
        random_state=RANDOM_STATE
    )

    real_sample = real_df.sample(
        n=n,
        random_state=RANDOM_STATE
    )

    result = pd.concat(
        [
            fake_sample,
            real_sample
        ],
        ignore_index=True
    )

    return result


# ============================================================
# CREATE SUBSETS
# ============================================================

english_df = create_language_subset(
    df,
    "English",
    MAX_ENGLISH
)

hindi_df = create_language_subset(
    df,
    "Hindi",
    MAX_HINDI
)

marathi_df = create_language_subset(
    df,
    "Marathi",
    MAX_MARATHI
)


# ============================================================
# COMBINE
# ============================================================

selected_df = pd.concat(
    [
        english_df,
        hindi_df,
        marathi_df
    ],
    ignore_index=True
)


# ============================================================
# SHUFFLE
# ============================================================

selected_df = selected_df.sample(
    frac=1,
    random_state=RANDOM_STATE
).reset_index(
    drop=True
)


# ============================================================
# TRAIN / VALIDATION SPLIT
# ============================================================

train_df, validation_df = train_test_split(
    selected_df,
    test_size=0.10,
    random_state=RANDOM_STATE,
    stratify=selected_df[
        [
            "language",
            "label"
        ]
    ]
)


# ============================================================
# SAVE
# ============================================================

train_df.to_csv(
    TRAIN_FILE,
    index=False
)

validation_df.to_csv(
    VALIDATION_FILE,
    index=False
)


# ============================================================
# RESULTS
# ============================================================

print("\n==============================================")
print(" PREPARATION COMPLETED")
print("==============================================")

print(
    "\nSelected records:",
    len(selected_df)
)

print(
    "Training records:",
    len(train_df)
)

print(
    "Validation records:",
    len(validation_df)
)


print("\nTraining distribution:")

print(
    train_df.groupby(
        [
            "language",
            "label"
        ]
    ).size()
)


print("\nValidation distribution:")

print(
    validation_df.groupby(
        [
            "language",
            "label"
        ]
    ).size()
)


print("\nSaved files:")

print(
    TRAIN_FILE
)

print(
    VALIDATION_FILE
)

print("\n==============================================")
print(" READY FOR INDICBERT TRAINING")
print("==============================================")