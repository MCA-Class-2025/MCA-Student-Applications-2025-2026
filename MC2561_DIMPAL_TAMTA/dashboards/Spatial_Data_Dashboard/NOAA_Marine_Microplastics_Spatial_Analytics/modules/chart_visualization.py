"""Non-map charts (Plotly). Every function takes already-filtered data and returns a styled figure."""
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from scipy.stats import gaussian_kde
from config.theme_manager import get_theme, style_fig, color_map, CLASS_COLORS
from config.settings import CLASS_ORDER


def _pal():
    return get_theme()["palette"]


def donut(df, col, title=None, height=260):
    c = df[col].value_counts().rename_axis(col).reset_index(name="n")
    cm = color_map(c[col])
    f = go.Figure(go.Pie(labels=c[col], values=c["n"], hole=.5, sort=True, textinfo="percent",
                         textfont=dict(size=14), insidetextorientation="horizontal",
                         marker=dict(colors=[cm[k] for k in c[col]], line=dict(color=get_theme()["card"], width=2)),
                         hovertemplate="%{label}<br>%{value:,} records (%{percent})<extra></extra>"))
    f = style_fig(f, height=height, title=title, legend=True)
    f.update_layout(legend=dict(orientation="v", x=1.0, y=.5, font=dict(size=12)))
    return f


def bar(df, value, cat, title=None, horizontal=True, height=260, color=None, text=True, colorful=True):
    """Bar chart of `value` per `cat`; every bar gets its own colour (oceans keep their fixed colour)."""
    kw = dict(x=value, y=cat, orientation="h") if horizontal else dict(x=cat, y=value)
    col = color or (cat if colorful else None)
    f = px.bar(df, color=col, color_discrete_map=color_map(df[col].astype(str).unique()) if col else None,
               color_discrete_sequence=_pal(), **kw)
    if text:
        f.update_traces(texttemplate="%{x:,.3~s}" if horizontal else "%{y:,.3~s}", textposition="outside",
                        textfont=dict(size=13, color=get_theme()["text"]), cliponaxis=False)
    if horizontal:
        f.update_yaxes(autorange="reversed")
    f.update_traces(marker_line_width=0)
    f = style_fig(f, height=height, title=title, legend=False)
    f.update_layout(bargap=.25)
    return f


def treemap(df, path, title=None, height=420, color_col=None, top_children=None):
    """Clean treemap: no root tile, one colour per top-level group, small tiles merged into 'Other'."""
    d = df.groupby(path).size().reset_index(name="samples")
    if top_children:
        d["rk"] = d.groupby(path[0])["samples"].rank(method="first", ascending=False)
        d.loc[d.rk > top_children, path[-1]] = "Other"
        d = d.drop(columns="rk").groupby(path, as_index=False)["samples"].sum()
    d["grp"] = d[path[0]]
    f = px.treemap(d, path=path, values="samples", color="grp", color_discrete_map=color_map(d.grp.unique()))
    f.update_traces(textinfo="label+value", textfont=dict(size=15), marker=dict(cornerradius=5, line=dict(width=3, color=get_theme()["card"])),
                    pathbar=dict(visible=False), hovertemplate="<b>%{label}</b><br>%{value:,} records<extra></extra>")
    f.update_layout(uniformtext=dict(minsize=11, mode="hide"))
    return style_fig(f, height=height, title=title)


def hist(df, col, title=None, nbins=40, height=260, xlabel=None, color=None):
    f = px.histogram(df, x=col, nbins=nbins, color_discrete_sequence=[color or _pal()[1]])
    f.update_traces(marker_line_width=0)
    f.update_layout(bargap=.05)
    f.update_xaxes(title=xlabel or col)
    f.update_yaxes(title="Records")
    return style_fig(f, height=height, title=title)


def heatmap(df, row, col, title=None, height=300, col_label=None):
    t = df.groupby([row, col]).size().unstack(fill_value=0)
    t = t.loc[t.sum(axis=1).sort_values(ascending=False).index]
    th = get_theme()
    f = go.Figure(go.Heatmap(z=t.values, x=[str(c) for c in t.columns], y=list(t.index), text=t.values,
                             texttemplate="%{text:,}", textfont=dict(size=13),
                             colorscale=[[i / 4, c] for i, c in enumerate(th["seq"])], xgap=3, ygap=3,
                             colorbar=dict(title=dict(text="Records", font=dict(size=12, color=th["text"])), thickness=12,
                                           tickfont=dict(color=th["text"])),
                             hovertemplate="%{y}<br>%{x}: %{z:,} records<extra></extra>"))
    f.update_yaxes(autorange="reversed")
    f.update_xaxes(title=col_label or col, type="category")
    return style_fig(f, height=height, title=title)


def box(df, x, y, title=None, height=300, violin=False, color=None, log_y=False):
    fn = px.violin if violin else px.box
    kw = dict(box=True, points=False) if violin else dict(points=False)
    c = color or x
    f = fn(df, x=x, y=y, color=c, color_discrete_map=color_map(df[c].astype(str).unique()), **kw)
    if log_y:
        f.update_yaxes(type="log")
    return style_fig(f, height=height, title=title, legend=False)


def kde_curve(values, title=None, height=300, xlabel="log10(value)"):
    v = np.asarray(values.dropna(), float)
    if len(v) < 10 or np.std(v) == 0:
        return None
    xs = np.linspace(v.min(), v.max(), 300)
    f = go.Figure(go.Scatter(x=xs, y=gaussian_kde(v)(xs), fill="tozeroy", line=dict(color=_pal()[0])))
    f.update_xaxes(title=xlabel)
    f.update_yaxes(title="Density")
    return style_fig(f, height=height, title=title)


def scatter(df, x, y, title=None, height=300, color=None):
    f = px.scatter(df, x=x, y=y, color=color, color_discrete_map=color_map(df[color].astype(str).unique()) if color else None,
                   color_discrete_sequence=_pal(), opacity=.6)
    f.update_traces(marker=dict(size=5))
    return style_fig(f, height=height, title=title, legend=color is not None)


def stacked_bar(df, cat, stack, title=None, height=300, normalize=False):
    t = df.groupby([cat, stack], observed=True).size().reset_index(name="n")
    f = px.bar(t, x=cat, y="n", color=stack, barmode="relative", color_discrete_map=CLASS_COLORS if stack == "conc_class" else None, color_discrete_sequence=_pal(),
               category_orders={stack: CLASS_ORDER} if stack == "conc_class" else None)
    if normalize:
        f.update_layout(barnorm="percent")
    return style_fig(f, height=height, title=title, legend=True)


def dot_plot(stats, group, title=None, height=300):
    s = stats.sort_values("median")
    f = go.Figure()
    f.add_trace(go.Scatter(x=s["median"], y=s[group], mode="markers", name="Median",
                           marker=dict(size=10, color=_pal()[0])))
    f.add_trace(go.Scatter(x=s["mean"], y=s[group], mode="markers", name="Mean",
                           marker=dict(size=10, symbol="diamond", color=_pal()[2])))
    f.update_xaxes(type="log", title="Value (log scale)")
    return style_fig(f, height=height, title=title, legend=True)


def moran_scatter(z, lag, height=340, title="Moran scatter plot"):
    f = px.scatter(x=z, y=lag, opacity=.5, color_discrete_sequence=_pal(), render_mode="webgl")
    m, b = np.polyfit(z, lag, 1)
    xs = np.array([z.min(), z.max()])
    f.add_trace(go.Scatter(x=xs, y=m * xs + b, mode="lines", line=dict(color=_pal()[6], width=2), name="slope = Moran's I"))
    f.add_hline(y=0, line_dash="dot"); f.add_vline(x=0, line_dash="dot")
    f.update_xaxes(title="Standardised cell value (z)")
    f.update_yaxes(title="Spatial lag of z")
    return style_fig(f, height=height, title=title)


def line_ts(df, x, color, title=None, height=300):
    """Time-series line chart: records per `x` (year) for every `color` group (ocean)."""
    t = df.groupby([x, color]).size().reset_index(name="samples")
    f = px.line(t, x=x, y="samples", color=color, markers=True,
                color_discrete_map=color_map(t[color].astype(str).unique()))
    f.update_traces(line=dict(width=3), marker=dict(size=6))
    f.update_xaxes(title="Year")
    f.update_yaxes(title="Records")
    f = style_fig(f, height=height, title=title, legend=True)
    f.update_layout(hovermode="x unified")
    return f
