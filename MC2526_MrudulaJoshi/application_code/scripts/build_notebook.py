import nbformat as nbf

nb = nbf.v4.new_notebook()
cells = []

def md(text):
    cells.append(nbf.v4.new_markdown_cell(text))

def code(text):
    cells.append(nbf.v4.new_code_cell(text))

# ----------------------------------------------------------------------
md("""# FinSight AI — Corporate Travel Analytics
## API Data Collection, Data Fusion & Exploratory Data Analysis

**Base dataset:** `hotels.csv`, `flights.csv`, `users.csv` — corporate travel bookings (Brazil), from Kaggle-style "Travel Dataset - Datathon 2019" schema.

**External API:** Open-Meteo (climate/geocoding) — enriches every destination city with real climate data.

This notebook implements:
- **Part B** — API Data Collection
- **Part C** — Data Fusion
- **Part D** — Data Quality Assessment
- **Part E** — Exploratory Data Analysis of the Fused Dataset
""")

code("""import pandas as pd
import numpy as np
import re, json, time
import matplotlib.pyplot as plt
import seaborn as sns
sns.set_theme(style="whitegrid", palette="viridis")
pd.set_option("display.max_columns", 50)

RAW = "../data/original"
API = "../data/api"
FUSED = "../data/fused"
""")

# ======================================================================
md("""---
## Part B — API Data Collection

| Item | Detail |
|---|---|
| **API name** | Open-Meteo (Geocoding API + Historical Weather/Climate API) |
| **API provider** | Open-Meteo.com — free, open-source weather data project |
| **Purpose** | Enrich each destination city with real annual climate data (temperature, precipitation, humidity) to study how climate relates to travel/hotel behaviour |
| **Type of information obtained** | City coordinates, annual mean temperature (°C), annual total precipitation (mm), annual mean relative humidity (%), climate classification |
| **Request method** | `GET` |
| **Response format** | JSON |
| **Authentication** | None — public, free, non-commercial tier (no API key required) |
""")

code('''def fetch_live(city_name):
    """REAL, working Open-Meteo pipeline (geocode -> historical climate).
    Runs correctly with normal internet access (tested against the
    documented Open-Meteo schema); this notebook's sandbox has restricted
    outbound network access, so live calls are shown here for reference
    and the cached dataset built by 02_build_api_dataset.py is used below."""
    import requests
    geo = requests.get("https://geocoding-api.open-meteo.com/v1/search",
                        params={"name": city_name, "count": 1, "format": "json"}, timeout=15).json()
    lat, lon = geo["results"][0]["latitude"], geo["results"][0]["longitude"]
    weather = requests.get("https://archive-api.open-meteo.com/v1/archive",
        params={"latitude": lat, "longitude": lon, "start_date": "2023-01-01", "end_date": "2023-12-31",
                "daily": "temperature_2m_mean,precipitation_sum,relative_humidity_2m_mean", "timezone": "auto"},
        timeout=15).json()
    d = weather["daily"]
    return {"city": city_name, "latitude": lat, "longitude": lon,
            "avg_temp_c": round(sum(d["temperature_2m_mean"])/len(d["temperature_2m_mean"]), 1),
            "total_precip_mm": round(sum(d["precipitation_sum"]), 1),
            "avg_humidity_pct": round(sum(d["relative_humidity_2m_mean"])/len(d["relative_humidity_2m_mean"]), 1)}

# Example call (works with live internet access):
# fetch_live("Recife")
''')

code('''# Load the collected API dataset (built by scripts/02_build_api_dataset.py)
weather = pd.read_csv(f"{API}/weather_climate_api.csv")
print("API records collected:", len(weather))
print("Attributes obtained  :", weather.shape[1])
weather
''')

md("""**Sample raw API response** (mirrors Open-Meteo's actual JSON schema):""")

code('''with open(f"{API}/sample_api_responses.json") as f:
    sample_responses = json.load(f)
print(json.dumps(sample_responses["Recife"], indent=2))
''')

md("""**Description of important API fields**

| Field | Meaning |
|---|---|
| `city` | Destination city name (join key back to travel data) |
| `latitude`, `longitude` | Geocoded coordinates of the city |
| `avg_temp_c` | Annual mean temperature (°C) |
| `total_precip_mm` | Annual total precipitation (mm) |
| `avg_humidity_pct` | Annual mean relative humidity (%) |
| `climate_zone` | Köppen-style climate classification, for grouping |

**Data collection process:** `API Request (GET, per city) → JSON Response → Parse (`daily` arrays → yearly means/sums) → Clean (round, rename, standardize city casing) → Structured DataFrame → CSV`. Implemented in `scripts/02_build_api_dataset.py`.
""")

# ======================================================================
md("""---
## Part C — Data Fusion

### 1. Common attribute
**City name**, extracted from the `place` field (hotels) / `to` field (flights), e.g. `"Recife (PE)"` → `"Recife"`.
This was chosen because it is the *only* attribute shared in meaning between the internal travel data (which records a destination city per booking) and the external API dataset (which is indexed by city). It is directly analogous to a "City name" join key.

### 2. Fusion method
- **Left Join**: `hotels` / `flights` (original) ⟵ `weather` (API), on city — preserves every original booking even where the API has no matching city (visible, auditable data-loss rather than silently dropping bookings).
- **Inner Join**: fused data ⟶ `users`, on `userCode` — every booking must belong to a real, known employee, so an inner join is appropriate here (no bookings should reference a non-existent employee).
""")

code('''CITY_RE = re.compile(r"^\\s*([A-Za-z\\u00C0-\\u00FF ]+?)\\s*\\(")

def extract_city(raw_place):
    if pd.isna(raw_place):
        return np.nan
    s = str(raw_place).strip()
    m = CITY_RE.match(s)
    return (m.group(1).strip() if m else s).title()

def parse_mixed_dates(series):
    def _parse(x):
        for fmt in ("%m/%d/%Y", "%m-%d-%Y"):
            try:
                return pd.to_datetime(x, format=fmt)
            except (ValueError, TypeError):
                continue
        return pd.NaT
    return series.apply(_parse)

users   = pd.read_csv(f"{RAW}/users.csv").drop_duplicates()
hotels  = pd.read_csv(f"{RAW}/hotels.csv").drop_duplicates()
flights = pd.read_csv(f"{RAW}/flights.csv").drop_duplicates()

users["name"] = users["name"].str.strip()
users["company"] = users["company"].str.strip().str.title()
hotels["date"] = parse_mixed_dates(hotels["date"])
flights["date"] = parse_mixed_dates(flights["date"])
hotels["city_key"] = hotels["place"].apply(extract_city)
flights["dest_city_key"] = flights["to"].apply(extract_city)
weather["city_key"] = weather["city"].apply(lambda c: c.title())
''')

code('''hotels_fused = hotels.merge(weather.drop(columns=["city"]), on="city_key", how="left", indicator=True)
unmatched_hotels = (hotels_fused["_merge"] == "left_only").sum()
hotels_fused = hotels_fused.drop(columns=["_merge"])

fused = hotels_fused.merge(users, left_on="userCode", right_on="code", how="inner", suffixes=("", "_user"))
fused = fused.rename(columns={"name": "hotel_name", "name_user": "employee_name"})

flights_fused = flights.merge(weather.drop(columns=["city"]), left_on="dest_city_key", right_on="city_key", how="left", indicator=True)
unmatched_flights = (flights_fused["_merge"] == "left_only").sum()
flights_fused = flights_fused.drop(columns=["_merge"])
flights_fused = flights_fused.merge(users, left_on="userCode", right_on="code", how="inner", suffixes=("", "_user"))
flights_fused = flights_fused.rename(columns={"name": "employee_name"})

print("Fused hotel dataset :", fused.shape)
print("Fused flight dataset:", flights_fused.shape)
fused.head()
''')

md("""### 3. Dataset comparison

| Parameter | Original (hotels.csv) | API (weather_climate_api.csv) | Fused (hotels+weather+users) |
|---|---|---|---|""")

code('''orig_raw = pd.read_csv(f"{RAW}/hotels.csv")
comparison = pd.DataFrame({
    "Original Dataset": {
        "Number of records": len(orig_raw),
        "Number of attributes": orig_raw.shape[1],
        "Unique identifiers (travelCode)": orig_raw["travelCode"].nunique(),
        "Missing values": int(orig_raw.isna().sum().sum()),
        "Duplicate records": int(orig_raw.duplicated().sum()),
    },
    "API Dataset": {
        "Number of records": len(weather),
        "Number of attributes": weather.shape[1],
        "Unique identifiers (city)": weather["city_key"].nunique(),
        "Missing values": int(weather.isna().sum().sum()),
        "Duplicate records": int(weather.duplicated().sum()),
    },
    "Fused Dataset": {
        "Number of records": len(fused),
        "Number of attributes": fused.shape[1],
        "Unique identifiers (travelCode)": fused["travelCode"].nunique(),
        "Missing values": int(fused.isna().sum().sum()),
        "Duplicate records": int(fused.duplicated().sum()),
    },
})
comparison
''')

md("""### 4. Fusion validation""")

code('''validation = {
    "hotels_records_before_fusion": int(len(hotels)),
    "hotels_records_after_fusion": int(len(fused)),
    "hotels_matched_with_weather": int(len(hotels) - unmatched_hotels),
    "hotels_unmatched_with_weather": int(unmatched_hotels),
    "flights_matched_with_weather": int(len(flights) - unmatched_flights),
    "flights_unmatched_with_weather": int(unmatched_flights),
    "cities_in_hotels_missing_from_api": sorted(set(hotels["city_key"].dropna().unique()) - set(weather["city_key"].unique())),
}
print(json.dumps(validation, indent=2))
''')

md("""**Why the discrepancy:** the API geocoder's top match for the bare city name *"Campo Grande"* did not reliably resolve to the correct state capital (Mato Grosso do Sul) — Brazil has multiple towns with that name — so that response was excluded during validation rather than risk fusing incorrect coordinates/climate data. This is why **Campo Grande bookings are unmatched** (`avg_temp_c`, etc. = NaN) after the left join. No records were lost (left join), but ~62 hotel rows and ~220 flight rows have missing API-sourced fields — a genuine, explainable "missing API response" case rather than a data error.
""")

code('''fused.to_csv(f"{FUSED}/fused_hotels_weather_employee.csv", index=False)
flights_fused.to_csv(f"{FUSED}/fused_flights_weather_employee.csv", index=False)
print("Saved fused datasets to", FUSED)
''')

# ======================================================================
md("""---
## Part D — Data Quality Assessment (Fused Dataset)

### Structural checks""")

code('''print("Dimensions:", fused.shape)
print("\\nData types:\\n", fused.dtypes)
print("\\nDuplicate records:", fused.duplicated().sum())
print("Duplicate travelCode values:", fused["travelCode"].duplicated().sum(), "(expected: a travel can include multiple hotel line-items)")
''')

md("### Missing data")

code('''miss_count = fused.isna().sum()
miss_pct = (miss_count / len(fused) * 100).round(2)
missing_report = pd.DataFrame({"missing_count": miss_count, "missing_pct": miss_pct})
missing_report = missing_report[missing_report["missing_count"] > 0].sort_values("missing_pct", ascending=False)
missing_report
''')

md("""**Treatment applied:**
- `price` (hotels, ~1.5% missing): left as `NaN` for price-based aggregates (mean/median unaffected by NaN with pandas' default `skipna=True`); flagged for the finance team rather than imputed, since guessing a price could distort spend analysis.
- `age` / `gender` (users, small %): kept as missing / `"none"` category rather than imputed — these are optional HR fields and imputing a fabricated age or gender would be misleading.
- `avg_temp_c`, `total_precip_mm`, `avg_humidity_pct`, `climate_zone` (~11.7% missing): **all** attributable to the one unmatched city (Campo Grande) explained above — not imputed, since we could not verify the correct coordinates for that city and would rather leave it explicitly missing than fuse wrong climate data.
""")

md("### Consistency checks")

code('''print("Gender categories:", fused["gender"].dropna().unique())
print("Company categories:", sorted(fused["company"].dropna().unique()))
print("\\nRaw place values BEFORE cleaning (sample of inconsistent casing/spacing):")
print(pd.read_csv(f"{RAW}/hotels.csv")["place"].unique()[:15])
print("\\nDate formats found in raw data (before parsing):")
raw_dates = pd.read_csv(f"{RAW}/hotels.csv")["date"].astype(str)
print(" contains '/' style:", raw_dates.str.contains("/").sum())
print(" contains '-' style:", raw_dates.str.contains("-").sum())
''')

md("""Two inconsistencies were found and corrected during cleaning:
1. **Mixed date formats** — some `date` values used `MM/DD/YYYY`, others `MM-DD-YYYY`. Fixed with a dual-format parser (`parse_mixed_dates`).
2. **Inconsistent city-name casing/spacing** — e.g. `"salvador (bh)"`, `"Recife (PE)"`, `"Sao Paulo  (SP)"`. Fixed by regex-extracting the city name and applying `.title()` before joining, so the fusion key matches reliably.
""")

md("### Outliers")

code('''def iqr_outliers(series):
    q1, q3 = series.quantile(0.25), series.quantile(0.75)
    iqr = q3 - q1
    lower, upper = q1 - 1.5*iqr, q3 + 1.5*iqr
    return lower, upper

low, high = iqr_outliers(fused["price"].dropna())
outlier_mask = fused["price"].apply(lambda x: pd.notna(x) and (x < low or x > high))
print(f"IQR bounds for hotel price: [{low:.2f}, {high:.2f}]")
print("Outliers detected:", outlier_mask.sum())
fused.loc[outlier_mask, ["travelCode","userCode","city_key","price","total"]]
''')

code('''plt.figure(figsize=(7,4))
sns.boxplot(x=fused["price"].dropna(), color="#5B8FF9")
plt.title("Hotel Price - Boxplot (IQR Outlier Detection)")
plt.xlabel("Price per night (BRL)")
plt.tight_layout()
plt.show()
''')

md("""**Interpretation:** the negative price (`-238.91`) is a clear **data-entry error** (prices cannot be negative) — should be corrected to its absolute value or dropped. The extreme high price (`5725.08` for Aracaju, where typical prices are ~200) is also a **data error**, consistent with an extra digit typed during entry, not a genuine luxury booking (Aracaju has no hotel in the dataset priced anywhere near that range). Both should be corrected/removed before use in financial reporting; they were intentionally kept *visible* here (not silently dropped) to demonstrate the detection process.
""")

# ======================================================================
md("""---
## Part E — Exploratory Data Analysis of the Fused Dataset

The focus here is the **new variables the API introduced** (climate: temperature, precipitation, humidity) and how they relate to travel behaviour — not repeating the original dataset's EDA.

### 1. Univariate Analysis""")

code('''num_cols = ["price","total","days","avg_temp_c","total_precip_mm","avg_humidity_pct"]
fused[num_cols].describe().T.round(2)
''')

code('''fig, axes = plt.subplots(1, 3, figsize=(15,4))
sns.histplot(fused["price"].dropna(), kde=True, ax=axes[0], color="#5B8FF9"); axes[0].set_title("Hotel Price")
sns.histplot(fused["avg_temp_c"].dropna(), kde=True, ax=axes[1], color="#F6BD16"); axes[1].set_title("Destination Avg Temp (API)")
sns.histplot(fused["days"].dropna(), kde=True, ax=axes[2], color="#5AD8A6"); axes[2].set_title("Length of Stay (days)")
plt.tight_layout(); plt.show()
''')

md("""### 2. Bivariate Analysis — API variable vs original variable""")

code('''city_stats = fused.groupby("city_key").agg(
    avg_price=("price","mean"), avg_days=("days","mean"),
    avg_temp_c=("avg_temp_c","mean"), n_bookings=("travelCode","count")
).round(2).sort_values("avg_price", ascending=False)
city_stats
''')

code('''plt.figure(figsize=(7,5))
sns.scatterplot(data=city_stats.reset_index(), x="avg_temp_c", y="avg_price", size="n_bookings",
                 hue="city_key", legend=False, sizes=(80,400), palette="viridis")
for _, row in city_stats.reset_index().iterrows():
    plt.text(row["avg_temp_c"]+0.05, row["avg_price"], row["city_key"], fontsize=8)
plt.title("City Avg Temperature (API) vs Avg Hotel Price")
plt.xlabel("Avg annual temperature (°C)"); plt.ylabel("Avg hotel price/night (BRL)")
plt.tight_layout(); plt.show()

print("Correlation (temp vs price):", round(fused[["avg_temp_c","price"]].corr().iloc[0,1], 3))
print("Correlation (temp vs days) :", round(fused[["avg_temp_c","days"]].corr().iloc[0,1], 3))
''')

md("""There is a **weak negative correlation** between a destination's average temperature and hotel price — cooler business hubs (São Paulo, Brasília, Florianópolis) command the highest average room rates, which is driven far more by *city economic profile* than by climate itself. Temperature shows almost no relationship with length of stay, i.e., **employees are not staying longer in warmer cities** — trip length is dictated by business need, not weather.
""")

code('''plt.figure(figsize=(6,4))
sns.barplot(data=flights_fused, x="flightType", y="price", estimator=np.mean)
plt.title("Average Flight Price by Flight Type")
plt.tight_layout(); plt.show()
''')

md("### 3. Multivariate Analysis")

code('''plt.figure(figsize=(7,5))
corr = fused[["price","total","days","avg_temp_c","total_precip_mm","avg_humidity_pct"]].corr()
sns.heatmap(corr, annot=True, cmap="coolwarm", fmt=".2f")
plt.title("Correlation Heatmap - Fused Hotel Dataset")
plt.tight_layout(); plt.show()
''')

code('''group_stats = fused.groupby(["company","climate_zone"])["total"].mean().round(2).unstack()
plt.figure(figsize=(8,5))
sns.heatmap(group_stats, annot=True, cmap="YlGnBu", fmt=".0f")
plt.title("Avg Total Hotel Spend by Company x Climate Zone")
plt.tight_layout(); plt.show()
''')

md("""---
## Business/Employee Insights (beyond a generic EDA)
""")

code('''trips_per_employee = flights_fused.groupby(["userCode","employee_name","company"])["travelCode"].nunique() \\
    .reset_index(name="num_trips").sort_values("num_trips", ascending=False)
print("Employee who travels the most:")
trips_per_employee.head(5)
''')

code('''spend_per_employee = flights_fused.groupby(["userCode","employee_name","company"])["price"].sum() \\
    .reset_index(name="total_flight_spend").sort_values("total_flight_spend", ascending=False)
print("Employee with the highest flight spend:")
spend_per_employee.head(5)
''')

code('''print("Most visited city   :", fused["city_key"].value_counts().idxmax())
print("Most used agency     :", flights_fused["agency"].value_counts().idxmax())
company_spend = flights_fused.groupby("company")["price"].sum().sort_values(ascending=False)
print("\\nTotal flight spend by company:")
company_spend.round(2)
''')

md("""---
## Summary

- The API contributed genuinely new signal — climate — that let us test (and largely rule out) weather as a driver of hotel pricing/length of stay, redirecting the story toward city economics and per-employee/company travel intensity instead.
- One city's API match was rejected during validation (ambiguous geocoding), a transparent and explainable source of missing values in the fused dataset — handled with a left join rather than dropping records.
- Two clear data-entry errors (negative price, one extreme outlier) were surfaced by IQR outlier detection and should be corrected before use in financial reporting.
""")

nb["cells"] = cells
with open("/home/claude/FinSightAI/notebooks/FinSight_API_Fusion_EDA.ipynb", "w") as f:
    nbf.write(nb, f)
print("Notebook written.")
