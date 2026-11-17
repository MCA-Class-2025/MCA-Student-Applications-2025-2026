
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

# Load fused dataset
df = pd.read_csv("data/fused_country_intelligence.csv")

# Create output folder
output_folder = "data/part_f_visualizations"
os.makedirs(output_folder, exist_ok=True)

# Convert GDP per capita to numeric
df["GDP per capita"] = pd.to_numeric(
    df["GDP per capita"], errors="coerce"
)

# Remove missing and invalid values
gdp = df["GDP per capita"].dropna()
gdp = gdp[gdp >= 0]

# Figure 5: Distribution plot
plt.figure(figsize=(10, 6))
sns.histplot(gdp, bins=25, kde=True)
plt.title("Distribution of GDP per Capita Across Countries")
plt.xlabel("GDP per Capita")
plt.ylabel("Number of Countries")
plt.tight_layout()

plt.savefig(
    os.path.join(output_folder, "05_gdp_distribution.png"),
    dpi=300
)
plt.close()

print("Created: 05_gdp_distribution.png")

# Figure 6: Boxplot
plt.figure(figsize=(10, 5))
sns.boxplot(x=gdp)
plt.title("Boxplot of GDP per Capita Across Countries")
plt.xlabel("GDP per Capita")
plt.tight_layout()

plt.savefig(
    os.path.join(output_folder, "06_gdp_boxplot.png"),
    dpi=300
)
plt.close()

print("Created: 06_gdp_boxplot.png")

print("\nBoth additional visualizations created successfully!")
print("Folder:", output_folder)
