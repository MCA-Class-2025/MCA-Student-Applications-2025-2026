
import os
import time
import pandas as pd
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("ABUSEIPDB_API_KEY")

INPUT_FILE = "SecureSense_NSL_CIC_1000_API_Fusion_Base.csv"
OUTPUT_FILE = "abuseipdb_api_data.csv"

URL = "https://api.abuseipdb.com/api/v2/check"


def check_ip(ip):
    headers = {
        "Key": API_KEY,
        "Accept": "application/json"
    }

    params = {
        "ipAddress": ip,
        "maxAgeInDays": 90
    }

    response = requests.get(
        URL,
        headers=headers,
        params=params,
        timeout=20
    )

    if response.status_code != 200:
        return {
            "threat_ip": ip,
            "abuse_confidence_score": None,
            "country": None,
            "isp": None,
            "domain": None,
            "total_reports": None,
            "last_reported_at": None,
            "api_status": f"error_{response.status_code}"
        }

    data = response.json().get("data", {})

    return {
        "threat_ip": ip,
        "abuse_confidence_score": data.get("abuseConfidenceScore"),
        "country": data.get("countryCode"),
        "isp": data.get("isp"),
        "domain": data.get("domain"),
        "total_reports": data.get("totalReports"),
        "last_reported_at": data.get("lastReportedAt"),
        "api_status": "ok"
    }


def main():
    if not API_KEY:
        raise ValueError("ABUSEIPDB_API_KEY is missing from .env")

    df = pd.read_csv(INPUT_FILE)

    if "threat_ip" not in df.columns:
        raise ValueError("Column 'threat_ip' not found in input dataset")

    # One API call per unique IP, not once per 1,000 rows.
    ips = df["threat_ip"].dropna().astype(str).str.strip().unique()

    results = []

    print(f"Unique IPs to check: {len(ips)}")

    for i, ip in enumerate(ips, start=1):
        print(f"[{i}/{len(ips)}] Checking {ip}")
        results.append(check_ip(ip))
        time.sleep(0.1)

    result_df = pd.DataFrame(results)

    result_df.to_csv(OUTPUT_FILE, index=False)

    print("\nCreated:")
    print(OUTPUT_FILE)
    print("Rows:", len(result_df))
    print("Columns:", len(result_df.columns))


if __name__ == "__main__":
    main()