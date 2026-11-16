from modules.rag.document_loader import load_documents
from modules.rag.text_splitter import split_text
from modules.rag.embeddings import generate_embeddings
from modules.rag.vector_store import VectorStore

def build_knowledge_base(document_folder="data/documents"):

    # Load all documents
    text = load_documents(document_folder)

    # Split text into chunks
    chunks = split_text(text)

    # Generate embeddings
    embeddings = generate_embeddings(chunks)

    # Create vector store
    store = VectorStore(embeddings.shape[1])

    # Add embeddings
    store.add_embeddings(embeddings, chunks)

    # Save FAISS index
    store.save()

    return {
        "documents": len([
            f for f in __import__("os").listdir(document_folder)
            if f.endswith(".pdf") or f.endswith(".docx")
        ]),
        "chunks": len(chunks)
    }