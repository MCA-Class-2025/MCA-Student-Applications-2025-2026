import os
import re

from pypdf import PdfReader
from docx import Document

from url_extractor import URLExtractor
from url_haus import URLHaus


class URLScanner:

    def __init__(self, auth_key):

        self.extractor = URLExtractor()
        self.urlhaus = URLHaus(auth_key)

    # ==========================================
    # Extract URLs from PDF
    # ==========================================

    def extract_pdf_urls(self, file_path):

        urls = []

        try:

            reader = PdfReader(file_path)

            for page in reader.pages:

                # ----------------------------------
                # Extract URLs from visible text
                # ----------------------------------

                text = page.extract_text() or ""

                urls.extend(
                    self.extractor.extract_urls(text)
                )

                # ----------------------------------
                # Extract URLs from PDF hyperlinks
                # ----------------------------------

                annotations = page.get("/Annots")

                if annotations:

                    for annotation in annotations:

                        try:

                            obj = annotation.get_object()

                            action = obj.get("/A")

                            if action:

                                uri = action.get("/URI")

                                if uri:

                                    urls.append(str(uri))

                        except Exception:

                            continue

        except Exception as e:

            print(
                f"PDF extraction error: {file_path} -> {e}"
            )

        return self.clean_urls(urls)

    # ==========================================
    # Extract URLs from DOCX
    # ==========================================

    def extract_docx_urls(self, file_path):

        urls = []

        try:

            document = Document(file_path)

            # ----------------------------------
            # URLs written as normal text
            # ----------------------------------

            for paragraph in document.paragraphs:

                text = paragraph.text

                urls.extend(
                    self.extractor.extract_urls(text)
                )

            # ----------------------------------
            # URLs stored as hyperlinks
            # ----------------------------------

            relationships = document.part.rels

            for rel in relationships.values():

                if "hyperlink" in rel.reltype.lower():

                    target = rel.target_ref

                    if target:

                        urls.append(target)

        except Exception as e:

            print(
                f"DOCX extraction error: {file_path} -> {e}"
            )

        return self.clean_urls(urls)

    # ==========================================
    # Extract URLs from TXT
    # ==========================================

    def extract_txt_urls(self, file_path):

        urls = []

        try:

            with open(
                file_path,
                "r",
                encoding="utf-8",
                errors="ignore"
            ) as file:

                text = file.read()

            urls = self.extractor.extract_urls(text)

        except Exception as e:

            print(
                f"TXT extraction error: {file_path} -> {e}"
            )

        return self.clean_urls(urls)

    # ==========================================
    # Extract URLs from a file
    # ==========================================

    def extract_file_urls(self, file_path):

        extension = os.path.splitext(file_path)[1].lower()

        if extension == ".pdf":

            return self.extract_pdf_urls(file_path)

        elif extension == ".docx":

            return self.extract_docx_urls(file_path)

        elif extension == ".txt":

            return self.extract_txt_urls(file_path)

        return []

    # ==========================================
    # Clean URLs
    # ==========================================

    def clean_urls(self, urls):

        cleaned = []

        for url in urls:

            if not url:
                continue

            url = str(url).strip()

            url = url.rstrip(
                ".,!?;:'\"()[]{}<>"
            )

            # Remove duplicate URLs
            if url not in cleaned:

                cleaned.append(url)

        return cleaned

    # ==========================================
    # Scan one file
    # ==========================================

    def scan_file(self, file):

        file_name = file["file_name"]
        database_path = file["file_path"]

        # --------------------------------------
        # Actual SecureShare upload folder
        # --------------------------------------

        upload_folder = (
            r"C:\xampp\htdocs\zero_trust_system\uploads"
        )

        full_path = os.path.join(
            upload_folder,
            os.path.basename(database_path)
        )

        result = {

            "file_name": file_name,

            "file_path": full_path,

            "urls": [],

            "malicious_urls": [],

            "not_found_urls": [],

            "error_urls": []

        }

        # --------------------------------------
        # Check file exists
        # --------------------------------------

        if not os.path.exists(full_path):

            print(
                f"File not found: {full_path}"
            )

            return result

        # --------------------------------------
        # Extract URLs
        # --------------------------------------

        urls = self.extract_file_urls(full_path)

        result["urls"] = urls

        # --------------------------------------
        # Check URLs with URLhaus
        # --------------------------------------

        for url in urls:

            print(
                f"    Checking URLhaus: {url}"
            )

            api_result = self.urlhaus.check_url(url)

            query_status = api_result.get(
                "query_status"
            )

            # ----------------------------------
            # URL found in URLhaus
            # ----------------------------------

            if query_status == "ok":

                result["malicious_urls"].append({

                    "url": url,

                    "status": api_result.get(
                        "url_status"
                    ),

                    "threat": api_result.get(
                        "threat"
                    ),

                    "host": api_result.get(
                        "host"
                    ),

                    "date_added": api_result.get(
                        "date_added"
                    ),

                    "tags": api_result.get(
                        "tags",
                        []
                    )

                })

            # ----------------------------------
            # URL not found
            # ----------------------------------

            elif query_status == "no_results":

                result["not_found_urls"].append(url)

            # ----------------------------------
            # API error
            # ----------------------------------

            else:

                result["error_urls"].append({

                    "url": url,

                    "error": api_result.get(
                        "error",
                        "Unknown error"
                    )

                })

        return result

    # ==========================================
    # Scan multiple files
    # ==========================================

    def scan_files(self, files):

        results = []

        for file in files:

            result = self.scan_file(file)

            results.append(result)

        return results

    # ==========================================
    # Create summary
    # ==========================================

    def create_summary(self, results):

        total_files = len(results)

        files_with_urls = 0
        total_urls = 0
        malicious_urls = 0
        not_found_urls = 0
        error_urls = 0

        malicious_details = []

        for result in results:

            if result["urls"]:

                files_with_urls += 1

            total_urls += len(result["urls"])

            malicious_urls += len(
                result["malicious_urls"]
            )

            not_found_urls += len(
                result["not_found_urls"]
            )

            error_urls += len(
                result["error_urls"]
            )

            # ----------------------------------
            # Keep filename with URL
            # ----------------------------------

            for item in result["malicious_urls"]:

                malicious_details.append({

                    "file_name":
                        result["file_name"],

                    "url":
                        item["url"],

                    "status":
                        item["status"],

                    "threat":
                        item["threat"],

                    "host":
                        item["host"],

                    "tags":
                        item["tags"]

                })

        return {

            "total_files": total_files,

            "files_with_urls":
                files_with_urls,

            "total_urls":
                total_urls,

            "malicious_urls":
                malicious_urls,

            "not_found_urls":
                not_found_urls,

            "error_urls":
                error_urls,

            "malicious_details":
                malicious_details

        }