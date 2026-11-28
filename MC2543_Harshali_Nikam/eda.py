
import os
import pandas as pd
import matplotlib.pyplot as plt

# Load dataset
df = pd.read_csv("data/processed/fused_dataset.csv")

# Create report folders
os.makedirs("reports/plots", exist_ok=True)

# Basic information
with open("reports/eda_summary.txt", "w", encoding="utf-8") as f:
    f.write("CITYFUSION - EXPLORATORY DATA ANALYSIS\n")
    f.write("=" * 45 + "\n\n")

    f.write(f"Total Records: {len(df)}\n")
    f.write(f"Total Columns: {len(df.columns)}\n\n")

    f.write("Dataset Information:\n")
    f.write(str(df.info(buf=None)) + "\n\n")

    f.write("Missing Values:\n")
    f.write(str(df.isnull().sum()) + "\n\n")

    f.write("Duplicate Records: " + str(df.duplicated().sum()) + "\n\n")

    f.write("Statistical Summary:\n")
    f.write(str(df.describe(include="all")) + "\n\n")

    if "city" in df.columns:
        f.write("Records Per City:\n")
        f.write(str(df["city"].value_counts()) + "\n\n")

# 1. Records per city
if "city" in df.columns:
    df["city"].value_counts().plot(kind="bar", figsize=(10, 5))
    plt.title("Records Per City")
    plt.xlabel("City")
    plt.ylabel("Number of Records")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig("reports/plots/records_per_city.png")
    plt.close()

# 2. PM2.5 distribution
if "pm2_5" in df.columns:
    df["pm2_5"].dropna().plot(kind="hist", bins=30, figsize=(8, 5))
    plt.title("PM2.5 Distribution")
    plt.xlabel("PM2.5")
    plt.ylabel("Frequency")
    plt.tight_layout()
    plt.savefig("reports/plots/pm25_distribution.png")
    plt.close()

# 3. Average PM2.5 by city
if "city" in df.columns and "pm2_5" in df.columns:
    df.groupby("city")["pm2_5"].mean().sort_values().plot(
        kind="bar", figsize=(10, 5)
    )
    plt.title("Average PM2.5 by City")
    plt.xlabel("City")
    plt.ylabel("Average PM2.5")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig("reports/plots/average_pm25_by_city.png")
    plt.close()

# 4. Temperature vs PM2.5
if "temperature_2m" in df.columns and "pm2_5" in df.columns:
    plt.figure(figsize=(8, 5))
    plt.scatter(df["temperature_2m"], df["pm2_5"], alpha=0.5)
    plt.title("Temperature vs PM2.5")
    plt.xlabel("Temperature")
    plt.ylabel("PM2.5")
    plt.tight_layout()
    plt.savefig("reports/plots/temperature_vs_pm25.png")
    plt.close()

# 5. Correlation matrix
numeric_df = df.select_dtypes(include="number")

if not numeric_df.empty:
    plt.figure(figsize=(10, 7))
    plt.imshow(numeric_df.corr(), cmap="coolwarm", aspect="auto")
    plt.colorbar()
    plt.xticks(range(len(numeric_df.columns)), numeric_df.columns,
               rotation=90)
    plt.yticks(range(len(numeric_df.columns)), numeric_df.columns)
    plt.title("Correlation Matrix")
    plt.tight_layout()
    plt.savefig("reports/plots/correlation_matrix.png")
    plt.close()

print("EDA completed successfully!")
print("Check the reports folder for summary and graphs.")
