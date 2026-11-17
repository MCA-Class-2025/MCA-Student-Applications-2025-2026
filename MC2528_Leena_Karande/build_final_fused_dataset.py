"""
Build the FINAL fused dataset: original curated data + 5-API enrichment
+ Kaggle enrichment, all combined into one standalone CSV.

This is the top of the fusion chain. Everything before this stays in its
own file, untouched, so the live Streamlit app is never affected:

  data/dance_forms.json                 (20 x 15)  original, self-authored
        |
        v  (+ 5 APIs: Wikidata, Wikipedia, Nominatim, Open Library, MusicBrainz)
  data/dancecompass_merged.csv          (20 x 73)  <-- the live app reads THIS file
        |
        v  (+ Kaggle "Dance Styles & Genres", after QA -- see kaggle_data/)
  data/dancecompass_final_fused_allsources.csv   (20 x 83)  <-- FINAL fused output

Run from the project root:
    python build_final_fused_dataset.py
"""

from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent
MERGED_CSV = ROOT / "data" / "dancecompass_merged.csv"          # curated + 5 APIs
KAGGLE_FUSED_CSV = ROOT / "kaggle_data" / "dancecompass_kaggle_fused.csv"  # curated + Kaggle
OUT_CSV = ROOT / "data" / "dancecompass_final_fused_allsources.csv"


def main():
    merged = pd.read_csv(MERGED_CSV)
    kaggle_fused = pd.read_csv(KAGGLE_FUSED_CSV)

    kaggle_new_cols = [c for c in kaggle_fused.columns if c.startswith("kaggle_")]
    final = merged.merge(kaggle_fused[["name"] + kaggle_new_cols], on="name", how="left")
    final["kaggle_matched"] = final["kaggle_matched"].fillna(False)

    # IMPORTANT: this file is read by the LIVE app (utils/merged_data.py),
    # so missing values are left as real NaN here, not relabeled text.
    # utils.merged_data._clean() treats NaN as "no value" and skips it;
    # a literal string like "Not available in source" would instead be
    # treated as real content and leak into RAG answers and the UI.
    # The human-readable "Not available in source" labeling is applied
    # ONLY in kaggle_data/build_final_workbook.py, for the submitted
    # Excel report -- never to this source-of-truth CSV.
    final.to_csv(OUT_CSV, index=False)

    print(f"Original (5-API) dataset: {merged.shape}")
    print(f"Kaggle enrichment layer:  {kaggle_fused.shape} ({len(kaggle_new_cols)} new columns)")
    print(f"FINAL fused dataset:      {final.shape}  -> {OUT_CSV}")
    print(f"Kaggle-matched rows: {int(final['kaggle_matched'].sum())} / {len(final)}")


if __name__ == "__main__":
    main()
