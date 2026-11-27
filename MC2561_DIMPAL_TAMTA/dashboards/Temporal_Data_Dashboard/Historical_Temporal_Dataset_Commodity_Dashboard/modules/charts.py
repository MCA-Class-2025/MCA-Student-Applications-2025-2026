"""All Plotly figures for the main dashboard. Each function returns a go.Figure."""
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from .data import METRICS, agg, pick_interval, period_labels

NOTE = dict(x=0.5, y=0.5, xref="paper", yref="paper", showarrow=False)


def color_map(names, theme, all_names=None):
    pal = theme["palette"]
    base = list(names) if names else list(all_names or [])
    return {n: pal[i % len(pal)] for i, n in enumerate(base)}


def _col(n, cmap, t, i):
    """Colour for a commodity: its selection colour if it has one, else the next free palette colour."""
    return cmap[n] if n in cmap else t["palette"][(len(cmap) + i) % len(t["palette"])]


def _layout(fig, t, h, legend=False, **kw):
    fam = f"{t['font']}, system-ui, sans-serif"
    fig.update_layout(
        height=h, margin=dict(l=8, r=10, t=6, b=6), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=t["text"], size=12, family=fam), showlegend=legend,
        hoverlabel=dict(bgcolor=t["card"], font_color=t["text"], bordercolor=t["border"], font_size=12),
        legend=dict(orientation="h", y=1.02, x=0, yanchor="bottom", font=dict(size=12, color=t["text"], family=fam),
                    bgcolor="rgba(0,0,0,0)"), **kw)
    fig.update_xaxes(showgrid=False, linecolor=t["border"], tickfont=dict(color=t["text"], size=11), zeroline=False, automargin=True)
    fig.update_yaxes(gridcolor=t["grid"], zeroline=False, tickfont=dict(color=t["text"], size=11), automargin=True)
    return fig


def axes(fig, t, x=None, y=None):
    """Bold, readable axis titles (with units)."""
    if x:
        fig.update_xaxes(title_text=f"<b>{x}</b>", title_font=dict(size=12, color=t["text"]), title_standoff=6)
    if y:
        fig.update_yaxes(title_text=f"<b>{y}</b>", title_font=dict(size=12, color=t["text"]), title_standoff=6)
    return fig


def key_items(fig, items):
    """Legend-only entries (square swatches) that explain what the colours mean."""
    for name, color in items:
        fig.add_trace(go.Scatter(x=[None], y=[None], mode="markers", name=name, marker=dict(symbol="square", size=12, color=color)))
    return fig


def _ink(hex_):
    h = hex_.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    return "#0B1220" if (0.299 * r + 0.587 * g + 0.114 * b) > 150 else "#FFFFFF"


def _rgba(hex_, a):
    h = hex_.lstrip("#")
    return f"rgba({int(h[0:2], 16)},{int(h[2:4], 16)},{int(h[4:6], 16)},{a})"


def _indexed(d, names, interval, col):
    """Each commodity rebased to 100 at its first value in the range (columns = commodities)."""
    out = {}
    for n in names:
        a = agg(d[d["name"] == n], interval)[col].dropna()
        if len(a) >= 2 and a.iloc[0] > 0:
            out[n] = a / a.iloc[0] * 100
    return pd.DataFrame(out)


def _delta(v):
    f = f"{v:+,.0f}" if abs(v) >= 100 else f"{v:+,.1f}"
    return f.replace("-", "\u2212")


def empty_fig(t, h, msg="Select a commodity to see this chart"):
    fig = go.Figure()
    fig.add_annotation(text=msg, font=dict(size=13, color=t["muted"]), **NOTE)
    fig.update_xaxes(visible=False)
    fig.update_yaxes(visible=False)
    return _layout(fig, t, h)


def _hover(a):
    return [f"O {o:,.2f} · H {hi:,.2f} · L {lo:,.2f} · C {c:,.2f}<br>Volume {('n/a' if pd.isna(v) else f'{v:,.0f}')}"
            for o, hi, lo, c, v in zip(a.open, a.high, a.low, a.close, a.volume)]


# 1 ─ Historical price trend ------------------------------------------------------------
def line_fig(d, sel, interval, metric, t, cmap, h):
    col = METRICS[metric]
    if not sel:  # nothing selected: all commodities indexed to 100 + bold equal-weighted Market Index
        names = sorted(d["name"].unique())
        X = _indexed(d, names, interval, col)
        if X.empty:
            return empty_fig(t, h, "No data in this range")
        fig = go.Figure()
        for i, n in enumerate(X.columns):
            fig.add_trace(go.Scatter(x=X.index, y=X[n], name=n, mode="lines", opacity=0.8,
                                     line=dict(color=t["palette"][i % len(t["palette"])], width=1.4),
                                     hovertemplate="<b>" + n + "</b> · %{x|%d %b %Y}<br>Index %{y:,.1f}<extra></extra>"))
        mi = X.mean(axis=1)
        fig.add_trace(go.Scatter(x=mi.index, y=mi, name="Market Index (average of all)", mode="lines",
                                 line=dict(color=t["text"], width=4),
                                 hovertemplate="<b>Market Index</b> · %{x|%d %b %Y}<br>%{y:,.1f}<extra></extra>"))
        fig = _layout(fig, t, h, legend=True, hovermode="closest", legend_orientation="v", legend_x=1.01, legend_y=1,
                      legend_xanchor="left", legend_yanchor="top")
        fig.update_yaxes(type="log")
        return axes(fig, t, "Date", "Index (each = 100 at start, log scale)")
    multi = len(sel) > 1
    fig = go.Figure()
    for n in sel:
        a = agg(d[d["name"] == n], interval)
        if a.empty:
            continue
        y = a[col] / a[col].dropna().iloc[0] * 100 if multi else a[col]
        dots = len(a) <= 400
        fig.add_trace(go.Scatter(
            x=a.index, y=y, name=n, mode="lines+markers" if dots else "lines", line=dict(color=cmap[n], width=2.6),
            marker=dict(size=5, color=cmap[n], line=dict(width=1, color=t["card"])),
            text=_hover(a), customdata=a[col],
            hovertemplate="<b>" + n + "</b> · %{x|%d %b %Y}<br>" + metric + " %{customdata:,.2f}"
                          + (" (index %{y:,.1f})" if multi else "") + "<br>%{text}<extra></extra>"))
        if not multi:  # mark the peak, the low and the latest point
            ys = a[col].dropna()
            pts = [("Peak", ys.idxmax(), "top center"), ("Low", ys.idxmin(), "bottom center"), ("Latest", ys.index[-1], "middle left")]
            fig.add_trace(go.Scatter(
                x=[p[1] for p in pts], y=[ys[p[1]] for p in pts], mode="markers+text", showlegend=False,
                text=[f"<b>{p[0]} {ys[p[1]]:,.1f}</b>" for p in pts], textposition=[p[2] for p in pts],
                textfont=dict(size=11, color=t["text"]), cliponaxis=False,
                marker=dict(size=11, symbol="diamond", color=[t["up"], t["down"], t["palette"][1]], line=dict(width=1.5, color=t["card"])),
                hoverinfo="skip"))
    fig = _layout(fig, t, h, legend=multi, hovermode="closest")
    return axes(fig, t, "Date", "Index (each = 100 at start of range)" if multi else f"{metric} price (as reported)")


# 2 ─ Composition (share of records) ----------------------------------------------------
def donut_fig(d, sel, t, cmap, h):
    counts = d.groupby("name").size().sort_values(ascending=False)
    if counts.empty:
        return empty_fig(t, h, "No records in this range")
    if sel:
        keep = counts[counts.index.isin(sel)]
        labels, vals = list(keep.index), list(keep.values)
        rest = counts.drop(keep.index).sum()
    else:
        labels, vals = list(counts.index[:8]), list(counts.values[:8])
        rest = counts.iloc[8:].sum()
    if rest > 0:
        labels.append("Others"); vals.append(rest)
    colors = [t["other"] if n == "Others" else _col(n, cmap, t, i) for i, n in enumerate(labels)]
    fig = go.Figure(go.Pie(labels=labels, values=vals, hole=0.62, sort=False, marker=dict(colors=colors, line=dict(color=t["card"], width=2)),
                           textinfo="percent", textfont=dict(size=12, color="#FFFFFF"),
                           hovertemplate="<b>%{label}</b><br>%{value:,} records · %{percent}<extra></extra>"))
    fig.add_annotation(text=f"<b>{int(sum(vals)):,}</b><br><span style='font-size:10px;color:{t['muted']}'>records</span>",
                       showarrow=False, font=dict(size=16, color=t["text"]), x=0.5, y=0.5, xref="paper", yref="paper")
    return _layout(fig, t, h, legend=True, legend_orientation="v", legend_x=1.0, legend_y=0.5,
                   legend_xanchor="right", legend_yanchor="middle")


# 3 ─ Ribbon chart (Power BI style: stacked columns + ribbons, ordered by value) --------
def ribbon_fig(d, sel, interval, metric, t, cmap, h, max_periods=6):
    col = METRICS[metric]
    if d.empty:
        return empty_fig(t, h, "No data in this range")
    iv = pick_interval(d["date"].min(), d["date"].max(), interval, max_periods + 1)
    series = {}
    for n, g in d.groupby("name"):
        a = agg(g, iv)[col].dropna()
        if len(a) >= 3 and a.iloc[0] > 0:
            series[n] = a / a.iloc[0] * 100          # price index, start of range = 100
    if len(sel) >= 2:
        names = [n for n in sel if n in series][:8]
    else:
        tot = pd.Series({n: s.iloc[-1] for n, s in series.items()}).sort_values(ascending=False)
        names = list(tot.index[:6])
        if sel and sel[0] in series and sel[0] not in names:
            names = names[:5] + [sel[0]]
    if len(names) < 2:
        return empty_fig(t, h, "Need at least 2 commodities with data in range")
    V = pd.DataFrame({n: series[n] for n in names}).dropna(how="all").tail(max_periods)
    if len(V) < 2:
        return empty_fig(t, h, "Range too short for a ribbon chart")
    labels = period_labels(V.index, iv)
    m, w = len(V), 0.3
    lo, hi = {n: [np.nan] * m for n in names}, {n: [np.nan] * m for n in names}
    for j in range(m):                                # stack: biggest value on top
        run = 0.0
        for n in V.iloc[j].dropna().sort_values().index:
            lo[n][j], hi[n][j] = run, run + V.iloc[j][n]
            run += V.iloc[j][n]
    ymax = max(np.nanmax(list(hi[n])) for n in names)
    fig = go.Figure()
    u = np.linspace(0, 1, 18)
    sm = u * u * (3 - 2 * u)
    final = V.ffill().iloc[-1]
    for i, n in enumerate(sorted(names, key=lambda k: -final[k])):
        c = _col(n, cmap, t, names.index(n))
        dim = len(sel) == 1 and n != sel[0]
        rx, ry = [], []
        for j in range(m - 1):
            if np.isnan(hi[n][j]) or np.isnan(hi[n][j + 1]):
                continue
            cx = (j + w) + u * (1 - 2 * w)
            top = hi[n][j] + (hi[n][j + 1] - hi[n][j]) * sm
            bot = lo[n][j] + (lo[n][j + 1] - lo[n][j]) * sm
            rx += list(cx) + list(cx[::-1]) + [cx[0], None]
            ry += list(top) + list(bot[::-1]) + [top[0], None]
        fig.add_trace(go.Scatter(x=rx, y=ry, mode="lines", fill="toself", hoverinfo="skip", showlegend=False,
                                 line=dict(width=0), fillcolor=_rgba(c, 0.18 if dim else 0.32), legendgroup=n))
        cx_, cy_ = [], []
        for j in range(m):
            if np.isnan(hi[n][j]):
                continue
            cx_ += [j - w, j + w, j + w, j - w, j - w, None]
            cy_ += [lo[n][j], lo[n][j], hi[n][j], hi[n][j], lo[n][j], None]
        fig.add_trace(go.Scatter(x=cx_, y=cy_, mode="lines", fill="toself", name=n, hoverinfo="skip", legendgroup=n,
                                 line=dict(color=t["card"], width=1), fillcolor=c, opacity=0.4 if dim else 1))
        xs = [j for j in range(m) if not np.isnan(hi[n][j])]
        mid = [(lo[n][j] + hi[n][j]) / 2 for j in xs]
        val = [V.iloc[j][n] for j in xs]
        txt = [f"<b>{v:,.0f}</b>" if (hi[n][j] - lo[n][j]) >= ymax * 0.055 else "" for j, v in zip(xs, val)]
        fig.add_trace(go.Scatter(x=xs, y=mid, mode="markers+text", showlegend=False, legendgroup=n, text=txt,
                                 textfont=dict(size=11, color=_ink(c)), marker=dict(size=22, opacity=0, color=c),
                                 customdata=np.c_[[labels[j] for j in xs], val],
                                 hovertemplate="<b>" + n + "</b><br>%{customdata[0]}<br>Price index %{customdata[1]:,.1f}<extra></extra>"))
    fig = _layout(fig, t, h, legend=True, hovermode="closest")
    fig.update_xaxes(tickmode="array", tickvals=list(range(m)), ticktext=labels, range=[-0.55, m - 0.45])
    return axes(fig, t, f"Period ({iv.lower()})", "Price index (start of range = 100)")


# 4 ─ Waterfall (period-to-period change as a running total) -----------------------------
def waterfall_fig(d, focus, interval, metric, t, h, max_steps=14):
    col = METRICS[metric]
    if d.empty or (focus and len(d[d["name"] == focus]) < 3):
        return empty_fig(t, h, "Not enough data in this range")
    one = d[d["name"] == focus] if focus else d
    iv = pick_interval(one["date"].min(), one["date"].max(), interval, max_steps + 1)
    if focus:
        s, ytitle = agg(one, iv)[col].dropna().tail(max_steps + 1), f"{focus} {metric.lower()} price"
    else:
        X = _indexed(d, sorted(d["name"].unique()), iv, col)
        if X.empty:
            return empty_fig(t, h, "Not enough data in this range")
        s, ytitle = X.mean(axis=1).tail(max_steps + 1), "Market Index (start = 100)"
    if len(s) < 2:
        return empty_fig(t, h, "Range too short for a waterfall")
    lab = period_labels(s.index, iv)
    steps = s.diff().iloc[1:]
    navy = t["primary"] if t["mode"] == "light" else t["accent"]
    txt = [f"<b>{s.iloc[0]:,.0f}</b>"] + [f"<b>{_delta(v)}</b>" for v in steps.values] + [f"<b>{s.iloc[-1]:,.0f}</b>"]
    fig = go.Figure(go.Waterfall(
        x=[f"Start<br>{lab[0]}"] + lab[1:] + [f"End<br>{lab[-1]}"], measure=["absolute"] + ["relative"] * len(steps) + ["total"],
        y=[s.iloc[0]] + list(steps.values) + [0], text=txt, textposition="outside", textfont=dict(size=11, color=t["text"]),
        connector=dict(line=dict(color=t["muted"], width=1, dash="dot")), cliponaxis=False,
        increasing=dict(marker=dict(color=t["up"])), decreasing=dict(marker=dict(color=t["down"])),
        totals=dict(marker=dict(color=navy)),
        hovertemplate="%{x}<br>Change %{y:+,.2f}<extra></extra>"))
    key_items(fig, [("Start / End level", navy), ("Rise", t["up"]), ("Fall", t["down"])])
    fig = _layout(fig, t, h, legend=True, waterfallgap=0.3)
    fig.update_xaxes(tickangle=-45 if len(lab) > 6 else 0, tickfont=dict(size=10, color=t["text"]))
    return axes(fig, t, f"Period ({iv.lower()})", ytitle)


# 5 ─ Trading activity (volume bars + moving-average line) ------------------------------
def volume_fig(d, focus, interval, t, h):
    if not focus:  # nothing selected: total volume of every commodity
        tot = d.groupby("name")["volume"].sum(min_count=1).dropna().sort_values()
        if tot.empty:
            return empty_fig(t, h, "No volume reported in this range")
        fig = go.Figure(go.Bar(x=tot.values, y=tot.index, orientation="h", marker_color=t["palette"][0],
                               hovertemplate="<b>%{y}</b><br>Total volume %{x:,.0f}<extra></extra>"))
        fig = _layout(fig, t, h)
        fig.update_xaxes(showgrid=True, gridcolor=t["grid"])
        return axes(fig, t, "Total volume (contracts, not comparable across commodities)")
    a = agg(d[d["name"] == focus], interval)
    if a["volume"].notna().sum() == 0:
        return empty_fig(t, h, "No volume reported for this commodity in this range")
    fig = go.Figure(go.Bar(x=a.index, y=a["volume"], marker_color=t["palette"][0], opacity=0.9, name="Volume",
                           hovertemplate="%{x|%d %b %Y}<br>Volume %{y:,.0f}<extra></extra>"))
    miss = int(a["volume"].isna().sum())
    fig = _layout(fig, t, h, legend=True, bargap=0.15)
    if miss:
        fig.add_annotation(text=f"{miss} period(s) with no reported volume", x=1, y=0.02, xref="paper", yref="paper",
                           xanchor="right", yanchor="bottom", showarrow=False, font=dict(size=10, color=t["muted"]))
    return axes(fig, t, "Date", f"{focus} volume ({interval.lower()} total)")


# 6 ─ Price & volume (combo) ------------------------------------------------------------
def combo_fig(d, focus, interval, metric, t, h):
    col = METRICS[metric]
    line_c = t["palette"][1]
    fig = go.Figure()
    if not focus:  # nothing selected: total volume bars + % change line per commodity
        tot = d.groupby("name")["volume"].sum(min_count=1).dropna().sort_values(ascending=False)
        if tot.empty:
            return empty_fig(t, h, "No volume reported in this range")
        chg = {}
        for n in tot.index:
            g = d[d["name"] == n].sort_values("date")["close"]
            if len(g) and g.iloc[0] > 0:
                chg[n] = (g.iloc[-1] / g.iloc[0] - 1) * 100
        fig.add_trace(go.Bar(x=tot.index, y=tot.values, name="Total volume", marker_color=_rgba(t["palette"][0], 0.8),
                             hovertemplate="<b>%{x}</b><br>Volume %{y:,.0f}<extra></extra>"))
        fig.add_trace(go.Scatter(x=list(chg), y=list(chg.values()), name="% change over range", yaxis="y2", mode="lines+markers",
                                 line=dict(color=line_c, width=2.6), marker=dict(size=7),
                                 hovertemplate="<b>%{x}</b><br>Change %{y:+.1f}%<extra></extra>"))
        fig = _layout(fig, t, h, legend=True, bargap=0.25,
                      yaxis2=dict(overlaying="y", side="right", showgrid=False, tickfont=dict(color=t["text"], size=11),
                                  title=dict(text="<b>% change over range</b>", font=dict(size=12, color=t["text"]))))
        fig.update_xaxes(tickangle=-40, tickfont=dict(size=10, color=t["text"]))
        return axes(fig, t, None, "Total volume (contracts)")
    a = agg(d[d["name"] == focus], interval)
    fig.add_trace(go.Bar(x=a.index, y=a["volume"], name="Volume", yaxis="y2", marker_color=_rgba(t["palette"][0], 0.6),
                         hovertemplate="%{x|%d %b %Y}<br>Volume %{y:,.0f}<extra></extra>"))
    fig.add_trace(go.Scatter(x=a.index, y=a[col], name=f"{metric} price", mode="lines", line=dict(color=line_c, width=2.6),
                             hovertemplate="%{x|%d %b %Y}<br>" + metric + " %{y:,.2f}<extra></extra>"))
    fig = _layout(fig, t, h, legend=True, bargap=0.1, hovermode="x unified",
                  yaxis2=dict(overlaying="y", side="right", showgrid=False, tickfont=dict(color=t["text"], size=11),
                              title=dict(text="<b>Volume (contracts)</b>", font=dict(size=12, color=t["text"]))))
    return axes(fig, t, "Date", f"{focus} {metric.lower()} price")


# 7 ─ Candlestick (open-close body, high-low wick) --------------------------------------
def candle_fig(a, focus, t, h):
    if not focus or a is None or a.empty:
        return empty_fig(t, h, "Pick a commodity for candles")
    fig = go.Figure(go.Candlestick(
        x=a.index, open=a["open"], high=a["high"], low=a["low"], close=a["close"], name=focus, showlegend=False,
        increasing=dict(line=dict(color=t["cu"], width=1), fillcolor=t["cu"]),
        decreasing=dict(line=dict(color=t["cd"], width=1), fillcolor=t["cd"]), whiskerwidth=0.3))
    key_items(fig, [("Up candle (close above open)", t["cu"]), ("Down candle (close below open)", t["cd"])])
    fig = _layout(fig, t, h, legend=True, hovermode="x")
    fig.update_xaxes(rangeslider_visible=False)
    fig.add_annotation(text="Body = open to close · thin line = high to low", x=1, y=0, xref="paper", yref="paper",
                       xanchor="right", yanchor="bottom", showarrow=False, font=dict(size=10, color=t["muted"]))
    return axes(fig, t, "Date", f"{focus} price (open / high / low / close)")
