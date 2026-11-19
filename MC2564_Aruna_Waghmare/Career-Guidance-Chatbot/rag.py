import os
import pickle

from langchain_community.vectorstores import FAISS

from langchain_huggingface import HuggingFaceEmbeddings

from langchain_core.documents import Document



# Load chunks

chunks_file = "processed_data/chunks.txt"


documents = []


with open(
    chunks_file,
    "r",
    encoding="utf-8"
) as f:

    content = f.read()



chunks = content.split(
    "===== CHUNK"
)



for i, chunk in enumerate(chunks):

    if chunk.strip():

        documents.append(
            Document(
                page_content=chunk,
                metadata={
                    "chunk_id": i
                }
            )
        )


print(
    "Documents loaded:",
    len(documents)
)



# Create embedding model

embedding_model = HuggingFaceEmbeddings(

    model_name=
    "sentence-transformers/all-MiniLM-L6-v2"

)



print("Creating embeddings...")



# Create FAISS vector database

vectorstore = FAISS.from_documents(

    documents,

    embedding_model

)



# Save FAISS index

os.makedirs(
    "faiss_index",
    exist_ok=True
)


vectorstore.save_local(
    "faiss_index"
)



print("====================")
print("FAISS INDEX CREATED")
print("====================")



# Test search

retriever = vectorstore.as_retriever(
    search_kwargs={
        "k":3
    }
)



query = "What skills are required for a data scientist?"


results = retriever.invoke(query)



print("\nSearch Results:\n")


for r in results:

    print(
        r.page_content[:300]
    )

    print("----------------")