"""
Fuse the external Kaggle "Dance Styles & Genres" dataset with DanceCompass AI's
curated 20-form dataset and the existing 5-API merged dataset.

Source: https://www.kaggle.com/datasets/melissamonfared/dances
Local copy: kaggle_data/dance_styles_kaggle.csv  (206 rows, 18 columns)

QA findings (see kaggle_data/qa_findings.csv, produced by this script):
  - The 'Origin' column defaults to "United States" for 135 of 206 rows (65.5%),
    including for dances that are demonstrably NOT of US origin (Ballet, Salsa,
    Flamenco). It is not used as a trusted source for origin/geography.
  - 'Dance Type' mislabels both matched Indian classical forms (Bharatanatyam,
    Odissi) as "Belly dance". It is not used as a trusted category label for
    those two rows; the raw value is still carried through, tagged as
    unverified, for transparency.
  - Because of the two issues above, only the lower-risk supplementary columns
    (Hardness Ratio, Tempo (BPM), Dance Formation, Learning Difficulty,
    Associated Music Genre, Health Benefits) are treated as usable enrichment.
    'Origin' and 'Dance Type' are carried through as *_raw_unverified columns
    instead of overwriting anything in the curated dataset.

This script never modifies data/dance_forms.json or data/dancecompass_merged.csv;
it writes a new file, kaggle_data/dancecompass_kaggle_fused.csv.
"""

import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
CURATED_JSON = ROOT / "data" / "dance_forms.json"
KAGGLE_CSV = Path(__file__).resolve().parent / "dance_styles_kaggle.csv"
OUT_CSV = Path(__file__).resolve().parent / "dancecompass_kaggle_fused.csv"
QA_CSV = Path(__file__).resolve().parent / "qa_findings.csv"

# Hand-verified alias map: curated dance name -> exact Kaggle 'Dance style' value.
# Built by inspecting all 197 unique Kaggle dance-style names against the 20
# curated names (see project chat for the matching process). Only exact,
# unambiguous matches are included; near-miss substring matches (e.g.
# "Kathakali" ~ "Haka") were checked and rejected as false positives.
ALIAS_MAP = {
    "Bharatanatyam": "Bharat Natyam",
    "Odissi": "Odissi",
    "Bhangra": "Bhangra",
    "Ballet": "Ballet",
    "Salsa": "Salsa",
    "Flamenco": "Flamenco",
    "Hip-Hop": "Hip-hop dance",
    "Tango": "Argentine tango",
    "Contemporary": "Contemporary dance",
    "Belly Dance": "Belly dance",
    "Tap Dance": "tap dancing",
    "Breaking (Breakdance)": "Break dancing",
}

# Columns judged low-risk to carry over as genuine enrichment.
SAFE_COLUMNS = {
    "Hardness Ratio": "kaggle_hardness_ratio",
    "Tempo (BPM)": "kaggle_tempo_bpm",
    "Dance Formation": "kaggle_dance_formation",
    "Learning Difficulty": "kaggle_learning_difficulty",
    "Associated Music Genre": "kaggle_associated_music_genre",
    "Health Benefits": "kaggle_health_benefits",
}

# Columns known to be unreliable for at least one matched row; carried
# through unmodified but explicitly labeled unverified, never used to
# override the curated dataset's own origin_region/category fields.
UNVERIFIED_COLUMNS = {
    "Origin": "kaggle_origin_raw_unverified",
    "Dance Type": "kaggle_dance_type_raw_unverified",
}


def load_curated() -> list:
    with open(CURATED_JSON, "r", encoding="utf-8") as f:
        return json.load(f)


def run_qa(kaggle_df: pd.DataFrame) -> pd.DataFrame:
    total = len(kaggle_df)
    us_count = (kaggle_df["Origin"].str.strip() == "United States").sum()
    findings = [
        {
            "check": "Origin defaults to 'United States'",
            "affected_rows": int(us_count),
            "total_rows": total,
            "pct": round(100 * us_count / total, 1),
            "verdict": "UNRELIABLE - not used to override curated origin_region",
        },
    ]
    for curated_name, kaggle_name in ALIAS_MAP.items():
        row = kaggle_df[kaggle_df["Dance style"].str.strip() == kaggle_name]
        if row.empty:
            continue
        dtype = row.iloc[0]["Dance Type"]
        if curated_name in ("Bharatanatyam", "Odissi") and "belly" in str(dtype).lower():
            findings.append({
                "check": f"Dance Type mislabeled for '{curated_name}'",
                "affected_rows": 1,
                "total_rows": total,
                "pct": round(100 / total, 2),
                "verdict": f"Kaggle Dance Type = '{dtype}' (wrong) - not used to override curated category",
            })
    return pd.DataFrame(findings)


def main():
    curated = load_curated()
    kaggle_df = pd.read_csv(KAGGLE_CSV, encoding="latin1")
    kaggle_df["Dance style"] = kaggle_df["Dance style"].str.strip()

    qa_df = run_qa(kaggle_df)
    qa_df.to_csv(QA_CSV, index=False)
    print(f"QA findings written to {QA_CSV}")
    print(qa_df.to_string(index=False))

    rows = []
    matched = 0
    for dance in curated:
        name = dance["name"]
        record = dict(dance)
        record["id"] = dance["id"]
        record["kaggle_matched"] = False
        record["kaggle_dance_style_matched"] = ""

        kaggle_name = ALIAS_MAP.get(name)
        if kaggle_name:
            krow = kaggle_df[kaggle_df["Dance style"] == kaggle_name]
            if not krow.empty:
                krow = krow.iloc[0]
                record["kaggle_matched"] = True
                record["kaggle_dance_style_matched"] = kaggle_name
                for src, dst in SAFE_COLUMNS.items():
                    record[dst] = krow[src]
                for src, dst in UNVERIFIED_COLUMNS.items():
                    record[dst] = krow[src]
                matched += 1

        # Blank placeholders for unmatched forms, so every row has every column.
        for dst in list(SAFE_COLUMNS.values()) + list(UNVERIFIED_COLUMNS.values()):
            record.setdefault(dst, "")

        rows.append(record)

    out_df = pd.DataFrame(rows)
    out_df.to_csv(OUT_CSV, index=False, encoding="utf-8-sig")

    print(f"\nMatched {matched} / {len(curated)} curated dance forms against the Kaggle dataset.")
    print(f"Kaggle source: {len(kaggle_df)} rows, {len(kaggle_df.columns)} columns.")
    print(f"Fused output written to {OUT_CSV} ({out_df.shape[0]} rows, {out_df.shape[1]} columns).")


if __name__ == "__main__":
    main()
