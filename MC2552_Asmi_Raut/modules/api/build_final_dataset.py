import os
import re
import time
from pathlib import Path
from urllib.parse import urlparse

import pandas as pd
import requests
from dotenv import load_dotenv

load_dotenv()

ROOT = Path(__file__).resolve().parents[2]

NSL_FILE = (
    ROOT
    / "data"
    / "sample_network_data"
    / "KDDTrain+.txt"
)

URLHAUS_FILE = ROOT / "urlhaus_data.csv"

OUTPUT_DIR = ROOT / "data" / "api_results"
BASE_OUTPUT = (
    ROOT
    / "data"
    / "sample_network_data"
    / "SecureSense_FINAL_BASE_1000.csv"
)
FINAL_OUTPUT = OUTPUT_DIR / "SecureSense_FINAL_5API_FUSED.csv"

ABUSE_KEY = os.getenv("ABUSEIPDB_API_KEY", "").strip()
VT_KEY = os.getenv("VIRUSTOTAL_API_KEY", "").strip()
OTX_KEY = os.getenv("OTX_API_KEY", "").strip()

ABUSE_URL = "https://api.abuseipdb.com/api/v2/check"
VT_URL = "https://www.virustotal.com/api/v3/ip_addresses/{ip}"
OTX_URL = "https://otx.alienvault.com/api/v1/indicators/IPv4/{ip}/general"
SHODAN_URL = "https://internetdb.shodan.io/{ip}"
IPAPI_URL = "http://ip-api.com/json/{ip}"


NSL_COLUMNS = [
    "duration", "protocol_type", "service", "flag",
    "src_bytes", "dst_bytes", "land", "wrong_fragment", "urgent",
    "hot", "num_failed_logins", "logged_in", "num_compromised",
    "root_shell", "su_attempted", "num_root", "num_file_creations",
    "num_shells", "num_access_files", "num_outbound_cmds",
    "is_host_login", "is_guest_login", "count", "srv_count",
    "serror_rate", "srv_serror_rate", "rerror_rate",
    "srv_rerror_rate", "same_srv_rate", "diff_srv_rate",
    "srv_diff_host_rate", "dst_host_count", "dst_host_srv_count",
    "dst_host_same_srv_rate", "dst_host_diff_srv_rate",
    "dst_host_same_src_port_rate", "dst_host_srv_diff_host_rate",
    "dst_host_serror_rate", "dst_host_srv_serror_rate",
    "dst_host_rerror_rate", "dst_host_srv_rerror_rate",
    "attack", "difficulty_level"
]


def valid_public_ip(ip):
    try:
        import ipaddress

        obj = ipaddress.ip_address(str(ip).strip())

        return (
            obj.version in (4, 6)
            and obj.is_global
            and not obj.is_multicast
        )

    except Exception:
        return False


def get_url_ip(value):
    try:
        parsed = urlparse(str(value))

        host = parsed.hostname

        if host and valid_public_ip(host):
            return host

    except Exception:
        pass

    match = re.search(
        r"(?:https?://)?(\d{1,3}(?:\.\d{1,3}){3})",
        str(value)
    )

    if match and valid_public_ip(match.group(1)):
        return match.group(1)

    return None


def abuseipdb(ip):
    if not ABUSE_KEY:
        raise RuntimeError("Missing ABUSEIPDB_API_KEY")

    response = requests.get(
        ABUSE_URL,
        headers={
            "Key": ABUSE_KEY,
            "Accept": "application/json"
        },
        params={
            "ipAddress": ip,
            "maxAgeInDays": 90
        },
        timeout=20
    )

    response.raise_for_status()

    data = response.json()["data"]

    return {
        "abuse_confidence_score":
            data.get("abuseConfidenceScore", 0),
        "abuse_country":
            data.get("countryCode", ""),
        "abuse_isp":
            data.get("isp", ""),
        "abuse_domain":
            data.get("domain", ""),
        "abuse_total_reports":
            data.get("totalReports", 0)
    }


def virustotal(ip):
    if not VT_KEY:
        raise RuntimeError("Missing VIRUSTOTAL_API_KEY")

    response = requests.get(
        VT_URL.format(ip=ip),
        headers={
            "x-apikey": VT_KEY
        },
        timeout=30
    )

    response.raise_for_status()

    attrs = response.json()["data"]["attributes"]

    stats = attrs.get(
        "last_analysis_stats",
        {}
    )

    return {
        "vt_malicious":
            stats.get("malicious", 0),
        "vt_suspicious":
            stats.get("suspicious", 0),
        "vt_harmless":
            stats.get("harmless", 0),
        "vt_undetected":
            stats.get("undetected", 0),
        "vt_reputation":
            attrs.get("reputation", 0),
        "vt_country":
            attrs.get("country", ""),
        "vt_as_owner":
            attrs.get("as_owner", "")
    }


def otx(ip):
    if not OTX_KEY:
        raise RuntimeError("Missing OTX_API_KEY")

    response = requests.get(
        OTX_URL.format(ip=ip),
        headers={
            "X-OTX-API-KEY": OTX_KEY
        },
        timeout=30
    )

    response.raise_for_status()

    data = response.json()

    pulse_info = data.get(
        "pulse_info",
        {}
    )

    return {
        "otx_pulses":
            pulse_info.get("count", 0),
        "otx_reputation":
            data.get("reputation", 0),
        "otx_country":
            data.get("country_name", "")
    }


def shodan_internetdb(ip):
    response = requests.get(
        SHODAN_URL.format(ip=ip),
        timeout=20
    )

    if response.status_code != 200:
        raise RuntimeError(
            f"Shodan InternetDB HTTP {response.status_code}"
        )

    data = response.json()

    return {
        "shodan_ports":
            ",".join(
                map(str, data.get("ports", []))
            ),
        "shodan_hostnames":
            ",".join(
                data.get("hostnames", [])
            ),
        "shodan_cpes":
            ",".join(
                data.get("cpes", [])
            ),
        "shodan_tags":
            ",".join(
                data.get("tags", [])
            ),
        "shodan_vulnerabilities":
            ",".join(
                data.get("vulns", [])
            )
    }


def ipapi(ip):
    response = requests.get(
        IPAPI_URL.format(ip=ip),
        params={
            "fields":
            "status,message,query,country,countryCode,"
            "regionName,city,isp,org,as,asname,lat,lon,"
            "timezone,proxy,hosting"
        },
        timeout=20
    )

    response.raise_for_status()

    data = response.json()

    if data.get("status") != "success":
        raise RuntimeError(
            data.get("message", "IP-API failed")
        )

    return {
        "ipapi_country":
            data.get("country", ""),
        "ipapi_country_code":
            data.get("countryCode", ""),
        "ipapi_region":
            data.get("regionName", ""),
        "ipapi_city":
            data.get("city", ""),
        "ipapi_isp":
            data.get("isp", ""),
        "ipapi_org":
            data.get("org", ""),
        "ipapi_as":
            data.get("as", ""),
        "ipapi_asname":
            data.get("asname", ""),
        "ipapi_lat":
            data.get("lat", ""),
        "ipapi_lon":
            data.get("lon", ""),
        "ipapi_timezone":
            data.get("timezone", ""),
        "ipapi_proxy":
            data.get("proxy", False),
        "ipapi_hosting":
            data.get("hosting", False)
    }


def query_all_five(ip):
    """
    Returns only when ALL FIVE APIs successfully answer.
    No API_ERROR/NO_MATCH IP is accepted into the final dataset.
    """

    results = {}

    results.update(abuseipdb(ip))
    time.sleep(0.2)

    results.update(virustotal(ip))
    time.sleep(15)

    results.update(otx(ip))
    time.sleep(1)

    results.update(shodan_internetdb(ip))
    time.sleep(0.2)

    results.update(ipapi(ip))

    return results


def main():

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    print("=" * 70)
    print("BUILDING FINAL 5-API DATASET")
    print("=" * 70)

    # ---------------------------------------------------------
    # 1. Load first 1,000 NSL-KDD records
    # ---------------------------------------------------------

    nsl = pd.read_csv(
        NSL_FILE,
        header=None
    )

    nsl.columns = NSL_COLUMNS

    nsl = nsl.iloc[:1000].copy()

    normal_count = int(
        nsl["attack"]
        .astype(str)
        .str.lower()
        .eq("normal")
        .sum()
    )

    attack_count = (
        len(nsl) - normal_count
    )

    print(
        f"NSL normal rows : {normal_count}"
    )

    print(
        f"NSL attack rows : {attack_count}"
    )

    # ---------------------------------------------------------
    # 2. Build malicious candidate IPs from URLhaus
    # ---------------------------------------------------------

    attack_candidates = []

    if URLHAUS_FILE.exists():

        uh = pd.read_csv(
            URLHAUS_FILE,
            dtype=str,
            keep_default_na=False
        )

        if "url" in uh.columns:

            for value in uh["url"]:

                ip = get_url_ip(value)

                if ip:
                    attack_candidates.append(ip)

    attack_candidates = list(
        dict.fromkeys(
            attack_candidates
        )
    )

    print(
        f"URLhaus public IP candidates: "
        f"{len(attack_candidates)}"
    )

    # ---------------------------------------------------------
    # 3. Clean public benign candidates
    # ---------------------------------------------------------

    benign_candidates = [
        "8.8.8.8",
        "1.1.1.1",
        "9.9.9.9",
        "208.67.222.222",
        "208.67.220.220",
        "8.8.4.4",
        "1.0.0.1"
    ]

    benign_candidates = [
        ip
        for ip in benign_candidates
        if valid_public_ip(ip)
    ]

    # ---------------------------------------------------------
    # 4. Validate candidates against ALL FIVE APIs
    # ---------------------------------------------------------

    def find_valid_candidates(
        candidates,
        needed,
        category
    ):

        valid = []

        for ip in candidates:

            if len(valid) >= needed:
                break

            print(
                f"Validating {category} IP: {ip}"
            )

            try:

                data = query_all_five(ip)

                valid.append(
                    (
                        ip,
                        data
                    )
                )

                print(
                    f"  -> VALID {category} IP"
                )

            except Exception as exc:

                print(
                    f"  -> rejected: {exc}"
                )

        if not valid:
            raise RuntimeError(
                f"No {category} IP passed all five APIs."
            )

        return valid

    # We only need a few validated IPs.
    # They are reused across the 1,000 rows.
    attack_valid = find_valid_candidates(
        attack_candidates,
        needed=5,
        category="ATTACK"
    )

    benign_valid = find_valid_candidates(
        benign_candidates,
        needed=3,
        category="BENIGN"
    )

    print(
        f"Validated attack IPs: "
        f"{len(attack_valid)}"
    )

    print(
        f"Validated benign IPs: "
        f"{len(benign_valid)}"
    )

    # ---------------------------------------------------------
    # 5. Assign validated IPs to the 1,000 NSL rows
    # ---------------------------------------------------------

    attack_pool = [
        item
        for item in attack_valid
    ]

    benign_pool = [
        item
        for item in benign_valid
    ]

    attack_index = 0
    benign_index = 0

    final_rows = []

    for _, row in nsl.iterrows():

        current = row.to_dict()

        if (
            str(row["attack"])
            .strip()
            .lower()
            == "normal"
        ):

            ip, api_data = benign_pool[
                benign_index % len(
                    benign_pool
                )
            ]

            benign_index += 1

            traffic_class = (
                "BENIGN"
            )

        else:

            ip, api_data = attack_pool[
                attack_index % len(
                    attack_pool
                )
            ]

            attack_index += 1

            traffic_class = (
                "ATTACK"
            )

        current[
            "threat_ip"
        ] = ip

        current[
            "ip_traffic_class"
        ] = traffic_class

        current[
            "ip_source"
        ] = (
            "CLEAN_PUBLIC_IP"
            if traffic_class == "BENIGN"
            else "URLHAUS_ATTACK_IP"
        )

        current.update(api_data)

        final_rows.append(
            current
        )

    final = pd.DataFrame(
        final_rows
    )

    # ---------------------------------------------------------
    # 6. Fill every expected field
    # ---------------------------------------------------------

    final = final.fillna(
        "NOT_AVAILABLE"
    )

    for column in final.columns:

        if final[column].dtype == "object":

            final[column] = (
                final[column]
                .astype(str)
                .str.strip()
            )

            final[column] = (
                final[column]
                .replace(
                    "",
                    "NOT_AVAILABLE"
                )
            )

    # ---------------------------------------------------------
    # 7. Validation
    # ---------------------------------------------------------

    if len(final) != 1000:
        raise RuntimeError(
            f"Expected 1000 rows, "
            f"got {len(final)}"
        )

    if final["threat_ip"].eq(
        ""
    ).any():

        raise RuntimeError(
            "Blank threat_ip found."
        )

    if final["threat_ip"].isna().any():

        raise RuntimeError(
            "Missing threat_ip found."
        )

    # Every normal row must have benign source.
    normal_check = final[
        final["attack"]
        .astype(str)
        .str.lower()
        == "normal"
    ]

    if not (
        normal_check[
            "ip_traffic_class"
        ] == "BENIGN"
    ).all():

        raise RuntimeError(
            "Normal/benign alignment failed."
        )

    # Every attack row must have attack source.
    attack_check = final[
        final["attack"]
        .astype(str)
        .str.lower()
        != "normal"
    ]

    if not (
        attack_check[
            "ip_traffic_class"
        ] == "ATTACK"
    ).all():

        raise RuntimeError(
            "Attack alignment failed."
        )

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    final.to_csv(
        BASE_OUTPUT,
        index=False
    )

    final.to_csv(
        FINAL_OUTPUT,
        index=False
    )

    print("\n" + "=" * 70)
    print("FINAL DATASET CREATED")
    print("=" * 70)

    print(
        f"Rows    : {len(final)}"
    )

    print(
        f"Columns : {len(final.columns)}"
    )

    print(
        f"Unique threat IPs: "
        f"{final['threat_ip'].nunique()}"
    )

    print(
        "\nTraffic alignment:"
    )

    print(
        final["ip_traffic_class"]
        .value_counts()
        .to_string()
    )

    print(
        f"\nBase output:\n{BASE_OUTPUT}"
    )

    print(
        f"\nFinal output:\n{FINAL_OUTPUT}"
    )

    print(
        "\nALL FIVE APIs successfully responded "
        "for every IP used in this final dataset."
    )


if __name__ == "__main__":
    main()