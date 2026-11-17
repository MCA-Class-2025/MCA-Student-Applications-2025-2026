from pathlib import Path
import pandas as pd
import csv


# ============================================================
# PROJECT PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

RAW_DIR = PROJECT_ROOT / "data" / "raw"

OUTPUT_DIR = PROJECT_ROOT / "data" / "processed"

OUTPUT_FILE = OUTPUT_DIR / "multilingual_fake_news.csv"


# ============================================================
# GLOBAL RECORD LIST
# ============================================================

records = []


# ============================================================
# TEXT CLEANING
# ============================================================

def clean_text(value):
    """
    Convert value to clean string.
    """

    if value is None:
        return ""

    if pd.isna(value):
        return ""

    text = str(value)

    # Replace multiple spaces/newlines
    text = " ".join(text.split())

    return text.strip()


# ============================================================
# ADD RECORD
# ============================================================

def add_record(
    text,
    language,
    label,
    source,
    domain="",
    topic="",
    split="unknown"
):

    text = clean_text(text)
    language = clean_text(language)
    label = clean_text(label)
    source = clean_text(source)
    domain = clean_text(domain)
    topic = clean_text(topic)
    split = clean_text(split)

    if not text:
        return

    # Normalize label
    label_lower = label.lower()

    if label_lower in [
        "fake",
        "false",
        "0",
        "fake news"
    ]:
        label = "Fake"

    elif label_lower in [
        "real",
        "true",
        "1",
        "real news"
    ]:
        label = "Real"

    else:
        # Unknown label
        return

    records.append(
        {
            "text": text,
            "language": language,
            "label": label,
            "source": source,
            "domain": domain,
            "topic": topic,
            "split": split
        }
    )


# ============================================================
# 1. READ ISOT ENGLISH
# ============================================================

def read_isot():

    isot_dir = RAW_DIR / "ISOT_Fake_Real_News"

    print("\n========================================")
    print("READING ISOT ENGLISH DATA")
    print("========================================")

    if not isot_dir.exists():

        print(
            "ERROR: ISOT folder not found:"
        )

        print(isot_dir)

        return

    # --------------------------------------------------------
    # FAKE NEWS
    # --------------------------------------------------------

    fake_file = isot_dir / "Fake.csv"

    if fake_file.exists():

        print("\nReading Fake.csv...")

        try:

            fake_df = pd.read_csv(
                fake_file,
                encoding="utf-8",
                on_bad_lines="skip"
            )

            print(
                "Fake records found:",
                len(fake_df)
            )

            for _, row in fake_df.iterrows():

                title = clean_text(
                    row.get("title", "")
                )

                text = clean_text(
                    row.get("text", "")
                )

                subject = clean_text(
                    row.get("subject", "")
                )

                date = clean_text(
                    row.get("date", "")
                )

                # Combine title and article
                if title and text:

                    combined_text = (
                        title
                        + ". "
                        + text
                    )

                elif text:

                    combined_text = text

                else:

                    combined_text = title

                add_record(
                    text=combined_text,
                    language="English",
                    label="Fake",
                    source="ISOT",
                    domain=subject,
                    topic=title,
                    split="external"
                )

        except Exception as e:

            print(
                "ERROR reading Fake.csv:"
            )

            print(e)

    else:

        print(
            "WARNING: Fake.csv not found"
        )


    # --------------------------------------------------------
    # REAL NEWS
    # --------------------------------------------------------

    real_file = isot_dir / "True.csv"

    if real_file.exists():

        print("\nReading True.csv...")

        try:

            real_df = pd.read_csv(
                real_file,
                encoding="utf-8",
                on_bad_lines="skip"
            )

            print(
                "Real records found:",
                len(real_df)
            )

            for _, row in real_df.iterrows():

                title = clean_text(
                    row.get("title", "")
                )

                text = clean_text(
                    row.get("text", "")
                )

                subject = clean_text(
                    row.get("subject", "")
                )

                date = clean_text(
                    row.get("date", "")
                )

                # Combine title and article
                if title and text:

                    combined_text = (
                        title
                        + ". "
                        + text
                    )

                elif text:

                    combined_text = text

                else:

                    combined_text = title

                add_record(
                    text=combined_text,
                    language="English",
                    label="Real",
                    source="ISOT",
                    domain=subject,
                    topic=title,
                    split="external"
                )

        except Exception as e:

            print(
                "ERROR reading True.csv:"
            )

            print(e)

    else:

        print(
            "WARNING: True.csv not found"
        )


# ============================================================
# 2. READ HINDI F&R
# ============================================================

def read_hindi_fr():

    hindi_dir = RAW_DIR / "Hindi_F&R_News"

    print("\n========================================")
    print("READING HINDI F&R DATA")
    print("========================================")

    if not hindi_dir.exists():

        print(
            "ERROR: Hindi F&R folder not found:"
        )

        print(hindi_dir)

        return

    # --------------------------------------------------------
    # HINDI FAKE
    # --------------------------------------------------------

    fake_dir = hindi_dir / "Hindi_fake_news"

    if fake_dir.exists():

        fake_files = list(
            fake_dir.glob("*.txt")
        )

        print(
            "Hindi_fake_news:",
            len(fake_files),
            "files"
        )

        for file_path in fake_files:

            try:

                text = file_path.read_text(
                    encoding="utf-8",
                    errors="ignore"
                )

                add_record(
                    text=text,
                    language="Hindi",
                    label="Fake",
                    source="Hindi_F&R",
                    domain="",
                    topic="",
                    split="external"
                )

            except Exception as e:

                print(
                    f"Error reading {file_path.name}: {e}"
                )

    else:

        print(
            "WARNING: Hindi_fake_news folder not found"
        )


    # --------------------------------------------------------
    # HINDI REAL
    # --------------------------------------------------------

    real_dir = hindi_dir / "Hindi_real_news"

    if real_dir.exists():

        real_files = list(
            real_dir.glob("*.txt")
        )

        print(
            "Hindi_real_news:",
            len(real_files),
            "files"
        )

        for file_path in real_files:

            try:

                text = file_path.read_text(
                    encoding="utf-8",
                    errors="ignore"
                )

                add_record(
                    text=text,
                    language="Hindi",
                    label="Real",
                    source="Hindi_F&R",
                    domain="",
                    topic="",
                    split="external"
                )

            except Exception as e:

                print(
                    f"Error reading {file_path.name}: {e}"
                )

    else:

        print(
            "WARNING: Hindi_real_news folder not found"
        )


# ============================================================
# 3. READ MARATHI F&R
# ============================================================

def read_marathi_fr():

    marathi_dir = RAW_DIR / "Marathi_F&R_News"

    print("\n========================================")
    print("READING MARATHI F&R DATA")
    print("========================================")

    if not marathi_dir.exists():

        print(
            "ERROR: Marathi F&R folder not found:"
        )

        print(marathi_dir)

        return

    # --------------------------------------------------------
    # MARATHI FAKE
    # --------------------------------------------------------

    fake_dir = marathi_dir / "Marathi_fake_news"

    if fake_dir.exists():

        fake_files = list(
            fake_dir.glob("*.txt")
        )

        print(
            "Marathi_fake_news:",
            len(fake_files),
            "files"
        )

        for file_path in fake_files:

            try:

                text = file_path.read_text(
                    encoding="utf-8",
                    errors="ignore"
                )

                add_record(
                    text=text,
                    language="Marathi",
                    label="Fake",
                    source="Marathi_F&R",
                    domain="",
                    topic="",
                    split="external"
                )

            except Exception as e:

                print(
                    f"Error reading {file_path.name}: {e}"
                )

    else:

        print(
            "WARNING: Marathi_fake_news folder not found"
        )


    # --------------------------------------------------------
    # MARATHI REAL
    # --------------------------------------------------------

    real_dir = marathi_dir / "Marathi_real_news"

    if real_dir.exists():

        real_files = list(
            real_dir.glob("*.txt")
        )

        print(
            "Marathi_real_news:",
            len(real_files),
            "files"
        )

        for file_path in real_files:

            try:

                text = file_path.read_text(
                    encoding="utf-8",
                    errors="ignore"
                )

                add_record(
                    text=text,
                    language="Marathi",
                    label="Real",
                    source="Marathi_F&R",
                    domain="",
                    topic="",
                    split="external"
                )

            except Exception as e:

                print(
                    f"Error reading {file_path.name}: {e}"
                )

    else:

        print(
            "WARNING: Marathi_real_news folder not found"
        )


# ============================================================
# 4. READ TALLIP HINDI
# ============================================================

def read_tallip_hindi():

    hindi_dir = (
        RAW_DIR
        / "TALLIP-FakeNews-Dataset"
        / "Hindi"
    )

    print("\n========================================")
    print("READING TALLIP HINDI")
    print("========================================")

    if not hindi_dir.exists():

        print(
            "WARNING: TALLIP Hindi folder not found:"
        )

        print(hindi_dir)

        return

    train_dir = hindi_dir / "Train"
    test_dir = hindi_dir / "Test"


    # --------------------------------------------------------
    # READ TRAIN + TEST
    # --------------------------------------------------------

    for folder, split_name in [
        (train_dir, "train"),
        (test_dir, "test")
    ]:

        if not folder.exists():

            print(
                f"WARNING: {folder} not found"
            )

            continue

        files = list(
            folder.glob("*.txt")
        )

        print(
            f"Hindi {split_name.title()}:",
            len(files),
            "files"
        )

        for file_path in files:

            try:

                with open(
                    file_path,
                    "r",
                    encoding="utf-8",
                    errors="ignore"
                ) as f:

                    reader = csv.reader(
                        f,
                        delimiter="\t"
                    )

                    first_row = True

                    for row in reader:

                        if not row:
                            continue

                        # Skip header
                        if first_row:

                            first_row = False

                            row_text = " ".join(
                                row
                            ).lower()

                            if (
                                "domain" in row_text
                                and "news" in row_text
                                and "label" in row_text
                            ):
                                continue

                        # ------------------------------------------------
                        # Expected TALLIP structure:
                        #
                        # Domain | Topic | News | Label
                        # ------------------------------------------------

                        if len(row) >= 4:

                            domain = clean_text(
                                row[0]
                            )

                            topic = clean_text(
                                row[1]
                            )

                            news = clean_text(
                                row[2]
                            )

                            label = clean_text(
                                row[3]
                            )

                            add_record(
                                text=news,
                                language="Hindi",
                                label=label,
                                source="TALLIP",
                                domain=domain,
                                topic=topic,
                                split=split_name
                            )

                        elif len(row) >= 2:

                            # Fallback for unexpected format
                            text = clean_text(
                                " ".join(row[:-1])
                            )

                            label = clean_text(
                                row[-1]
                            )

                            add_record(
                                text=text,
                                language="Hindi",
                                label=label,
                                source="TALLIP",
                                domain="",
                                topic="",
                                split=split_name
                            )

            except Exception as e:

                print(
                    f"Error reading {file_path.name}: {e}"
                )


# ============================================================
# 5. REMOVE DUPLICATES
# ============================================================

def remove_duplicates(df):

    print("\n========================================")
    print("REMOVING DUPLICATES")
    print("========================================")

    before = len(df)

    df = df.drop_duplicates(
        subset=[
            "text",
            "language",
            "label"
        ]
    ).reset_index(drop=True)

    removed = before - len(df)

    print(
        "Duplicates removed:",
        removed
    )

    return df


# ============================================================
# 6. CLEAN DATA
# ============================================================

def clean_dataset(df):

    print("\n========================================")
    print("CLEANING DATA")
    print("========================================")

    before = len(df)

    # Remove empty text
    df["text"] = (
        df["text"]
        .fillna("")
        .astype(str)
        .str.strip()
    )

    df = df[
        df["text"] != ""
    ]

    print(
        "Empty records removed:",
        before - len(df)
    )

    # Remove very short news
    before = len(df)

    df = df[
        df["text"].str.len() >= 20
    ]

    print(
        "Very short records removed:",
        before - len(df)
    )

    return df.reset_index(drop=True)


# ============================================================
# 7. CREATE FINAL DATASET
# ============================================================

def main():

    print("\n")
    print("======================================================")
    print(" MULTILINGUAL NEWS VERIFICATION")
    print(" DATASET PREPARATION")
    print("======================================================")

    print("\nProject root:")
    print(PROJECT_ROOT)

    print("\nRaw data directory:")
    print(RAW_DIR)


    # --------------------------------------------------------
    # CLEAR RECORD LIST
    # --------------------------------------------------------

    records.clear()


    # --------------------------------------------------------
    # READ DATASETS
    # --------------------------------------------------------

    # IMPORTANT:
    # English = ISOT
    # Hindi = Hindi F&R + TALLIP Hindi
    # Marathi = Marathi F&R

    read_isot()

    read_hindi_fr()

    read_marathi_fr()

    read_tallip_hindi()


    # --------------------------------------------------------
    # CHECK RECORDS
    # --------------------------------------------------------

    print("\n========================================")
    print("COMBINING DATA")
    print("========================================")

    print(
        "Total raw records:",
        len(records)
    )

    if len(records) == 0:

        print(
            "\nERROR: No records were loaded."
        )

        return


    # --------------------------------------------------------
    # CREATE DATAFRAME
    # --------------------------------------------------------

    df = pd.DataFrame(records)


    # --------------------------------------------------------
    # ADD ID
    # --------------------------------------------------------

    df.insert(
        0,
        "id",
        range(
            1,
            len(df) + 1
        )
    )


    # --------------------------------------------------------
    # REMOVE DUPLICATES
    # --------------------------------------------------------

    df = remove_duplicates(df)


    # --------------------------------------------------------
    # CLEAN DATA
    # --------------------------------------------------------

    df = clean_dataset(df)


    # --------------------------------------------------------
    # RECREATE IDs
    # --------------------------------------------------------

    df["id"] = range(
        1,
        len(df) + 1
    )


    # --------------------------------------------------------
    # ENSURE COLUMN ORDER
    # --------------------------------------------------------

    columns = [
        "id",
        "text",
        "language",
        "label",
        "source",
        "domain",
        "topic",
        "split"
    ]

    df = df[columns]


    # --------------------------------------------------------
    # CREATE OUTPUT DIRECTORY
    # --------------------------------------------------------

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )


    # --------------------------------------------------------
    # SAVE DATASET
    # --------------------------------------------------------

    df.to_csv(
        OUTPUT_FILE,
        index=False,
        encoding="utf-8-sig"
    )


    # ========================================================
    # FINAL REPORT
    # ========================================================

    print("\n========================================")
    print("FINAL DATASET")
    print("========================================")

    print(
        "\nFinal records:",
        len(df)
    )

    print(
        "\nFinal columns:"
    )

    print(
        list(df.columns)
    )


    # --------------------------------------------------------
    # LANGUAGE DISTRIBUTION
    # --------------------------------------------------------

    print("\n========================================")
    print("LANGUAGE DISTRIBUTION")
    print("========================================")

    print(
        df["language"].value_counts()
    )


    # --------------------------------------------------------
    # LABEL DISTRIBUTION
    # --------------------------------------------------------

    print("\n========================================")
    print("LABEL DISTRIBUTION")
    print("========================================")

    print(
        df["label"].value_counts()
    )


    # --------------------------------------------------------
    # LANGUAGE + LABEL
    # --------------------------------------------------------

    print("\n========================================")
    print("LANGUAGE + LABEL DISTRIBUTION")
    print("========================================")

    print(
        pd.crosstab(
            df["language"],
            df["label"]
        )
    )


    # --------------------------------------------------------
    # SOURCE DISTRIBUTION
    # --------------------------------------------------------

    print("\n========================================")
    print("SOURCE DISTRIBUTION")
    print("========================================")

    print(
        df["source"].value_counts()
    )


    # --------------------------------------------------------
    # DOMAIN DISTRIBUTION
    # --------------------------------------------------------

    print("\n========================================")
    print("DOMAIN DISTRIBUTION")
    print("========================================")

    print(
        df["domain"]
        .replace("", "Unknown")
        .value_counts()
        .head(20)
    )


    # --------------------------------------------------------
    # SAMPLE RECORDS
    # --------------------------------------------------------

    print("\n========================================")
    print("FIRST 5 RECORDS")
    print("========================================")

    print(
        df.head(5).to_string()
    )


    # --------------------------------------------------------
    # OUTPUT
    # --------------------------------------------------------

    print("\n========================================")
    print("DATASET PREPARATION COMPLETED")
    print("========================================")

    print("\nOutput file:")

    print(OUTPUT_FILE)

    print("\n========================================")


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":
    main()