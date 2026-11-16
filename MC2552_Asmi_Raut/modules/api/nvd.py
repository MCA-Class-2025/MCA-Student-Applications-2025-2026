"""
nvd.py

API 2: NVD (National Vulnerability Database) — NIST

Official REST API v2.0:
    https://services.nvd.nist.gov/rest/json/cves/2.0

API key is optional but recommended (raises the rate limit from 5
requests/30s to 50 requests/30s). Read from NVD_API_KEY in .env; the
module works without one, just slower.

Join key with the existing dataset
-----------------------------------
NSL-KDD attack categories are generic behavior labels (e.g. "buffer_overflow",
"guess_passwd"), not specific CVE IDs — NSL-KDD predates most CVEs it would
even correspond to, and there is no ground-truth CVE per record. Inventing a
specific CVE per attack category would violate the "no fabricated joins"
requirement.

Instead we use NVD's own `keywordSearch` parameter — a real, documented
feature of the NVD API — to retrieve real, current CVEs whose descriptions
match a keyword derived from the attack category's behavior (e.g.
"buffer_overflow" -> keyword "buffer overflow"). This is a legitimate,
reproducible one(attack)-to-many(CVE) relationship, not a fabricated
one-to-one join. The pipeline keeps this explicit: the individual CSV can
carry multiple CVEs per attack; the per-record fusion keeps only the
top (highest CVSS) match to avoid uncontrolled row multiplication.
"""

import os
import time
from typing import Dict, List, Optional

from dotenv import load_dotenv

from modules.api.base_client import safe_request, logger

load_dotenv()

NVD_API_URL = "https://services.nvd.nist.gov/rest/json/cves/2.0"
NVD_API_KEY = os.getenv("NVD_API_KEY", "").strip()

# NSL-KDD attack category -> NVD keyword search term.
ATTACK_TO_KEYWORD: Dict[str, Optional[str]] = {
    "normal": None,
    "neptune": "SYN flood denial of service",
    "smurf": "ICMP flood denial of service",
    "back": "denial of service Apache",
    "land": "denial of service spoofed packet",
    "pod": "ping of death denial of service",
    "teardrop": "fragmented packet denial of service",
    "ipsweep": "network scanning",
    "nmap": "port scanning",
    "portsweep": "port scanning",
    "satan": "vulnerability scanner",
    "ftp_write": "FTP unauthorized write access",
    "guess_passwd": "brute force authentication",
    "imap": "IMAP remote code execution",
    "multihop": "proxy relay attack",
    "phf": "CGI script command injection",
    "spy": "keystroke logging",
    "warezclient": "FTP unauthorized access",
    "warezmaster": "FTP unauthorized access",
    "buffer_overflow": "buffer overflow",
    "loadmodule": "kernel module privilege escalation",
    "perl": "perl script code injection",
    "rootkit": "rootkit privilege escalation",
}


def _severity_from_cvss(score: Optional[float]) -> str:
    if score is None:
        return ""
    if score == 0:
        return "None"
    if score < 4.0:
        return "Low"
    if score < 7.0:
        return "Medium"
    if score < 9.0:
        return "High"
    return "Critical"


def search_cves(keyword: str, results_per_page: int = 3) -> Dict:
    headers = {"apiKey": NVD_API_KEY} if NVD_API_KEY else {}

    params = {
        "keywordSearch": keyword,
        "resultsPerPage": results_per_page,
    }

    return safe_request(
        "GET", NVD_API_URL, api_name="NVD", headers=headers, params=params, timeout=30
    )


def enrich_attack_categories(attack_counts: Dict[str, int]) -> List[Dict]:
    """
    For each unique NSL-KDD attack category, query NVD by keyword and return
    the top CVE matches.

    Returns list of dict rows:
        attack, count_in_dataset, nvd_keyword, cve_id, cve_description,
        cvss_score, severity, published_date, api_status
    """
    records = []
    # NVD public rate limit without a key is 5 req/30s -> ~6s between calls.
    delay = 1.2 if NVD_API_KEY else 6.5

    for attack, count in attack_counts.items():
        keyword = ATTACK_TO_KEYWORD.get(attack)

        if keyword is None:
            records.append({
                "attack": attack,
                "count_in_dataset": count,
                "nvd_keyword": "",
                "cve_id": "",
                "cve_description": "",
                "cvss_score": "",
                "severity": "",
                "published_date": "",
                "api_status": "not_applicable",
            })
            continue

        result = search_cves(keyword)

        if not result["ok"]:
            records.append({
                "attack": attack,
                "count_in_dataset": count,
                "nvd_keyword": keyword,
                "cve_id": "",
                "cve_description": "",
                "cvss_score": "",
                "severity": "",
                "published_date": "",
                "api_status": f"api_error:{result['error']}",
            })
            time.sleep(delay)
            continue

        vulnerabilities = result["data"].get("vulnerabilities", [])

        if not vulnerabilities:
            records.append({
                "attack": attack,
                "count_in_dataset": count,
                "nvd_keyword": keyword,
                "cve_id": "",
                "cve_description": "",
                "cvss_score": "",
                "severity": "",
                "published_date": "",
                "api_status": "no_results",
            })
            time.sleep(delay)
            continue

        for vuln in vulnerabilities:
            cve = vuln.get("cve", {})
            cve_id = cve.get("id", "")

            descriptions = cve.get("descriptions", [])
            description = next(
                (d["value"] for d in descriptions if d.get("lang") == "en"), ""
            )[:300]

            metrics = cve.get("metrics", {})
            cvss_score = None
            for metric_key in ("cvssMetricV31", "cvssMetricV30", "cvssMetricV2"):
                if metric_key in metrics and metrics[metric_key]:
                    cvss_score = metrics[metric_key][0]["cvssData"].get("baseScore")
                    break

            records.append({
                "attack": attack,
                "count_in_dataset": count,
                "nvd_keyword": keyword,
                "cve_id": cve_id,
                "cve_description": description,
                "cvss_score": cvss_score if cvss_score is not None else "",
                "severity": _severity_from_cvss(cvss_score),
                "published_date": cve.get("published", ""),
                "api_status": "ok",
            })

        time.sleep(delay)

    return records
