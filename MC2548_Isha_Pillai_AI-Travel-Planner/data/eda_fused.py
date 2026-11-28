import pandas as pd
import matplotlib.pyplot as plt

# Load fused dataset
df = pd.read_csv("data/final_fusion.csv")

print("=" * 60)
print("EDA ON FUSED DATASET")
print("=" * 60)

# ---------------------------------------------------------
# 1. UNIVARIATE ANALYSIS
# ---------------------------------------------------------

print("\n1. UNIVARIATE ANALYSIS")
print("-" * 40)

univariate_cols = [
    "Weather_Temperature_C",
    "Weather_Humidity",
    "Place_Count"
]

for col in univariate_cols:
    s = pd.to_numeric(df[col], errors="coerce").dropna()

    print(f"\n{col}")
    print("Mean:", round(s.mean(), 2))
    print("Median:", round(s.median(), 2))
    print("Standard Deviation:", round(s.std(), 2))
    print("Minimum:", round(s.min(), 2))
    print("Maximum:", round(s.max(), 2))
    print("Q1:", round(s.quantile(0.25), 2))
    print("Q3:", round(s.quantile(0.75), 2))

# Temperature distribution
plt.figure(figsize=(8, 5))
plt.hist(
    pd.to_numeric(df["Weather_Temperature_C"], errors="coerce").dropna(),
    bins=10
)
plt.title("Distribution of API Weather Temperature")
plt.xlabel("Temperature (°C)")
plt.ylabel("Number of Records")
plt.tight_layout()
plt.savefig("temperature_distribution.png", dpi=300)
plt.show()

# Place count distribution
plt.figure(figsize=(8, 5))
plt.hist(
    pd.to_numeric(df["Place_Count"], errors="coerce").dropna(),
    bins=10
)
plt.title("Distribution of Places Collected from API")
plt.xlabel("Number of Places")
plt.ylabel("Number of Records")
plt.tight_layout()
plt.savefig("place_count_distribution.png", dpi=300)
plt.show()


# ---------------------------------------------------------
# 2. BIVARIATE ANALYSIS
# ---------------------------------------------------------

print("\n2. BIVARIATE ANALYSIS")
print("-" * 40)

x = pd.to_numeric(df["Weather_Temperature_C"], errors="coerce")
y = pd.to_numeric(df["Weather_Humidity"], errors="coerce")

print(
    "Temperature vs Humidity Correlation:",
    round(x.corr(y), 3)
)

plt.figure(figsize=(8, 5))
plt.scatter(x, y)
plt.title("API Temperature vs Humidity")
plt.xlabel("Temperature (°C)")
plt.ylabel("Humidity (%)")
plt.tight_layout()
plt.savefig("temperature_vs_humidity.png", dpi=300)
plt.show()


# ---------------------------------------------------------
# 3. MULTIVARIATE ANALYSIS
# ---------------------------------------------------------

print("\n3. MULTIVARIATE ANALYSIS")
print("-" * 40)

api_numeric = [
    "Weather_Temperature_C",
    "Weather_Feels_Like_C",
    "Weather_Humidity",
    "Weather_Wind_Speed",
    "Currency_Exchange_Rate",
    "Currency_Converted_Amount",
    "Place_Count"
]

numeric_df = df[api_numeric].apply(
    pd.to_numeric,
    errors="coerce"
)

correlation = numeric_df.corr()

print("\nCorrelation Matrix:")
print(correlation.round(3))

plt.figure(figsize=(10, 8))
plt.imshow(correlation, interpolation="nearest")
plt.colorbar()

plt.xticks(
    range(len(correlation.columns)),
    correlation.columns,
    rotation=90
)

plt.yticks(
    range(len(correlation.columns)),
    correlation.columns
)

plt.title("Correlation Heatmap of API Variables")
plt.tight_layout()
plt.savefig("api_correlation_heatmap.png", dpi=300)
plt.show()

print("\nEDA COMPLETE")