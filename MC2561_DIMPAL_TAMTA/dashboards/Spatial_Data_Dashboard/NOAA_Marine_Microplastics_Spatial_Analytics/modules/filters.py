"""Horizontal filter bar. Filters live in st.session_state['F'] so they survive page changes."""
import datetime as dt
import pandas as pd
import streamlit as st

LISTS = ["ocean", "country", "region", "conc_class", "setting", "method", "unit"]


def _defaults(df):
    return dict(ocean=[], country=[], region=[], conc_class=[], setting=[], method=[], unit=[],
                date=(df.date.min().date(), df.date.max().date()), lat=(-90.0, 90.0), lon=(-180.0, 180.0))


def get_state(df):
    if "F" not in st.session_state:
        st.session_state["F"] = _defaults(df)
        st.session_state["map_ver"] = 0
    return st.session_state["F"]


def reset(df):
    st.session_state["F"] = _defaults(df)
    st.session_state["map_ver"] = st.session_state.get("map_ver", 0) + 1
    for k in ("sel_sig", "sel_point", "bar_sig"):
        st.session_state.pop(k, None)


def apply_filters(df, F, skip=()):
    m = pd.Series(True, index=df.index)
    for k in LISTS:
        if k not in skip and F[k]:
            m &= df[k].isin(F[k])
    d0, d1 = F["date"]
    m &= (df.date >= pd.Timestamp(d0)) & (df.date < pd.Timestamp(d1) + pd.Timedelta(days=1))
    m &= df.lat.between(*F["lat"]) & df.lon.between(*F["lon"])
    return df[m]


def _opts(df, col):
    return sorted(df[col].astype(str).unique())


def _multi(col, label, df, F, key):
    o = _opts(df, key)
    F[key] = col.multiselect(label, o, default=[v for v in F[key] if v in o], key=f"w_{key}_{hash(tuple(F[key]))}")


def filter_bar(df, advanced=True):
    """Render filters; returns (filtered_df, filtered_df_without_country_filter, F)."""
    F = get_state(df)
    with st.container(border=True, key="card_filters"):
        c = st.columns([1.2, 1.3, 1.5, 1.5, 1.2, 0.7])
        _multi(c[0], "Ocean", df, F, "ocean")
        _multi(c[1], "Country", df, F, "country")
        _multi(c[2], "Region", df, F, "region")
        d = c[3].date_input("Date", value=F["date"], min_value=df.date.min().date(),
                            max_value=df.date.max().date(), key=f"w_date_{F['date']}")
        if isinstance(d, (tuple, list)) and len(d) == 2:
            F["date"] = (d[0], d[1])
        _multi(c[4], "Class", df, F, "conc_class")
        c[5].write("")
        c[5].button("↺ Reset", on_click=reset, args=(df,), use_container_width=True, help="Restore the global view")
        if advanced:
            with st.expander("Advanced filters"):
                a = st.columns(5)
                _multi(a[0], "Marine setting", df, F, "setting")
                _multi(a[1], "Sampling method", df, F, "method")
                _multi(a[2], "Measurement unit", df, F, "unit")
                F["lat"] = a[3].slider("Latitude range", -90.0, 90.0, F["lat"], key=f"w_lat_{F['lat']}")
                F["lon"] = a[4].slider("Longitude range", -180.0, 180.0, F["lon"], key=f"w_lon_{F['lon']}")
    return apply_filters(df, F), apply_filters(df, F, skip=("country",)), F


def describe(F):
    parts = [f"{k}: {', '.join(F[k][:4])}{'…' if len(F[k]) > 4 else ''}" for k in LISTS if F[k]]
    parts.append(f"date: {F['date'][0]} to {F['date'][1]}")
    if F["lat"] != (-90.0, 90.0):
        parts.append(f"lat: {F['lat'][0]:.0f} to {F['lat'][1]:.0f}")
    if F["lon"] != (-180.0, 180.0):
        parts.append(f"lon: {F['lon'][0]:.0f} to {F['lon'][1]:.0f}")
    return "; ".join(parts)
