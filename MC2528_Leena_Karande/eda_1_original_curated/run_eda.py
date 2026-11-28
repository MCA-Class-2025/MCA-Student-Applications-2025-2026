"""
EDA #1 of 3 -- Original Curated Dataset

Analyzes ONLY data/dance_forms.json (20 rows x 15 fields), before any API
or Kaggle enrichment. This is the earliest point in the fusion chain:

  data/dance_forms.json                                20x15  <- THIS SCRIPT
        v (+ 5 APIs)
  data/dancecompass_merged.csv                          20x73  (see eda.py / data/eda/)
        v (+ Kaggle)
  data/dancecompass_final_fused_allsources.csv          20x83  (see eda_3_final_fused/)

Run from the project root:
    python eda_1_original_curated/run_eda.py
"""

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
CURATED_JSON = ROOT / "data" / "dance_forms.json"
OUT_DIR = Path(__file__).resolve().parent / "outputs"
OUT_DIR.mkdir(exist_ok=True)


def main():
    with open(CURATED_JSON, "r", encoding="utf-8") as f:
        records = json.load(f)
    df = pd.DataFrame(records)
    df["n_instruments"] = df["instruments"].apply(len)

    print(f"Shape: {df.shape}")
    print(f"Duplicate names: {df['name'].duplicated().sum()}")
    print(f"Missing values: {df.isnull().sum().sum()}")
    print()
    print("category counts:\n", df["category"].value_counts())
    print()
    print("energy_level counts:\n", df["energy_level"].value_counts())
    print()
    print("learning_difficulty counts:\n", df["learning_difficulty"].value_counts())
    print()
    print("n_instruments describe:\n", df["n_instruments"].describe())

    # Save summary tables
    df["category"].value_counts().to_csv(OUT_DIR / "category_summary.csv", header=["count"])
    df["energy_level"].value_counts().to_csv(OUT_DIR / "energy_summary.csv", header=["count"])
    df["learning_difficulty"].value_counts().to_csv(OUT_DIR / "difficulty_summary.csv", header=["count"])

    plt.rcParams.update({"font.size": 11})
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.2))
    df["category"].value_counts().plot(kind="bar", ax=axes[0], color="#1F4E79")
    axes[0].set_title("Dance Forms by Category (n=20)")
    axes[0].tick_params(axis="x", rotation=30)

    order = ["Low-Medium", "Medium", "Medium-High", "High"]
    df["energy_level"].value_counts().reindex(order).plot(kind="bar", ax=axes[1], color="#2E75B6")
    axes[1].set_title("Dance Forms by Energy Level (n=20)")
    axes[1].tick_params(axis="x", rotation=30)
    plt.tight_layout()
    plt.savefig(OUT_DIR / "category_and_energy.png", dpi=150)
    plt.close()

    print(f"\nOutputs written to {OUT_DIR}")


if __name__ == "__main__":
    main()
