from pypdf import PdfReader
from docx import Document
import os


def load_document(file_path):

    extension = os.path.splitext(file_path)[1].lower()

    if extension == ".pdf":

        reader = PdfReader(file_path)

        text = ""

        for page in reader.pages:
            extracted = page.extract_text()

            if extracted:
                text += extracted + "\n"

        return text

    elif extension == ".docx":

        document = Document(file_path)

        text = "\n".join(
            paragraph.text
            for paragraph in document.paragraphs
        )

        return text

    else:
        return ""


def load_documents(folder_path):

    all_text = ""

    for file in os.listdir(folder_path):

        file_path = os.path.join(folder_path, file)

        if file.endswith(".pdf") or file.endswith(".docx"):

            print(f"Loading: {file}")

            text = load_document(file_path)

            all_text += "\n\n" + text

    return all_text