import pandas as pd
import os
import re
import json


# =========================================================
# CONFIGURATION
# =========================================================

DATA_FOLDER = "data_fusion"

OUTPUT_CSV = os.path.join(
    DATA_FOLDER,
    "rag_documents.csv"
)

OUTPUT_JSONL = os.path.join(
    DATA_FOLDER,
    "rag_documents.jsonl"
)


# =========================================================
# FIND CLEANED CSV
# =========================================================

print("\n========================================")
print(" DATA PREPROCESSING STARTED")
print("========================================")


csv_files = [
    file for file in os.listdir(DATA_FOLDER)
    if file.lower().endswith(".csv")
    and "rag_documents" not in file.lower()
]


if not csv_files:

    print("\nERROR: No CSV file found inside data_fusion folder.")
    print("Please keep your cleaned fused CSV inside data_fusion.")

    exit()


# Prefer cleaned/fused dataset
preferred_files = [
    file for file in csv_files
    if any(
        word in file.lower()
        for word in [
            "clean",
            "fused",
            "fusion",
            "final"
        ]
    )
]


if preferred_files:

    input_file = os.path.join(
        DATA_FOLDER,
        preferred_files[0]
    )

else:

    input_file = os.path.join(
        DATA_FOLDER,
        csv_files[0]
    )


print(f"\nInput file: {input_file}")


# =========================================================
# LOAD DATA
# =========================================================

df = pd.read_csv(
    input_file
)

print(
    f"Rows loaded: {len(df)}"
)

print(
    f"Columns loaded: {len(df.columns)}"
)


# =========================================================
# BASIC CLEANING
# =========================================================

# Replace NaN values
df = df.fillna("Not Available")


# Convert all columns to string
for column in df.columns:

    df[column] = df[column].astype(str)


# Remove extra spaces
for column in df.columns:

    df[column] = df[column].apply(
        lambda x: re.sub(
            r"\s+",
            " ",
            x
        ).strip()
    )


# =========================================================
# CREATE TEXT DOCUMENTS
# =========================================================

documents = []


for index, row in df.iterrows():

    text_parts = []

    for column in df.columns:

        value = row[column]

        # Ignore empty values
        if value in [
            "",
            "nan",
            "None",
            "Not Available"
        ]:

            continue

        # Convert column name to readable format
        readable_column = column.replace(
            "_",
            " "
        )

        text_parts.append(
            f"{readable_column}: {value}"
        )


    document_text = ". ".join(
        text_parts
    )


    documents.append({

        "Document_ID":
            index + 1,

        "Text":
            document_text,

        "Source":
            "SmartWasteAssistant Fused Dataset"

    })


# =========================================================
# CREATE DATAFRAME
# =========================================================

documents_df = pd.DataFrame(
    documents
)


# =========================================================
# SAVE CSV
# =========================================================

documents_df.to_csv(
    OUTPUT_CSV,
    index=False
)


# =========================================================
# SAVE JSONL
# =========================================================

with open(
    OUTPUT_JSONL,
    "w",
    encoding="utf-8"
) as file:

    for document in documents:

        file.write(
            json.dumps(
                document,
                ensure_ascii=False
            )
            + "\n"
        )


# =========================================================
# DISPLAY SAMPLE
# =========================================================

print("\n========================================")
print(" PREPROCESSING COMPLETED")
print("========================================")

print(
    f"Documents created: {len(documents_df)}"
)

print(
    f"Output CSV: {OUTPUT_CSV}"
)

print(
    f"Output JSONL: {OUTPUT_JSONL}"
)


print("\nFirst 3 documents:\n")

for document in documents[:3]:

    print(
        "----------------------------------------"
    )

    print(
        f"Document ID: {document['Document_ID']}"
    )

    print(
        document["Text"][:1000]
    )


print(
    "\n✅ Data is now ready for embedding generation!"
)