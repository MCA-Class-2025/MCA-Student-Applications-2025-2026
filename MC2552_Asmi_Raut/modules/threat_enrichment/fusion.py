# """
# fusion.py

# Fuses the base NSL-KDD dataset with all 5 API datasets into one validated
# final CSV: data/api_results/fused_threat_dataset.csv

# Fusion strategy (see module docstrings in modules/api/*.py for the full
# reasoning behind each join key)
# ------------------------------------------------------------------------
# Two of the five APIs (MITRE ATT&CK, NVD) share a real join key with the
# base dataset: `attack`. Those are merged with a LEFT JOIN on `attack`,
# which preserves every one of the base dataset's 23 attack categories
# (and, by extension, all 125,973 underlying rows) regardless of whether an
# API had a match — this is exactly the join type required by the spec:
# "preserve the intended population of the base dataset".

# For NVD specifically, a single attack category can map to multiple CVEs
# (one-to-many). To avoid uncontrolled row multiplication in the per-category
# grain, only the highest-CVSS CVE per attack is kept in the fused table; the
# complete one-to-many result is preserved separately in nvd_data.csv.

# The other three APIs (URLhaus, VirusTotal, AbuseIPDB) have NO valid join
# key against NSL-KDD (no URLs/hashes/IPs exist in the dataset). Per the
# project requirement ("do not perform an arbitrary Cartesian join or
# approximate join simply to make the fusion work"), these are NOT forced
# onto the network-traffic rows. Instead they are UNIONED into the final
# table as their own rows, tagged `record_type = threat_intel_ioc`, clearly
# distinguished from `record_type = network_traffic_category` rows. This
# keeps the final CSV = base dataset + all 5 APIs, without fabricating a
# relationship that doesn't exist in the data.
# """

# import os
# from typing import Dict, List

# import pandas as pd

# from modules.api.base_client import logger
# from modules.threat_enrichment.validation import validate_merge, print_report

# BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# OUTPUT_DIR = os.path.join(BASE_DIR, "data", "api_results")
# FUSED_PATH = os.path.join(OUTPUT_DIR, "fused_threat_dataset.csv")


# def _top_cve_per_attack(nvd_df: pd.DataFrame) -> pd.DataFrame:
#     """Collapse NVD's one-to-many attack->CVE rows to the single highest-CVSS CVE per attack."""
#     df = nvd_df.copy()
#     df["cvss_score_numeric"] = pd.to_numeric(df["cvss_score"], errors="coerce")
#     df = df.sort_values("cvss_score_numeric", ascending=False)
#     top = df.drop_duplicates(subset=["attack"], keep="first")
#     return top.drop(columns=["cvss_score_numeric"])


# def fuse(
#     base_summary: pd.DataFrame,
#     mitre_df: pd.DataFrame,
#     nvd_df: pd.DataFrame,
#     urlhaus_df: pd.DataFrame,
#     virustotal_df: pd.DataFrame,
#     abuseipdb_df: pd.DataFrame,
# ) -> pd.DataFrame:
#     """Build the final fused dataset. Returns the fused dataframe and writes it to CSV."""
#     merge_reports: List[Dict] = []

#     # --- Part A: network_traffic_category rows (base + MITRE + NVD) -----
#     fused = base_summary.copy()
#     rows_before = len(fused)

#     mitre_join_cols = [c for c in mitre_df.columns if c not in ("count_in_dataset",)]
#     fused = fused.merge(mitre_df[mitre_join_cols], on="attack", how="left")
#     merge_reports.append(validate_merge(base_summary, fused, "base+MITRE", "left"))

#     nvd_top = _top_cve_per_attack(nvd_df)
#     nvd_join_cols = [c for c in nvd_top.columns if c not in ("count_in_dataset",)]
#     before_nvd = fused.copy()
#     fused = fused.merge(nvd_top[nvd_join_cols], on="attack", how="left", suffixes=("", "_nvd"))
#     merge_reports.append(validate_merge(before_nvd, fused, "+NVD", "left"))

#     fused["record_type"] = "network_traffic_category"
#     fused["source_apis"] = "MITRE_ATTACK, NVD"

#     if len(fused) != rows_before:
#         logger.warning(
#             f"[FUSION] Row count changed for network_traffic_category rows: "
#             f"{rows_before} -> {len(fused)}. Investigate before trusting this output."
#         )
#     else:
#         logger.info(f"[FUSION] network_traffic_category grain preserved: {len(fused)} rows "
#                      f"(matches base dataset's {rows_before} unique attack categories).")

#     # --- Part B: threat_intel_ioc rows (URLhaus + VirusTotal + AbuseIPDB) --
#     ioc_frames = []

#     uh = urlhaus_df.copy()
#     uh["record_type"] = "threat_intel_ioc"
#     uh["source_apis"] = "URLhaus"
#     uh["ioc_value"] = uh.get("url", "")
#     uh["ioc_type"] = "url"
#     ioc_frames.append(uh)

#     vt = virustotal_df.copy()
#     vt["record_type"] = "threat_intel_ioc"
#     vt["source_apis"] = "VirusTotal"
#     vt["ioc_value"] = vt.get("ioc", "")
#     ioc_frames.append(vt)

#     ab = abuseipdb_df.copy()
#     ab["record_type"] = "threat_intel_ioc"
#     ab["source_apis"] = "AbuseIPDB"
#     ab["ioc_value"] = ab.get("ip_address", "")
#     ab["ioc_type"] = "ip_address"
#     ioc_frames.append(ab)

#     ioc_union = pd.concat(ioc_frames, ignore_index=True, sort=False)
#     logger.info(f"[FUSION] threat_intel_ioc rows unioned: {len(ioc_union)} "
#                 f"(URLhaus={len(uh)}, VirusTotal={len(vt)}, AbuseIPDB={len(ab)})")

#     # --- Final union of both parts ---------------------------------------
#     final_df = pd.concat([fused, ioc_union], ignore_index=True, sort=False)

#     # Clean up: no unintended _x/_y suffix columns should exist.
#     suffix_cols = [c for c in final_df.columns if c.endswith("_x") or c.endswith("_y")]
#     if suffix_cols:
#         logger.warning(f"[FUSION] Unexpected merge-suffix columns found: {suffix_cols}")

#     duplicate_key_count = int(
#         final_df[final_df["record_type"] == "network_traffic_category"]["attack"].duplicated().sum()
#     )

#     final_df.to_csv(FUSED_PATH, index=False)

#     logger.info(f"[FUSION] Final fused dataset written: {FUSED_PATH}")
#     logger.info(f"[FUSION] Final shape: {final_df.shape[0]} rows x {final_df.shape[1]} columns")

#     print_report(merge_reports, "MERGE VALIDATION REPORT")

#     _print_final_summary(base_summary, final_df, merge_reports, duplicate_key_count)

#     return final_df


# def _print_final_summary(base_summary, final_df, merge_reports, duplicate_key_count):
#     print("\n" + "=" * 60)
#     print("FINAL VERIFICATION REPORT")
#     print("=" * 60)
#     print(f"Base dataset (unique attack categories): {len(base_summary)}")
#     print(f"Final fused rows: {len(final_df)}")
#     print(f"Final fused columns: {len(final_df.columns)}")
#     print(f"Duplicate attack keys (network_traffic_category rows): {duplicate_key_count}")
#     print(f"record_type breakdown:\n{final_df['record_type'].value_counts().to_string()}")
#     print(f"Final CSV path: {FUSED_PATH}")
#     print("=" * 60)


# if __name__ == "__main__":
#     from modules.threat_enrichment.pipeline import run_all

#     results = run_all()
#     fuse(
#         results["base_summary"],
#         results["mitre"],
#         results["nvd"],
#         results["urlhaus"],
#         results["virustotal"],
#         results["abuseipdb"],
#     )







from __future__ import annotations
import os
from typing import List
import pandas as pd
from modules.api.base_client import logger

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUTPUT_DIR = os.path.join(BASE_DIR, "data", "api_results")
FUSED_PATH = os.path.join(OUTPUT_DIR, "fused_threat_dataset.csv")

NSL_KDD_COLUMNS = [
    "duration","protocol_type","service","flag","src_bytes","dst_bytes",
    "land","wrong_fragment","urgent","hot","num_failed_logins","logged_in",
    "num_compromised","root_shell","su_attempted","num_root","num_file_creations",
    "num_shells","num_access_files","num_outbound_cmds","is_host_login",
    "is_guest_login","count","srv_count","serror_rate","srv_serror_rate",
    "rerror_rate","srv_rerror_rate","same_srv_rate","diff_srv_rate",
    "srv_diff_host_rate","dst_host_count","dst_host_srv_count","dst_host_same_srv_rate",
    "dst_host_diff_srv_rate","dst_host_same_src_port_rate","dst_host_srv_diff_host_rate",
    "dst_host_serror_rate","dst_host_srv_serror_rate","dst_host_rerror_rate",
    "dst_host_srv_rerror_rate","attack","difficulty_level"
]

def _find_base_dataset():
    candidates = [
        os.path.join(BASE_DIR,"data","sample_network_data","KDDTrain+.txt"),
        os.path.join(BASE_DIR,"KDDTrain+.txt")
    ]
    for p in candidates:
        if os.path.isfile(p): return p
    for root, _, files in os.walk(BASE_DIR):
        if "KDDTrain+.txt" in files: return os.path.join(root,"KDDTrain+.txt")
    raise FileNotFoundError("KDDTrain+.txt not found under the project folder.")

def load_full_nsl_kdd():
    path = _find_base_dataset()
    df = pd.read_csv(path, header=None)
    if df.shape[1] != 43:
        raise ValueError(f"KDDTrain+.txt must have 43 columns; found {df.shape[1]}.")
    df.columns = NSL_KDD_COLUMNS
    df.insert(0,"record_id",range(1,len(df)+1))
    df["record_type"] = "network_traffic"
    df["source_apis"] = ""
    return df

def _full_base(base_summary):
    if base_summary is not None and "attack" in base_summary.columns and len(base_summary) >= 1000:
        df = base_summary.copy()
        if "record_id" not in df.columns: df.insert(0,"record_id",range(1,len(df)+1))
        if "record_type" not in df.columns: df["record_type"]="network_traffic"
        if "source_apis" not in df.columns: df["source_apis"]=""
        return df
    logger.info("[FUSION] Reloading complete KDDTrain+.txt instead of 23-row attack summary.")
    return load_full_nsl_kdd()

def _top_nvd(nvd_df):
    if nvd_df is None or nvd_df.empty or "attack" not in nvd_df.columns:
        return pd.DataFrame()
    df=nvd_df.copy()
    df["_cvss"] = pd.to_numeric(df.get("cvss_score"),errors="coerce")
    df=df.sort_values(["attack","_cvss"],ascending=[True,False],na_position="last")
    return df.drop_duplicates("attack",keep="first").drop(columns="_cvss")

def _merge_attack(base, api_df, prefix):
    if api_df is None or api_df.empty or "attack" not in api_df.columns: return base
    e=api_df.drop_duplicates("attack",keep="first").copy()
    e=e.drop(columns=["count_in_dataset"],errors="ignore")
    rename={c:f"{prefix}_{c}" for c in e.columns if c!="attack" and c not in base.columns}
    e=e.rename(columns=rename)
    cols=["attack"]+[c for c in e.columns if c!="attack"]
    before=len(base)
    out=base.merge(e[cols],on="attack",how="left",validate="many_to_one")
    if len(out)!=before: raise RuntimeError(f"{prefix} merge changed base rows: {before}->{len(out)}")
    return out

def fuse(base_summary, mitre_df, nvd_df, urlhaus_df, virustotal_df, abuseipdb_df):
    os.makedirs(OUTPUT_DIR,exist_ok=True)
    base=_full_base(base_summary)
    original_rows=len(base)
    base=_merge_attack(base,mitre_df,"mitre")
    base=_merge_attack(base,_top_nvd(nvd_df),"nvd")
    sources=[]
    if mitre_df is not None and not mitre_df.empty: sources.append("MITRE_ATTACK")
    if nvd_df is not None and not nvd_df.empty: sources.append("NVD")
    base["source_apis"]=", ".join(sources)
    base["record_type"]="network_traffic"

    iocs=[]
    if urlhaus_df is not None and not urlhaus_df.empty:
        x=urlhaus_df.copy(); x["record_type"]="threat_intel_ioc"; x["source_apis"]="URLhaus"; x["ioc_type"]="url"; x["ioc_value"]=x.get("url",""); iocs.append(x)
    if virustotal_df is not None and not virustotal_df.empty:
        x=virustotal_df.copy(); x["record_type"]="threat_intel_ioc"; x["source_apis"]="VirusTotal"; x["ioc_type"]=x.get("ioc_type","file_hash"); x["ioc_value"]=x.get("ioc",""); iocs.append(x)
    if abuseipdb_df is not None and not abuseipdb_df.empty:
        x=abuseipdb_df.copy(); x["record_type"]="threat_intel_ioc"; x["source_apis"]="AbuseIPDB"; x["ioc_type"]="ip_address"; x["ioc_value"]=x.get("ip_address",""); iocs.append(x)
    ioc_union=pd.concat(iocs,ignore_index=True,sort=False) if iocs else pd.DataFrame()
    final=pd.concat([base,ioc_union],ignore_index=True,sort=False)

    first=["record_id","record_type","source_apis","attack","duration","protocol_type","service","flag","src_bytes","dst_bytes","difficulty_level","ioc_type","ioc_value"]
    first=[c for c in first if c in final.columns]
    final=final[first+[c for c in final.columns if c not in first]]

    network_rows=int((final["record_type"]=="network_traffic").sum())
    ioc_rows=sum(len(x) for x in [urlhaus_df,virustotal_df,abuseipdb_df] if x is not None)
    expected=original_rows+ioc_rows
    if network_rows!=original_rows: raise RuntimeError(f"VALIDATION FAILED: network rows {network_rows}, expected {original_rows}")
    if len(final)!=expected: raise RuntimeError(f"VALIDATION FAILED: final rows {len(final)}, expected {expected}")
    final.to_csv(FUSED_PATH,index=False)
    print("="*65)
    print("FINAL FUSION VERIFICATION")
    print(f"Original NSL-KDD rows : {original_rows}")
    print(f"Network rows          : {network_rows}")
    print(f"URLhaus rows          : {len(urlhaus_df) if urlhaus_df is not None else 0}")
    print(f"VirusTotal rows       : {len(virustotal_df) if virustotal_df is not None else 0}")
    print(f"AbuseIPDB rows        : {len(abuseipdb_df) if abuseipdb_df is not None else 0}")
    print(f"Final rows             : {len(final)}")
    print(f"Final columns          : {len(final.columns)}")
    print(f"Output                 : {FUSED_PATH}")
    print("="*65)
    return final

if __name__ == "__main__":
    from modules.threat_enrichment.pipeline import run_all
    r=run_all()
    fuse(r.get("base_summary"),r["mitre"],r["nvd"],r["urlhaus"],r["virustotal"],r["abuseipdb"])
