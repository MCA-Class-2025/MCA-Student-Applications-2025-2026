"""
EDA #3 of 3 -- Final Fused Dataset (curated + 5 APIs + Kaggle)

Analyzes data/dancecompass_final_fused_allsources.csv (20 rows x 83 cols) --
the top of the fusion chain, and the file the LIVE APP now reads
(utils/merged_data.py). Extends the numeric outlier/correlation analysis
from phase1_eda/ (which covers the 5-API-only file, matching the submitted
Phase 1 report) to also include the new Kaggle-derived numeric fields.

  data/dance_forms.json                                 20x15  (see eda_1_original_curated/)
        v (+ 5 APIs)
  data/dancecompass_merged.csv                           20x73  (see eda.py / data/eda/ and phase1_eda/)
        v (+ Kaggle)
  data/dancecompass_final_fused_allsources.csv           20x83  <- THIS SCRIPT

Run from the project root:
    python eda_3_final_fused/run_eda.py
"""

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
FINAL_CSV = ROOT / "data" / "dancecompass_final_fused_allsources.csv"
OUT_DIR = Path(__file__).resolve().parent / "outputs"
OUT_DIR.mkdir(exist_ok=True)

# Numeric columns from the 5 APIs + the 2 genuinely numeric Kaggle fields
# (hardness_ratio, tempo_bpm -- the others are categorical/text).
NUMERIC_COLS = [
    "latitude", "longitude", "openlibrary_total_results", "book_count_selected",
    "musicbrainz_total_results", "music_recording_count_selected",
    "kaggle_hardness_ratio", "kaggle_tempo_bpm",
]


def main():
    df = pd.read_csv(FINAL_CSV)
    for c in ["kaggle_hardness_ratio", "kaggle_tempo_bpm"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")

    print(f"Shape: {df.shape}")
    print(f"Kaggle-matched rows: {int(df['kaggle_matched'].sum())} / {len(df)}")
    print()

    # --- Structural / missing-data summary across ALL sources ---
    miss = df.isnull().sum()
    miss = miss[miss > 0].sort_values(ascending=False)
    miss_pct = (miss / len(df) * 100).round(1)
    summary = pd.DataFrame({"missing_count": miss, "missing_pct": miss_pct})
    summary.to_csv(OUT_DIR / "missing_data_summary.csv")
    print("Top missing-data columns:\n", summary.head(10))
    print()

    # --- Numeric summary, now including Kaggle numeric fields ---
    desc = df[NUMERIC_COLS].describe().T
    desc.to_csv(OUT_DIR / "numeric_summary.csv")
    print("Numeric summary (incl. Kaggle):\n", desc.round(2))
    print()

    # --- Correlation heatmap including Kaggle numeric fields ---
    corr = df[NUMERIC_COLS].corr()
    corr.to_csv(OUT_DIR / "correlation_matrix.csv")
    plt.rcParams.update({"font.size": 9})
    fig, ax = plt.subplots(figsize=(8, 7))
    im = ax.imshow(corr, cmap="RdBu_r", vmin=-1, vmax=1)
    ax.set_xticks(range(len(NUMERIC_COLS))); ax.set_xticklabels(NUMERIC_COLS, rotation=45, ha="right")
    ax.set_yticks(range(len(NUMERIC_COLS))); ax.set_yticklabels(NUMERIC_COLS)
    for i in range(len(NUMERIC_COLS)):
        for j in range(len(NUMERIC_COLS)):
            val = corr.iloc[i, j]
            if pd.notna(val):
                ax.text(j, i, f"{val:.2f}", ha="center", va="center",
                        color="white" if abs(val) > 0.5 else "black", fontsize=7)
    plt.colorbar(im, ax=ax, fraction=0.046)
    ax.set_title("Correlation Heatmap: ALL Numeric Fields (5 APIs + Kaggle)")
    plt.tight_layout()
    plt.savefig(OUT_DIR / "correlation_heatmap_all_sources.png", dpi=150)
    plt.close()

    # --- Kaggle-specific: hardness_ratio vs energy_level (original attribute) ---
    matched = df[df["kaggle_matched"] == True]
    order = ["Low-Medium", "Medium", "Medium-High", "High"]
    means = matched.groupby("energy_level")["kaggle_hardness_ratio"].mean().reindex(order)
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.bar(means.dropna().index, means.dropna().values, color="#7C3AED")
    ax.set_title("Mean Kaggle hardness_ratio by energy_level (12 Kaggle-matched forms)")
    plt.tight_layout()
    plt.savefig(OUT_DIR / "kaggle_hardness_by_energy.png", dpi=150)
    plt.close()

    print(f"\nOutputs written to {OUT_DIR}")


if __name__ == "__main__":
    main()
