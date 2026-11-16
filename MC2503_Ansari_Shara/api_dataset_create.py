
import os
import json
import random
import ipaddress
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv

from src.abuse_ipdb import AbuseIPDB
from src.ipinfo_api import IPInfo


# ============================================================
# CONFIGURATION
# ============================================================

load_dotenv()

AUTH_FILE = Path("data/processed/authentication_dataset_cleaned.csv")
EXISTING_FILE = Path("SecureShare_API_Dataset_v2.xlsx")
OUTPUT_FILE = Path("API dataset.csv")
CACHE_FILE = Path("data/processed/ip_api_cache.json")

# Safety limit: maximum NEW IP addresses queried in this run.
# Cached IPs will not be queried again.
MAX_NEW_IP_LOOKUPS = 900

RANDOM_SEED = 42


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def clean_value(value):
    """Convert missing values into empty strings."""
    if pd.isna(value):
        return ""
    return value


def load_cache():
    CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)

    if CACHE_FILE.exists():
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            print("Warning: Cache could not be read. Starting a new cache.")

    return {}


def save_cache(cache):
    CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)

    temporary_file = CACHE_FILE.with_suffix(".tmp")

    with open(temporary_file, "w", encoding="utf-8") as f:
        json.dump(cache, f, indent=2, ensure_ascii=False)

    temporary_file.replace(CACHE_FILE)


def valid_public_ip(value):
    """Only consider valid, globally routable IP addresses."""
    try:
        address = ipaddress.ip_address(str(value).strip())
        return address.is_global
    except ValueError:
        return False


def safe_api_call(api_object, method_name, identifier):
    """Keep the script running if an API wrapper raises an exception."""
    try:
        result = getattr(api_object, method_name)(identifier)

        if isinstance(result, dict):
            return result

        return {"error": "Unexpected API response format"}

    except Exception as exc:
        return {"error": str(exc)}


def has_value(value):
    """Return True when a value is not blank or a missing-value marker."""
    if value is None:
        return False

    if isinstance(value, (dict, list)):
        return bool(value)

    return str(value).strip().lower() not in {
        "", "nan", "none", "null"
    }


# ============================================================
# LOAD DATASETS
# ============================================================

print("=" * 65)
print("SECURESHARE - API DATASET COLLECTION")
print("=" * 65)

if not AUTH_FILE.exists():
    raise FileNotFoundError(f"Authentication dataset not found: {AUTH_FILE}")

if not EXISTING_FILE.exists():
    raise FileNotFoundError(f"Existing API workbook not found: {EXISTING_FILE}")

auth_df = pd.read_csv(AUTH_FILE)
file_df = pd.read_excel(EXISTING_FILE)

if "ip_address" not in auth_df.columns:
    raise ValueError("The authentication dataset has no ip_address column.")

if "File SHA-256" not in file_df.columns:
    raise ValueError("The existing workbook has no File SHA-256 column.")

print(f"Authentication records: {len(auth_df)}")
print(f"Existing file/API records: {len(file_df)}")

# Deduplicate IPs while preserving their original order.
all_ips = (
    auth_df["ip_address"]
    .dropna()
    .astype(str)
    .str.strip()
)

all_ips = list(dict.fromkeys(
    ip for ip in all_ips
    if valid_public_ip(ip)
))

print(f"Valid globally routable unique IPs: {len(all_ips)}")


# ============================================================
# INITIALIZE APIS
# ============================================================

abuse_ipdb = AbuseIPDB()
ipinfo = IPInfo()

cache = load_cache()

cached_ips = [ip for ip in all_ips if ip in cache]
uncached_ips = [ip for ip in all_ips if ip not in cache]

random.seed(RANDOM_SEED)
random.shuffle(uncached_ips)

selected_new_ips = uncached_ips[:MAX_NEW_IP_LOOKUPS]

print(f"Cached IPs available: {len(cached_ips)}")
print(f"New IPs selected for lookup: {len(selected_new_ips)}")
print(f"New IPs not queried in this run: "
      f"{len(uncached_ips) - len(selected_new_ips)}")

# Do not query every IP automatically.
# Existing cached results are reused.


# ============================================================
# COLLECT ABUSEIPDB + IPINFO DATA
# ============================================================

print("\nCollecting IP intelligence...")

for number, ip in enumerate(selected_new_ips, start=1):
    print(f"[{number}/{len(selected_new_ips)}] Checking {ip}")

    abuse_result = safe_api_call(abuse_ipdb, "check_ip", ip)
    ipinfo_result = safe_api_call(ipinfo, "lookup_ip", ip)

    cache[ip] = {
        "abuseipdb": abuse_result,
        "ipinfo": ipinfo_result
    }

    # Save after each IP so an interruption does not lose all progress.
    save_cache(cache)

print("IP collection stage finished.")


# ============================================================
# BUILD IP API RECORDS
# ============================================================

ip_rows = []

for ip in all_ips:
    if ip not in cache:
        continue

    cached = cache[ip]
    abuse = cached.get("abuseipdb", {})
    info = cached.get("ipinfo", {})

    row = {
        "Entity Type": "IP",
        "Entity Identifier": ip,
        "IP Address": ip,

        "AbuseIPDB Abuse Confidence Score":
            abuse.get("abuse_confidence_score", ""),
        "AbuseIPDB Total Reports":
            abuse.get("total_reports", ""),
        "AbuseIPDB Country Code":
            abuse.get("country_code", ""),
        "AbuseIPDB Usage Type":
            abuse.get("usage_type", ""),
        "AbuseIPDB ISP":
            abuse.get("isp", ""),
        "AbuseIPDB Domain":
            abuse.get("domain", ""),
        "AbuseIPDB Is Whitelisted":
            abuse.get("is_whitelisted", ""),
        "AbuseIPDB Last Reported At":
            abuse.get("last_reported_at", ""),
        "AbuseIPDB Error":
            abuse.get("error", ""),

        "IPinfo Hostname": info.get("hostname", ""),
        "IPinfo City": info.get("city", ""),
        "IPinfo Region": info.get("region", ""),
        "IPinfo Country": info.get("country", ""),
        "IPinfo Location": info.get("location", ""),
        "IPinfo Organization": info.get("organization", ""),
        "IPinfo Postal": info.get("postal", ""),
        "IPinfo Timezone": info.get("timezone", ""),
        "IPinfo Error": info.get("error", "")
    }

    ip_rows.append(row)

ip_api_df = pd.DataFrame(ip_rows)

print(f"IP API records available: {len(ip_api_df)}")


# ============================================================
# BUILD FILE API RECORDS
# Use existing genuine results; do not make unnecessary
# VirusTotal, MalwareBazaar or URLHaus requests here.
# ============================================================

file_rows = []

for _, source in file_df.iterrows():
    file_hash = clean_value(source.get("File SHA-256", ""))

    if not has_value(file_hash):
        continue

    row = {
        "Entity Type": "FILE",
        "Entity Identifier": str(file_hash).strip(),
        "File Name": clean_value(source.get("File Name", "")),
        "File SHA-256": str(file_hash).strip(),

        "VirusTotal Found": clean_value(source.get("VT Found", "")),
        "VirusTotal Malicious": clean_value(source.get("VT Malicious", "")),
        "VirusTotal Suspicious": clean_value(source.get("VT Suspicious", "")),
        "VirusTotal Harmless": clean_value(source.get("VT Harmless", "")),
        "VirusTotal Undetected": clean_value(source.get("VT Undetected", "")),
        "VirusTotal Error": clean_value(source.get("VT Error", "")),

        "MalwareBazaar Found": clean_value(source.get("MB Found", "")),
        "MalwareBazaar Malicious": clean_value(source.get("MB Malicious", "")),
        "MalwareBazaar Query Status": clean_value(
            source.get("MB Query Status", "")
        ),
        "MalwareBazaar Error": clean_value(source.get("MB Error", "")),

        "URLHaus URLs Found": clean_value(source.get("URLs Found", "")),
        "URLHaus Malicious Count": clean_value(
            source.get("URLhaus Malicious Count", "")
        ),
        "URLHaus Not Found Count": clean_value(
            source.get("URLhaus Not Found Count", "")
        ),
        "URLHaus Error Count": clean_value(
            source.get("URLhaus Error Count", "")
        )
    }

    file_rows.append(row)

file_api_df = pd.DataFrame(file_rows)

print(f"Existing file API records retained: {len(file_api_df)}")


# ============================================================
# COMBINE AS A TYPED API RECORD REGISTER
# IP and file rows have different entity identifiers.
# They will NOT be falsely joined to each other.
# ============================================================

final_df = pd.concat(
    [ip_api_df, file_api_df],
    ignore_index=True,
    sort=False
)

# Remove columns that are empty for every record.
final_df = final_df.replace(
    {"": pd.NA, "nan": pd.NA, "None": pd.NA, "null": pd.NA}
)

final_df = final_df.dropna(axis=1, how="all")

# Keep each entity/API record unique.
before = len(final_df)
final_df = final_df.drop_duplicates()
duplicates_removed = before - len(final_df)

# Ensure no database usernames or unrelated NVD/MITRE columns are included.
excluded_terms = ["username", "nvd", "mitre"]

final_df = final_df[
    [
        column for column in final_df.columns
        if not any(term in column.lower() for term in excluded_terms)
    ]
]

# Put entity identifiers first.
preferred_order = [
    "Entity Type",
    "Entity Identifier",
    "IP Address",
    "AbuseIPDB Abuse Confidence Score",
    "AbuseIPDB Total Reports",
    "AbuseIPDB Country Code",
    "AbuseIPDB Usage Type",
    "AbuseIPDB ISP",
    "AbuseIPDB Domain",
    "AbuseIPDB Is Whitelisted",
    "AbuseIPDB Last Reported At",
    "AbuseIPDB Error",
    "IPinfo Hostname",
    "IPinfo City",
    "IPinfo Region",
    "IPinfo Country",
    "IPinfo Location",
    "IPinfo Organization",
    "IPinfo Postal",
    "IPinfo Timezone",
    "IPinfo Error",
    "File Name",
    "File SHA-256",
    "VirusTotal Found",
    "VirusTotal Malicious",
    "VirusTotal Suspicious",
    "VirusTotal Harmless",
    "VirusTotal Undetected",
    "VirusTotal Error",
    "MalwareBazaar Found",
    "MalwareBazaar Malicious",
    "MalwareBazaar Query Status",
    "MalwareBazaar Error",
    "URLHaus URLs Found",
    "URLHaus Malicious Count",
    "URLHaus Not Found Count",
    "URLHaus Error Count"
]

ordered = [c for c in preferred_order if c in final_df.columns]
remaining = [c for c in final_df.columns if c not in ordered]
final_df = final_df[ordered + remaining]

final_df.to_csv(OUTPUT_FILE, index=False, encoding="utf-8-sig")


# ============================================================
# COLLECTION SUMMARY
# ============================================================

print("\n" + "=" * 65)
print("API DATASET CREATED")
print("=" * 65)
print(f"Output: {OUTPUT_FILE}")
print(f"Rows: {len(final_df)}")
print(f"Columns: {len(final_df.columns)}")
print(f"IP records: {(final_df['Entity Type'] == 'IP').sum()}")
print(f"File records: {(final_df['Entity Type'] == 'FILE').sum()}")
print(f"Duplicate rows removed: {duplicates_removed}")
print(f"Cache file: {CACHE_FILE}")
print("\nAPIs represented:")
print("1. AbuseIPDB")
print("2. IPinfo")
print("3. VirusTotal (existing results)")
print("4. MalwareBazaar (existing results)")
print("5. URLHaus (existing results)")
print("\nExcluded: usernames, NVD, MITRE ATT&CK")
print("=" * 65)
