import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR / "data" / "building_defect_knowledge.csv"
OUT_DIR = BASE_DIR / "analysis" / "original_eda"
OUT_DIR.mkdir(parents=True, exist_ok=True)

df = pd.read_csv(DATA_FILE)

# Normalize column names
df.columns = [c.strip().lower() for c in df.columns]

print("=" * 70)
print("FIXAI PHASE 1 — ORIGINAL DATASET EDA")
print("=" * 70)

print(f"\nRecords: {len(df)}")
print(f"Attributes: {len(df.columns)}")
print("\nColumns:")
for c in df.columns:
    print(" -", c)

# ---------------------------------------------------------
# BASIC QUALITY
# ---------------------------------------------------------
quality = pd.DataFrame({
    "attribute": df.columns,
    "data_type": [str(df[c].dtype) for c in df.columns],
    "unique_values": [int(df[c].nunique()) for c in df.columns],
    "missing_values": [int(df[c].isna().sum()) for c in df.columns],
    "duplicate_values": [int(df[c].duplicated().sum()) for c in df.columns],
})
quality.to_csv(OUT_DIR / "original_quality.csv", index=False)

print("\nMissing values:")
print(quality[["attribute", "missing_values"]].to_string(index=False))

print(f"\nDuplicate rows: {int(df.duplicated().sum())}")

# ---------------------------------------------------------
# FREQUENCY TABLES
# ---------------------------------------------------------
def save_counts(column, filename):
    counts = (
        df[column]
        .value_counts(dropna=False)
        .rename_axis(column)
        .reset_index(name="count")
    )
    counts.to_csv(OUT_DIR / filename, index=False)
    return counts

def plot_bar(counts, category_col, title, filename):
    plt.figure(figsize=(9, 5.5))
    plt.bar(
        counts[category_col].astype(str),
        counts["count"]
    )
    plt.xlabel(category_col.replace("_", " ").title())
    plt.ylabel("Number of records")
    plt.title(title)
    plt.xticks(rotation=35, ha="right")
    plt.tight_layout()
    plt.savefig(OUT_DIR / filename, dpi=180)
    plt.close()

# Defect
defect_counts = save_counts("defect", "defect_counts.csv")
plot_bar(
    defect_counts,
    "defect",
    "Original Dataset — Defect Distribution",
    "01_defect_distribution.png"
)

# Work type
work_counts = save_counts("work_type", "work_type_counts.csv")
plot_bar(
    work_counts,
    "work_type",
    "Original Dataset — Work Type Distribution",
    "02_work_type_distribution.png"
)

# Element
element_counts = save_counts("element", "element_counts.csv")
plot_bar(
    element_counts,
    "element",
    "Original Dataset — Affected Element Distribution",
    "03_element_distribution.png"
)

# Location
location_counts = save_counts("location", "location_counts.csv")
plot_bar(
    location_counts,
    "location",
    "Original Dataset — Location Distribution",
    "04_location_distribution.png"
)

# ---------------------------------------------------------
# COMBINED SUMMARY
# ---------------------------------------------------------
summary = pd.DataFrame({
    "metric": [
        "records",
        "attributes",
        "duplicate_rows",
        "total_missing_values"
    ],
    "value": [
        len(df),
        len(df.columns),
        int(df.duplicated().sum()),
        int(df.isna().sum().sum())
    ]
})
summary.to_csv(OUT_DIR / "original_dataset_summary.csv", index=False)

print("\nCreated charts and tables in:")
print(OUT_DIR)
print("\nDONE.")
