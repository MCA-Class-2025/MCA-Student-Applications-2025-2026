
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

# Project paths
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "datasets"
OUTPUT_DIR = BASE_DIR / "visualizations"
OUTPUT_DIR.mkdir(exist_ok=True)

# Load datasets
spatial = pd.read_csv(DATA_DIR / "Spatial_Dataset.csv")
temporal = pd.read_csv(DATA_DIR / "Temporal_Dataset.csv")

sns.set_theme(style="whitegrid")

# Prepare temporal data
temporal["Timestamp"] = pd.to_datetime(temporal["Timestamp"])
temporal["Date"] = pd.to_datetime(temporal["Date"])

# =====================================
# 1. SPATIAL DASHBOARD
# =====================================

fig, axes = plt.subplots(2, 2, figsize=(15, 10))
fig.suptitle("SPATIAL DATA ANALYSIS DASHBOARD",
             fontsize=18, fontweight="bold")

# Location distribution
sns.countplot(
    data=spatial, x="Location",
    ax=axes[0, 0]
)
axes[0, 0].set_title("Records by Location")
axes[0, 0].tick_params(axis="x", rotation=45)

# Geographic coordinate distribution
scatter = axes[0, 1].scatter(
    spatial["Longitude"],
    spatial["Latitude"],
    c=spatial["Activity_Score"],
    s=50,
    cmap="viridis"
)
axes[0, 1].set_title("Geographical Distribution")
axes[0, 1].set_xlabel("Longitude")
axes[0, 1].set_ylabel("Latitude")
fig.colorbar(scatter, ax=axes[0, 1],
             label="Activity Score")

# Event count by location
sns.barplot(
    data=spatial,
    x="Location",
    y="Event_Count",
    estimator="sum",
    errorbar=None,
    ax=axes[1, 0]
)
axes[1, 0].set_title("Total Events by Location")
axes[1, 0].tick_params(axis="x", rotation=45)

# Category distribution
spatial["Category"].value_counts().plot(
    kind="pie",
    autopct="%1.1f%%",
    ax=axes[1, 1]
)
axes[1, 1].set_title("Activity Category Distribution")
axes[1, 1].set_ylabel("")

plt.tight_layout()
plt.savefig(
    OUTPUT_DIR / "Spatial_Dashboard.png",
    dpi=300, bbox_inches="tight"
)
plt.close()

# =====================================
# 2. TEMPORAL DASHBOARD
# =====================================

fig, axes = plt.subplots(2, 2, figsize=(15, 10))
fig.suptitle("TEMPORAL DATA ANALYSIS DASHBOARD",
             fontsize=18, fontweight="bold")

# Daily metric trend
daily = temporal.groupby("Date")["Metric_Value"].mean()
axes[0, 0].plot(daily.index, daily.values, marker="o")
axes[0, 0].set_title("Daily Metric Trend")
axes[0, 0].set_xlabel("Date")
axes[0, 0].set_ylabel("Average Metric")
axes[0, 0].tick_params(axis="x", rotation=45)

# Hourly activity
hourly = temporal.groupby("Hour")["Metric_Value"].mean()
axes[0, 1].plot(hourly.index, hourly.values, marker="o")
axes[0, 1].set_title("Hourly Activity Pattern")
axes[0, 1].set_xlabel("Hour")
axes[0, 1].set_ylabel("Average Metric")

# Day-wise analysis
day_order = [
    "Monday", "Tuesday", "Wednesday",
    "Thursday", "Friday", "Saturday", "Sunday"
]
sns.barplot(
    data=temporal,
    x="Day",
    y="Metric_Value",
    order=day_order,
    errorbar=None,
    ax=axes[1, 0]
)
axes[1, 0].set_title("Day-wise Average Metric")
axes[1, 0].tick_params(axis="x", rotation=35)

# Peak vs off-peak
sns.boxplot(
    data=temporal,
    x="Time_Category",
    y="Metric_Value",
    ax=axes[1, 1]
)
axes[1, 1].set_title("Peak vs Off-Peak Analysis")

plt.tight_layout()
plt.savefig(
    OUTPUT_DIR / "Temporal_Dashboard.png",
    dpi=300, bbox_inches="tight"
)
plt.close()

# =====================================
# 3. COMBINED DASHBOARD
# =====================================

fig, axes = plt.subplots(2, 3, figsize=(18, 10))
fig.suptitle("SPATIAL AND TEMPORAL ANALYTICS",
             fontsize=20, fontweight="bold")

# Spatial plot
axes[0, 0].scatter(
    spatial["Longitude"],
    spatial["Latitude"],
    c=spatial["Activity_Score"],
    cmap="viridis"
)
axes[0, 0].set_title("Spatial Distribution")
axes[0, 0].set_xlabel("Longitude")
axes[0, 0].set_ylabel("Latitude")

# Location events
spatial.groupby("Location")["Event_Count"].sum().plot(
    kind="bar", ax=axes[0, 1]
)
axes[0, 1].set_title("Events by Location")
axes[0, 1].tick_params(axis="x", rotation=45)

# Spatial category
spatial["Category"].value_counts().plot(
    kind="bar", ax=axes[0, 2]
)
axes[0, 2].set_title("Spatial Categories")

# Daily temporal trend
daily.plot(ax=axes[1, 0], marker="o")
axes[1, 0].set_title("Daily Trend")

# Hourly trend
hourly.plot(ax=axes[1, 1], marker="o")
axes[1, 1].set_title("Hourly Trend")
axes[1, 1].set_xlabel("Hour")

# Event count over time
daily_events = temporal.groupby("Date")["Event_Count"].sum()
daily_events.plot(ax=axes[1, 2], marker="o")
axes[1, 2].set_title("Daily Event Count")

plt.tight_layout()
plt.savefig(
    OUTPUT_DIR / "Combined_Dashboard.png",
    dpi=300, bbox_inches="tight"
)
plt.close()

print("\nALL VISUALIZATIONS GENERATED SUCCESSFULLY!")
print("------------------------------------------")
print("1. Spatial_Dashboard.png")
print("2. Temporal_Dashboard.png")
print("3. Combined_Dashboard.png")
print("\nSaved in:", OUTPUT_DIR)
