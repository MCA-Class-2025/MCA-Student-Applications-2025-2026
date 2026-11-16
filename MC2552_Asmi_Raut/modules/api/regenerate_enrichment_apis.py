from __future__ import annotations

import ipaddress
import os
import sys
import time
from pathlib import Path
from typing import Any

import pandas as pd
import requests
from dotenv import load_dotenv

load_dotenv()

ROOT = Path(__file__).resolve().parents[2]
BASE_FILE = ROOT / "data" / "sample_network_data" / "SecureSense_NSL_CIC_1000_API_Fusion_Base.csv"
OUTPUT_DIR = ROOT

API_KEYS = {
    "abuseipdb": os.getenv("ABUSEIPDB_API_KEY", "").strip(),
    "virustotal": os.getenv("VIRUSTOTAL_API_KEY", "").strip(),
    "otx": os.getenv("OTX_API_KEY", "").strip(),
    "threatfox": os.getenv("THREATFOX_API_KEY", "").strip(),
}

URLS = {
    "abuseipdb": "https://api.abuseipdb.com/api/v2/check",
    "virustotal": "https://www.virustotal.com/api/v3/ip_addresses/{ip}",
    "otx": "https://otx.alienvault.com/api/v1/indicators/IPv4/{ip}/general",
    "shodan": "https://internetdb.shodan.io/{ip}",
    "threatfox": "https://threatfox-api.abuse.ch/api/v1/",
}

OUTPUTS = {
    "abuseipdb": ROOT / "abuseipdb_api_data.csv",
    "virustotal": ROOT / "virustotal_api_data.csv",
    "otx": ROOT / "otx_api_data.csv",
    "shodan": ROOT / "shodan_api_data.csv",
    "threatfox": ROOT / "threatfox_api_data.csv",
}

REQUEST_TIMEOUT_SECONDS = 15
MAX_ATTEMPTS = 2
VIRUSTOTAL_DELAY_SECONDS = 15


def is_public_ip(value: str) -> bool:
    try:
        address = ipaddress.ip_address(value)
        return address.is_global and not address.is_multicast
    except ValueError:
        return False


def request_json(api_name: str, ip: str) -> tuple[str, Any, str]:
    headers: dict[str, str] = {}
    params: dict[str, Any] | None = None
    payload: dict[str, Any] | None = None
    method = "get"

    if api_name == "abuseipdb":
        if not API_KEYS[api_name]:
            return "API_ERROR", None, "missing_api_key"
        headers = {"Key": API_KEYS[api_name], "Accept": "application/json"}
        params = {"ipAddress": ip, "maxAgeInDays": 90}
    elif api_name == "virustotal":
        if not API_KEYS[api_name]:
            return "API_ERROR", None, "missing_api_key"
        headers = {"x-apikey": API_KEYS[api_name]}
    elif api_name == "otx":
        if not API_KEYS[api_name]:
            return "API_ERROR", None, "missing_api_key"
        headers = {"X-OTX-API-KEY": API_KEYS[api_name]}
    elif api_name == "threatfox":
        if not API_KEYS[api_name]:
            return "API_ERROR", None, "missing_api_key"
        method = "post"
        headers = {"Auth-Key": API_KEYS[api_name], "Content-Type": "application/json"}
        payload = {"query": "search_ioc", "search_term": ip}

    for attempt in range(MAX_ATTEMPTS):
        try:
            response = requests.request(
                method,
                URLS[api_name].format(ip=ip),
                headers=headers,
                params=params,
                json=payload,
                timeout=REQUEST_TIMEOUT_SECONDS,
            )
            if api_name == "shodan" and response.status_code == 404:
                return "NO_MATCH", None, "http_404_no_match"
            if response.status_code != 200:
                if response.status_code in {429, 500, 502, 503, 504} and attempt < MAX_ATTEMPTS - 1:
                    time.sleep(2**attempt)
                    continue
                return "API_ERROR", None, f"http_{response.status_code}"
            try:
                return "API_OK", response.json(), ""
            except ValueError:
                return "API_ERROR", None, "invalid_json"
        except requests.RequestException as exc:
            if attempt < MAX_ATTEMPTS - 1:
                time.sleep(2**attempt)
                continue
            return "API_ERROR", None, type(exc).__name__
    return "API_ERROR", None, "request_failed"


def base_record(api_name: str, ip: str, status: str, error_detail: str = "") -> dict[str, Any]:
    return {"enrichment_ip": ip, "api_status": status, "api_error_detail": error_detail}


def parse_result(api_name: str, ip: str, status: str, data: Any, error_detail: str) -> dict[str, Any]:
    record = base_record(api_name, ip, status, error_detail)
    if status != "API_OK":
        if api_name == "shodan" and status == "NO_MATCH":
            record.update({"shodan_ports": "", "shodan_hostnames": "", "shodan_cpes": "", "shodan_tags": "", "shodan_vulnerabilities": ""})
        return record

    if api_name == "abuseipdb":
        data = data.get("data", {})
        record.update({"abuse_confidence_score": data.get("abuseConfidenceScore", ""), "country": data.get("countryCode", ""), "isp": data.get("isp", ""), "domain": data.get("domain", ""), "total_reports": data.get("totalReports", ""), "last_reported_at": data.get("lastReportedAt", "")})
    elif api_name == "virustotal":
        attrs = data.get("data", {}).get("attributes", {})
        stats = attrs.get("last_analysis_stats", {})
        record.update({"vt_malicious": stats.get("malicious", ""), "vt_suspicious": stats.get("suspicious", ""), "vt_harmless": stats.get("harmless", ""), "vt_undetected": stats.get("undetected", ""), "vt_reputation": attrs.get("reputation", ""), "vt_as_owner": attrs.get("as_owner", ""), "vt_country": attrs.get("country", "")})
    elif api_name == "otx":
        pulse_info = data.get("pulse_info", {})
        record.update({"otx_pulses": pulse_info.get("count", ""), "otx_reputation": data.get("reputation", ""), "otx_country": data.get("country_name", "")})
    elif api_name == "shodan":
        record.update({"shodan_ports": ",".join(map(str, data.get("ports", []))), "shodan_hostnames": ",".join(data.get("hostnames", [])), "shodan_cpes": ",".join(data.get("cpes", [])), "shodan_tags": ",".join(data.get("tags", [])), "shodan_vulnerabilities": ",".join(data.get("vulns", []))})
    elif api_name == "threatfox":
        if data.get("query_status") != "ok":
            return base_record(api_name, ip, "NO_MATCH", str(data.get("query_status", "no_result"))) | {"tf_ioc_count": 0, "tf_malware": "", "tf_threat_type": "", "tf_confidence_level": ""}
        iocs = data.get("data", []) or []
        record.update({"tf_ioc_count": len(iocs), "tf_malware": ", ".join(sorted({str(item.get("malware_printable", "")).strip() for item in iocs if item.get("malware_printable")})), "tf_threat_type": ", ".join(sorted({str(item.get("threat_type", "")).strip() for item in iocs if item.get("threat_type")})), "tf_confidence_level": max([item.get("confidence_level") for item in iocs if item.get("confidence_level") is not None], default="")})
    return record


def build_base_with_enrichment() -> pd.DataFrame:
    base = pd.read_csv(BASE_FILE, dtype=str, keep_default_na=False)
    if len(base) != 1000:
        raise ValueError(f"Expected 1000 base rows, found {len(base)}")
    roles = []
    enrichment = []
    for _, row in base.iterrows():
        source = str(row["cic_source_ip"]).strip()
        destination = str(row["cic_destination_ip"]).strip()
        if is_public_ip(source):
            enrichment.append(source)
            roles.append("source")
        elif is_public_ip(destination):
            enrichment.append(destination)
            roles.append("destination")
        else:
            enrichment.append("")
            roles.append("none")
    base["enrichment_ip"] = enrichment
    base["ip_entity_role"] = roles
    if not base.loc[base["enrichment_ip"].ne(""), "enrichment_ip"].map(is_public_ip).all():
        raise ValueError("Non-public enrichment_ip generated")
    base.to_csv(BASE_FILE, index=False)
    return base


def main() -> None:
    requested = sys.argv[1:]
    unknown = sorted(set(requested) - set(OUTPUTS))
    if unknown:
        raise ValueError(f"Unknown API names: {unknown}. Choose from: {sorted(OUTPUTS)}")
    api_names = requested or list(OUTPUTS)
    base = build_base_with_enrichment()
    ips = sorted(set(base.loc[base["enrichment_ip"].ne(""), "enrichment_ip"]))
    print(f"Base rows: {len(base)}; unique public enrichment IPs: {len(ips)}; APIs: {', '.join(api_names)}")
    for api_name in api_names:
        output = OUTPUTS[api_name]
        records = []
        completed_ips = set()
        if output.exists():
            existing = pd.read_csv(output, dtype=str, keep_default_na=False)
            if "enrichment_ip" in existing.columns:
                existing = existing.drop_duplicates(subset=["enrichment_ip"])
                records = existing.to_dict("records")
                completed_ips = set(existing["enrichment_ip"])
                print(f"{api_name}: resuming {len(completed_ips)}/{len(ips)} checkpointed IPs")
        for index, ip in enumerate(ips, start=1):
            if ip in completed_ips:
                continue
            status, data, detail = request_json(api_name, ip)
            records.append(parse_result(api_name, ip, status, data, detail))
            completed_ips.add(ip)
            pd.DataFrame(records).to_csv(output, index=False)
            print(f"{api_name} [{len(completed_ips)}/{len(ips)}] {ip}: {status}", flush=True)
            time.sleep(VIRUSTOTAL_DELAY_SECONDS if api_name == "virustotal" else 0.2)
        result = pd.DataFrame(records)
        if result["enrichment_ip"].duplicated().any():
            raise ValueError(f"{api_name}: duplicate enrichment_ip rows")
        result.to_csv(output, index=False)
        print(f"Wrote {output} ({len(result)} rows)")


if __name__ == "__main__":
    main()
