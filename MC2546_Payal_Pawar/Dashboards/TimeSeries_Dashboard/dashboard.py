"""Dynamic Time-Series Dashboard  ->  python dashboard.py  (http://127.0.0.1:8050)"""
import os, numpy as np, pandas as pd, plotly.graph_objects as go, plotly.express as px
from plotly.subplots import make_subplots
from dash import Dash, dcc, html, Input, Output, callback_context
import data_prep

if not os.path.exists("data.xlsx"): data_prep.build().to_excel("data.xlsx", index=False, sheet_name="Fused")
DF = pd.read_excel("data.xlsx", parse_dates=["date"])
PAL = ["#4f46e5", "#06b6d4", "#f59e0b", "#10b981", "#ef4444", "#8b5cf6"]
LAY = dict(template="plotly_white", font=dict(family="Segoe UI", size=12), margin=dict(l=50, r=20, t=30, b=40),
           legend=dict(orientation="h", y=-0.2), colorway=PAL, height=380)
FREQ = {"D": "Daily", "W": "Weekly", "M": "Monthly"}
inr = lambda v: f"₹{v/1e7:.2f} Cr" if v >= 1e7 else f"₹{v/1e5:.1f} L"

def empty(msg="No data for this selection"):
    f = go.Figure(); f.add_annotation(text=msg, showarrow=False, font=dict(size=16, color="#94a3b8"))
    return f.update_layout(**LAY, xaxis_visible=False, yaxis_visible=False)

def series(df, m, f="D"):
    s = df.groupby("date")[m].sum().sort_index()
    return s if f == "D" else s.resample({"W": "W-SUN", "M": "MS"}[f]).sum()

def decompose(s, period=7):
    trend = s.rolling(30, center=True, min_periods=10).mean()
    det = s - trend; seas = det.groupby(s.index.dayofweek).transform("mean")
    return trend, seas, s - trend - seas

def acf(s, n=35):
    x = s.values - s.values.mean(); d = (x * x).sum()
    return [(x[:-k] * x[k:]).sum() / d for k in range(1, n + 1)]

def build_figures(df, m, f, d0, d1):
    F, label = {}, m.replace("_", " ").title()
    s, daily = series(df, m, f), series(df, m, "D")
    # 1 trend + rolling + anomalies
    win = {"D": 14, "W": 4, "M": 3}[f]; roll = s.rolling(win, min_periods=1).mean()
    res = (s - roll); z = res / (res.std() or 1); an = s[z.abs() > 2.8]
    g = go.Figure()
    g.add_trace(go.Scatter(x=s.index, y=s, name=label, line=dict(color=PAL[1], width=1.5), fill="tozeroy", fillcolor="rgba(6,182,212,.12)"))
    g.add_trace(go.Scatter(x=roll.index, y=roll, name=f"{win}-pt rolling mean", line=dict(color=PAL[0], width=3)))
    g.add_trace(go.Scatter(x=an.index, y=an, mode="markers", name="Anomaly", marker=dict(color=PAL[4], size=10, symbol="diamond", line=dict(color="white", width=1))))
    g.update_layout(**LAY, hovermode="x unified", xaxis=dict(rangeslider=dict(visible=True, thickness=.06)), yaxis_title=label)
    F["trend"] = g
    # 2 YoY monthly
    mm = df.set_index("date")[m].resample("MS").sum().to_frame(); mm["y"], mm["mo"] = mm.index.year, mm.index.month
    g = px.line(mm, x="mo", y=m, color=mm.y.astype(str), markers=True, color_discrete_sequence=PAL)
    g.update_layout(**LAY, xaxis=dict(tickmode="array", tickvals=list(range(1, 13)), ticktext=list("JFMAMJJASOND")), yaxis_title=label, legend_title="Year"); F["yoy"] = g
    # 3 heatmap weekday x month
    h = df.assign(wd=df.date.dt.dayofweek, mo=df.date.dt.month).groupby(["date", "wd", "mo"])[m].sum().reset_index().groupby(["wd", "mo"])[m].mean().unstack()
    g = go.Figure(go.Heatmap(z=h.values, x=list("JFMAMJJASOND")[:h.shape[1]] if h.shape[1] == 12 else h.columns, y=["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"], colorscale="Viridis", colorbar=dict(title="avg/day")))
    F["heatmap"] = g.update_layout(**LAY)
    # 4 decomposition
    tr, se, re_ = decompose(daily)
    g = make_subplots(rows=3, cols=1, shared_xaxes=True, vertical_spacing=.04, subplot_titles=("Trend (30-day)", "Weekly seasonality", "Residual"))
    g.add_trace(go.Scatter(x=tr.index, y=tr, line=dict(color=PAL[0])), 1, 1)
    g.add_trace(go.Scatter(x=se.index, y=se, line=dict(color=PAL[2])), 2, 1)
    g.add_trace(go.Bar(x=re_.index, y=re_, marker_color=PAL[3]), 3, 1)
    F["decomp"] = g.update_layout(**{**LAY, "height": 460}, showlegend=False)
    # 5 category stacked area
    c = df.groupby(["date", "category"])[m].sum().reset_index().set_index("date").groupby("category")[m].resample("W-SUN" if f != "M" else "MS").sum().reset_index()
    F["area"] = px.area(c, x="date", y=m, color="category", color_discrete_sequence=PAL).update_layout(**LAY, yaxis_title=label)
    # 6 forecast
    hist = daily[-180:]; x = np.arange(len(hist)); co = np.polyfit(x, hist.values, 1)
    det = hist.values - np.polyval(co, x); sea = pd.Series(det, index=hist.index).groupby(hist.index.dayofweek).mean()
    resid = det - sea.reindex(hist.index.dayofweek).values; sd = resid.std()
    fd = pd.date_range(hist.index[-1] + pd.Timedelta(days=1), periods=60); fx = np.arange(len(hist), len(hist) + 60)
    fc = np.polyval(co, fx) + sea.reindex(fd.dayofweek).values
    g = go.Figure()
    g.add_trace(go.Scatter(x=fd, y=fc + 1.96 * sd, line=dict(width=0), showlegend=False, hoverinfo="skip"))
    g.add_trace(go.Scatter(x=fd, y=fc - 1.96 * sd, fill="tonexty", fillcolor="rgba(245,158,11,.2)", line=dict(width=0), name="95% band"))
    g.add_trace(go.Scatter(x=hist.index[-90:], y=hist[-90:], name="History", line=dict(color=PAL[0])))
    g.add_trace(go.Scatter(x=fd, y=fc, name="Forecast (60d)", line=dict(color=PAL[2], dash="dash", width=3)))
    F["forecast"] = g.update_layout(**LAY, hovermode="x unified", yaxis_title=label)
    # 7 ACF
    a = acf(daily); F["acf"] = go.Figure(go.Bar(x=list(range(1, 36)), y=a, marker_color=[PAL[4] if k % 7 == 0 else PAL[0] for k in range(1, 36)])).update_layout(**LAY, xaxis_title="Lag (days)", yaxis_title="Autocorrelation")
    F["_meta"] = dict(n_an=len(an), fc_total=fc.sum(), peak_wd=daily.groupby(daily.index.dayofweek).mean().idxmax(), lag7=a[6])
    return F

def card(title, gid, tip_id): return html.Div(className="card", children=[html.H3(title), dcc.Graph(id=gid, config={"displaylogo": False}), html.Div(id=tip_id, className="tip")])
def flt(lbl, comp): return html.Div([html.Label(lbl), comp], className="f")
STORES, CATS = sorted(DF.store.unique()), sorted(DF.category.unique())
DEF = dict(dr=(DF.date.min().date(), DF.date.max().date()))

app = Dash(__name__, title="Time-Series Dashboard"); server = app.server
app.layout = html.Div([
    html.Div(className="hdr", children=[html.H1("📈 RetailPulse · Time-Series Dashboard"),
        html.P("Trend, seasonality, anomaly detection & forecasting on 3.8 years of daily multi-store retail sales")]),
    html.Div(className="filters", children=[
        flt("DATE RANGE", dcc.DatePickerRange(id="dr", min_date_allowed=DEF["dr"][0], max_date_allowed=DEF["dr"][1], start_date=DEF["dr"][0], end_date=DEF["dr"][1], display_format="DD MMM YYYY")),
        flt("STORE", dcc.Dropdown(STORES, multi=True, placeholder="All stores", id="store")),
        flt("CATEGORY", dcc.Dropdown(CATS, multi=True, placeholder="All categories", id="cat")),
        flt("METRIC", dcc.Dropdown([{"label": "Revenue", "value": "revenue"}, {"label": "Orders", "value": "orders"}], "revenue", clearable=False, id="metric")),
        flt("FREQUENCY", dcc.RadioItems([{"label": " " + v, "value": k} for k, v in FREQ.items()], "W", inline=True, inputStyle={"marginLeft": "10px"}, id="freq")),
        html.Button("Reset", id="reset", className="btn")]),
    html.Div(className="wrap", children=[
        html.Div(id="kpis", className="kpis"),
        html.H2("Overview", className="sec"), html.P("How is the business moving over time, and where are the unusual days?", className="sub"),
        html.Div(className="row r21", children=[card("1 · Trend, Rolling Mean & Anomalies", "g1", "t1"), card("2 · Year-over-Year Monthly Comparison", "g2", "t2")]),
        html.H2("Seasonality & Structure", className="sec"), html.P("Which patterns repeat weekly and yearly?", className="sub"),
        html.Div(className="row r2", children=[card("3 · Weekday × Month Heatmap", "g3", "t3"), card("4 · Time-Series Decomposition", "g4", "t4")]),
        html.H2("Composition & Outlook", className="sec"), html.P("What drives growth, how persistent is it, and what comes next?", className="sub"),
        html.Div(className="row r3", children=[card("5 · Category Mix (Stacked Area)", "g5", "t5"), card("6 · 60-Day Forecast", "g6", "t6"), card("7 · Autocorrelation (ACF)", "g7", "t7")])])])

@app.callback([Output(k, "value") for k in ("store", "cat", "metric")] + [Output("freq", "value"), Output("dr", "start_date"), Output("dr", "end_date")], Input("reset", "n_clicks"), prevent_initial_call=True)
def reset(_): return None, None, "revenue", "W", DEF["dr"][0], DEF["dr"][1]

@app.callback([Output("kpis", "children")] + [Output(f"g{i}", "figure") for i in range(1, 8)] + [Output(f"t{i}", "children") for i in range(1, 8)],
              Input("dr", "start_date"), Input("dr", "end_date"), Input("store", "value"), Input("cat", "value"), Input("metric", "value"), Input("freq", "value"))
def update(d0, d1, st, ct, m, f):
    full = DF[(DF.store.isin(st or STORES)) & (DF.category.isin(ct or CATS))]
    df = full[(full.date >= d0) & (full.date <= d1)]
    if df.date.nunique() < 40: return [[]] + [empty("Select at least 40 days of data")] * 7 + [""] * 7
    F = build_figures(df, m, f, d0, d1); F["yoy"] = build_figures(full, m, f, d0, d1)["yoy"]
    M = F.pop("_meta"); daily = series(df, m); tot = daily.sum(); n = len(daily)
    prev = series(full[(full.date < d0)], m)[-n:]; gr = (tot / prev.sum() - 1) * 100 if len(prev) == n and prev.sum() else None
    mon = daily.resample("MS").sum(); fmt = inr if m == "revenue" else (lambda v: f"{v:,.0f}")
    k = lambda v, l, c, sub="": html.Div([html.Span(l), html.B(v), html.Small(sub, style={"color": "#059669" if "▲" in sub else "#dc2626"})], className="kpi", style={"--c": c})
    kp = [k(fmt(tot), "TOTAL " + m.upper(), PAL[0]), k(fmt(daily.mean()), "AVG PER DAY", PAL[1]),
          k("n/a" if gr is None else f"{gr:+.1f}%", "VS PREVIOUS PERIOD", PAL[3], "" if gr is None else ("▲ growth" if gr >= 0 else "▼ decline")),
          k(daily.idxmax().strftime("%d %b %Y"), "PEAK DAY", PAL[2], fmt(daily.max())), k(str(M["n_an"]), "ANOMALIES FLAGGED", PAL[4]),
          k(mon.idxmax().strftime("%b %Y"), "BEST MONTH", PAL[5], fmt(mon.max()))]
    days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    tips = [f"💡 {M['n_an']} points deviate >2.8σ from the rolling mean (red diamonds) – promo spikes or outages.",
            "💡 Lines of different years stacking upward show sustained growth; the Oct–Nov bump is the festive season.",
            f"💡 {days[M['peak_wd']]} is the strongest weekday – staff and stock accordingly.",
            "💡 Trend isolates growth, seasonality isolates the weekly cycle; residual spikes are anomalies.",
            "💡 Stacked weekly contribution of each category to total.",
            f"💡 Next 60 days ≈ {fmt(M['fc_total'])} (linear trend + weekday seasonality, 95% band).",
            f"💡 Lag‑7 autocorrelation = {M['lag7']:.2f}: strong weekly rhythm (red bars = multiples of 7)."]
    return [kp] + list(F.values()) + tips

if __name__ == "__main__": app.run(debug=True)
