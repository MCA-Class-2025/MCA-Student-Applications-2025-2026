import os
import hashlib
import requests
from dotenv import load_dotenv

load_dotenv()


class VirusTotal:

    def __init__(self):

        self.api_key = os.getenv("VIRUSTOTAL_API_KEY")

        if not self.api_key:
            raise ValueError("VirusTotal API key not found in .env")

        self.base_url = "https://www.virustotal.com/api/v3"


    # ==========================================
    # Calculate SHA-256 Hash
    # ==========================================

    def calculate_hash(self, file_path):

        sha256 = hashlib.sha256()

        with open(file_path, "rb") as file:

            for block in iter(lambda: file.read(4096), b""):
                sha256.update(block)

        return sha256.hexdigest()


    # ==========================================
    # Check Hash with VirusTotal
    # ==========================================

    def check_hash(self, file_hash):

        url = f"{self.base_url}/files/{file_hash}"

        headers = {
            "x-apikey": self.api_key
        }

        try:

            response = requests.get(
                url,
                headers=headers,
                timeout=10
            )   

            if response.status_code == 200:

                data = response.json()

                attributes = data["data"]["attributes"]

                stats = attributes.get("last_analysis_stats", {})

                return {
                    "found": True,
                    "hash": file_hash,
                    "malicious": stats.get("malicious", 0),
                    "suspicious": stats.get("suspicious", 0),
                    "harmless": stats.get("harmless", 0),
                    "undetected": stats.get("undetected", 0)
                }

            elif response.status_code == 404:

                return {
                    "found": False,
                    "hash": file_hash,
                    "error": "not_found"
                }

            else:

                return {
                    "found": False,
                    "hash": file_hash,
                    "error": response.status_code
                }

        except requests.exceptions.Timeout:

            return {
                "found": False,
                "hash": file_hash,
                "error": "timeout"
            }

        except requests.exceptions.RequestException as e:

            return {
                "found": False,
                "hash": file_hash,
                "error": str(e)
            }


    # ==========================================
    # Get File Report
    # ==========================================

    def check_file(self, file_path):

        file_hash = self.calculate_hash(file_path)

        return self.check_hash(file_hash)


# ==========================================
# Test VirusTotal
# ==========================================

if __name__ == "__main__":

    vt = VirusTotal()

    test_hash = "275A021BBFB6489E54D471899F7DB9D1663FC695EC2FE2A2C4538AABF651FD0F"

    result = vt.check_hash(test_hash)

    print("\nVirusTotal Result")
    print("-" * 40)
    print(result)