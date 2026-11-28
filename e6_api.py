import pandas as pd
import matplotlib.pyplot as plt
import os

# ==========================================
# E6 - API FUSION STATUS
# ==========================================

file_path = "fused_dataset/final_api_fused.csv"

df = pd.read_csv(file_path)

print("=" * 60)
print("E6 - API FUSION STATUS")
print("=" * 60)

print("Rows:", len(df))
print("Columns:", len(df.columns))

# Check API status
status_counts = (
    df["api_fusion_status"]
    .fillna("Missing")
    .astype(str)
    .value_counts()
)

print("\nAPI Fusion Status:")
print(status_counts)

# Create folder if it doesn't exist
os.makedirs("eda_figures", exist_ok=True)

# ==========================================
# CREATE BAR CHART
# ==========================================

plt.figure(figsize=(10, 6))

status_counts.plot(kind="bar")

plt.title("E6 – API Fusion Status")
plt.xlabel("API Fusion Status")
plt.ylabel("Number of Records")

plt.xticks(rotation=45, ha="right")

plt.tight_layout()

# Save figure
plt.savefig(
    "eda_figures/E6_api_fusion_status.png",
    dpi=300
)

print("\nFigure saved successfully:")
print("eda_figures/E6_api_fusion_status.png")

plt.show()