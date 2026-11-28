"""
Phase 1 EDA script: Data Quality Assessment (Part D) and Exploratory Data
Analysis (Part E) on the fused DanceCompass dataset.

Input:  data/dancecompass_merged.csv  (20 rows x 73 columns: 15 original +
        7 engineered text-EDA + 51 columns from the 5 data-fusion APIs)
Output: phase1_eda/outputs/*.png  (all charts embedded in the Phase 1 report)
        phase1_eda/outputs/outlier_report.csv

Run from the project root:
    python phase1_eda/run_eda.py
"""

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
MERGED_CSV = ROOT / "data" / "dancecompass_merged.csv"
OUT_DIR = Path(__file__).resolve().parent / "outputs"
OUT_DIR.mkdir(exist_ok=True)

NUMERIC_API_COLS = [
    "latitude", "longitude", "openlibrary_total_results", "book_count_selected",
    "musicbrainz_total_results", "music_recording_count_selected",
]


def outlier_report(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for col in NUMERIC_API_COLS:
        q1, q3 = df[col].quantile(.25), df[col].quantile(.75)
        iqr = q3 - q1
        low, high = q1 - 1.5 * iqr, q3 + 1.5 * iqr
        iqr_outliers = df[(df[col] < low) | (df[col] > high)]["name"].tolist()

        z = (df[col] - df[col].mean()) / df[col].std()
        z_outliers = df.loc[z.abs() > 2, "name"].tolist()

        rows.append({
            "attribute": col,
            "iqr_lower_bound": round(low, 2),
            "iqr_upper_bound": round(high, 2),
            "iqr_outliers": ", ".join(iqr_outliers) or "(none)",
            "zscore_outliers_abs_gt_2": ", ".join(z_outliers) or "(none)",
        })
    return pd.DataFrame(rows)


def main():
    df = pd.read_csv(MERGED_CSV)
    plt.rcParams.update({"font.size": 10})

    # --- Part D.4: outlier report ---
    report = outlier_report(df)
    report.to_csv(OUT_DIR / "outlier_report.csv", index=False)
    print(report.to_string(index=False))

    # --- Part E.1: univariate ---
    fig, axes = plt.subplots(1, 2, figsize=(11, 4))
    axes[0].hist(df["musicbrainz_total_results"], bins=8, color="#2E75B6", edgecolor="white")
    axes[0].set_title("Distribution: musicbrainz_total_results")
    axes[1].boxplot(df["musicbrainz_total_results"], vert=True, patch_artist=True,
                     boxprops=dict(facecolor="#DCE6F1"))
    axes[1].set_title("Boxplot: musicbrainz_total_results")
    plt.tight_layout()
    plt.savefig(OUT_DIR / "univariate_musicbrainz.png", dpi=150)
    plt.close()

    sorted_df = df.sort_values("openlibrary_total_results", ascending=False)
    fig, ax = plt.subplots(figsize=(10, 4.5))
    ax.bar(sorted_df["name"], sorted_df["openlibrary_total_results"], color="#1F4E79")
    ax.set_title("openlibrary_total_results by dance form")
    plt.xticks(rotation=60, ha="right")
    plt.tight_layout()
    plt.savefig(OUT_DIR / "univariate_openlibrary_bar.png", dpi=150)
    plt.close()

    # --- Part E.2: bivariate ---
    fig, ax = plt.subplots(figsize=(8, 4.5))
    cats = df["category"].unique()
    ax.boxplot([df[df["category"] == c]["latitude"].values for c in cats],
               tick_labels=cats, patch_artist=True, boxprops=dict(facecolor="#B4C7E7"))
    ax.axhline(0, color="gray", linestyle="--", linewidth=1)
    ax.set_title("Origin Latitude by Dance Category")
    plt.tight_layout()
    plt.savefig(OUT_DIR / "bivariate_category_latitude.png", dpi=150)
    plt.close()

    order = ["Low-Medium", "Medium", "Medium-High", "High"]
    means = df.groupby("energy_level")["musicbrainz_total_results"].mean().reindex(order)
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.bar(means.index, means.values, color="#2E75B6")
    ax.set_title("Mean musicbrainz_total_results by Energy Level")
    plt.tight_layout()
    plt.savefig(OUT_DIR / "bivariate_energy_musicbrainz.png", dpi=150)
    plt.close()

    # --- Part E.3: multivariate ---
    corr = df[NUMERIC_API_COLS].corr()
    fig, ax = plt.subplots(figsize=(7, 6))
    im = ax.imshow(corr, cmap="RdBu_r", vmin=-1, vmax=1)
    ax.set_xticks(range(len(NUMERIC_API_COLS)))
    ax.set_xticklabels(NUMERIC_API_COLS, rotation=45, ha="right")
    ax.set_yticks(range(len(NUMERIC_API_COLS)))
    ax.set_yticklabels(NUMERIC_API_COLS)
    for i in range(len(NUMERIC_API_COLS)):
        for j in range(len(NUMERIC_API_COLS)):
            ax.text(j, i, f"{corr.iloc[i, j]:.2f}", ha="center", va="center",
                     color="white" if abs(corr.iloc[i, j]) > 0.5 else "black", fontsize=8)
    plt.colorbar(im, ax=ax, fraction=0.046)
    ax.set_title("Correlation Heatmap: API-derived Numeric Attributes")
    plt.tight_layout()
    plt.savefig(OUT_DIR / "multivariate_heatmap.png", dpi=150)
    plt.close()

    print(f"\nAll charts written to {OUT_DIR}")


if __name__ == "__main__":
    main()
