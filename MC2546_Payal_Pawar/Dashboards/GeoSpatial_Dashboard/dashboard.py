"""Dynamic Geo-Spatial Dashboard  ->  python dashboard.py  (http://127.0.0.1:8050)"""
import os, numpy as np, pandas as pd, plotly.graph_objects as go, plotly.express as px
from dash import Dash, dcc, html, Input, Output
import data_prep

if not os.path.exists("data.xlsx"): data_prep.build().to_excel("data.xlsx", index=False, sheet_name="Fused")
DF = pd.read_excel("data.xlsx", parse_dates=["date"])
PAL = ["#0f766e", "#0ea5e9", "#f59e0b", "#ef4444", "#8b5cf6", "#10b981"]
METRICS = {"pm25": "PM2.5 (µg/m³)", "aqi": "AQI", "temp_c": "Temperature (°C)", "humidity": "Humidity (%)"}
CAT_ORDER = ["Good", "Satisfactory", "Moderate", "Poor", "Very Poor", "Severe"]
CAT_COL = dict(zip(CAT_ORDER, ["#22c55e", "#84cc16", "#facc15", "#f97316", "#ef4444", "#7f1d1d"]))
SCALE = "Turbo"; MAPSTYLE = "carto-positron"
LAY = dict(template="plotly_white", font=dict(family="Segoe UI", size=12), margin=dict(l=45, r=15, t=25, b=40), height=400, colorway=PAL)
CENTER = dict(lat=22.5, lon=80)

def empty(msg="No data for this selection"):
    f = go.Figure(); f.add_annotation(text=msg, showarrow=False, font=dict(size=16, color="#94a3b8"))
    return f.update_layout(**LAY, xaxis_visible=False, yaxis_visible=False)

def city_agg(df, m):
    g = df.groupby(["city", "state", "region", "lat", "lon"]).agg(v=(m, "mean"), pop=("population_m", "first"), veh=("vehicles_per_1000", "first"),
                                                                    green=("green_cover_pct", "first")).reset_index()
    g["v"] = g.v.round(1); return g

def build_figures(df, m, mode, sel_city):
    F, lab = {}, METRICS[m]; g = city_agg(df, m)
    # 1 main map
    if mode == "Density Heatmap":
        f = px.density_map(g, lat="lat", lon="lon", z="v", radius=45, zoom=3.6, center=CENTER, map_style=MAPSTYLE, color_continuous_scale=SCALE, hover_name="city")
    else:
        f = px.scatter_map(g, lat="lat", lon="lon", size="pop", size_max=34, color="v", color_continuous_scale=SCALE, hover_name="city", zoom=3.6, center=CENTER, map_style=MAPSTYLE,
                           hover_data={"state": True, "v": ":.1f", "pop": ":.1f", "lat": False, "lon": False}, labels={"v": lab, "pop": "Pop (M)"})
    F["map"] = f.update_layout(**{**LAY, "height": 520, "margin": dict(l=0, r=0, t=0, b=0)}, coloraxis_colorbar=dict(title=lab, len=.6))
    # 2 ranking
    r = pd.concat([g.nlargest(8, "v"), g.nsmallest(8, "v")]).drop_duplicates("city").sort_values("v")
    F["ranking"] = px.bar(r, x="v", y="city", orientation="h", color="v", color_continuous_scale=SCALE, labels={"v": lab, "city": ""}).update_layout(**{**LAY, "height": 520}, coloraxis_showscale=False)
    # 3 region trend
    t = df.groupby(["date", "region"])[m].mean().reset_index()
    F["trend"] = px.line(t, x="date", y=m, color="region", markers=True, labels={m: lab, "date": ""}, color_discrete_sequence=PAL).update_layout(**LAY, legend=dict(orientation="h", y=-.2))
    # 4 sunburst
    sb = px.sunburst(g, path=["region", "state", "city"], values="pop", color="v", color_continuous_scale=SCALE, labels={"v": lab})
    F["sunburst"] = sb.update_layout(**{**LAY, "margin": dict(l=5, r=5, t=5, b=5)})
    # 5 drivers scatter
    xs = g.veh.values; ys = g.v.values; ln = np.linspace(xs.min(), xs.max(), 20)
    f = px.scatter(g, x="veh", y="v", size="pop", color="region", hover_name="city", labels={"veh": "Vehicles per 1000 people", "v": lab}, color_discrete_sequence=PAL)
    if len(g) > 2:
        c = np.polyfit(xs, ys, 1); f.add_trace(go.Scatter(x=ln, y=np.polyval(c, ln), mode="lines", name="Trend", line=dict(color="#334155", dash="dash")))
    F["drivers"] = f.update_layout(**LAY, legend=dict(orientation="h", y=-.25))
    F["_corr"] = np.corrcoef(xs, ys)[0, 1] if len(g) > 2 else np.nan
    # 6 box by region
    F["box"] = px.box(df, x="region", y=m, color="region", points="outliers", labels={m: lab, "region": ""}, color_discrete_sequence=PAL).update_layout(**LAY, showlegend=False)
    # 7 animation (spatio-temporal)
    a = df.assign(month=df.date.dt.strftime("%Y-%m")).sort_values("date")
    f = px.scatter_map(a, lat="lat", lon="lon", size="population_m", size_max=26, color=m, animation_frame="month", range_color=[a[m].min(), a[m].max()], color_continuous_scale=SCALE,
                       hover_name="city", zoom=3.4, center=CENTER, map_style=MAPSTYLE, labels={m: lab})
    F["anim"] = f.update_layout(**{**LAY, "height": 520, "margin": dict(l=0, r=0, t=0, b=0)})
    # 8 city drill-down
    c = DF_ALL[DF_ALL.city == sel_city].sort_values("date"); nat = DF_ALL.groupby("date")[m].mean()
    f = go.Figure()
    f.add_trace(go.Scatter(x=nat.index, y=nat, name="India average", line=dict(color="#94a3b8", dash="dot")))
    f.add_trace(go.Scatter(x=c.date, y=c[m], name=sel_city, line=dict(color=PAL[3], width=3), fill="tozeroy", fillcolor="rgba(239,68,68,.1)"))
    F["city"] = f.update_layout(**LAY, yaxis_title=lab, hovermode="x unified", legend=dict(orientation="h", y=-.2))
    # 9 AQI category share by region
    s = df.groupby(["region", "aqi_category"]).size().reset_index(name="n"); s["p"] = s.n / s.groupby("region").n.transform("sum") * 100
    F["cats"] = px.bar(s, x="region", y="p", color="aqi_category", category_orders={"aqi_category": CAT_ORDER}, color_discrete_map=CAT_COL, labels={"p": "% of city-months", "region": "", "aqi_category": "AQI"}).update_layout(**LAY)
    return F

DF_ALL = DF
def card(title, gid, tip_id, **kw): return html.Div(className="card", children=[html.H3(title), dcc.Graph(id=gid, config={"displaylogo": False}), html.Div(id=tip_id, className="tip")], **kw)
def flt(lbl, comp): return html.Div([html.Label(lbl), comp], className="f")
REG, STA = sorted(DF.region.unique()), sorted(DF.state.unique()); D0, D1 = DF.date.min().date(), DF.date.max().date()

app = Dash(__name__, title="Geo-Spatial Dashboard"); server = app.server
app.layout = html.Div([
    html.Div(className="hdr", children=[html.H1("🗺️ BreatheIndia · Geo-Spatial Dashboard"),
        html.P("Interactive spatial analysis of urban air quality across 36 Indian cities (monthly, 2024–2026) – click any city on the map to drill down")]),
    html.Div(className="filters", children=[
        flt("DATE RANGE", dcc.DatePickerRange(id="dr", min_date_allowed=D0, max_date_allowed=D1, start_date=D0, end_date=D1, display_format="MMM YYYY")),
        flt("REGION", dcc.Dropdown(REG, multi=True, placeholder="All regions", id="reg")),
        flt("STATE", dcc.Dropdown(STA, multi=True, placeholder="All states", id="sta")),
        flt("AQI CATEGORY", dcc.Dropdown(CAT_ORDER, multi=True, placeholder="All categories", id="cat")),
        flt("METRIC", dcc.Dropdown([{"label": v, "value": k} for k, v in METRICS.items()], "pm25", clearable=False, id="metric")),
        flt("MAP MODE", dcc.RadioItems(["Bubble Map", "Density Heatmap"], "Bubble Map", inline=True, inputStyle={"marginLeft": "10px", "marginRight": "4px"}, id="mode")),
        html.Button("Reset", id="reset", className="btn")]),
    dcc.Store(id="city", data="Delhi"),
    html.Div(className="wrap", children=[
        html.Div(id="kpis", className="kpis"),
        html.H2("Spatial Overview", className="sec"), html.P("Where are the hotspots, and which cities rank highest and lowest?", className="sub"),
        html.Div(className="row r21", children=[card("1 · Interactive Map (click a city)", "g1", "t1"), card("2 · City Ranking (Top & Bottom 8)", "g2", "t2")]),
        html.H2("Regional Patterns", className="sec"), html.P("How do regions compare, and how is the hierarchy structured?", className="sub"),
        html.Div(className="row r3", children=[card("3 · Regional Trend", "g3", "t3"), card("4 · Region → State → City (Sunburst)", "g4", "t4"), card("5 · Regional Distribution (Box)", "g6", "t6")]),
        html.H2("Drivers & Categories", className="sec"), html.P("What explains the differences, and how severe is the exposure?", className="sub"),
        html.Div(className="row r2", children=[card("6 · Vehicles vs Metric (bubble = population)", "g5", "t5"), card("7 · AQI Category Share by Region", "g9", "t9")]),
        html.H2("Space × Time", className="sec"), html.P("Watch the pollution wave move across the country, then drill into one city.", className="sub"),
        html.Div(className="row r21", children=[card("8 · Animated Map (press ▶ Play)", "g7", "t7"), card("9 · City Profile", "g8", "t8")])])])

@app.callback(Output("city", "data"), Input("g1", "clickData"), prevent_initial_call=True)
def pick(cd):
    try: return cd["points"][0]["hovertext"]
    except Exception: return "Delhi"

@app.callback([Output(k, "value") for k in ("reg", "sta", "cat", "metric", "mode")] + [Output("dr", "start_date"), Output("dr", "end_date")], Input("reset", "n_clicks"), prevent_initial_call=True)
def reset(_): return None, None, None, "pm25", "Bubble Map", D0, D1

OUT = [Output("kpis", "children")] + [Output(f"g{i}", "figure") for i in range(1, 10)] + [Output(f"t{i}", "children") for i in range(1, 10)]
@app.callback(OUT, Input("dr", "start_date"), Input("dr", "end_date"), Input("reg", "value"), Input("sta", "value"), Input("cat", "value"), Input("metric", "value"), Input("mode", "value"), Input("city", "data"))
def update(d0, d1, rg, st, ct, m, mode, city):
    df = DF[(DF.date >= d0) & (DF.date <= d1) & DF.region.isin(rg or REG) & DF.state.isin(st or STA) & DF.aqi_category.isin(ct or CAT_ORDER)]
    if df.empty: return [[]] + [empty()] * 9 + [""] * 9
    F = build_figures(df, m, mode, city if city in set(DF.city) else "Delhi"); corr = F.pop("_corr")
    g = city_agg(df, m); hi, lo = g.loc[g.v.idxmax()], g.loc[g.v.idxmin()]
    bad = (df.groupby("city").aqi.mean() > 200).mean() * 100
    k = lambda v, l, c, s="": html.Div([html.Span(l), html.B(v), html.Small(s, style={"color": "#64748b"})], className="kpi", style={"--c": c})
    kp = [k(str(g.city.nunique()), "CITIES SHOWN", PAL[0], f"{g.state.nunique()} states"), k(f"{g.v.mean():.1f}", "AVG " + METRICS[m].split(" (")[0].upper(), PAL[1]),
          k(hi.city, "HIGHEST CITY", PAL[3], f"{hi.v:.1f}"), k(lo.city, "LOWEST CITY", PAL[5], f"{lo.v:.1f}"),
          k(f"{g['pop'].sum():.0f} M", "POPULATION COVERED", PAL[4]), k(f"{bad:.0f}%", "CITIES WITH POOR+ AQI", PAL[2], "avg AQI > 200")]
    reg_hi = df.groupby("region")[m].mean().idxmax()
    tips = ["💡 Bigger bubbles = larger population; colour shows the selected metric. Click a city for its profile.",
            f"💡 {hi.city} leads at {hi.v:.1f}, while {lo.city} is lowest at {lo.v:.1f}.",
            f"💡 {reg_hi} region has the highest average; winter peaks are visible in the north/east.",
            "💡 Ring size = population; click a region or state to zoom into it.",
            f"💡 Correlation between vehicle density and metric: r = {corr:.2f}." if corr == corr else "💡 Need 3+ cities for a trend line.",
            "💡 Boxes show spread across months and cities; dots are outlier months.",
            "💡 Use the slider under the map to scrub months – the wave follows the seasons.",
            f"💡 Showing {city}: grey dotted line is the national average.",
            "💡 Share of city-months in each AQI band – darker = more hazardous."]
    # order of outputs: g1..g9 -> map, ranking, trend, sunburst, drivers, box, anim, city, cats
    order = ["map", "ranking", "trend", "sunburst", "drivers", "box", "anim", "city", "cats"]
    return [kp] + [F[o] for o in order] + tips

if __name__ == "__main__": app.run(debug=True)
