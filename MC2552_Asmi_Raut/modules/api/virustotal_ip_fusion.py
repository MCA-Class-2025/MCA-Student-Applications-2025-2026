import os
import time
import pandas as pd
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("VIRUSTOTAL_API_KEY", "").strip()

INPUT_FILE = "data/sample_network_data/SecureSense_NSL_CIC_1000_API_Fusion_Base.csv"
OUTPUT_FILE = "virustotal_api_data.csv"

VT_URL = "https://www.virustotal.com/api/v3/ip_addresses/{ip}"


def lookup_ip(ip):
    headers = {
        "x-apikey": API_KEY
    }

    response = requests.get(
        VT_URL.format(ip=ip),
        headers=headers,
        timeout=30
    )

    if response.status_code != 200:
        return {
            "threat_ip": ip,
            "vt_malicious": "",
            "vt_suspicious": "",
            "vt_harmless": "",
            "vt_undetected": "",
            "vt_reputation": "",
            "vt_as_owner": "",
            "vt_country": "",
            "api_status": f"error_{response.status_code}"
        }

    data = response.json().get("data", {})
    attributes = data.get("attributes", {})

    stats = attributes.get("last_analysis_stats", {})

    return {
        "threat_ip": ip,
        "vt_malicious": stats.get("malicious", 0),
        "vt_suspicious": stats.get("suspicious", 0),
        "vt_harmless": stats.get("harmless", 0),
        "vt_undetected": stats.get("undetected", 0),
        "vt_reputation": attributes.get("reputation", ""),
        "vt_as_owner": attributes.get("as_owner", ""),
        "vt_country": attributes.get("country", ""),
        "api_status": "ok"
    }


def main():
    if not API_KEY:
        raise ValueError("VIRUSTOTAL_API_KEY is missing from .env")

    df = pd.read_csv(INPUT_FILE)

    if "threat_ip" not in df.columns:
        raise ValueError("Column 'threat_ip' not found in input dataset")

    ips = (
        df["threat_ip"]
        .dropna()
        .astype(str)
        .str.strip()
        .drop_duplicates()
        .tolist()
    )

    print(f"Unique IPs to check: {len(ips)}")

    results = []

    for i, ip in enumerate(ips, start=1):
        print(f"[{i}/{len(ips)}] Checking {ip}")

        try:
            results.append(lookup_ip(ip))
        except Exception as e:
            results.append({
                "threat_ip": ip,
                "vt_malicious": "",
                "vt_suspicious": "",
                "vt_harmless": "",
                "vt_undetected": "",
                "vt_reputation": "",
                "vt_as_owner": "",
                "vt_country": "",
                "api_status": f"error:{e}"
            })

        # Stay below the public API request rate.
        time.sleep(15)

    result_df = pd.DataFrame(results)

    result_df.to_csv(OUTPUT_FILE, index=False)

    print("\nCreated:")
    print(OUTPUT_FILE)
    print("Rows:", len(result_df))
    print("Columns:", len(result_df.columns))


if __name__ == "__main__":
    main()