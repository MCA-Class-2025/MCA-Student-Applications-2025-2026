"""GeoTime Analytics - pipeline. Run: python geotime_pipeline.py
Needs internet. pip install pandas numpy requests scikit-learn pyarrow
Outputs (in ./Dataset): raw, cleaned CSV, daily anomalies CSV, extraction log."""
import os, json, datetime as dt
import numpy as np, pandas as pd, requests
from sklearn.cluster import DBSCAN

URL = "https://earthquake.usgs.gov/fdsnws/event/1/query"
LIMIT = 20000
os.makedirs("../Dataset", exist_ok=True)

def fetch(start, end):
    """GeoJSON (not CSV) is used because tsunami/sig/felt/alert are GeoJSON properties.
    If a range returns LIMIT events it is split in half - no silent truncation."""
    p = dict(format="geojson", starttime=start.isoformat(), endtime=end.isoformat(),
             minmagnitude=2.5, orderby="time-asc", limit=LIMIT)
    r = requests.get(URL, params=p, timeout=120); r.raise_for_status()
    feats = r.json()["features"]
    if len(feats) >= LIMIT:
        mid = start + (end - start) / 2
        return fetch(start, mid) + fetch(mid, end)
    print(start, "->", end, len(feats)); return feats

rows = []
for y in range(2021, 2026):
    for m in range(1, 13):
        s = dt.datetime(y, m, 1)
        e = dt.datetime(y + (m == 12), m % 12 + 1, 1)
        for f in fetch(s, e):
            d = dict(f["properties"]); lon, lat, dep = f["geometry"]["coordinates"][:3]
            d.update(id=f["id"], longitude=lon, latitude=lat, depth=dep); rows.append(d)

df = pd.DataFrame(rows)
keep = ["id","time","latitude","longitude","depth","mag","magType","place","type",
        "status","tsunami","sig","felt","alert","gap"]
df = df[[c for c in keep if c in df.columns]]
df["time"] = pd.to_datetime(df["time"], unit="ms", utc=True)
df.to_csv("../Dataset/USGS_Earthquake_Raw_2021_2025.csv", index=False)
open("../Dataset/extraction_log.txt", "w").write(
    f"Extracted: {dt.datetime.utcnow().isoformat()}Z\nSource: {URL}\nRows: {len(df)}\n")

# ---- cleaning ----
print(df.shape); print(df.isnull().sum())
print("duplicate ids:", df["id"].duplicated().sum())
df = df.drop_duplicates("id")
for c in ["latitude","longitude","depth","mag","sig","felt","tsunami","gap"]:
    if c in df: df[c] = pd.to_numeric(df[c], errors="coerce")
df = df[df.latitude.between(-90, 90) & df.longitude.between(-180, 180)]
df = df.dropna(subset=["time","latitude","longitude","mag"])
df.loc[~df["depth"].between(-100, 1000), "depth"] = np.nan   # keep rows, blank bad depth

# ---- features (UTC) ----
t = df["time"]
df["year"], df["month"], df["month_name"] = t.dt.year, t.dt.month, t.dt.month_name()
df["day"], df["hour"], df["day_of_week"] = t.dt.day, t.dt.hour, t.dt.day_name()
df["weekday_num"], df["quarter"] = t.dt.dayofweek + 1, t.dt.quarter
df["year_month"] = t.dt.strftime("%Y-%m")
df["EventDate"] = t.dt.date
bins = [-np.inf, 3, 4, 5, 6, 7, 8, np.inf]
labs = ["Below 3","3.0-3.9","4.0-4.9","5.0-5.9","6.0-6.9","7.0-7.9","8.0+"]
df["magnitude_category"] = pd.cut(df["mag"], bins, labels=labs, right=False).astype(str)
# depth classes: 70 / 300 km are a common convention, not defined in the project brief - cite/confirm
df["depth_category"] = pd.cut(df["depth"], [-np.inf, 70, 300, np.inf],
                              labels=["Shallow","Intermediate","Deep"], right=False).astype(str)

# ---- DBSCAN (50 km, min 10, haversine) ----
xy = np.radians(df[["latitude","longitude"]].values)
df["spatial_cluster"] = DBSCAN(eps=50/6371, min_samples=10, metric="haversine").fit_predict(xy)
print(df["spatial_cluster"].value_counts().head(20))

# ---- statistics ----
print("Total", len(df), "| mean mag", df.mag.mean(), "| median", df.mag.median(),
      "| max", df.mag.max(), "| std", df.mag.std())
print("M5+", (df.mag >= 5).sum(), "| M6+", (df.mag >= 6).sum())
print(df["depth_category"].value_counts(normalize=True) * 100)
print("Pearson", df["mag"].corr(df["depth"], method="pearson"),
      "| Spearman", df["mag"].corr(df["depth"], method="spearman"))

# ---- temporal anomaly (30-day rolling mean + 3 SD) ----
daily = df.set_index("time").resample("D").size().rename("event_count").to_frame()
daily["rolling_mean"] = daily.event_count.rolling(30).mean()
daily["rolling_std"] = daily.event_count.rolling(30).std()
daily["upper_threshold"] = daily.rolling_mean + 3 * daily.rolling_std
daily["anomaly"] = daily.event_count > daily.upper_threshold
daily.to_csv("../Dataset/Daily_Anomalies.csv")
print(daily[daily.anomaly])

df.to_csv("../Dataset/USGS_Earthquake_Cleaned.csv", index=False)

# ---- dashboard data (lets Dashboard/geotime_dashboard.html open with data, no upload) ----
import json
dcols = ["time","latitude","longitude","depth","mag","place","tsunami","year","month","hour",
         "weekday_num","magnitude_category","spatial_cluster","EventDate"]
os.makedirs("../Dashboard", exist_ok=True)
with open("../Dashboard/dashboard_data.js", "w", encoding="utf-8") as fh:
    fh.write("window.GEO_CSV = " + json.dumps(df[[c for c in dcols if c in df.columns]].to_csv(index=False)) + ";")
print("Done. Load Dataset/USGS_Earthquake_Cleaned.csv into the dashboard / Power BI.")
