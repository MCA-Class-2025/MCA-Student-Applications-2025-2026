"""All map figures (Plotly geo maps, styled by the active theme)."""
import numpy as np
import plotly.graph_objects as go
from config.theme_manager import get_theme, style_fig, color_map, ocean_colors

HOVER_COLS = ["id", "country", "ocean", "setting", "method", "value", "unit", "year"]
HOVER_TPL = ("<b>%{customdata[0]}</b><br>Country: %{customdata[1]}<br>Ocean: %{customdata[2]}"
             "<br>Setting: %{customdata[3]}<br>Method: %{customdata[4]}"
             "<br>Value: %{customdata[5]:.4g} %{customdata[6]}<br>Year: %{customdata[7]}<extra></extra>")


def _leg(th=None):
    th = th or get_theme()
    return dict(orientation="h", y=-0.02, x=0, bgcolor=th["card"], bordercolor=th["border"], borderwidth=1,
                font=dict(color=th["text"], size=13), itemsizing="constant")


def _bounds(df, pad=1.15):
    la0, la1, lo0, lo1 = df.lat.min(), df.lat.max(), df.lon.min(), df.lon.max()
    dla, dlo = max(la1 - la0, 2.0), max(lo1 - lo0, 2.0)
    return ([max(la0 - dla * (pad - 1) / 2 - 1, -90), min(la1 + dla * (pad - 1) / 2 + 1, 90)],
            [max(lo0 - dlo * (pad - 1) / 2 - 1, -180), min(lo1 + dlo * (pad - 1) / 2 + 1, 180)])


def base_geo(fig, df=None, zoom=False, height=420, th=None, projection="natural earth"):
    th = th or get_theme()
    sea = "#FFFFFF" if th["mode"] == "light" else th["ocean"]   # white map background on light themes
    fig.update_geos(projection_type=projection, showland=True, landcolor=th["land"],
                    showocean=True, oceancolor=sea, showcountries=True,
                    countrycolor=th["coast"], coastlinecolor=th["coast"], showlakes=False,
                    bgcolor="rgba(0,0,0,0)", showframe=False)
    if zoom and df is not None and len(df):
        la, lo = _bounds(df)
        fig.update_geos(projection_type="equirectangular", lataxis_range=la, lonaxis_range=lo)
    fig.update_layout(height=height, margin=dict(l=0, r=0, t=0, b=0),
                      paper_bgcolor="rgba(0,0,0,0)", font=dict(color=th["text"], size=13), showlegend=False, hoverlabel=dict(bgcolor="#fff", font=dict(size=13, color="#10243f")),
                      dragmode="pan", clickmode="event+select")
    return fig


def _custom(df):
    d = df[HOVER_COLS].astype(object).copy()
    if "country_source" in df:
        det = df["country_source"] != "recorded"
        d.loc[det, "country"] = d.loc[det, "country"].astype(str) + " (detected from coordinates)"
    return d.to_numpy()


def country_labels(counts, bounds_df=None, top=22):
    """Text-only layer with country names (centroids from data/processed/country_centroids.csv)."""
    import pandas as pd
    from config.settings import PROCESSED_DIR
    f = PROCESSED_DIR / "country_centroids.csv"
    if not f.exists():
        return None
    th = get_theme()
    c = pd.read_csv(f).set_index("country")
    names = [n for n in counts.index if n in c.index]
    if bounds_df is None:
        dx, dy, pool = 16.0, 9.0, names[:40]
    else:
        la, lo = _bounds(bounds_df)
        pool = [n for n in names if la[0] <= c.loc[n, "lat"] <= la[1] and lo[0] <= c.loc[n, "lon"] <= lo[1]]
        dx, dy = max((lo[1] - lo[0]) / 9, .3), max((la[1] - la[0]) / 12, .3)
    keep = []   # busiest first; skip a label that would sit on top of one already placed
    for n in pool:
        y, x = c.loc[n, "lat"], c.loc[n, "lon"]
        if all(abs(x - c.loc[k, "lon"]) > dx or abs(y - c.loc[k, "lat"]) > dy for k in keep):
            keep.append(n)
        if len(keep) >= (14 if bounds_df is None else 30):
            break
    names = keep
    if not names:
        return None
    return go.Scattergeo(lat=c.loc[names, "lat"], lon=c.loc[names, "lon"], mode="text", text=names, hoverinfo="skip",
                         textfont=dict(size=12 if bounds_df is not None else 11, color=th["text"], family="Arial, sans-serif"),
                         showlegend=False)


def overview_map(df_pts, df_countries, zoom=False, height=420, projection="natural earth"):
    """Layer 1: country choropleth (click to select a country). Layers 2+: sampling points, one colour per ocean."""
    th = get_theme()
    fig = go.Figure()
    cc = df_countries[df_countries.country != "Not recorded"].country.value_counts()
    fig.add_trace(go.Choropleth(
        locations=cc.index.tolist(), z=np.log10(cc.values), locationmode="country names",
        customdata=cc.index.tolist(), colorscale=[[0, th["land"]], [1, th["coast"]]],
        showscale=False, marker_line_color=th["coast"], marker_line_width=.6,
        text=[f"{k}: {v:,} samples (click to filter)" for k, v in cc.items()], hoverinfo="text", name="countries", showlegend=False))
    p = df_pts[df_pts.ocean != "Not recorded"]   # records without an ocean are not drawn
    lab = country_labels(cc, p if zoom else None)
    cm = color_map(sorted(p.ocean.unique()))
    for o, g in p.groupby("ocean"):
        fig.add_trace(go.Scattergeo(
            lat=g.lat, lon=g.lon, mode="markers", customdata=_custom(g), hovertemplate=HOVER_TPL,
            marker=dict(size=6 if zoom else 4.5, color=cm[o], opacity=.85, line=dict(width=.3, color="#fff")),
            name=f"{o} ({len(g):,})"))
    if lab is not None:
        fig.add_trace(lab)
    base_geo(fig, p, zoom, height, th, projection)
    if projection == "orthographic" and not zoom:
        fig.update_geos(projection_rotation=dict(lon=-40, lat=20), showframe=True, framecolor=th["coast"])
    fig.update_layout(showlegend=True, legend=_leg())
    return fig


def country_map(df, height=460):
    """One country (already filtered): points coloured by marine setting, zoomed to the data."""
    th = get_theme()
    fig = go.Figure()
    cm = color_map(sorted(df.setting.unique()))
    for sname, g in df.groupby("setting"):
        fig.add_trace(go.Scattergeo(lat=g.lat, lon=g.lon, mode="markers", customdata=_custom(g), hovertemplate=HOVER_TPL,
                                    name=f"{sname} ({len(g):,})",
                                    marker=dict(size=8, color=cm[sname], opacity=.85, line=dict(width=.6, color="#fff"))))
    base_geo(fig, df, True, height, th)
    fig.update_geos(resolution=50, showsubunits=True, subunitcolor="#9FB6C9", showrivers=False)
    fig.update_layout(showlegend=True, legend=_leg())
    return fig


def points_map(df, color_col=None, height=420, zoom=True, max_pts=30000):
    th = get_theme()
    if color_col == "ocean":
        df = df[df.ocean != "Not recorded"]
    d = df.sample(max_pts, random_state=0) if len(df) > max_pts else df
    fig = go.Figure()
    mk = dict(size=4, opacity=.75, color=th["palette"][0])
    if color_col:
        cats = d[color_col].astype(str)
        for i, (name, g) in enumerate(d.groupby(cats)):
            fig.add_trace(go.Scattergeo(lat=g.lat, lon=g.lon, mode="markers", name=str(name),
                                        customdata=_custom(g), hovertemplate=HOVER_TPL,
                                        marker=dict(size=5, opacity=.8, color=color_map([str(name)])[str(name)] if str(name) in ocean_colors() else th["palette"][i % 8])))
        fig.update_layout(showlegend=True)
    else:
        fig.add_trace(go.Scattergeo(lat=d.lat, lon=d.lon, mode="markers", customdata=_custom(d),
                                    hovertemplate=HOVER_TPL, marker=mk))
    base_geo(fig, d, zoom, height, th)
    if color_col:
        fig.update_layout(showlegend=True, legend=_leg())
    return fig


def bubble_map(cells, size_col="n", color_col=None, label="Samples", height=420, max_size=26):
    th = get_theme()
    s = cells[size_col].astype(float)
    sizes = 4 + max_size * np.sqrt(s / s.max())
    col = cells[color_col] if color_col else s
    fig = go.Figure(go.Scattergeo(
        lat=cells.lat, lon=cells.lon, mode="markers",
        marker=dict(size=sizes, color=col, colorscale=[[i / 4, c] for i, c in enumerate(th["seq"])],
                    opacity=.75, line=dict(width=.3, color="#fff"), showscale=True,
                    colorbar=dict(title=dict(text=label, font=dict(size=10)), thickness=10, len=.6)),
        text=[f"{label}: {v:,.4g}" for v in col], hoverinfo="text"))
    return base_geo(fig, cells, False, height, th)


def cells_map(cells, value_col, label, height=420, size=5):
    th = get_theme()
    fig = go.Figure(go.Scattergeo(
        lat=cells.lat, lon=cells.lon, mode="markers",
        marker=dict(size=size, symbol="square", color=cells[value_col],
                    colorscale=[[i / 4, c] for i, c in enumerate(th["seq"])], opacity=.9, showscale=True,
                    colorbar=dict(title=dict(text=label, font=dict(size=10)), thickness=10, len=.6)),
        text=[f"{label}: {v:,.3g}" for v in cells[value_col]], hoverinfo="text"))
    return base_geo(fig, cells, False, height, th)


def category_map(d, cat_col, colors, base=None, height=420, size=6):
    """Categorical cell map (clusters, LISA quadrants, Gi* classes). 'Not significant' is drawn faint."""
    th = get_theme()
    fig = go.Figure()
    order = [c for c in colors if c in set(d[cat_col])] + [c for c in set(d[cat_col]) if c not in colors]
    for cat in order:
        g = d[d[cat_col] == cat]
        faint = cat in ("Not significant", "Noise", "Non-hotspot")
        fig.add_trace(go.Scattergeo(lat=g.lat, lon=g.lon, mode="markers", name=f"{cat} ({len(g):,})",
                                    marker=dict(size=size - 2 if faint else size, color=colors.get(cat, th["palette"][0]),
                                                opacity=.35 if faint else .9), hoverinfo="text",
                                    text=[cat] * len(g)))
    base_geo(fig, d, False, height, th)
    fig.update_layout(showlegend=True, legend=_leg())
    return fig


def add_ellipse(fig, e):
    th = get_theme()
    fig.add_trace(go.Scattergeo(lat=e["poly_lat"], lon=e["poly_lon"], mode="lines",
                                line=dict(color=th["palette"][6], width=3), name="1-SD ellipse"))
    fig.add_trace(go.Scattergeo(lat=[e["centre_lat"]], lon=[e["centre_lon"]], mode="markers",
                                marker=dict(size=11, symbol="x", color=th["palette"][6]), name="Mean centre"))
    fig.update_layout(showlegend=True, legend=_leg())
    return fig


def choropleth(counts, label="Samples", height=420):
    th = get_theme()
    fig = go.Figure(go.Choropleth(
        locations=counts.iloc[:, 0], z=np.log10(counts.iloc[:, 1]), locationmode="country names",
        colorscale=[[i / 4, c] for i, c in enumerate(th["seq"])],
        text=[f"{a}: {b:,}" for a, b in zip(counts.iloc[:, 0], counts.iloc[:, 1])], hoverinfo="text",
        colorbar=dict(title=dict(text=f"log10 {label}", font=dict(size=10)), thickness=10, len=.6),
        marker_line_color=th["coast"], marker_line_width=.5))
    return base_geo(fig, None, False, height, th)


def arc_map(df, top=14, height=480):
    """Arcs from the busiest country's sampling centre to the other top countries' sampling centres."""
    th = get_theme()
    d = df[df.country != "Not recorded"]
    g = d.groupby("country").agg(lat=("lat", "median"), lon=("lon", "median"), n=("lat", "size")).sort_values("n", ascending=False)
    if len(g) < 2:
        return None
    hub = g.iloc[0]
    hub_name = g.index[0]
    g = g.iloc[1:top + 1]
    fig = go.Figure()
    mx = g.n.max()
    for i, (name, r) in enumerate(g.iterrows()):
        col = th["palette"][i % len(th["palette"])]
        fig.add_trace(go.Scattergeo(lat=[hub.lat, r.lat], lon=[hub.lon, r.lon], mode="lines",
                                    line=dict(width=1.5 + 5 * np.sqrt(r.n / mx), color=col), opacity=.85,
                                    hoverinfo="text", text=f"{hub_name} → {name}: {int(r.n):,} records in {name}", showlegend=False))
    fig.add_trace(go.Scattergeo(lat=g.lat, lon=g.lon, mode="markers+text", text=g.index, textposition="top center",
                                textfont=dict(size=11, color=th["text"]), hoverinfo="skip", showlegend=False,
                                marker=dict(size=8 + 14 * np.sqrt(g.n / mx), color=th["accent"], line=dict(width=1.5, color="#fff"))))
    fig.add_trace(go.Scattergeo(lat=[hub.lat], lon=[hub.lon], mode="markers+text", text=[hub_name], textposition="bottom center",
                                textfont=dict(size=13, color=th["text"]), showlegend=False, hoverinfo="text",
                                hovertext=f"{hub_name}: {int(hub.n):,} records (hub)",
                                marker=dict(size=22, color=th["palette"][1], symbol="star", line=dict(width=1.5, color="#fff"))))
    base_geo(fig, None, False, height, th)
    return fig


def surface3d(df, step=10, height=460):
    """3D surface: smoothed sampling density (log10 of records per lat/lon block)."""
    from scipy.ndimage import gaussian_filter
    th = get_theme()
    H, ye, xe = np.histogram2d(df.lat, df.lon, bins=[np.arange(-90, 90 + step, step), np.arange(-180, 180 + step, step)])
    z = gaussian_filter(np.log10(H + 1), 0.8)
    fig = go.Figure(go.Surface(x=(xe[:-1] + xe[1:]) / 2, y=(ye[:-1] + ye[1:]) / 2, z=z,
                               colorscale=[[i / 4, c] for i, c in enumerate(th["seq"])],
                               colorbar=dict(title=dict(text="log10 records", font=dict(color=th["text"])), thickness=12, tickfont=dict(color=th["text"])),
                               hovertemplate="Lon %{x}°, Lat %{y}°<br>density %{z:.2f}<extra></extra>"))
    ax = dict(backgroundcolor="rgba(0,0,0,0)", gridcolor=th["grid"], color=th["text"], tickfont=dict(size=11, color=th["text"]))
    fig.update_layout(height=height, margin=dict(l=0, r=0, t=0, b=0), paper_bgcolor="rgba(0,0,0,0)",
                      font=dict(color=th["text"], size=13),
                      scene=dict(xaxis=dict(title="<b>Longitude</b>", **ax), yaxis=dict(title="<b>Latitude</b>", **ax),
                                 zaxis=dict(title="<b>Density</b>", **ax), camera=dict(eye=dict(x=1.5, y=-1.6, z=.9)),
                                 aspectratio=dict(x=1.6, y=1, z=.6)))
    return fig
