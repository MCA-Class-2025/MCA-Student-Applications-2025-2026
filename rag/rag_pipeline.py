import os
from dotenv import load_dotenv

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings

from groq import Groq

# Load environment variables
load_dotenv()

print("API KEY:", os.getenv("GROQ_API_KEY"))

client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)


def design_answer(query, pdf_path):
    # Load PDF
    loader = PyPDFLoader(pdf_path)
    docs = loader.load()

    # Split PDF into chunks
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=600,
        chunk_overlap=100,
    )

    chunks = splitter.split_documents(docs)

    # Create embeddings
    embedding = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )

    # Create FAISS vector database
    db = FAISS.from_documents(chunks, embedding)

    retriever = db.as_retriever(search_kwargs={"k": 4})

    context = retriever.invoke(query)

    context_text = "\n\n".join(
        [doc.page_content for doc in context]
    )

    prompt = f"""
You are an expert Interior Designer.

Use the PDF information below.

{context_text}

User Request:
{query}

Generate:
1. Interior Theme
2. Furniture Suggestions
3. Colour Palette
4. Lighting
5. Flooring
6. Wall Design
7. Budget Estimate
8. Decoration Ideas

Answer professionally.
"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
    )

    return response.choices[0].message.content