import pandas as pd

# Load 2019 dataset
df_raw = pd.read_csv("data/2019.csv")
print("Raw 2019 columns found:", df_raw.columns.tolist())

# Map the exact Kaggle 2019 column headers to standard names
rename_map = {
    "Country or region": "country",
    "Overall rank": "happiness_rank",
    "Score": "happiness_score",
    "GDP per capita": "log_gdp_per_capita",
    "Social support": "social_support",
    "Healthy life expectancy": "healthy_life_expectancy",
    "Freedom to make life choices": "freedom",
    "Generosity": "generosity",
    "Perceptions of corruption": "corruption_perception"
}

df = df_raw.rename(columns=rename_map)

# Keep the standard columns and drop any incomplete rows
target_cols = [
    "country", "happiness_rank", "happiness_score",
    "log_gdp_per_capita", "social_support", "healthy_life_expectancy",
    "freedom", "generosity", "corruption_perception"
]
df = df[[c for c in target_cols if c in df.columns]].dropna().copy()

# Save cleaned baseline dataset
df.to_csv("data/original_dataset.csv", index=False)

print("\n--- BASELINE DATASET READY ---")
print(f"Total Records (Countries): {df.shape[0]}")
print(f"Total Attributes: {df.shape[1]}")
print("\nFirst 5 Records:")
print(df.head())
print("\nSummary Statistics:")
print(df.describe())