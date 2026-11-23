"""
Temporal Dashboard - Melbourne daily minimum temperature (1981-1990) + Monthly airline passengers (1949-1960)
Run:  python temporal_dashboard.py
Output: Dashboard/temporal_dashboard.html (opens automatically in your browser)
"""
import os
import numpy as np, pandas as pd
import plotly.express as px, plotly.graph_objects as go
from dashkit import build, style

BASE = os.path.dirname(os.path.abspath(__file__))
t = pd.read_csv(os.path.join(BASE, "Dataset", "melbourne_daily_min_temperature.csv"), parse_dates=["Date"])
a = pd.read_csv(os.path.join(BASE, "Dataset", "airline_passengers.csv"), parse_dates=["Month"])

# ---------------- clean: temperature file has a few non-numeric entries in some versions
t["Temp"] = pd.to_numeric(t["Temp"], errors="coerce")
t = t.dropna().drop_duplicates("Date").sort_values("Date").reset_index(drop=True)
a = a.dropna().sort_values("Month").reset_index(drop=True)

# ---------------- temporal features
t["year"], t["month"] = t.Date.dt.year, t.Date.dt.month
t["month_name"] = t.Date.dt.strftime("%b"); t["doy"] = t.Date.dt.dayofyear; t["dow"] = t.Date.dt.day_name()
t["season"] = t.month.map(lambda m: "Summer" if m in (12, 1, 2) else "Autumn" if m in (3, 4, 5)
                          else "Winter" if m in (6, 7, 8) else "Spring")   # southern hemisphere
t["roll30"] = t.Temp.rolling(30, center=True).mean()
mu, sd = t.Temp.rolling(30).mean(), t.Temp.rolling(30).std()
t["anomaly"] = (t.Temp - mu).abs() > 3 * sd                                  # 30-day rolling mean +/- 3 SD
MORD = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
a["year"], a["month"] = a.Month.dt.year, a.Month.dt.strftime("%b")
a["yoy"] = a.Passengers.pct_change(12) * 100
a["roll12"] = a.Passengers.rolling(12, center=True).mean()

kpis = [("Daily Records", f"{len(t):,}"), ("Mean Min Temp", f"{t.Temp.mean():.1f} C"),
        ("Coldest Day", f"{t.Temp.min():.1f} C"), ("Hottest Min", f"{t.Temp.max():.1f} C"),
        ("Anomaly Days", f"{int(t.anomaly.sum())}"), ("Passenger Growth", f"{a.Passengers.iloc[-1]/a.Passengers.iloc[0]:.1f}x")]

# ---------------- Temperature charts
l1 = go.Figure()
l1.add_trace(go.Scatter(x=t.Date, y=t.Temp, name="Daily", line=dict(color="#4cc9f0", width=1), opacity=.55))
l1.add_trace(go.Scatter(x=t.Date, y=t.roll30, name="30-day mean", line=dict(color="#ff7a45", width=2.5)))
an = t[t.anomaly]
l1.add_trace(go.Scatter(x=an.Date, y=an.Temp, mode="markers", name="Anomaly (3 SD)", marker=dict(color="#ef476f", size=7, symbol="diamond")))
l1.update_xaxes(rangeslider_visible=True); l1.update_layout(yaxis_title="Min temp (C)")
ms = t.groupby("month").Temp.mean().reindex(range(1, 13)); ms.index = MORD
r2 = px.bar(x=ms.index, y=ms.values, color=ms.values, color_continuous_scale="Turbo", labels={"x": "", "y": "Avg min temp (C)"})
r2.update_coloraxes(showscale=False)
hm = t.pivot_table(index="year", columns="month", values="Temp", aggfunc="mean"); hm.columns = MORD
r3 = px.imshow(hm, text_auto=".1f", color_continuous_scale="Turbo", aspect="auto"); r3.update_yaxes(type="category")
r4 = px.box(t, x="month_name", y="Temp", color="month_name", category_orders={"month_name": MORD},
            color_discrete_sequence=px.colors.sequential.Plasma_r)
yr = t.groupby("year").Temp.mean().reset_index()
z = np.polyfit(yr.year, yr.Temp, 1)
r5 = go.Figure([go.Scatter(x=yr.year, y=yr.Temp, mode="lines+markers", name="Yearly mean", line=dict(color="#3ddc97", width=3)),
                go.Scatter(x=yr.year, y=np.polyval(z, yr.year), name=f"Trend ({z[0]:+.3f} C/yr)", line=dict(color="#ffd166", dash="dash"))])
r5.update_yaxes(title="Mean min temp (C)")
r6 = px.violin(t, x="season", y="Temp", color="season", box=True, category_orders={"season": ["Summer", "Autumn", "Winter", "Spring"]},
               color_discrete_sequence=["#ff7a45", "#ffd166", "#4cc9f0", "#3ddc97"])
r7 = px.histogram(t, x="Temp", nbins=40, color="season", barmode="overlay", opacity=.65,
                  color_discrete_sequence=["#ff7a45", "#ffd166", "#4cc9f0", "#3ddc97"])
r7.update_layout(xaxis_title="Min temp (C)", yaxis_title="Days")
cal = t.pivot_table(index="year", columns="doy", values="Temp")
r8 = px.imshow(cal, color_continuous_scale="Turbo", aspect="auto", labels=dict(x="Day of year", color="C")); r8.update_yaxes(type="category")
sdv = t.set_index("Date").Temp.rolling(30).std().reset_index()
r9 = px.area(sdv, x="Date", y="Temp", color_discrete_sequence=["#b05cff"]); r9.update_layout(yaxis_title="30-day volatility (SD)")
lags = list(range(1, 61)); acf = [t.Temp.autocorr(l) for l in lags]
r10 = px.bar(x=lags, y=acf, color=acf, color_continuous_scale="Sunset", labels={"x": "Lag (days)", "y": "Autocorrelation"})
r10.update_coloraxes(showscale=False)
r11 = px.scatter(t.assign(prev=t.Temp.shift(1)).dropna(), x="prev", y="Temp", color="season", opacity=.5,
                 color_discrete_sequence=["#ff7a45", "#ffd166", "#4cc9f0", "#3ddc97"])
r11.update_layout(xaxis_title="Yesterday (C)", yaxis_title="Today (C)")

# ---------------- Passenger charts
p1 = go.Figure([go.Scatter(x=a.Month, y=a.Passengers, name="Passengers", fill="tozeroy", line=dict(color="#ff7a45"), fillcolor="rgba(255,122,69,.2)"),
                go.Scatter(x=a.Month, y=a.roll12, name="12-month trend", line=dict(color="#4cc9f0", width=3))])
p1.update_yaxes(title="Passengers (thousands)")
py = a.groupby("year").Passengers.sum().reset_index()
p2 = px.bar(py, x="year", y="Passengers", color="Passengers", color_continuous_scale="Sunset"); p2.update_coloraxes(showscale=False)
sm = a.pivot_table(index="month", columns="year", values="Passengers").reindex(MORD)
p3 = px.line(sm, color_discrete_sequence=px.colors.sequential.Plasma_r, labels={"value": "Passengers", "month": ""})
p3.update_layout(legend_title="Year")
p4 = px.imshow(sm.T, color_continuous_scale="Magma", aspect="auto", labels=dict(color="Pax")); p4.update_yaxes(type="category")
yy = a.dropna(subset=["yoy"])
p5 = px.bar(yy, x="Month", y="yoy", color="yoy", color_continuous_scale="RdYlGn", labels={"yoy": "YoY growth %"})
p5.update_coloraxes(showscale=False)
sa = a.groupby("month").Passengers.mean().reindex(MORD)
p6 = go.Figure(go.Scatterpolar(r=list(sa.values) + [sa.values[0]], theta=MORD + [MORD[0]], fill="toself", line_color="#b05cff"))
p6.update_layout(polar=dict(bgcolor="rgba(0,0,0,0)", radialaxis=dict(gridcolor="#25305a"), angularaxis=dict(gridcolor="#25305a")))
p7 = px.area(a, x="Month", y="Passengers", color="month", color_discrete_sequence=px.colors.qualitative.Vivid)

tabs = {
 "Temperature Trends": [("Daily min temperature - rolling mean & anomalies", style(l1, 440), 12),
                        ("Average by month", style(r2, 380, False), 4), ("Yearly mean + trend line", style(r5, 380), 4),
                        ("Seasonal spread", style(r6, 380, False), 4),
                        ("Year x month heat-map", style(r3, 420, False), 12)],
 "Seasonality": [("Distribution by month", style(r4, 420, False), 12),
                 ("Temperature distribution by season", style(r7, 380), 6), ("Day-of-year calendar", style(r8, 380, False), 6),
                 ("30-day volatility", style(r9, 360, False), 6), ("Autocorrelation (persistence)", style(r10, 360, False), 6),
                 ("Today vs yesterday", style(r11, 400), 12)],
 "Airline Passengers": [("Monthly passengers & trend", style(p1, 400), 12),
                        ("Yearly total", style(p2, 360, False), 4), ("Seasonal profile (radar)", style(p6, 360, False), 4),
                        ("Year-over-year growth", style(p5, 360, False), 4),
                        ("Seasonal curves by year", style(p3, 420), 6), ("Year x month heat-map", style(p4, 420, False), 6),
                        ("Stacked area by month", style(p7, 380, False), 12)],
}
build("Temporal Analytics Dashboard",
      "Melbourne daily minimum temperature (1981-1990) and monthly airline passengers (1949-1960)",
      kpis, tabs, os.path.join(BASE, "Dashboard", "temporal_dashboard.html"),
      footer="Python - pandas - Plotly  |  Temporal visualization project")
