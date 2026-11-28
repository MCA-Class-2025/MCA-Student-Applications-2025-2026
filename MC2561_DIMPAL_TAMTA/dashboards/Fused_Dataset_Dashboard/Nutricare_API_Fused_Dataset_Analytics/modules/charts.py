"""Main-dashboard charts and the two maps. Every colour comes from the active theme."""
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from .data import GLOB, IND, MACROS, SUPPORT, geojson, split, state_centroids

NUTRI = {"A": "#1E8E3E", "B": "#8BC34A", "C": "#F4C20D", "D": "#F08A4B", "E": "#D1495B", "-": "#9AA0A6"}
NOVA = {"1": "#1E8E3E", "2": "#8BC34A", "3": "#F08A4B", "4": "#D1495B"}


def layout(fig, t, h, legend=True, **kw):
    fig.update_layout(height=h, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", showlegend=legend,
                      font=dict(color=t["text"], family=t["font"], size=14), margin=dict(l=10, r=10, t=30, b=10),
                      colorway=t["palette"], legend=dict(font=dict(size=11)), **kw)
    fig.update_xaxes(gridcolor=t["grid"], zerolinecolor=t["grid"], linecolor=t["border"])
    fig.update_yaxes(gridcolor=t["grid"], zerolinecolor=t["grid"], linecolor=t["border"])
    return fig


def empty(t, h, msg="No data for the current filters"):
    f = go.Figure()
    f.add_annotation(text=msg, showarrow=False, font=dict(size=14, color=t["muted"]))
    f.update_xaxes(visible=False); f.update_yaxes(visible=False)
    return layout(f, t, h, False)


def nutrient_bar(row, t, h):
    d = pd.DataFrame({"Nutrient": MACROS, "Per 100 g": [row[n] for n in MACROS]})
    d["label"] = d["Per 100 g"].map(lambda v: f"{v:g}")
    f = px.bar(d.iloc[::-1], x="Per 100 g", y="Nutrient", orientation="h", color="Nutrient", text="label",
               color_discrete_sequence=t["palette"])
    f.update_traces(textposition="outside", cliponaxis=False)
    return layout(f, t, h, False)


def donut(d, col, cmap, t, h):
    if d.empty: return empty(t, h)
    c = d[col].value_counts().reset_index(); c.columns = [col, "Foods"]
    f = px.pie(c, names=col, values="Foods", hole=.58, color=col, color_discrete_map=cmap)
    f.update_traces(textinfo="label+percent+value", textfont_size=13, marker=dict(line=dict(color=t["card"], width=2)))
    f.add_annotation(text=f"<b>{len(d):,}</b><br>foods", showarrow=False, font=dict(size=15, color=t["text"]))
    return layout(f, t, h)


def cancer_stack(d, t, h):
    if d.empty: return empty(t, h)
    c = d.groupby([SUPPORT, "Risk Group"]).size().reset_index(name="Foods")
    f = px.bar(c, x=SUPPORT, y="Foods", color="Risk Group", color_discrete_sequence=t["palette"])
    f.update_xaxes(title="", tickangle=-20)
    return layout(f, t, h)


def prod_compare(d, col, food, n, t, h):
    """Top-n foods by production (log axis) with the selected food highlighted."""
    if d.empty: return empty(t, h)
    top = d.nlargest(n, col)[["Food Name", col]]
    if food is not None and food not in set(top["Food Name"]):
        top = pd.concat([top, d[d["Food Name"] == food][["Food Name", col]]])
    top["Group"] = np.where(top["Food Name"] == food, "Selected food", "Top producers")
    f = px.bar(top, x="Food Name", y=col, color="Group", log_y=True,
               color_discrete_map={"Selected food": t["down"], "Top producers": t["accent"]})
    f.update_xaxes(title="", tickangle=-35); f.update_yaxes(title="tonnes (log)")
    return layout(f, t, h)


def scatter(d, food_row, t, h):
    if d.empty: return empty(t, h)
    f = px.scatter(d, x="Protein (g)", y="Calories (kcal)", color="Nutri-Score Grade", color_discrete_map=NUTRI,
                   hover_name="Food Name", opacity=.65, category_orders={"Nutri-Score Grade": list(NUTRI)})
    if food_row is not None:
        f.add_trace(go.Scatter(x=[food_row["Protein (g)"]], y=[food_row["Calories (kcal)"]], mode="markers+text",
                               text=[food_row["Food Name"]], textposition="top center", name="Selected",
                               marker=dict(size=15, symbol="star", color=t["text"], line=dict(width=1, color=t["card"]))))
    return layout(f, t, h)


NOVA_NAME = {"1": "NOVA 1 · Unprocessed / minimally processed", "2": "NOVA 2 · Processed culinary ingredients",
             "3": "NOVA 3 · Processed foods", "4": "NOVA 4 · Ultra-processed"}


def treemap(d, t, h):
    if d.empty: return empty(t, h)
    c = d["NOVA Group"].value_counts().reset_index(); c.columns = ["g", "Foods"]
    c["NOVA"] = c["g"].map(NOVA_NAME); c["pct"] = (c["Foods"] / c["Foods"].sum() * 100).round(1)
    c["lbl"] = c["NOVA"] + "<br>" + c["Foods"].astype(str) + " foods · " + c["pct"].astype(str) + "%"
    f = px.treemap(c, path=["lbl"], values="Foods", color="g", color_discrete_map=NOVA)
    f.update_traces(textfont_size=16, textinfo="label", marker=dict(line=dict(color=t["card"], width=3)), hovertemplate="%{label}<extra></extra>")
    f.update_layout(margin=dict(l=0, r=0, t=10, b=0))
    return layout(f, t, h, False)


def top_names(counter_series, t, h, n=12):
    """Horizontal bars with the place name on the axis and the food count printed at the bar end."""
    s = counter_series.nlargest(n).sort_values().reset_index(); s.columns = ["Name", "Foods"]
    if s.empty: return empty(t, h)
    f = px.bar(s, x="Foods", y="Name", orientation="h", text="Foods", color="Foods", color_continuous_scale=[t["border"], t["accent"]])
    f.update_traces(textposition="outside", cliponaxis=False, textfont_size=14)
    f.update_yaxes(title="", dtick=1, tickfont_size=14); f.update_coloraxes(showscale=False)
    return layout(f, t, h, False)


def nutrient_top(d, nutrient, food, n, t, h):
    """Top-n foods for one selectable nutrient; the selected food is added and highlighted."""
    x = d.dropna(subset=[nutrient]).nlargest(n, nutrient)[["Food Name", nutrient]]
    if food is not None and food not in set(x["Food Name"]) and food in set(d["Food Name"]):
        x = pd.concat([x, d[d["Food Name"] == food][["Food Name", nutrient]]])
    if x.empty: return empty(t, h)
    x["Group"] = np.where(x["Food Name"] == food, "Selected food", "Highest foods")
    f = px.bar(x.iloc[::-1], x=nutrient, y="Food Name", orientation="h", color="Group", text=nutrient,
               color_discrete_map={"Selected food": t["down"], "Highest foods": t["accent"]})
    f.update_traces(textposition="outside", cliponaxis=False); f.update_yaxes(title="", dtick=1)
    return layout(f, t, h)


def scatter(d, food_row, t, h, compare=()):
    if d.empty: return empty(t, h)
    x = d.assign(Fiber=d["Fiber (g)"].fillna(0).clip(lower=0) + 1)
    f = px.scatter(x, x="Calories (kcal)", y="Protein (g)", size="Fiber", size_max=16, color="Nutri-Score Grade", color_discrete_map=NUTRI,
                   hover_name="Food Name", hover_data={"Calories (kcal)": True, "Protein (g)": True, "Fiber (g)": True, "Nutri-Score Grade": True, "Fiber": False},
                   opacity=.6, category_orders={"Nutri-Score Grade": list(NUTRI)})
    pick = [r for r in ([food_row] if food_row is not None else [])] + [d[d["Food Name"] == n].iloc[0] for n in compare if n in set(d["Food Name"])]
    for r in pick:
        f.add_trace(go.Scatter(x=[r["Calories (kcal)"]], y=[r["Protein (g)"]], mode="markers+text", text=[r["Food Name"]], textposition="top center",
                               textfont=dict(size=14), name=r["Food Name"], showlegend=False,
                               marker=dict(size=16, symbol="star", color=t["text"], line=dict(width=1, color=t["card"]))))
    return layout(f, t, h)


def rank_dict(row, col):
    return {c: i + 1 for i, c in enumerate(split(row[col]))}


def geo_map(vals, t, h, india=False, discrete=True, hover=None, label="Foods", max_labels=30):
    """Choropleth with the place NAMES drawn on it. discrete=True: vals are ranks 1-3 and the map zooms to them.
    discrete=False: vals are food counts over the whole map (labels on the biggest `max_labels`)."""
    if not vals: return empty(t, h, "Not produced in India" if india else "No producing country listed")
    locs = list(vals); hover = hover or {}
    fig = go.Figure()
    kw = dict(geojson=geojson(), featureidkey="properties.state") if india else dict(locationmode="country names")
    if india:
        allst = [f["properties"]["state"] for f in geojson()["features"]]
        fig.add_trace(go.Choropleth(locations=allst, z=[0] * len(allst), colorscale=[[0, t["border"]], [1, t["border"]]], showscale=False,
                                    marker_line_color=t["card"], marker_line_width=.6, hoverinfo="skip", **kw))
    if discrete:
        z, cs, zr = [4 - vals[k] for k in locs], [[0, t["palette"][2]], [.5, t["palette"][1]], [1, t["accent"]]], (1, 3)
        txt = {k: f"{k}<br>#{vals[k]}" for k in locs}
        ht = [hover.get(k, f"{k} · Rank #{vals[k]}") for k in locs]
    else:
        z, cs, zr = [vals[k] for k in locs], [[0, t["border"]], [1, t["accent"]]], (None, None)
        top = sorted(locs, key=lambda k: -vals[k])[:max_labels]
        txt = {k: f"{k}" for k in top}
        ht = [hover.get(k, f"{k}: {vals[k]} foods") for k in locs]
    fig.add_trace(go.Choropleth(locations=locs, z=z, colorscale=cs, zmin=zr[0], zmax=zr[1], showscale=not discrete,
                                colorbar=dict(title=dict(text=label), len=.6), marker_line_color=t["card"], marker_line_width=.8,
                                hovertext=ht, hoverinfo="text", **kw))
    names = list(txt)
    tf = dict(size=14, color=t["text"], family=t["font"])
    if india:
        cent = state_centroids(); names = [k for k in names if k in cent]
        fig.add_trace(go.Scattergeo(lat=[cent[k][0] for k in names], lon=[cent[k][1] for k in names], text=[txt[k] for k in names],
                                    mode="text", textfont=tf, hoverinfo="skip", showlegend=False))
        fig.update_geos(fitbounds="locations", visible=False, bgcolor="rgba(0,0,0,0)")
    else:
        fig.add_trace(go.Scattergeo(locations=names, locationmode="country names", text=[txt[k] for k in names],
                                    mode="text", textfont=tf, hoverinfo="skip", showlegend=False))
        fig.update_geos(showcountries=True, countrycolor=t["muted"], showland=True, landcolor="rgba(128,138,155,.22)", showframe=False,
                        showcoastlines=True, coastlinecolor=t["muted"], projection_type="natural earth", bgcolor="rgba(0,0,0,0)",
                        **({"fitbounds": "locations"} if discrete else {}))
    return layout(fig, t, h, False)
