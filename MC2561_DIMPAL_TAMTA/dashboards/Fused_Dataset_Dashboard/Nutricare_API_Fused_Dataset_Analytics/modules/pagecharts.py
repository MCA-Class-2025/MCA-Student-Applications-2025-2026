"""Charts for the three supporting pages."""
import numpy as np
import pandas as pd
import plotly.express as px
from .charts import empty, layout
from .data import GLOB, GRADES, IND, MACROS, MICROS, NUTR, SHARE


def compare(d, by, cols, log, t, h):
    if d.empty: return empty(t, h)
    g = d.groupby(by)[cols].mean().reset_index().melt(by, var_name="Nutrient", value_name="Mean per 100 g")
    f = px.bar(g, x=by, y="Mean per 100 g", color="Nutrient", barmode="group", log_y=log, color_discrete_sequence=t["palette"])
    f.update_xaxes(title="", tickangle=-15)
    return layout(f, t, h)


def nutri_nova_heat(d, t, h):
    if d.empty: return empty(t, h)
    x = pd.crosstab(d["Nutri-Score Grade"], d["NOVA Group"])
    x = x.reindex([g for g in GRADES if g in x.index])
    f = px.imshow(x, text_auto=True, aspect="auto", color_continuous_scale=[t["card"], t["accent"]],
                  labels=dict(x="NOVA Group", y="Nutri-Score", color="Foods"))
    return layout(f, t, h, False)


def top_bar(series, title, t, h):
    if series.empty: return empty(t, h)
    s = series.sort_values().reset_index(); s.columns = ["Name", "Foods"]
    f = px.bar(s, x="Foods", y="Name", orientation="h", color_discrete_sequence=[t["accent"]], text="Foods")
    f.update_yaxes(title="", dtick=1); f.update_traces(textposition="outside", cliponaxis=False)
    return layout(f, t, h, False)


def glob_vs_india(d, n, t, h):
    if d.empty: return empty(t, h)
    x = d.nlargest(n, GLOB).melt("Food Name", [GLOB, IND], var_name="Scope", value_name="Tonnes")
    f = px.bar(x, x="Food Name", y="Tonnes", color="Scope", barmode="group", log_y=True, color_discrete_sequence=t["palette"])
    f.update_xaxes(title="", tickangle=-35)
    return layout(f, t, h)


def share_bar(d, n, t, h):
    if d.empty: return empty(t, h)
    x = d.nlargest(n, SHARE)
    f = px.bar(x, x="Food Name", y=SHARE, color=SHARE, color_continuous_scale=[t["border"], t["accent"]])
    f.update_xaxes(title="", tickangle=-35); f.update_coloraxes(showscale=False)
    return layout(f, t, h, False)


def corr_heat(d, t, h):
    if len(d) < 3: return empty(t, h)
    c = d[NUTR].corr().round(2)
    f = px.imshow(c, text_auto=True, zmin=-1, zmax=1, aspect="auto", color_continuous_scale=[t["down"], t["card"], t["accent"]])
    return layout(f, t, h, False)


def box_z(d, t, h):
    if len(d) < 3: return empty(t, h)
    z = ((d[NUTR] - d[NUTR].mean()) / d[NUTR].std()).melt(var_name="Nutrient", value_name="z-score")
    f = px.box(z, x="Nutrient", y="z-score", color="Nutrient", color_discrete_sequence=t["palette"] * 2)
    f.update_xaxes(title="", tickangle=-20)
    return layout(f, t, h, False)


def missing_bar(m, t, h):
    m = m.sort_values("Missing")
    f = px.bar(m, x="Missing", y="Column", orientation="h", text="% Missing", color_discrete_sequence=[t["down"]])
    f.update_traces(texttemplate="%{text}%", textposition="outside", cliponaxis=False)
    f.update_yaxes(title="", dtick=1)
    return layout(f, t, h, False)
