import os
from src.pdf_handler import load_pdfs
from src.docx_handler import load_docx
from src.txt_handler import load_txt
from src.image_handler import load_images

def load_fusion_dataset(dataset_path="fusion_dataset"):
    documents = []

    pdf_dir = os.path.join(dataset_path, "pdfs")
    docx_dir = os.path.join(dataset_path, "docx")
    txt_dir = os.path.join(dataset_path, "txt")
    img_dir = os.path.join(dataset_path, "images")

    if os.path.exists(pdf_dir):
        pdf_files = [
            os.path.join(pdf_dir, f)
            for f in os.listdir(pdf_dir)
            if f.lower().endswith(".pdf")
        ]
        documents.extend(load_pdfs(pdf_files))

    if os.path.exists(docx_dir):
        docx_files = [
            os.path.join(docx_dir, f)
            for f in os.listdir(docx_dir)
            if f.lower().endswith(".docx")
        ]
        documents.extend(load_docx(docx_files))

    if os.path.exists(txt_dir):
        txt_files = [
            os.path.join(txt_dir, f)
            for f in os.listdir(txt_dir)
            if f.lower().endswith(".txt")
        ]
        documents.extend(load_txt(txt_files))

    if os.path.exists(img_dir):
        image_files = [
            os.path.join(img_dir, f)
            for f in os.listdir(img_dir)
            if f.lower().endswith((".png", ".jpg", ".jpeg"))
        ]
        documents.extend(load_images(image_files))

    return documents