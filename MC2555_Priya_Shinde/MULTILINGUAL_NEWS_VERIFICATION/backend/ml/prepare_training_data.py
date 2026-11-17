from pathlib import Path

import pandas as pd

from sklearn.model_selection import train_test_split


# ============================================================
# PROJECT PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

INPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "multilingual_fake_news.csv"
)

OUTPUT_DIR = (
    PROJECT_ROOT
    / "data"
    / "processed"
)

TRAIN_FILE = OUTPUT_DIR / "train.csv"
TEST_FILE = OUTPUT_DIR / "test.csv"


# ============================================================
# SETTINGS
# ============================================================

RANDOM_STATE = 42
TEST_SIZE = 0.20


# ============================================================
# LOAD MASTER DATASET
# ============================================================

print("\n==============================================")
print(" PREPARING TRAINING AND TESTING DATA")
print("==============================================")

print("\nLoading master dataset...")

df = pd.read_csv(INPUT_FILE)

print(
    "Original records:",
    len(df)
)


# ============================================================
# BASIC CLEANING
# ============================================================

print("\n==============================================")
print("CLEANING DATA")
print("==============================================")

before = len(df)

df["text"] = (
    df["text"]
    .fillna("")
    .astype(str)
    .str.strip()
)

df = df[df["text"] != ""]

print(
    "Empty text removed:",
    before - len(df)
)


# ============================================================
# REMOVE VERY SHORT TEXT
# ============================================================

before = len(df)

df = df[
    df["text"].str.len() >= 20
]

print(
    "Very short records removed:",
    before - len(df)
)


# ============================================================
# REMOVE DUPLICATES AGAIN
# ============================================================

before = len(df)

df = df.drop_duplicates(
    subset=[
        "text",
        "language",
        "label"
    ]
).reset_index(drop=True)

print(
    "Duplicate records removed:",
    before - len(df)
)


# ============================================================
# SHOW CURRENT DISTRIBUTION
# ============================================================

print("\n==============================================")
print("MASTER DATASET DISTRIBUTION")
print("==============================================")

print("\nLanguage:")

print(
    df["language"].value_counts()
)

print("\nLanguage + Label:")

print(
    pd.crosstab(
        df["language"],
        df["label"]
    )
)


# ============================================================
# CREATE STRATIFICATION GROUP
# ============================================================

df["stratify_group"] = (
    df["language"]
    + "_"
    + df["label"]
)


print("\n==============================================")
print("STRATIFICATION GROUPS")
print("==============================================")

print(
    df["stratify_group"].value_counts()
)


# ============================================================
# TRAIN / TEST SPLIT
# ============================================================

print("\n==============================================")
print("CREATING TRAIN / TEST SPLIT")
print("==============================================")

train_df, test_df = train_test_split(
    df,
    test_size=TEST_SIZE,
    random_state=RANDOM_STATE,
    stratify=df["stratify_group"]
)


print(
    "\nTraining records before balancing:",
    len(train_df)
)

print(
    "Testing records:",
    len(test_df)
)


# ============================================================
# BALANCE ONLY MARATHI TRAINING DATA
# ============================================================

print("\n==============================================")
print("BALANCING TRAINING DATA")
print("==============================================")


balanced_parts = []


for language in [
    "English",
    "Hindi",
    "Marathi"
]:

    language_df = train_df[
        train_df["language"] == language
    ].copy()


    print("\n----------------------------------------------")
    print("Language:", language)
    print("----------------------------------------------")

    print(
        "\nBefore balancing:"
    )

    print(
        language_df["label"].value_counts()
    )


    # ========================================================
    # ENGLISH
    # ========================================================

    if language == "English":

        print(
            "\nEnglish is reasonably balanced."
        )

        print(
            "Keeping all English training records."
        )

        balanced_parts.append(
            language_df
        )


    # ========================================================
    # HINDI
    # ========================================================

    elif language == "Hindi":

        print(
            "\nHindi is reasonably balanced."
        )

        print(
            "Keeping all Hindi training records."
        )

        balanced_parts.append(
            language_df
        )


    # ========================================================
    # MARATHI
    # ========================================================

    elif language == "Marathi":

        fake_df = language_df[
            language_df["label"] == "Fake"
        ]

        real_df = language_df[
            language_df["label"] == "Real"
        ]


        print(
            "\nMarathi requires balancing."
        )

        print(
            "Fake:",
            len(fake_df)
        )

        print(
            "Real:",
            len(real_df)
        )


        target_count = min(
            len(fake_df),
            len(real_df)
        )


        print(
            "Using",
            target_count,
            "records from each class."
        )


        fake_sample = fake_df.sample(
            n=target_count,
            random_state=RANDOM_STATE
        )

        real_sample = real_df.sample(
            n=target_count,
            random_state=RANDOM_STATE
        )


        balanced_marathi = pd.concat(
            [
                fake_sample,
                real_sample
            ],
            ignore_index=True
        )


        balanced_parts.append(
            balanced_marathi
        )


# ============================================================
# COMBINE TRAINING DATA
# ============================================================

balanced_train_df = pd.concat(
    balanced_parts,
    ignore_index=True
)


# ============================================================
# SHUFFLE TRAINING DATA
# ============================================================

balanced_train_df = balanced_train_df.sample(
    frac=1,
    random_state=RANDOM_STATE
).reset_index(drop=True)


# ============================================================
# REMOVE HELPER COLUMN
# ============================================================

balanced_train_df = balanced_train_df.drop(
    columns=["stratify_group"]
)

test_df = test_df.drop(
    columns=["stratify_group"]
)


# ============================================================
# OUTPUT DIRECTORY
# ============================================================

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# ============================================================
# SAVE TRAINING DATA
# ============================================================

balanced_train_df.to_csv(
    TRAIN_FILE,
    index=False,
    encoding="utf-8-sig"
)


# ============================================================
# SAVE TEST DATA
# ============================================================

test_df.to_csv(
    TEST_FILE,
    index=False,
    encoding="utf-8-sig"
)


# ============================================================
# FINAL REPORT
# ============================================================

print("\n==============================================")
print(" DATA PREPARATION COMPLETED")
print("==============================================")


print(
    "\nBalanced training records:",
    len(balanced_train_df)
)

print(
    "Testing records:",
    len(test_df)
)


# ============================================================
# TRAINING DISTRIBUTION
# ============================================================

print("\n==============================================")
print("TRAINING LANGUAGE + LABEL")
print("==============================================")

print(
    pd.crosstab(
        balanced_train_df["language"],
        balanced_train_df["label"]
    )
)


# ============================================================
# TEST DISTRIBUTION
# ============================================================

print("\n==============================================")
print("TEST LANGUAGE + LABEL")
print("==============================================")

print(
    pd.crosstab(
        test_df["language"],
        test_df["label"]
    )
)


# ============================================================
# LANGUAGE COUNTS
# ============================================================

print("\n==============================================")
print("TRAINING LANGUAGE DISTRIBUTION")
print("==============================================")

print(
    balanced_train_df["language"].value_counts()
)


print("\n==============================================")
print("TESTING LANGUAGE DISTRIBUTION")
print("==============================================")

print(
    test_df["language"].value_counts()
)


# ============================================================
# SAVED FILES
# ============================================================

print("\n==============================================")
print("SAVED FILES")
print("==============================================")

print(
    "\nTraining file:"
)

print(
    TRAIN_FILE
)


print(
    "\nTesting file:"
)

print(
    TEST_FILE
)


print("\n==============================================")
print(" STEP 2 COMPLETED")
print("==============================================")