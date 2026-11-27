"""
Spatial Dashboard - US Airport Traffic (Feb 2011) + US City Populations (2014)
Run:  python spatial_dashboard.py
Output: Dashboard/spatial_dashboard.html (opens automatically in your browser)
"""
import os
import numpy as np, pandas as pd
import plotly.express as px, plotly.graph_objects as go
from dashkit import build, style

BASE = os.path.dirname(os.path.abspath(__file__))
ap = pd.read_csv(os.path.join(BASE, "Dataset", "us_airport_traffic.csv"))
ct = pd.read_csv(os.path.join(BASE, "Dataset", "us_cities_population.csv"))

# ---------------- clean: drop missing rows, tidy text, keep valid coordinates
ap = ap.dropna(subset=["lat", "long", "cnt", "state"]).drop_duplicates("iata")
ct = ct.dropna().drop_duplicates()
ct["name"] = ct["name"].str.strip()
ap = ap[ap.lat.between(15, 72) & ap.long.between(-170, -60)]      # keep US (incl. AK/HI)
ct = ct[ct.lat.between(15, 72) & ct.lon.between(-170, -60)]

# ---------------- spatial features
ap["region"] = pd.cut(ap["long"], [-180, -105, -90, -60], labels=["West", "Central", "East"])
ap["lat_band"] = pd.cut(ap["lat"], [0, 30, 35, 40, 45, 80], labels=["<30N", "30-35N", "35-40N", "40-45N", ">45N"])
def haversine(lat1, lon1, lat2, lon2):
    p1, p2 = np.radians(lat1), np.radians(lat2)
    a = np.sin((p2 - p1) / 2) ** 2 + np.cos(p1) * np.cos(p2) * np.sin(np.radians(lon2 - lon1) / 2) ** 2
    return 6371 * 2 * np.arcsin(np.sqrt(a))
ap["km_from_center"] = haversine(ap.lat, ap.long, 39.8, -98.6)   # distance from geographic centre of the US
st = ap.groupby("state").agg(traffic=("cnt", "sum"), airports=("iata", "count"), avg=("cnt", "mean")).reset_index()

kpis = [("Airports", f"{len(ap):,}"), ("Total Flights", f"{ap.cnt.sum():,}"),
        ("Busiest Airport", ap.sort_values("cnt").iloc[-1].iata), ("States Covered", f"{ap.state.nunique()}"),
        ("US Cities", f"{len(ct):,}"), ("Largest City", ct.sort_values("pop").iloc[-1]["name"])]

def usgeo(f, **k):
    f.update_geos(scope="usa", bgcolor="rgba(0,0,0,0)", landcolor="#1b2547", subunitcolor="#25305a",
                  showlakes=False, **k)
    f.update_layout(margin=dict(l=0, r=0, t=0, b=0))
    return f

# ---------------- charts: airports
m1 = px.scatter_geo(ap, lat="lat", lon="long", size="cnt", color="cnt", hover_name="airport",
                    hover_data=["city", "state", "cnt"], color_continuous_scale="Sunset", size_max=38, scope="usa")
usgeo(m1)
m2 = px.choropleth(st, locations="state", locationmode="USA-states", color="traffic", scope="usa",
                   color_continuous_scale="Purp", hover_data=["airports"])
usgeo(m2)
top = ap.nlargest(15, "cnt").sort_values("cnt")
b1 = px.bar(top, x="cnt", y="iata", orientation="h", color="cnt", color_continuous_scale="Sunset",
            hover_name="airport", labels={"cnt": "Flights", "iata": ""}); b1.update_coloraxes(showscale=False)
b2 = px.bar(st.nlargest(12, "airports").sort_values("airports"), x="airports", y="state", orientation="h",
            color="airports", color_continuous_scale="Tealgrn"); b2.update_coloraxes(showscale=False)
tm = px.treemap(ap, path=[px.Constant("USA"), "region", "state", "iata"], values="cnt", color="cnt",
                color_continuous_scale="Magma")
h1 = px.histogram(ap, x="cnt", nbins=40, log_y=True, color_discrete_sequence=["#4cc9f0"])
h1.update_layout(xaxis_title="Flights per airport", yaxis_title="Airports (log)", bargap=.05)
rg = ap.groupby("region", observed=True).agg(traffic=("cnt", "sum"), airports=("iata", "count")).reset_index()
p1 = px.pie(rg, names="region", values="traffic", hole=.55, color_discrete_sequence=["#ff7a45", "#b05cff", "#3ddc97"])
lb = ap.groupby("lat_band", observed=True).cnt.sum().reset_index()
b3 = px.bar(lb, x="lat_band", y="cnt", color="cnt", color_continuous_scale="Viridis", labels={"lat_band": "Latitude band", "cnt": "Flights"})
b3.update_coloraxes(showscale=False)
sc = px.scatter(ap, x="km_from_center", y="cnt", color="region", size="cnt", hover_name="airport", log_y=True,
                color_discrete_sequence=["#ff7a45", "#b05cff", "#3ddc97"], size_max=30)
sc.update_layout(xaxis_title="Distance from US centre (km)", yaxis_title="Flights (log)")
d2 = px.density_heatmap(ap, x="long", y="lat", z="cnt", histfunc="sum", nbinsx=30, nbinsy=18, color_continuous_scale="Inferno")
d2.update_layout(xaxis_title="Longitude", yaxis_title="Latitude")
bx = px.box(ap, x="region", y="cnt", color="region", points="all", log_y=True,
            color_discrete_sequence=["#ff7a45", "#b05cff", "#3ddc97"])

# ---------------- charts: cities
c1 = px.scatter_geo(ct, lat="lat", lon="lon", size="pop", color="pop", hover_name="name",
                    color_continuous_scale="Turbo", size_max=30, scope="usa", opacity=.7)
usgeo(c1)
c2 = px.bar(ct.nlargest(15, "pop").sort_values("pop"), x="pop", y="name", orientation="h", color="pop",
            color_continuous_scale="Purp"); c2.update_coloraxes(showscale=False)
c3 = px.histogram(ct, x="pop", nbins=60, log_y=True, color_discrete_sequence=["#ef476f"])
c3.update_layout(xaxis_title="City population", yaxis_title="Cities (log)", bargap=.05)
c4 = px.density_heatmap(ct, x="lon", y="lat", z="pop", histfunc="sum", nbinsx=40, nbinsy=25, color_continuous_scale="Viridis")
c4.update_layout(xaxis_title="Longitude", yaxis_title="Latitude")
ct["lon_band"] = pd.cut(ct.lon, [-180, -105, -90, -60], labels=["West", "Central", "East"])
c5 = px.violin(ct, x="lon_band", y="pop", color="lon_band", box=True, log_y=True,
               color_discrete_sequence=["#ff7a45", "#b05cff", "#3ddc97"])

tabs = {
 "Airport Map": [("Airport traffic map (bubble = flights)", style(m1, 520, False), 8),
                 ("Traffic by state", style(m2, 520, False), 4),
                 ("Top 15 busiest airports", style(b1, 400, False), 6), ("States with most airports", style(b2, 400, False), 6)],
 "Spatial Patterns": [("Region > state > airport", style(tm, 440, False), 12),
                      ("Traffic share by region", style(p1, 380), 4), ("Traffic by latitude band", style(b3, 380, False), 4),
                      ("Traffic distribution", style(h1, 380, False), 4),
                      ("Distance from centre vs traffic", style(sc, 420), 6), ("Spatial density of flights", style(d2, 420, False), 6),
                      ("Traffic spread by region", style(bx, 380, False), 12)],
 "City Population": [("City population map", style(c1, 500, False), 12),
                     ("15 largest cities", style(c2, 420, False), 4), ("Population distribution", style(c3, 420, False), 4),
                     ("Population density grid", style(c4, 420, False), 4), ("Population by longitude band", style(c5, 400, False), 12)],
}
build("Spatial Analytics Dashboard",
      "US airport traffic (Feb 2011) and US city populations (2014) - maps, regional and density analysis",
      kpis, tabs, os.path.join(BASE, "Dashboard", "spatial_dashboard.html"),
      footer="Python - pandas - Plotly  |  Spatial visualization project")
