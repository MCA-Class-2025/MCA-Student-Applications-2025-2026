import os

from database import Database
from virus_total import VirusTotal
from malware_bazaar import MalwareBazaar


class FileSecurityScanner:

    # SecureShare upload folder
    UPLOAD_FOLDER = r"C:\xampp\htdocs\zero_trust_system\uploads"

    def __init__(self):

        self.db = Database()
        self.vt = VirusTotal()
        self.mb = MalwareBazaar()


    # ==========================================
    # Scan all files of a user
    # ==========================================

    def scan_user_files(self, username):

        files = self.db.get_user_files(username)

        if not files:

            return {
                "username": username,
                "files_found": 0,
                "files_scanned": 0,
                "malicious_files": [],
                "suspicious_files": [],
                "unknown_files": [],
                "results": []
            }


        malicious_files = []
        suspicious_files = []
        unknown_files = []

        results = []


        # ==========================================
        # Scan every file
        # ==========================================

        for file in files:

            file_name = file["file_name"]
            file_path = file["file_path"]

            full_path = os.path.join(
                self.UPLOAD_FOLDER,
                os.path.basename(file_path)
            )


            # --------------------------------------
            # File does not exist
            # --------------------------------------

            if not os.path.exists(full_path):

                unknown_files.append(file_name)

                results.append({

                    "file_name": file_name,

                    "status": "UNKNOWN",

                    "reason": "File not found on server."

                })

                continue


            # ======================================
            # VirusTotal
            # ======================================

            # ======================================
            # VirusTotal
            # ======================================

            print(
                f"SCANNING WITH VIRUSTOTAL: {file_name}",
                flush=True
            )

            vt_result = self.vt.check_file(full_path)

            print(
                f"VIRUSTOTAL FINISHED: {file_name}",
                flush=True
            )


            # Get hash calculated by VirusTotal
            file_hash = vt_result.get("hash")


            # ======================================
            # MalwareBazaar
            # ======================================

            print(
                f"SCANNING WITH MALWAREBAZAAR: {file_name}",
                flush=True
            )

            mb_result = self.mb.check_hash(file_hash)

            print(
                f"MALWAREBAZAAR FINISHED: {file_name}",
                flush=True
            )

            # ======================================
            # Determine combined result
            # ======================================

            vt_malicious = (
                vt_result.get("found", False)
                and vt_result.get("malicious", 0) > 0
            )

            vt_suspicious = (
                vt_result.get("found", False)
                and vt_result.get("suspicious", 0) > 0
            )

            mb_malicious = mb_result.get(
                "malicious",
                False
            )


            # ======================================
            # MALICIOUS
            # ======================================

            if vt_malicious or mb_malicious:

                malicious_files.append(file_name)

                results.append({

                    "file_name": file_name,
                    "sha256": file_hash,
                    "status": "MALICIOUS",

                    "virustotal": {
                        "found": vt_result.get("found", False),
                        "malicious": vt_result.get("malicious", 0),
                        "suspicious": vt_result.get("suspicious", 0)
                    },

                    "malwarebazaar": {
                        "malicious": mb_result.get("malicious", False)
                    }

                })  


            # ======================================
            # SUSPICIOUS
            # ======================================

            elif vt_suspicious:

                suspicious_files.append(file_name)

                results.append({

                    "file_name": file_name,
                    "sha256": file_hash,
                    "status": "SUSPICIOUS",

                    "virustotal": {
                        "found": vt_result.get("found", False),
                        "malicious": vt_result.get("malicious", 0),
                        "suspicious": vt_result.get("suspicious", 0)
                    },

                    "malwarebazaar": {
                    "malicious": mb_result.get("malicious", False)
                    }

                })


            # ======================================
            # VIRUSTOTAL NOT FOUND
            # ======================================

            elif not vt_result.get("found", False):

                unknown_files.append(file_name)

                results.append({

                    "file_name": file_name,
                    "sha256": file_hash,
                    "status": "UNKNOWN",

                    "reason": "VirusTotal has no report for this file.",

                    "virustotal": {
                        "found": vt_result.get("found", False),
                        "malicious": vt_result.get("malicious", 0),
                        "suspicious": vt_result.get("suspicious", 0)
                    },

                    "malwarebazaar": {
                        "malicious": mb_result.get("malicious", False)
                    }

                })


            # ======================================
            # CLEAN
            # ======================================

            else:

                results.append({

                    "file_name": file_name,
                    "sha256": file_hash,
                    "status": "NO_KNOWN_THREAT",

                    "virustotal": {
                        "found": vt_result.get("found", False),
                        "malicious": vt_result.get("malicious", 0),
                        "suspicious": vt_result.get("suspicious", 0)
                    },

                    "malwarebazaar": {
                        "malicious": mb_result.get("malicious", False)
                    }

                })


        # ==========================================
        # Final result
        # ==========================================

        return {

            "username": username,

            "files_found": len(files),

            "files_scanned": len(files),

            "malicious_files": malicious_files,

            "suspicious_files": suspicious_files,

            "unknown_files": unknown_files,

            "results": results

        }