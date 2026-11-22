
from rag.pdf_loader import load_pdf_documents
from rag.excel_loader import load_excel_documents


def load_food_documents():
    pdf_documents = load_pdf_documents()
    excel_documents = load_excel_documents()

    all_documents = pdf_documents + excel_documents

    print("\n========== KNOWLEDGE BASE ==========")
    print(f"PDF documents: {len(pdf_documents)}")
    print(f"Excel documents: {len(excel_documents)}")
    print(f"Total documents: {len(all_documents)}")

    return all_documents


if __name__ == "__main__":
    documents = load_food_documents()

    if documents:
        print("\nFirst document source:")
        print(documents[0]["source_type"])
        print(documents[0]["text"][:300])
