import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# Set aesthetics
plt.style.use("seaborn-v0_8-whitegrid" if "seaborn-v0_8-whitegrid" in plt.style.available else "default")
os.makedirs("report/figures", exist_ok=True)

df = pd.read_csv("data/fused_dataset.csv")
print(f"Loaded dataset for EDA: {df.shape[0]} rows x {df.shape[1]} columns")

# --- 1. Correlation Heatmap ---
cols_for_corr = [
    "happiness_score", "log_gdp_per_capita", "social_support", 
    "healthy_life_expectancy", "freedom", "generosity", 
    "annual_mean_temp_c", "annual_precipitation_mm", "wb_life_expectancy"
]
available_corr_cols = [c for c in cols_for_corr if c in df.columns]

plt.figure(figsize=(10, 8))
corr_matrix = df[available_corr_cols].corr()
sns.heatmap(corr_matrix, annot=True, fmt=".2f", cmap="coolwarm", cbar=True, square=True)
plt.title("Correlation Matrix: Socioeconomic vs Climate Indicators", fontsize=14, fontweight="bold", pad=15)
plt.tight_layout()
heatmap_path = "report/figures/fig1_correlation_matrix.png"
plt.savefig(heatmap_path, dpi=300)
plt.close()
print(f"Saved: {heatmap_path}")

# --- 2. Bivariate Scatter: Happiness Score vs. Annual Mean Temperature ---
plt.figure(figsize=(8, 6))
sns.regplot(
    data=df, 
    x="annual_mean_temp_c", 
    y="happiness_score", 
    scatter_kws={"alpha": 0.6, "color": "#1f77b4"}, 
    line_kws={"color": "#d62728", "linewidth": 2}
)
r_temp = df["annual_mean_temp_c"].corr(df["happiness_score"])
plt.title(f"Bivariate Analysis: Happiness Score vs Annual Mean Temperature (r = {r_temp:.2f})", fontsize=12, fontweight="bold")
plt.xlabel("Annual Mean Temperature (°C)", fontsize=11)
plt.ylabel("World Happiness Score", fontsize=11)
plt.tight_layout()
temp_scatter_path = "report/figures/fig2_happiness_vs_temp.png"
plt.savefig(temp_scatter_path, dpi=300)
plt.close()
print(f"Saved: {temp_scatter_path}")

# --- 3. Bivariate Scatter: Happiness Score vs. Life Expectancy ---
plt.figure(figsize=(8, 6))
sns.regplot(
    data=df, 
    x="wb_life_expectancy", 
    y="happiness_score", 
    scatter_kws={"alpha": 0.6, "color": "#2ca02c"}, 
    line_kws={"color": "#1f77b4", "linewidth": 2}
)
r_le = df["wb_life_expectancy"].corr(df["happiness_score"])
plt.title(f"Bivariate Analysis: Happiness Score vs World Bank Life Expectancy (r = {r_le:.2f})", fontsize=12, fontweight="bold")
plt.xlabel("World Bank Life Expectancy (Years)", fontsize=11)
plt.ylabel("World Happiness Score", fontsize=11)
plt.tight_layout()
le_scatter_path = "report/figures/fig3_happiness_vs_life_expectancy.png"
plt.savefig(le_scatter_path, dpi=300)
plt.close()
print(f"Saved: {le_scatter_path}")

# --- 4. Regional Distribution of Happiness Scores ---
if "region" in df.columns:
    plt.figure(figsize=(10, 6))
    order = df.groupby("region")["happiness_score"].median().sort_values(ascending=False).index
    sns.boxplot(data=df, x="region", y="happiness_score", order=order, palette="Set2")
    plt.title("Regional Distribution of Happiness Scores", fontsize=12, fontweight="bold")
    plt.xlabel("Geographic Region", fontsize=11)
    plt.ylabel("Happiness Score", fontsize=11)
    plt.xticks(rotation=30, ha="right")
    plt.tight_layout()
    region_box_path = "report/figures/fig4_happiness_by_region.png"
    plt.savefig(region_box_path, dpi=300)
    plt.close()
    print(f"Saved: {region_box_path}")

print("\n--- EDA STATISTICAL SUMMARY ---")
print(df[available_corr_cols].describe().T[["mean", "std", "min", "50%", "max"]])