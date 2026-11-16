"""
pipeline.py

Orchestrates the full 5-API enrichment pipeline on top of the EXISTING
SecureSense AI project. Does not modify the existing NSL-KDD dataset,
the existing Isolation Forest model, or any existing module — it only
reads from them.

Steps (matches the required execution order):
    1. Load the existing NSL-KDD dataset (unchanged, read-only).
    2. Run the EXISTING Isolation Forest predictor to get Normal/Anomaly
       predictions (reuses modules.anomaly_detection.predictor.predict).
    3. Reduce to the 23 unique attack categories with row counts + majority
       prediction (NOT one API call per 125,973 rows — see design note).
    4. Call MITRE ATT&CK for each unique attack category -> mitre_attack_data.csv
    5. Call NVD for each unique attack category -> nvd_data.csv
    6. Call URLhaus for recent malicious URLs (independent IOC feed) -> urlhaus_data.csv
    7. Call VirusTotal for the seed IOC hash list -> virustotal_data.csv
    8. Call AbuseIPDB for the seed IOC IP list -> abuseipdb_data.csv
    9. Validate every dataset before/after generation.
   10. Hand off to fusion.py to build the final fused CSV.

Design note on why we don't call APIs per-row
-----------------------------------------------
KDDTrain+ has 125,973 rows but only 23 unique `attack` values. Calling
MITRE/NVD once per unique category (23 calls) instead of once per row
(125,973 calls) avoids rate-limit failures and is the standard "dimension
table" pattern: enrich the small set of distinct categories, then join
that back onto the full-grain dataset in fusion.py. No information is
lost — every one of the 125,973 rows still receives its enrichment via the
join on `attack` in fusion.py.
"""

import os
from typing import Dict

import pandas as pd

from modules.api import mitre_attack, nvd, urlhaus, virustotal, abuseipdb
from modules.api.base_client import logger
from modules.threat_enrichment import config
from modules.threat_enrichment.validation import validate_dataframe, print_report

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATASET_PATH = os.path.join(BASE_DIR, "data", "sample_network_data", "KDDTrain+.txt")
OUTPUT_DIR = os.path.join(BASE_DIR, "data", "api_results")

os.makedirs(OUTPUT_DIR, exist_ok=True)

NSL_KDD_COLUMNS = [
    "duration", "protocol_type", "service", "flag", "src_bytes", "dst_bytes",
    "land", "wrong_fragment", "urgent", "hot", "num_failed_logins", "logged_in",
    "num_compromised", "root_shell", "su_attempted", "num_root", "num_file_creations",
    "num_shells", "num_access_files", "num_outbound_cmds", "is_host_login",
    "is_guest_login", "count", "srv_count", "serror_rate", "srv_serror_rate",
    "rerror_rate", "srv_rerror_rate", "same_srv_rate", "diff_srv_rate",
    "srv_diff_host_rate", "dst_host_count", "dst_host_srv_count",
    "dst_host_same_srv_rate", "dst_host_diff_srv_rate", "dst_host_same_src_port_rate",
    "dst_host_srv_diff_host_rate", "dst_host_serror_rate", "dst_host_srv_serror_rate",
    "dst_host_rerror_rate", "dst_host_srv_rerror_rate", "attack", "difficulty",
]


def load_base_dataset() -> pd.DataFrame:
    """Load the existing NSL-KDD dataset exactly as-is (read-only)."""
    df = pd.read_csv(DATASET_PATH, header=None)
    df.columns = NSL_KDD_COLUMNS
    logger.info(f"[PIPELINE] Loaded base dataset: {len(df)} rows, {len(df.columns)} columns from {DATASET_PATH}")
    return df


def get_attack_summary(df: pd.DataFrame) -> pd.DataFrame:
    """
    Reduce the full dataset to one row per unique attack category, with the
    row count and the model's predicted-anomaly rate for that category.
    Runs the EXISTING trained model — does not retrain or modify it.
    """
    from modules.anomaly_detection.predictor import predict

    feature_df = df.drop(columns=["attack", "difficulty"]).copy()
    predictions = predict(feature_df)

    working = df.copy()
    working["prediction"] = predictions

    summary = (
        working.groupby("attack")
        .agg(
            count_in_dataset=("attack", "size"),
            anomaly_rate_pct=("prediction", lambda s: round((s == "Anomaly").mean() * 100, 2)),
        )
        .reset_index()
        .sort_values("count_in_dataset", ascending=False)
    )

    logger.info(f"[PIPELINE] Reduced {len(df)} rows to {len(summary)} unique attack categories.")
    return summary


def run_mitre(attack_counts: Dict[str, int]) -> pd.DataFrame:
    logger.info("[PIPELINE] Running API 1: MITRE ATT&CK ...")
    records = mitre_attack.enrich_attack_categories(attack_counts)
    df = pd.DataFrame(records)
    path = os.path.join(OUTPUT_DIR, "mitre_attack_data.csv")
    df.to_csv(path, index=False)
    validate_dataframe(df, "mitre_attack_data.csv", join_key="attack")
    logger.info(f"[PIPELINE] Wrote {path} ({len(df)} rows)")
    return df


def run_nvd(attack_counts: Dict[str, int]) -> pd.DataFrame:
    logger.info("[PIPELINE] Running API 2: NVD ...")
    records = nvd.enrich_attack_categories(attack_counts)
    df = pd.DataFrame(records)
    path = os.path.join(OUTPUT_DIR, "nvd_data.csv")
    df.to_csv(path, index=False)
    validate_dataframe(df, "nvd_data.csv", join_key="attack")
    logger.info(f"[PIPELINE] Wrote {path} ({len(df)} rows)")
    return df


def run_urlhaus() -> pd.DataFrame:
    logger.info("[PIPELINE] Running API 3: URLhaus ...")
    records = urlhaus.fetch_recent_urls(limit=25)
    df = pd.DataFrame(records)
    path = os.path.join(OUTPUT_DIR, "urlhaus_data.csv")
    df.to_csv(path, index=False)
    validate_dataframe(df, "urlhaus_data.csv", join_key="url")
    logger.info(f"[PIPELINE] Wrote {path} ({len(df)} rows)")
    return df


def run_virustotal() -> pd.DataFrame:
    logger.info("[PIPELINE] Running API 4: VirusTotal ...")
    records = virustotal.enrich_iocs(config.VT_SEED_HASHES)
    df = pd.DataFrame(records)
    path = os.path.join(OUTPUT_DIR, "virustotal_data.csv")
    df.to_csv(path, index=False)
    validate_dataframe(df, "virustotal_data.csv", join_key="ioc")
    logger.info(f"[PIPELINE] Wrote {path} ({len(df)} rows)")
    return df


def run_abuseipdb() -> pd.DataFrame:
    logger.info("[PIPELINE] Running API 5: AbuseIPDB ...")
    records = abuseipdb.enrich_ips(config.ABUSEIPDB_SEED_IPS)
    df = pd.DataFrame(records)
    path = os.path.join(OUTPUT_DIR, "abuseipdb_data.csv")
    df.to_csv(path, index=False)
    validate_dataframe(df, "abuseipdb_data.csv", join_key="ip_address")
    logger.info(f"[PIPELINE] Wrote {path} ({len(df)} rows)")
    return df


def run_all() -> Dict[str, pd.DataFrame]:
    """Run the full pipeline end to end and return every dataframe produced."""
    base_df = load_base_dataset()
    summary_df = get_attack_summary(base_df)
    attack_counts = dict(zip(summary_df["attack"], summary_df["count_in_dataset"]))

    results = {
        "base_summary": summary_df,
        "mitre": run_mitre(attack_counts),
        "nvd": run_nvd(attack_counts),
        "urlhaus": run_urlhaus(),
        "virustotal": run_virustotal(),
        "abuseipdb": run_abuseipdb(),
    }

    print_report(
        [validate_dataframe(v, k, join_key="attack" if k in ("mitre", "nvd") else "n/a")
         for k, v in results.items() if k != "base_summary"],
        "PRE-FUSION VALIDATION SUMMARY",
    )

    return results


if __name__ == "__main__":
    run_all()
    print("\nAll 5 API CSVs generated in data/api_results/. Run fusion.py next.")
