from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings


# ==========================================
# CONFIGURATION
# ==========================================

VECTORSTORE_PATH = "vectorstore"


# ==========================================
# LOAD EMBEDDING MODEL
# ==========================================

print("Loading embedding model...")

embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)

print("Embedding model loaded.")


# ==========================================
# LOAD FAISS VECTOR DATABASE
# ==========================================

print("\nLoading FAISS vector database...")

vectorstore = FAISS.load_local(
    VECTORSTORE_PATH,
    embeddings,
    allow_dangerous_deserialization=True
)

print("FAISS loaded successfully.")


# ==========================================
# ASK USER QUESTION
# ==========================================

while True:

    question = input(
        "\nAsk a weather question "
        "(type 'exit' to quit): "
    )

    if question.lower() == "exit":
        break


    # ======================================
    # SEARCH FAISS
    # ======================================

    results = vectorstore.similarity_search(
        question,
        k=5
    )


    # ======================================
    # DISPLAY RESULTS
    # ======================================

    print("\n======================================")
    print("RELEVANT WEATHER RECORDS")
    print("======================================")


    for i, document in enumerate(
        results,
        start=1
    ):

        print(
            f"\n---------- RESULT {i} ----------"
        )

        print(
            document.page_content
        )

        print(
            "\nMetadata:",
            document.metadata
        )
        