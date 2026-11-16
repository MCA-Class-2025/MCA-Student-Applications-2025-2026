import os
import pandas as pd
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("THREATFOX_API_KEY", "").strip()

INPUT_FILE = "data/sample_network_data/SecureSense_NSL_CIC_1000_API_Fusion_Base.csv"
OUTPUT_FILE = "threatfox_api_data.csv"

URL = "https://threatfox-api.abuse.ch/api/v1/"


def lookup_ip(ip):
    headers = {
        "Auth-Key": API_KEY,
        "Content-Type": "application/json"
    }

    payload = {
        "query": "search_ioc",
        "search_term": ip
    }

    response = requests.post(
        URL,
        headers=headers,
        json=payload,
        timeout=30
    )

    if response.status_code != 200:
        return {
            "threat_ip": ip,
            "tf_ioc_count": "",
            "tf_malware": "",
            "tf_threat_type": "",
            "tf_confidence_level": "",
            "api_status": f"error_{response.status_code}"
        }

    data = response.json()

    if data.get("query_status") != "ok":
        return {
            "threat_ip": ip,
            "tf_ioc_count": 0,
            "tf_malware": "",
            "tf_threat_type": "",
            "tf_confidence_level": "",
            "api_status": data.get("query_status", "no_result")
        }

    iocs = data.get("data", []) or []

    malware = sorted({
        str(ioc.get("malware_printable", "")).strip()
        for ioc in iocs
        if ioc.get("malware_printable")
    })

    threat_types = sorted({
        str(ioc.get("threat_type", "")).strip()
        for ioc in iocs
        if ioc.get("threat_type")
    })

    confidence = [
        ioc.get("confidence_level")
        for ioc in iocs
        if ioc.get("confidence_level") is not None
    ]

    return {
        "threat_ip": ip,
        "tf_ioc_count": len(iocs),
        "tf_malware": ", ".join(malware),
        "tf_threat_type": ", ".join(threat_types),
        "tf_confidence_level": max(confidence) if confidence else "",
        "api_status": "ok"
    }


def main():
    if not API_KEY:
        raise ValueError("THREATFOX_API_KEY is missing from .env")

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
                "tf_ioc_count": "",
                "tf_malware": "",
                "tf_threat_type": "",
                "tf_confidence_level": "",
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