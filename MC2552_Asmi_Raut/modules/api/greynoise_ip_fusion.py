import os
import pandas as pd
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("GREYNOISE_API_KEY", "").strip()

INPUT_FILE = "data/sample_network_data/SecureSense_NSL_CIC_1000_API_Fusion_Base.csv"
OUTPUT_FILE = "greynoise_api_data.csv"

URL = "https://api.greynoise.io/v3/community/{ip}"


def lookup_ip(ip):
    headers = {
        "key": API_KEY
    }

    response = requests.get(
        URL.format(ip=ip),
        headers=headers,
        timeout=30
    )

    if response.status_code != 200:
        return {
            "threat_ip": ip,
            "gn_noise": "",
            "gn_riot": "",
            "gn_classification": "",
            "gn_name": "",
            "gn_last_seen": "",
            "api_status": f"error_{response.status_code}"
        }

    data = response.json()

    return {
        "threat_ip": ip,
        "gn_noise": data.get("noise", ""),
        "gn_riot": data.get("riot", ""),
        "gn_classification": data.get("classification", ""),
        "gn_name": data.get("name", ""),
        "gn_last_seen": data.get("last_seen", ""),
        "api_status": "ok"
    }


def main():
    if not API_KEY:
        raise ValueError("GREYNOISE_API_KEY is missing from .env")

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
                "gn_noise": "",
                "gn_riot": "",
                "gn_classification": "",
                "gn_name": "",
                "gn_last_seen": "",
                "api_status": f"error:{e}"
            })

    result_df = pd.DataFrame(results)

    result_df.to_csv(OUTPUT_FILE, index=False)

    print("\nCreated:")
    print(OUTPUT_FILE)
    print("Rows:", len(result_df))
    print("Columns:", len(result_df.columns))


if __name__ == "__main__":
    main()