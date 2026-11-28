
import pandas as pd
import matplotlib.pyplot as plt

# Load the existing integrated dataset
df = pd.read_csv("Practical1_AirQuality_Export.csv")

# Select the required columns
data = df[
    ["OpenWeather_Temperature_C", "Sentinel5P_NO2"]
].dropna()

# Calculate correlation
correlation = data["OpenWeather_Temperature_C"].corr(
    data["Sentinel5P_NO2"]
)

# Create scatter plot
plt.figure(figsize=(9, 6))

plt.scatter(
    data["OpenWeather_Temperature_C"],
    data["Sentinel5P_NO2"],
    alpha=0.6
)

plt.title("Scatter Plot: Temperature vs Satellite NO2")
plt.xlabel("Temperature (°C)")
plt.ylabel("Sentinel-5P NO2")
plt.grid(True)

plt.figtext(
    0.15, 0.01,
    f"Correlation: {correlation:.3f}",
    fontsize=10
)

plt.tight_layout()

# Save graph
plt.savefig("PartF_Temperature_vs_NO2.png", dpi=300)
plt.show()

print("Correlation:", round(correlation, 3))
print("Graph saved successfully!")
