"""Pure calculation helpers (no Streamlit)."""
import numpy as np
import pandas as pd
from config.settings import NOT_RECORDED


def kpis(df: pd.DataFrame) -> dict:
    n = len(df)
    countries = df.loc[df.country != NOT_RECORDED, "country"].nunique()
    oc = df.loc[df.ocean != NOT_RECORDED, "ocean"].value_counts()
    return {
        "samples": n,
        "countries": int(countries),
        "countries_missing_pct": round(100 * (df.country == NOT_RECORDED).mean(), 1) if n else 0.0,
        "oceans": int(len(oc)),
        "top_ocean": oc.index[0] if len(oc) else "n/a",
        "top_ocean_pct": round(100 * oc.iloc[0] / n, 1) if len(oc) and n else 0.0,
    }


def counts(df, col, exclude_nr=False, top=None):
    s = df[col]
    if exclude_nr:
        s = s[s != NOT_RECORDED]
    out = s.value_counts().rename_axis(col).reset_index(name="samples")
    return out.head(top) if top else out


def unit_subset(df, unit):
    """Rows of ONE unit with a valid value. Units are never mixed."""
    return df[(df.unit == unit) & df.value.notna()]


def available_units(df):
    return [u for u, k in df[df.value.notna()].unit.value_counts().items() if k > 0]


def group_stats(d, col, top=12):
    top_groups = d[col].value_counts().head(top).index
    g = d[d[col].isin(top_groups)].groupby(col)["value"].agg(
        n="count", mean="mean", median="median", max="max").reset_index()
    return g.sort_values("n", ascending=False)


def lat_zone(lat):
    a = abs(lat)
    z = np.where(a >= 66.5, "Polar (>=66.5°)", np.where(a >= 23.5, "Temperate (23.5–66.5°)", "Tropical (<23.5°)"))
    return pd.Series(z, index=lat.index)
