"""Plotly figures for the detail pages (and the extra main-dashboard visuals)."""
import calendar
import numpy as np
import pandas as pd
import plotly.graph_objects as go

from .charts import _col, _layout, empty_fig
from .data import METRICS, agg, performance_table

DOW = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
MON = [calendar.month_abbr[m] for m in range(1, 13)]


def rgba(hex_, a):
    h = hex_.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    return f"rgba({r},{g},{b},{a})"


def _yt(fig, t, text, **kw):
    fig.update_yaxes(title_text=text, title_font=dict(size=10, color=t["muted"]), **kw)
    return fig


def _line_color(t):
    return t["accent"]


def _none(t, h, msg="No data in this range"):
    return empty_fig(t, h, msg)


# ════════════════════════ price trends ═══════════════════════════════════════════════════
def price_main(a, name, ctype, metric, t, h, ma=()):
    if a is None or a.empty:
        return _none(t, h)
    col = METRICS[metric]
    fig = go.Figure()
    if ctype == "Candlestick":
        fig.add_trace(go.Candlestick(x=a.index, open=a["open"], high=a["high"], low=a["low"], close=a["close"], name=name,
                                     increasing_line_color=t["up"], decreasing_line_color=t["down"]))
    elif ctype == "OHLC":
        fig.add_trace(go.Ohlc(x=a.index, open=a["open"], high=a["high"], low=a["low"], close=a["close"], name=name,
                              increasing_line_color=t["up"], decreasing_line_color=t["down"]))
    else:
        fig.add_trace(go.Scatter(x=a.index, y=a[col], name=f"{name} · {metric}", mode="lines",
                                 line=dict(color=_line_color(t), width=2),
                                 fill="tozeroy" if ctype == "Area" else None,
                                 fillcolor=rgba(t["accent"], 0.16) if ctype == "Area" else None,
                                 hovertemplate="%{x|%d %b %Y}<br>" + metric + " %{y:,.2f}<extra></extra>"))
    for i, w in enumerate(ma):
        fig.add_trace(go.Scatter(x=a.index, y=a["close"].rolling(w).mean(), name=f"MA {w}", mode="lines",
                                 line=dict(color=t["palette"][(i + 1) % len(t["palette"])], width=1.4, dash="dot")))
    fig = _layout(fig, t, h, legend=True, hovermode="x unified" if ctype in ("Line", "Area") else "x")
    fig.update_xaxes(rangeslider_visible=False)
    return _yt(fig, t, f"{name} · price")


def open_close(daily, t, h):
    if daily.empty:
        return _none(t, h)
    up, dn = daily[daily["close"] >= daily["open"]], daily[daily["close"] < daily["open"]]
    fig = go.Figure()
    for x, nm, c in ((up, "Close ≥ Open", t["up"]), (dn, "Close < Open", t["down"])):
        fig.add_trace(go.Scattergl(x=x["open"], y=x["close"], mode="markers", name=nm,
                                   marker=dict(size=4, color=c, opacity=0.45),
                                   hovertemplate="Open %{x:,.2f}<br>Close %{y:,.2f}<extra>" + nm + "</extra>"))
    lo, hi = float(min(daily["open"].min(), daily["close"].min())), float(max(daily["open"].max(), daily["close"].max()))
    fig.add_trace(go.Scatter(x=[lo, hi], y=[lo, hi], mode="lines", name="Open = Close",
                             line=dict(color=t["muted"], dash="dash", width=1)))
    fig = _layout(fig, t, h, legend=True)
    fig.update_xaxes(title_text="Open", title_font=dict(size=10, color=t["muted"]))
    return _yt(fig, t, "Close")


def avg_series(daily, metric, freq, t, h, bars=False):
    col = METRICS[metric]
    s = daily.set_index("date")[col].resample(freq).mean().dropna()
    if s.empty:
        return _none(t, h)
    x = [str(i.year) for i in s.index] if freq == "YE" else s.index
    if bars:
        fig = go.Figure(go.Bar(x=x, y=s.values, marker_color=t["accent"], hovertemplate="%{x}<br>Average %{y:,.2f}<extra></extra>"))
    else:
        fig = go.Figure(go.Scatter(x=x, y=s.values, mode="lines+markers", line=dict(color=t["accent"], width=2),
                                   marker=dict(size=4), hovertemplate="%{x|%b %Y}<br>Average %{y:,.2f}<extra></extra>"))
    return _yt(_layout(fig, t, h, bargap=0.2), t, f"average {metric.lower()}")


def range_band(a, t, h):
    if a.empty:
        return _none(t, h)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=a.index, y=a["low"], name="Low", mode="lines", line=dict(color=t["down"], width=1)))
    fig.add_trace(go.Scatter(x=a.index, y=a["high"], name="High", mode="lines", line=dict(color=t["up"], width=1),
                             fill="tonexty", fillcolor=rgba(t["accent"], 0.15)))
    fig.add_trace(go.Scatter(x=a.index, y=a["close"], name="Close", mode="lines", line=dict(color=t["accent"], width=1.8)))
    return _yt(_layout(fig, t, h, legend=True, hovermode="x unified"), t, "price")


def ma_trend(full, start, end, t, h, windows=(20, 50, 200)):
    s = full.set_index("date")["close"]
    frame = pd.DataFrame({"Close": s, **{f"MA {w}": s.rolling(w).mean() for w in windows}}).loc[start:end]
    if frame.empty:
        return _none(t, h)
    fig = go.Figure()
    for i, c in enumerate(frame.columns):
        fig.add_trace(go.Scatter(x=frame.index, y=frame[c], name=c, mode="lines",
                                 line=dict(color=t["accent"] if i == 0 else t["palette"][i], width=1.6 if i == 0 else 1.3)))
    return _yt(_layout(fig, t, h, legend=True, hovermode="x unified"), t, "close · moving averages (trading days)")


# ════════════════════════ comparison ═════════════════════════════════════════════════════
def multi_price(dU, U, interval, metric, t, cmap, h, log=True):
    col, fig = METRICS[metric], go.Figure()
    for i, n in enumerate(U):
        a = agg(dU[dU["name"] == n], interval)
        if a.empty:
            continue
        fig.add_trace(go.Scatter(x=a.index, y=a[col], name=n, mode="lines", line=dict(color=_col(n, cmap, t, i), width=1.5),
                                 hovertemplate="<b>" + n + "</b> %{x|%d %b %Y}<br>" + metric + " %{y:,.2f}<extra></extra>"))
    fig = _layout(fig, t, h, legend=True, hovermode="closest")
    if log:
        fig.update_yaxes(type="log")
    return _yt(fig, t, f"{metric.lower()} ({'log scale' if log else 'linear'})")


def avg_bar(dU, U, metric, t, cmap, h):
    s = dU.groupby("name")[METRICS[metric]].mean().reindex(U).dropna().sort_values()
    if s.empty:
        return _none(t, h)
    fig = go.Figure(go.Bar(x=s.values, y=s.index, orientation="h",
                           marker_color=[_col(n, cmap, t, list(U).index(n)) for n in s.index],
                           hovertemplate="<b>%{y}</b><br>Average %{x:,.2f}<extra></extra>"))
    fig = _layout(fig, t, h)
    fig.update_xaxes(type="log", showgrid=True, gridcolor=t["grid"], title_text=f"average {metric.lower()} (log scale, own units)",
                     title_font=dict(size=10, color=t["muted"]))
    return fig


def highlow_bar(dU, U, t, h):
    g = dU.groupby("name").agg(hi=("high", "max"), lo=("low", "min")).reindex(U).dropna()
    g = g[g["lo"] > 0]
    if g.empty:
        return _none(t, h)
    fig = go.Figure()
    fig.add_trace(go.Bar(x=g.index, y=g["hi"], name="Highest high", marker_color=t["up"]))
    fig.add_trace(go.Bar(x=g.index, y=g["lo"], name="Lowest low", marker_color=t["down"]))
    fig = _layout(fig, t, h, legend=True, barmode="group", bargap=0.25)
    fig.update_yaxes(type="log")
    fig.update_xaxes(tickangle=-40, tickfont=dict(size=9))
    return _yt(fig, t, "price (log scale)")


def corr_heatmap(piv, t, h, title_note=""):
    """piv: DataFrame date x commodity (returns or prices)."""
    c = piv.corr(min_periods=30)
    c = c.dropna(how="all").dropna(axis=1, how="all")
    if c.shape[0] < 2:
        return _none(t, h, "Need ≥2 commodities with overlapping dates")
    big = c.shape[0] > 10
    fig = go.Figure(go.Heatmap(z=c.values, x=list(c.columns), y=list(c.index), zmin=-1, zmax=1,
                               colorscale=[[0, t["down"]], [0.5, t["card"]], [1, t["accent"]]],
                               text=np.round(c.values, 2), texttemplate=None if big else "%{text}", textfont=dict(size=10),
                               colorbar=dict(thickness=10, len=0.8, tickfont=dict(size=9, color=t["muted"])),
                               hovertemplate="%{y} × %{x}<br>correlation %{z:.2f}<extra></extra>"))
    fig = _layout(fig, t, h)
    fig.update_yaxes(autorange="reversed", showgrid=False, tickfont=dict(size=9))
    fig.update_xaxes(tickangle=-40, tickfont=dict(size=9))
    return fig


def rank_bar(dU, t, h):
    p = performance_table(dU).sort_values("change_pct")
    if p.empty:
        return _none(t, h)
    fig = go.Figure(go.Bar(x=p["change_pct"], y=p["name"], orientation="h",
                           marker_color=[t["up"] if v >= 0 else t["down"] for v in p["change_pct"]],
                           text=[f"{v:+.1f}%" for v in p["change_pct"]], textposition="outside", textfont=dict(size=9, color=t["muted"]),
                           hovertemplate="<b>%{y}</b><br>%{x:+.2f}% (first → last close in range)<extra></extra>"))
    fig = _layout(fig, t, h)
    fig.update_xaxes(showgrid=True, gridcolor=t["grid"], title_text="% change in close over range", title_font=dict(size=10, color=t["muted"]))
    return fig


def movers(dU, sel, t, h):
    """Main-dashboard extra: % change of every commodity over the range, selected ones highlighted."""
    p = performance_table(dU).sort_values("change_pct")
    if p.empty:
        return _none(t, h)
    cols = [t["accent"] if n in sel else (t["up"] if v >= 0 else t["down"]) for n, v in zip(p["name"], p["change_pct"])]
    op = [1.0 if (not sel or n in sel) else 0.45 for n in p["name"]]
    fig = go.Figure(go.Bar(x=p["change_pct"], y=p["name"], orientation="h", marker=dict(color=cols, opacity=op),
                           hovertemplate="<b>%{y}</b><br>%{x:+.2f}%<extra></extra>"))
    fig = _layout(fig, t, h)
    fig.update_xaxes(showgrid=True, gridcolor=t["grid"], title_text="<b>% change over range</b>", title_font=dict(size=12, color=t["text"]))
    fig.update_yaxes(tickfont=dict(size=11, color=t["text"]))
    return fig


# ════════════════════════ volume ═════════════════════════════════════════════════════════
def vol_daily(full, start, end, t, h, w=20):
    s = full.set_index("date")["volume"]
    f = pd.DataFrame({"v": s, "ma": s.rolling(w, min_periods=max(5, w // 2)).mean()}).loc[start:end]
    if f["v"].notna().sum() == 0:
        return _none(t, h, "No volume reported in this range")
    fig = go.Figure()
    fig.add_trace(go.Bar(x=f.index, y=f["v"], name="Daily volume", marker_color=rgba(t["accent"], 0.55),
                         hovertemplate="%{x|%d %b %Y}<br>%{y:,.0f}<extra></extra>"))
    fig.add_trace(go.Scatter(x=f.index, y=f["ma"], name=f"{w}-day average", mode="lines", line=dict(color=t["palette"][1], width=1.8)))
    return _yt(_layout(fig, t, h, legend=True, bargap=0), t, "volume (contracts)")


def vol_period(daily, freq, t, h):
    s = daily.set_index("date")["volume"].resample(freq).sum(min_count=1).dropna()
    if s.empty:
        return _none(t, h, "No volume reported in this range")
    x = [str(i.year) for i in s.index] if freq == "YE" else s.index
    fig = go.Figure(go.Bar(x=x, y=s.values, marker_color=t["accent"], hovertemplate="%{x}<br>%{y:,.0f}<extra></extra>"))
    return _yt(_layout(fig, t, h, bargap=0.15), t, "total volume")


def vol_compare(dU, U, t, cmap, h):
    s = dU.groupby("name")["volume"].mean().reindex(U).dropna().sort_values()
    if s.empty:
        return _none(t, h, "No volume reported")
    fig = go.Figure(go.Bar(x=s.values, y=s.index, orientation="h",
                           marker_color=[_col(n, cmap, t, list(U).index(n)) for n in s.index],
                           hovertemplate="<b>%{y}</b><br>avg daily volume %{x:,.0f}<extra></extra>"))
    fig = _layout(fig, t, h)
    fig.update_xaxes(type="log", showgrid=True, gridcolor=t["grid"], title_text="average daily volume (log) · contract-specific, not directly comparable",
                     title_font=dict(size=9, color=t["muted"]))
    return fig


def price_volume_scatter(daily, metric, t, h):
    x = daily.dropna(subset=["volume"])
    x = x[x["volume"] > 0]
    if x.empty:
        return _none(t, h, "No volume reported")
    fig = go.Figure(go.Scattergl(x=x["volume"], y=x[METRICS[metric]], mode="markers",
                                 marker=dict(size=4, color=x["year"], colorscale="Viridis", opacity=0.6, showscale=True,
                                             colorbar=dict(thickness=9, len=0.8, tickfont=dict(size=9, color=t["muted"]))),
                                 hovertemplate="Volume %{x:,.0f}<br>Price %{y:,.2f}<extra></extra>"))
    fig = _layout(fig, t, h)
    fig.update_xaxes(type="log", title_text="volume (log)", title_font=dict(size=10, color=t["muted"]))
    return _yt(fig, t, metric.lower())


def vol_rolling(full, start, end, t, h):
    s = full.set_index("date")["volume"]
    f = pd.DataFrame({"v": s, "m20": s.rolling(20, min_periods=10).mean(), "m60": s.rolling(60, min_periods=30).mean(),
                      "sd60": s.rolling(60, min_periods=30).std()})
    f["spike"] = f["v"] > f["m60"] + 3 * f["sd60"]
    f = f.loc[start:end]
    if f["v"].notna().sum() == 0:
        return _none(t, h, "No volume reported in this range")
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=f.index, y=f["m20"], name="20-day avg", mode="lines", line=dict(color=t["accent"], width=1.6)))
    fig.add_trace(go.Scatter(x=f.index, y=f["m60"], name="60-day avg", mode="lines", line=dict(color=t["palette"][1], width=1.6)))
    sp = f[f["spike"]]
    fig.add_trace(go.Scatter(x=sp.index, y=sp["v"], name="Unusually high (> 60-day mean + 3σ)", mode="markers",
                             marker=dict(color=t["down"], size=5), hovertemplate="%{x|%d %b %Y}<br>%{y:,.0f}<extra></extra>"))
    return _yt(_layout(fig, t, h, legend=True), t, "volume")


def top_volume(daily, n=10):
    x = daily.dropna(subset=["volume"]).nlargest(n, "volume")[["date", "name", "close", "volume", "ret"]]
    return x.rename(columns={"ret": "return_%"})


# ════════════════════════ volatility & risk ══════════════════════════════════════════════
def returns_line(d, names, t, cmap, h):
    fig = go.Figure()
    for i, n in enumerate(names):
        x = d[d["name"] == n].dropna(subset=["ret"])
        fig.add_trace(go.Scatter(x=x["date"], y=x["ret"], name=n, mode="lines", line=dict(color=_col(n, cmap, t, i), width=0.9),
                                 hovertemplate="<b>" + n + "</b> %{x|%d %b %Y}<br>%{y:+.2f}%<extra></extra>"))
    if not fig.data:
        return _none(t, h)
    return _yt(_layout(fig, t, h, legend=len(names) > 1), t, "daily return (%)")


def rolling_vol(df, names, start, end, window, annual, t, cmap, h):
    fig = go.Figure()
    for i, n in enumerate(names):
        s = df[df["name"] == n].set_index("date")["ret"].rolling(window, min_periods=window).std()
        if annual:
            s = s * np.sqrt(252)
        s = s.loc[start:end].dropna()
        if s.empty:
            continue
        fig.add_trace(go.Scatter(x=s.index, y=s.values, name=n, mode="lines", line=dict(color=_col(n, cmap, t, i), width=1.6),
                                 hovertemplate="<b>" + n + "</b> %{x|%d %b %Y}<br>%{y:.2f}%<extra></extra>"))
    if not fig.data:
        return _none(t, h, "Range too short for this window")
    return _yt(_layout(fig, t, h, legend=len(names) > 1), t, f"{window}-obs {'annualised ' if annual else ''}volatility (%)")


def hist_returns(daily, t, h, bins=60):
    r = daily["ret"].dropna()
    if len(r) < 30:
        return _none(t, h, "Not enough returns")
    lo, hi = r.quantile(0.005), r.quantile(0.995)
    rr = r[(r >= lo) & (r <= hi)]
    bw = (hi - lo) / bins
    xs = np.linspace(lo, hi, 200)
    mu, sd = r.mean(), r.std()
    pdf = np.exp(-0.5 * ((xs - mu) / sd) ** 2) / (sd * np.sqrt(2 * np.pi)) * len(rr) * bw
    fig = go.Figure()
    fig.add_trace(go.Histogram(x=rr, xbins=dict(start=lo, end=hi, size=bw), name="Daily returns", marker_color=t["accent"], opacity=0.8,
                               hovertemplate="%{x:.2f}%<br>%{y} days<extra></extra>"))
    fig.add_trace(go.Scatter(x=xs, y=pdf, name="Normal curve", mode="lines", line=dict(color=t["palette"][1], width=2)))
    fig.add_annotation(text=f"{len(r) - len(rr)} extreme obs (outside 0.5–99.5 pct) not drawn", x=1, y=1, xref="paper", yref="paper",
                       xanchor="right", yanchor="top", showarrow=False, font=dict(size=9, color=t["muted"]))
    fig = _layout(fig, t, h, legend=True, bargap=0.03)
    fig.update_xaxes(title_text="daily return (%)", title_font=dict(size=10, color=t["muted"]))
    return _yt(fig, t, "days")


def vol_bar(dU, U, annual, t, cmap, h):
    s = dU.groupby("name")["ret"].std().reindex(U).dropna().sort_values()
    if s.empty:
        return _none(t, h)
    if annual:
        s = s * np.sqrt(252)
    fig = go.Figure(go.Bar(x=s.values, y=s.index, orientation="h",
                           marker_color=[_col(n, cmap, t, list(U).index(n)) for n in s.index],
                           hovertemplate="<b>%{y}</b><br>%{x:.2f}%<extra></extra>"))
    fig = _layout(fig, t, h)
    fig.update_xaxes(showgrid=True, gridcolor=t["grid"], title_text=("annualised " if annual else "daily ") + "volatility (std of returns, %)",
                     title_font=dict(size=10, color=t["muted"]))
    return fig


def range_chart(daily, t, h):
    x = daily.dropna(subset=["range_pct"]).set_index("date")["range_pct"]
    if x.empty:
        return _none(t, h)
    fig = go.Figure()
    fig.add_trace(go.Scattergl(x=x.index, y=x.values, mode="lines", name="Daily (High−Low)/Open", line=dict(color=rgba(t["accent"], 0.4), width=0.8)))
    fig.add_trace(go.Scatter(x=x.index, y=x.rolling(20, min_periods=10).mean(), mode="lines", name="20-day average",
                             line=dict(color=t["palette"][1], width=1.8)))
    return _yt(_layout(fig, t, h, legend=True), t, "daily price range (% of open)")


def box_vol(dU, U, t, cmap, h):
    fig = go.Figure()
    for i, n in enumerate(U):
        r = dU.loc[dU["name"] == n, "ret"].dropna()
        if len(r) < 30:
            continue
        q1, md, q3 = r.quantile([.25, .5, .75])
        iqr = q3 - q1
        lf, uf = max(r.min(), q1 - 1.5 * iqr), min(r.max(), q3 + 1.5 * iqr)
        fig.add_trace(go.Box(name=n, q1=[q1], median=[md], q3=[q3], lowerfence=[lf], upperfence=[uf], mean=[r.mean()], sd=[r.std()],
                             marker_color=_col(n, cmap, t, i), line=dict(width=1.2), showlegend=False))
    if not fig.data:
        return _none(t, h)
    fig = _layout(fig, t, h)
    fig.update_xaxes(tickangle=-40, tickfont=dict(size=9))
    return _yt(fig, t, "daily return (%) · box = IQR, whiskers = 1.5×IQR")


def drawdown(daily, t, h):
    c = daily.sort_values("date").set_index("date")["close"].dropna()
    if c.empty:
        return _none(t, h)
    dd = (c / c.cummax() - 1) * 100
    fig = go.Figure(go.Scatter(x=dd.index, y=dd.values, mode="lines", fill="tozeroy", line=dict(color=t["down"], width=1.2),
                               fillcolor=rgba(t["down"], 0.2), hovertemplate="%{x|%d %b %Y}<br>%{y:.1f}% below prior peak<extra></extra>"))
    return _yt(_layout(fig, t, h), t, "drawdown from running peak (%)")


def risk_metrics(daily):
    r, c = daily["ret"].dropna(), daily["close"].dropna()
    if len(r) < 30:
        return None
    dd = (c / c.cummax() - 1) * 100
    return dict(vol_ann=r.std() * np.sqrt(252), var95=r.quantile(0.05), worst=r.min(), best=r.max(), maxdd=dd.min())


# ════════════════════════ seasonality ════════════════════════════════════════════════════
def season_month(daily, metric, t, h):
    s = daily.groupby("month")[METRICS[metric]].mean().reindex(range(1, 13))
    fig = go.Figure(go.Bar(x=MON, y=s.values, marker_color=t["accent"], hovertemplate="%{x}<br>average %{y:,.2f}<extra></extra>"))
    return _yt(_layout(fig, t, h, bargap=0.2), t, f"average {metric.lower()}")


def heat_year_month(full, start, end, mode, t, h):
    m = full.set_index("date")["close"].resample("ME").last().dropna()
    if mode.startswith("Monthly return"):
        v = m.pct_change() * 100
    else:
        v = full.set_index("date")["close"].resample("ME").mean().dropna()
    v = v.loc[start:end]
    if v.empty:
        return _none(t, h)
    tab = pd.DataFrame({"y": v.index.year, "m": v.index.month, "v": v.values}).pivot_table(index="y", columns="m", values="v").reindex(columns=range(1, 13))
    ret = mode.startswith("Monthly return")
    cs = [[0, t["down"]], [0.5, t["card"]], [1, t["up"]]] if ret else [[0, t["card"]], [1, t["accent"]]]
    kw = dict(zmid=0) if ret else {}
    fig = go.Figure(go.Heatmap(z=tab.values, x=MON, y=[str(i) for i in tab.index], colorscale=cs, **kw,
                               colorbar=dict(thickness=10, len=0.85, tickfont=dict(size=9, color=t["muted"])),
                               hovertemplate="%{y} %{x}<br>" + ("%{z:+.2f}%" if ret else "%{z:,.2f}") + "<extra></extra>"))
    fig = _layout(fig, t, h)
    fig.update_yaxes(autorange="reversed", showgrid=False, type="category", tickfont=dict(size=9))
    return fig


def quarter_avg(daily, metric, t, h):
    s = daily.groupby("quarter")[METRICS[metric]].mean().reindex([1, 2, 3, 4])
    fig = go.Figure(go.Bar(x=[f"Q{i}" for i in s.index], y=s.values, marker_color=t["accent"], hovertemplate="%{x}<br>average %{y:,.2f}<extra></extra>"))
    return _yt(_layout(fig, t, h, bargap=0.3), t, f"average {metric.lower()}")


def yearly_trend(daily, metric, t, h):
    g = daily.groupby("year")
    a, last = g[METRICS[metric]].mean(), g["close"].last()
    if a.empty:
        return _none(t, h)
    fig = go.Figure()
    fig.add_trace(go.Bar(x=[str(i) for i in a.index], y=a.values, name=f"Average {metric.lower()}", marker_color=rgba(t["accent"], 0.6)))
    fig.add_trace(go.Scatter(x=[str(i) for i in last.index], y=last.values, name="Year-end close", mode="lines+markers",
                             line=dict(color=t["palette"][1], width=2), marker=dict(size=5)))
    return _yt(_layout(fig, t, h, legend=True, bargap=0.2), t, "price")


def dow_returns(daily, t, h):
    g = daily.dropna(subset=["ret"]).groupby("dow")["ret"].agg(["mean", "count"]).reindex([d for d in DOW if d in set(daily["dow"])])
    if g.empty:
        return _none(t, h)
    fig = go.Figure(go.Bar(x=[d[:3] for d in g.index], y=g["mean"], customdata=g["count"],
                           marker_color=[t["up"] if v >= 0 else t["down"] for v in g["mean"]],
                           hovertemplate="%{x}<br>avg return %{y:+.3f}%<br>%{customdata:,} observations<extra></extra>"))
    return _yt(_layout(fig, t, h, bargap=0.3), t, "average daily return (%)")


def month_volume(daily, t, h):
    m = daily.set_index("date")["volume"].resample("ME").sum(min_count=1).dropna()
    if m.empty:
        return _none(t, h, "No volume reported")
    s = m.groupby(m.index.month).mean().reindex(range(1, 13))
    fig = go.Figure(go.Bar(x=MON, y=s.values, marker_color=t["accent"], hovertemplate="%{x}<br>avg monthly volume %{y:,.0f}<extra></extra>"))
    return _yt(_layout(fig, t, h, bargap=0.2), t, "average monthly total volume")


# ════════════════════════ statistics ═════════════════════════════════════════════════════
def box_price(dU, U, metric, t, cmap, h):
    col, fig = METRICS[metric], go.Figure()
    for i, n in enumerate(U):
        r = dU.loc[dU["name"] == n, col].dropna()
        if len(r) < 10:
            continue
        q1, md, q3 = r.quantile([.25, .5, .75])
        iqr = q3 - q1
        fig.add_trace(go.Box(name=n, q1=[q1], median=[md], q3=[q3], lowerfence=[max(r.min(), q1 - 1.5 * iqr)],
                             upperfence=[min(r.max(), q3 + 1.5 * iqr)], mean=[r.mean()], marker_color=_col(n, cmap, t, i), showlegend=False))
    if not fig.data:
        return _none(t, h)
    fig = _layout(fig, t, h)
    fig.update_yaxes(type="log")
    fig.update_xaxes(tickangle=-40, tickfont=dict(size=9))
    return _yt(fig, t, f"{metric.lower()} (log scale)")


def outlier_bar(out, t, h):
    if out.empty:
        return _none(t, h, "No outliers flagged")
    c = out.groupby("name").size().sort_values()
    fig = go.Figure(go.Bar(x=c.values, y=c.index, orientation="h", marker_color=t["palette"][1],
                           hovertemplate="<b>%{y}</b><br>%{x} flagged observations<extra></extra>"))
    fig = _layout(fig, t, h)
    fig.update_xaxes(showgrid=True, gridcolor=t["grid"], title_text="flagged daily returns (|z| > 4)", title_font=dict(size=10, color=t["muted"]))
    return fig
