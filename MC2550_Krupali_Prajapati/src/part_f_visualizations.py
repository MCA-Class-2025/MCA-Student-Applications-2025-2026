
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

# Create output folder
output_folder = "data/part_f_visualizations"
os.makedirs(output_folder, exist_ok=True)

# Load datasets
wdi = pd.read_csv("wdi_country_baseline_multiyear.csv")
fused = pd.read_csv("data/fused_country_intelligence.csv")

# Load analysis reports
coverage = pd.read_csv("data/part_f_api_coverage.csv")
missing = pd.read_csv("data/part_f_missing_values.csv")
relationships = pd.read_csv("data/part_f_relationships.csv")

sns.set_theme(style="whitegrid")

# ------------------------------------------------
# CHART 1: ORIGINAL VS FUSED DATASET
# ------------------------------------------------

comparison = pd.DataFrame({
    "Dataset": ["Original WDI", "Fused Dataset"],
    "Rows": [len(wdi), len(fused)],
    "Columns": [len(wdi.columns), len(fused.columns)]
})

fig, axes = plt.subplots(1, 2, figsize=(12, 5))

sns.barplot(data=comparison, x="Dataset", y="Rows", ax=axes[0])
axes[0].set_title("Number of Records")
axes[0].set_ylabel("Records")

sns.barplot(data=comparison, x="Dataset", y="Columns", ax=axes[1])
axes[1].set_title("Number of Attributes")
axes[1].set_ylabel("Columns")

fig.suptitle("Original WDI vs Fused Dataset")
plt.tight_layout()
plt.savefig(
    f"{output_folder}/01_dataset_comparison.png",
    dpi=300,
    bbox_inches="tight"
)
plt.close()

# ------------------------------------------------
# CHART 2: API COUNTRY COVERAGE
# ------------------------------------------------

plt.figure(figsize=(10, 6))

sns.barplot(
    data=coverage,
    x="API",
    y="Unique Country Codes"
)

plt.title("Country Coverage Across Five APIs")
plt.xlabel("External APIs")
plt.ylabel("Unique Country Codes")
plt.xticks(rotation=20, ha="right")
plt.tight_layout()

plt.savefig(
    f"{output_folder}/02_api_coverage.png",
    dpi=300,
    bbox_inches="tight"
)
plt.close()

# ------------------------------------------------
# CHART 3: TOP MISSING VALUE COLUMNS
# ------------------------------------------------

top_missing = missing.head(10).copy()

plt.figure(figsize=(11, 6))

sns.barplot(
    data=top_missing,
    x="Missing Percentage",
    y="Column"
)

plt.title("Top 10 Columns with Missing Values")
plt.xlabel("Missing Values (%)")
plt.ylabel("Dataset Attributes")
plt.tight_layout()

plt.savefig(
    f"{output_folder}/03_missing_values.png",
    dpi=300,
    bbox_inches="tight"
)
plt.close()

# ------------------------------------------------
# CHART 4: CORRELATION HEATMAP
# ------------------------------------------------

heatmap_data = relationships.copy()

heatmap_data["Pearson Correlation"] = pd.to_numeric(
    heatmap_data["Pearson Correlation"],
    errors="coerce"
)

heatmap_data = heatmap_data.dropna(
    subset=["Pearson Correlation"]
)

heatmap_data["Relationship"] = (
    heatmap_data["WDI Variable"]
    + " vs "
    + heatmap_data["API Variable"]
)

heatmap_matrix = heatmap_data.set_index(
    "Relationship"
)[["Pearson Correlation"]]

plt.figure(figsize=(9, 6))

sns.heatmap(
    heatmap_matrix,
    annot=True,
    cmap="coolwarm",
    center=0,
    fmt=".4f",
    linewidths=0.5
)

plt.title("Correlation Between WDI and API Variables")
plt.tight_layout()

plt.savefig(
    f"{output_folder}/04_correlation_heatmap.png",
    dpi=300,
    bbox_inches="tight"
)
plt.close()

# ------------------------------------------------
# COMPLETION MESSAGE
# ------------------------------------------------

print("\n========== PART F VISUALIZATIONS ==========")

for file in os.listdir(output_folder):
    print("Created:", file)

print("\nAll four visualizations saved successfully!")
print("Folder:", output_folder)
