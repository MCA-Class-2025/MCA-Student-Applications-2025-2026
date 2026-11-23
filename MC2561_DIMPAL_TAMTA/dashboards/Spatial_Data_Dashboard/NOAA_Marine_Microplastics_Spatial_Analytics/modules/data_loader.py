"""Cached data loading."""
import pandas as pd
from config.settings import RAW_PATH
from modules.data_cleaning import clean_data
from modules.data_validation import quality_report

try:
    import streamlit as st
    cache = st.cache_data(show_spinner="Loading dataset...")
except Exception:  # allows unit-testing without Streamlit
    cache = lambda f: f


@cache
def load_raw(path: str = str(RAW_PATH)) -> pd.DataFrame:
    return pd.read_csv(path)


def add_detected_country(df):
    """Fill 'Not recorded' countries from the coordinates (lookup made by scripts/infer_countries.py).
    The original value is kept in `country_source` ('recorded' / 'detected from coordinates')."""
    from config.settings import PROCESSED_DIR, NOT_RECORDED
    df["country_source"] = "recorded"
    f = PROCESSED_DIR / "inferred_country.csv"
    if f.exists():
        m = pd.read_csv(f).drop_duplicates("loc_key").set_index("loc_key")["country"]
        hit = (df.country == NOT_RECORDED) & df.loc_key.isin(m.index)
        df.loc[hit, "country"] = df.loc[hit, "loc_key"].map(m)
        df.loc[hit, "country_source"] = "detected from coordinates"
    return df


@cache
def load_data(path: str = str(RAW_PATH)):
    raw = load_raw(path)
    df, log = clean_data(raw)
    df = add_detected_country(df)
    return df, quality_report(df, log)
