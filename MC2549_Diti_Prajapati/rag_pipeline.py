import pandas as pd
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

DATA_PATH = "data/amazon_products.csv"
CHROMA_PATH = "chroma_db"

def load_and_process_data(csv_path=DATA_PATH):
    """Loads CSV dataset and converts each row into a LangChain Document with metadata."""
    df = pd.read_csv(csv_path)
    df = df.fillna("")
    
    documents = []
    
    for idx, row in df.iterrows():
        content = (
            f"Product Name: {row.get('product_name', '')}\n"
            f"Category: {row.get('category', '')}\n"
            f"Price: {row.get('discounted_price', '')} (Original: {row.get('actual_price', '')}, Discount: {row.get('discount_percentage', '')})\n"
            f"Rating: {row.get('rating', '')} based on {row.get('rating_count', '')} reviews\n"
            f"About Product: {row.get('about_product', '')}\n"
            f"Review Title: {row.get('review_title', '')}\n"
            f"Review Content: {row.get('review_content', '')}"
        )
        
        metadata = {
            "product_id": str(row.get('product_id', '')),
            "product_name": str(row.get('product_name', '')),
            "category": str(row.get('category', '')),
            "discounted_price": str(row.get('discounted_price', '')),
            "rating": str(row.get('rating', '')),
            "img_link": str(row.get('img_link', '')),
            "product_link": str(row.get('product_link', ''))
        }
        
        documents.append(Document(page_content=content, metadata=metadata))
        
    return documents


def build_vector_db():
    """Chunk documents, build embeddings using sentence-transformers, and persist to ChromaDB."""
    print("Loading documents from dataset...")
    docs = load_and_process_data()
    
    print(f"Loaded {len(docs)} document records. Splitting text into chunks...")
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=600,
        chunk_overlap=100
    )
    chunks = text_splitter.split_documents(docs)
    print(f"Created {len(chunks)} text chunks.")
    
    print("Initializing embedding model (sentence-transformers/all-MiniLM-L6-v2)...")
    embedding_model = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )
    
    print("Creating vector database in ChromaDB...")
    vector_db = Chroma.from_documents(
        documents=chunks,
        embedding=embedding_model,
        persist_directory=CHROMA_PATH
    )
    
    print(f"✅ ChromaDB vector database built and saved at '{CHROMA_PATH}'!")
    return vector_db


def query_vector_db(query: str, k=3):
    """Retrieve top-k relevant documents for a given query."""
    embedding_model = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )
    vector_db = Chroma(
        persist_directory=CHROMA_PATH,
        embedding_function=embedding_model
    )
    
    results = vector_db.similarity_search(query, k=k)
    return results


if __name__ == "__main__":
    print("Building Vector Store...")
    build_vector_db()
    
    print("\n--- Testing Retrieval ---")
    test_query = "Looking for fast charging cables with good reviews"
    results = query_vector_db(test_query, k=2)
    
    for i, res in enumerate(results, 1):
        print(f"\nResult {i}:")
        print(f"Product: {res.metadata.get('product_name')}")
        print(f"Content Sample:\n{res.page_content[:200]}...")