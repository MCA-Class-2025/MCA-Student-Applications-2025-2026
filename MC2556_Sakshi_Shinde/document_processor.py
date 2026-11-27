import os
import json
import pandas as pd
from PIL import Image
import pypdf
import docx
try:
    import pytesseract
except ImportError:
    pytesseract = None

class RecursiveTextSplitter:
    """
    A custom implementation of RecursiveCharacterTextSplitter to split text
    recursively based on separator hierarchy, preventing LangChain dependencies.
    """
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200, separators=None):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separators = separators or ["\n\n", "\n", ". ", " ", ""]

    def split_text(self, text: str) -> list[str]:
        if not text or not text.strip():
            return []

        def split_recursive(txt: str, separators: list[str]) -> list[str]:
            if len(txt) <= self.chunk_size:
                return [txt]
            
            if not separators:
                return [txt[i:i+self.chunk_size] for i in range(0, len(txt), self.chunk_size)]
            
            separator = separators[0]
            if separator == "":
                return [txt[i:i+self.chunk_size] for i in range(0, len(txt), self.chunk_size)]
            
            splits = txt.split(separator)
            chunks = []
            current_chunk = []
            current_len = 0
            
            for split in splits:
                if len(split) > self.chunk_size:
                    # If a single split exceeds chunk_size, process any pending chunks
                    if current_chunk:
                        chunks.append(separator.join(current_chunk))
                        current_chunk = []
                        current_len = 0
                    # Recursively split the long block
                    sub_splits = split_recursive(split, separators[1:])
                    chunks.extend(sub_splits)
                else:
                    sep_len = len(separator) if current_chunk else 0
                    if current_len + sep_len + len(split) > self.chunk_size:
                        chunks.append(separator.join(current_chunk))
                        # Create overlap
                        overlap_chunk = []
                        overlap_len = 0
                        for prev in reversed(current_chunk):
                            p_sep_len = len(separator) if overlap_chunk else 0
                            if overlap_len + p_sep_len + len(prev) <= self.chunk_overlap:
                                overlap_chunk.insert(0, prev)
                                overlap_len += p_sep_len + len(prev)
                            else:
                                break
                        current_chunk = overlap_chunk
                        current_len = overlap_len
                        sep_len = len(separator) if current_chunk else 0
                    
                    current_chunk.append(split)
                    current_len += sep_len + len(split)
                    
            if current_chunk:
                chunks.append(separator.join(current_chunk))
                
            return chunks

        return split_recursive(text, self.separators)


def extract_text_from_pdf(file_path: str) -> list[dict]:
    """
    Extracts text from PDF and returns a list of dictionaries, one per page:
    [{'text': page_text, 'page': page_num}]
    """
    pages_data = []
    try:
        reader = pypdf.PdfReader(file_path)
        for idx, page in enumerate(reader.pages):
            text = page.extract_text() or ""
            pages_data.append({
                "text": text.strip(),
                "page": idx + 1
            })
    except Exception as e:
        pages_data.append({
            "text": f"Error parsing PDF: {str(e)}",
            "page": 1
        })
    return pages_data


def extract_text_from_docx(file_path: str) -> list[dict]:
    """Extracts text from Word documents."""
    try:
        doc = docx.Document(file_path)
        text = "\n".join([para.text for para in doc.paragraphs if para.text])
        return [{"text": text.strip(), "page": 1}]
    except Exception as e:
        return [{"text": f"Error parsing DOCX: {str(e)}", "page": 1}]


def extract_text_from_txt(file_path: str) -> list[dict]:
    """Extracts text from standard text files with fallback encoding."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            text = f.read()
        return [{"text": text.strip(), "page": 1}]
    except UnicodeDecodeError:
        try:
            with open(file_path, 'r', encoding='latin-1') as f:
                text = f.read()
            return [{"text": text.strip(), "page": 1}]
        except Exception as e:
            return [{"text": f"Error parsing TXT: {str(e)}", "page": 1}]
    except Exception as e:
        return [{"text": f"Error parsing TXT: {str(e)}", "page": 1}]


def extract_text_from_csv(file_path: str) -> list[dict]:
    """Converts CSV rows into textual descriptions for retrieval."""
    try:
        df = pd.read_csv(file_path)
        rows_text = []
        for idx, row in df.iterrows():
            row_items = [f"{col}='{val}'" for col, val in row.items() if pd.notna(val)]
            rows_text.append(f"Row {idx + 1}: " + ", ".join(row_items))
        full_text = "\n".join(rows_text)
        return [{"text": full_text, "page": 1}]
    except Exception as e:
        return [{"text": f"Error parsing CSV: {str(e)}", "page": 1}]


def extract_text_from_json(file_path: str) -> list[dict]:
    """Converts JSON into formatted key-value descriptions."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Flatten dictionary or list of dicts to readable format
        if isinstance(data, list):
            formatted_items = []
            for idx, item in enumerate(data):
                formatted_items.append(f"Item {idx + 1}: {json.dumps(item)}")
            full_text = "\n".join(formatted_items)
        else:
            full_text = json.dumps(data, indent=2)
            
        return [{"text": full_text, "page": 1}]
    except Exception as e:
        return [{"text": f"Error parsing JSON: {str(e)}", "page": 1}]


def extract_text_from_image(file_path: str) -> list[dict]:
    """Extracts text from images using PyTesseract OCR if installed."""
    if pytesseract is None:
        return [{"text": "[OCR Warning] pytesseract Python package is not installed.", "page": 1}]
    
    try:
        img = Image.open(file_path)
        # Attempt OCR
        text = pytesseract.image_to_string(img)
        return [{"text": text.strip(), "page": 1}]
    except Exception as e:
        # Check if tesseract cmd error
        err_msg = str(e)
        if "tesseract is not installed" in err_msg.lower() or "no such file or directory" in err_msg.lower():
            return [{
                "text": "[OCR Error] Tesseract-OCR binary was not found on this system.\n"
                        "Please install the Tesseract system binary or use API-based vision processing.",
                "page": 1
            }]
        return [{"text": f"Error during image OCR: {err_msg}", "page": 1}]


def process_document(file_path: str, chunk_size: int = 1000, chunk_overlap: int = 200) -> list[dict]:
    """
    Main orchestrator that parses a file based on its extension, chunks the text,
    and returns a list of chunks with complete metadata:
    [{'text': chunk_text, 'metadata': {'source': filename, 'page': page_num, 'chunk_idx': idx}}]
    """
    filename = os.path.basename(file_path)
    _, ext = os.path.splitext(filename)
    ext = ext.lower()
    
    # 1. Extract raw content page-by-page (or as single page)
    if ext == '.pdf':
        pages_content = extract_text_from_pdf(file_path)
    elif ext in ['.docx', '.doc']:
        pages_content = extract_text_from_docx(file_path)
    elif ext in ['.txt', '.md', '.py', '.html', '.xml']:
        pages_content = extract_text_from_txt(file_path)
    elif ext == '.csv':
        pages_content = extract_text_from_csv(file_path)
    elif ext == '.json':
        pages_content = extract_text_from_json(file_path)
    elif ext in ['.png', '.jpg', '.jpeg', '.tiff']:
        pages_content = extract_text_from_image(file_path)
    else:
        # Fallback to general text loading
        pages_content = extract_text_from_txt(file_path)

    # 2. Chunk text and preserve metadata per page
    splitter = RecursiveTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    processed_chunks = []
    
    global_chunk_idx = 0
    for page_data in pages_content:
        text = page_data["text"]
        page_num = page_data["page"]
        
        if not text.strip():
            continue
            
        chunks = splitter.split_text(text)
        for chunk in chunks:
            if chunk.strip():
                processed_chunks.append({
                    "text": chunk,
                    "metadata": {
                        "source": filename,
                        "file_type": ext[1:] if ext.startswith('.') else ext,
                        "page": page_num,
                        "chunk_index": global_chunk_idx
                    }
                })
                global_chunk_idx += 1
                
    return processed_chunks
