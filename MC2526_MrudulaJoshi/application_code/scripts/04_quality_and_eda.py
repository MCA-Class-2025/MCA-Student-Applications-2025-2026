"""
04_quality_and_eda.py -- Part D (Data Quality) and Part E (EDA)
"""
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
import json

sns.set_theme(style="whitegrid", palette="viridis")
FUSED = "/home/claude/FinSightAI/data/fused"
SHOTS = "/home/claude/FinSightAI/screenshots"

hotels = pd.read_csv(f"{FUSED}/fused_hotels_weather_employee.csv")
flights = pd.read_csv(f"{FUSED}/fused_flights_weather_employee.csv")

# =====================================================================
# PART D -- DATA QUALITY ASSESSMENT (on the fused hotel dataset)
# =====================================================================
quality = {}
quality["dimensions"] = {"rows": hotels.shape[0], "columns": hotels.shape[1]}
quality["dtypes"] = hotels.dtypes.astype(str).to_dict()
quality["unique_values_per_column"] = hotels.nunique().to_dict()
quality["duplicate_records"] = int(hotels.duplicated().sum())
quality["duplicate_travelCode"] = int(hotels["travelCode"].duplicated().sum())

miss_count = hotels.isna().sum()
miss_pct = (miss_count / len(hotels) * 100).round(2)
quality["missing_values"] = {
    col: {"count": int(miss_count[col]), "pct": float(miss_pct[col])}
    for col in hotels.columns if miss_count[col] > 0
}
quality["attribute_with_max_missing"] = miss_count.idxmax() if miss_count.max() > 0 else None

# consistency: gender categories, company casing, city casing already fixed via city_key
quality["gender_categories_found"] = hotels["gender"].dropna().unique().tolist()
quality["company_categories_found"] = sorted(hotels["company"].dropna().unique().tolist())

# outliers via IQR on price and total
def iqr_outliers(series):
    q1, q3 = series.quantile(0.25), series.quantile(0.75)
    iqr = q3 - q1
    lower, upper = q1 - 1.5 * iqr, q3 + 1.5 * iqr
    mask = (series < lower) | (series > upper)
    return mask, lower, upper

price_mask, price_low, price_high = iqr_outliers(hotels["price"].dropna())
full_price_mask = hotels["price"].apply(lambda x: (x < price_low or x > price_high) if pd.notna(x) else False)
quality["price_outliers"] = {
    "count": int(full_price_mask.sum()),
    "lower_bound": round(price_low, 2), "upper_bound": round(price_high, 2),
    "example_rows": hotels.loc[full_price_mask, ["travelCode", "userCode", "city_key", "price", "total"]].head(10).to_dict("records"),
}

with open(f"{FUSED}/quality_report.json", "w") as f:
    json.dump(quality, f, indent=2, default=str)
print("=== PART D: DATA QUALITY SUMMARY ===")
print(json.dumps(quality, indent=2, default=str))

# Boxplot screenshot for outliers
plt.figure(figsize=(7, 4))
sns.boxplot(x=hotels["price"].dropna(), color="#5B8FF9")
plt.title("Hotel Price - Boxplot (IQR Outlier Detection)")
plt.xlabel("Price per night (BRL)")
plt.tight_layout()
plt.savefig(f"{SHOTS}/d1_price_boxplot.png", dpi=140)
plt.close()

# =====================================================================
# PART E -- EXPLORATORY DATA ANALYSIS OF THE FUSED DATASET
# =====================================================================
insights = {}

# ---- Univariate: price, total, avg_temp_c, days ----
num_cols = ["price", "total", "days", "avg_temp_c", "total_precip_mm", "avg_humidity_pct"]
univariate = hotels[num_cols].describe().T
univariate["missing"] = hotels[num_cols].isna().sum()
insights["univariate_stats"] = univariate.round(2).to_dict("index")

fig, axes = plt.subplots(1, 3, figsize=(15, 4))
sns.histplot(hotels["price"].dropna(), kde=True, ax=axes[0], color="#5B8FF9")
axes[0].set_title("Distribution of Hotel Price")
sns.histplot(hotels["avg_temp_c"].dropna(), kde=True, ax=axes[1], color="#F6BD16")
axes[1].set_title("Distribution of Destination Avg Temp (API)")
sns.histplot(hotels["days"].dropna(), kde=True, ax=axes[2], color="#5AD8A6")
axes[2].set_title("Distribution of Length of Stay (days)")
plt.tight_layout()
plt.savefig(f"{SHOTS}/e1_univariate_histograms.png", dpi=140)
plt.close()

# ---- Bivariate: API variable (avg_temp_c) vs original variable (price / days) ----
city_stats = hotels.groupby("city_key").agg(
    avg_price=("price", "mean"), avg_days=("days", "mean"),
    avg_temp_c=("avg_temp_c", "mean"), n_bookings=("travelCode", "count")
).round(2).sort_values("avg_price", ascending=False)
insights["city_level_stats"] = city_stats.to_dict("index")

plt.figure(figsize=(7, 5))
sns.scatterplot(data=city_stats.reset_index(), x="avg_temp_c", y="avg_price", size="n_bookings",
                 hue="city_key", legend=False, sizes=(80, 400), palette="viridis")
for _, row in city_stats.reset_index().iterrows():
    plt.text(row["avg_temp_c"] + 0.05, row["avg_price"], row["city_key"], fontsize=8)
plt.title("City Avg Temperature (API) vs Avg Hotel Price")
plt.xlabel("Avg annual temperature (\u00b0C)")
plt.ylabel("Avg hotel price/night (BRL)")
plt.tight_layout()
plt.savefig(f"{SHOTS}/e2_temp_vs_price.png", dpi=140)
plt.close()

corr_temp_price = hotels[["avg_temp_c", "price"]].corr().iloc[0, 1]
corr_temp_days = hotels[["avg_temp_c", "days"]].corr().iloc[0, 1]
insights["correlation_temp_vs_price"] = round(float(corr_temp_price), 3)
insights["correlation_temp_vs_days"] = round(float(corr_temp_days), 3)

# ---- Bivariate: flightType vs price ----
plt.figure(figsize=(6, 4))
sns.barplot(data=flights, x="flightType", y="price", estimator=np.mean, palette="magma")
plt.title("Average Flight Price by Flight Type")
plt.tight_layout()
plt.savefig(f"{SHOTS}/e3_flighttype_vs_price.png", dpi=140)
plt.close()

# ---- Multivariate: correlation heatmap ----
plt.figure(figsize=(7, 5))
corr = hotels[["price", "total", "days", "avg_temp_c", "total_precip_mm", "avg_humidity_pct"]].corr()
sns.heatmap(corr, annot=True, cmap="coolwarm", fmt=".2f")
plt.title("Correlation Heatmap - Fused Hotel Dataset")
plt.tight_layout()
plt.savefig(f"{SHOTS}/e4_correlation_heatmap.png", dpi=140)
plt.close()

# ---- Multivariate: group-wise (company x climate_zone avg spend) ----
group_stats = hotels.groupby(["company", "climate_zone"])["total"].mean().round(2).unstack()
plt.figure(figsize=(8, 5))
sns.heatmap(group_stats, annot=True, cmap="YlGnBu", fmt=".0f")
plt.title("Avg Total Hotel Spend by Company x Climate Zone")
plt.tight_layout()
plt.savefig(f"{SHOTS}/e5_company_climate_spend.png", dpi=140)
plt.close()

# =====================================================================
# EMPLOYEE / BUSINESS INSIGHTS (for report + chatbot)
# =====================================================================
trips_per_employee = flights.groupby(["userCode", "employee_name", "company"])["travelCode"].nunique().reset_index()
trips_per_employee = trips_per_employee.rename(columns={"travelCode": "num_trips"}).sort_values("num_trips", ascending=False)
insights["top_10_employees_by_trips"] = trips_per_employee.head(10).to_dict("records")

spend_per_employee = flights.groupby(["userCode", "employee_name", "company"])["price"].sum().reset_index()
spend_per_employee = spend_per_employee.rename(columns={"price": "total_flight_spend"}).sort_values("total_flight_spend", ascending=False)
insights["top_10_employees_by_flight_spend"] = spend_per_employee.head(10).to_dict("records")

hotel_spend_per_employee = hotels.groupby(["userCode", "employee_name", "company"])["total"].sum().reset_index()
hotel_spend_per_employee = hotel_spend_per_employee.rename(columns={"total": "total_hotel_spend"}).sort_values("total_hotel_spend", ascending=False)
insights["top_10_employees_by_hotel_spend"] = hotel_spend_per_employee.head(10).to_dict("records")

company_spend = (flights.groupby("company")["price"].sum() + hotels.groupby("company")["total"].sum().reindex(flights["company"].unique(), fill_value=0)).sort_values(ascending=False)
insights["company_total_travel_spend"] = company_spend.round(2).to_dict()

most_used_agency = flights["agency"].value_counts().to_dict()
insights["most_used_agency"] = most_used_agency

most_visited_city = hotels["city_key"].value_counts().to_dict()
insights["most_visited_city"] = most_visited_city

import re as _re
_raw_json = json.dumps(insights, indent=2, default=str, allow_nan=True)
_raw_json = _re.sub(r"\bNaN\b", "null", _raw_json)
with open(f"{FUSED}/eda_insights.json", "w") as f:
    f.write(_raw_json)

print("\n=== PART E: KEY EDA INSIGHTS ===")
print("Correlation (avg_temp_c vs price):", insights["correlation_temp_vs_price"])
print("Correlation (avg_temp_c vs days)  :", insights["correlation_temp_vs_days"])
print("\nTop 3 employees by number of trips:")
for r in insights["top_10_employees_by_trips"][:3]:
    print(" ", r)
print("\nTop 3 employees by flight spend:")
for r in insights["top_10_employees_by_flight_spend"][:3]:
    print(" ", r)
print("\nMost visited city:", max(most_visited_city, key=most_visited_city.get))
print("Most used agency:", max(most_used_agency, key=most_used_agency.get))
print("\nAll charts saved to", SHOTS)
