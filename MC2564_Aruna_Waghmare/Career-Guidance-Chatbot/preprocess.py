import pandas as pd

from langchain_core.documents import Document

from langchain_text_splitters import RecursiveCharacterTextSplitter

import os


# Load cleaned dataset

DATA_PATH = "processed_data/career_data_cleaned.csv"


df = pd.read_csv(
    DATA_PATH,
    encoding="latin1"
)


print("Dataset Loaded")
print("Shape:", df.shape)



# Convert rows into documents

documents = []


for index, row in df.iterrows():

    text = ""


    for column in df.columns:

        text += (
            f"{column}: {row[column]}\n"
        )


    document = Document(
        page_content=text,
        metadata={
            "row": index
        }
    )


    documents.append(document)



print(
    "Total Documents:",
    len(documents)
)



# Text chunking

text_splitter = RecursiveCharacterTextSplitter(

    chunk_size=500,

    chunk_overlap=100

)



chunks = text_splitter.split_documents(
    documents
)



print(
    "Total Chunks:",
    len(chunks)
)



# Save chunks

os.makedirs(
    "processed_data",
    exist_ok=True
)


with open(
    "processed_data/chunks.txt",
    "w",
    encoding="utf-8"
) as f:


    for i, chunk in enumerate(chunks):

        f.write(
            f"\n\n===== CHUNK {i} =====\n"
        )

        f.write(
            chunk.page_content
        )



print(
    "Chunks saved successfully"
)
