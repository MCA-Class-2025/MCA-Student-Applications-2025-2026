import pandas as pd
import requests
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]

INPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "sample_network_data"
    / "SecureSense_NSL_CIC_1000_API_Fusion_Base.csv"
)

OUTPUT_FILE = PROJECT_ROOT / "shodan_api_data.csv"

URL = "https://internetdb.shodan.io/{ip}"


def lookup_ip(ip):
    try:
        response = requests.get(
            URL.format(ip=ip),
            timeout=20
        )

        if response.status_code == 404:
            return {
                "threat_ip": ip,
                "shodan_ports": "",
                "shodan_hostnames": "",
                "shodan_cpes": "",
                "shodan_tags": "",
                "shodan_vulnerabilities": "",
                "shodan_api_status": "no_match"
            }

        if response.status_code != 200:
            return {
                "threat_ip": ip,
                "shodan_ports": "",
                "shodan_hostnames": "",
                "shodan_cpes": "",
                "shodan_tags": "",
                "shodan_vulnerabilities": "",
                "shodan_api_status": f"error_{response.status_code}"
            }

        data = response.json()

        return {
            "threat_ip": ip,
            "shodan_ports": ",".join(
                str(x) for x in data.get("ports", [])
            ),
            "shodan_hostnames": ",".join(
                str(x) for x in data.get("hostnames", [])
            ),
            "shodan_cpes": ",".join(
                str(x) for x in data.get("cpes", [])
            ),
            "shodan_tags": ",".join(
                str(x) for x in data.get("tags", [])
            ),
            "shodan_vulnerabilities": ",".join(
                str(x) for x in data.get("vulns", [])
            ),
            "shodan_api_status": "ok"
        }

    except Exception as e:
        return {
            "threat_ip": ip,
            "shodan_ports": "",
            "shodan_hostnames": "",
            "shodan_cpes": "",
            "shodan_tags": "",
            "shodan_vulnerabilities": "",
            "shodan_api_status": f"error:{e}"
        }


def main():

    df = pd.read_csv(INPUT_FILE)

    if "threat_ip" not in df.columns:
        raise ValueError(
            "Column 'threat_ip' not found in base dataset."
        )

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

        print(
            f"[{i}/{len(ips)}] Checking {ip}"
        )

        results.append(
            lookup_ip(ip)
        )

    result_df = pd.DataFrame(results)

    result_df.to_csv(
        OUTPUT_FILE,
        index=False
    )

    print("\nCreated:")
    print(OUTPUT_FILE)

    print(
        "Rows:",
        len(result_df)
    )

    print(
        "Columns:",
        len(result_df.columns)
    )

    print("\nStatus:")
    print(
        result_df[
            "shodan_api_status"
        ].value_counts()
    )


if __name__ == "__main__":
    main()