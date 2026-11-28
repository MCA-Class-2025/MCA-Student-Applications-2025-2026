"""Quick console EDA of the geo-spatial dataset."""
import pandas as pd
df = pd.read_excel("data.xlsx", parse_dates=["date"])
print(df.info(), "\n"); print(df.describe().round(1), "\n")
print("Missing:", int(df.isna().sum().sum()), "| cities:", df.city.nunique(), "| states:", df.state.nunique())
print("\nLat/Lon bounds:", df.lat.min(), df.lat.max(), df.lon.min(), df.lon.max())
print("\nMean PM2.5 by region:\n", df.groupby("region").pm25.mean().round(1).sort_values())
print("\nTop 5 most polluted cities:\n", df.groupby("city").pm25.mean().round(1).nlargest(5))
print("\nAQI category share (%):\n", (df.aqi_category.value_counts(normalize=True) * 100).round(1))
print("\nCorrelation with PM2.5:\n", df[["pm25", "temp_c", "humidity", "green_cover_pct", "vehicles_per_1000", "population_m"]].corr()["pm25"].round(2))
