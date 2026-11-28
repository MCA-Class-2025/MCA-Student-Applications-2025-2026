
import os
from dotenv import load_dotenv

load_dotenv()

keys = [
    "GEMINI_API_KEY",
    "GOOGLE_SAFE_BROWSING_API_KEY",
    "VIRUSTOTAL_API_KEY",
    "ABUSEIPDB_API_KEY",
    "PHISHTANK_APP_KEY",
    "URLHAUS_AUTH_KEY"
]

for key in keys:
    value = os.getenv(key)
    print(key, "CONFIGURED" if value else "MISSING")
