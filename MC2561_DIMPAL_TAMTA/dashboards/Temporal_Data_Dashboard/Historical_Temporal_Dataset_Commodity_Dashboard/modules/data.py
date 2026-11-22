"""Data loading, validation report, filtering, resampling and summary maths.

Nothing here invents data: rows are only de-duplicated on (date, symbol) and every
suspicious row is counted in the quality report instead of being silently removed.
"""
from pathlib import Path
import numpy as np
import pandas as pd
import streamlit as st

DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "commodity-prices.csv"
FREQ = {"Daily": "D", "Weekly": "W", "Monthly": "ME", "Quarterly": "QE", "Yearly": "YE"}
ORDER = list(FREQ)
METRICS = {"Open": "open", "High": "high", "Low": "low", "Close": "close"}
RANGES = ["All Time", "Last 1 Year", "Last 3 Years", "Last 5 Years", "Last 10 Years", "Custom"]


@st.cache_data(show_spinner="Loading commodity data...")
def load_data(path: str = str(DATA_PATH)):
    raw = pd.read_csv(path)
    raw.columns = [c.strip().lower() for c in raw.columns]
    raw["date"] = pd.to_datetime(raw["date"], errors="coerce")
    for c in ["open", "high", "low", "close", "volume"]:
        raw[c] = pd.to_numeric(raw[c], errors="coerce")
    raw["name"] = raw["name"].astype(str).str.strip()
    raw["symbol"] = raw["symbol"].astype(str).str.strip()

    q = {"raw_rows": len(raw)}
    q["bad_dates"] = int(raw["date"].isna().sum())
    raw = raw.dropna(subset=["date", "close"])
    dup_mask = raw.duplicated(["date", "symbol"], keep="last")
    q["duplicate_keys_removed"] = int(dup_mask.sum())
    q["exact_duplicate_rows"] = int(raw.duplicated(keep="last").sum())
    df = raw[~dup_mask].sort_values(["symbol", "date"]).reset_index(drop=True)
    # derived fields, always calculated per symbol so one commodity never leaks into another
    g = df.groupby("symbol", sort=False)["close"]
    prev = g.shift()
    df["change"] = df["close"] - prev
    df["ret"] = (df["close"] / prev - 1) * 100
    bad = (prev <= 0) | (df["close"] <= 0)          # returns are undefined across zero/negative prices
    q["returns_excluded"] = int((bad & prev.notna()).sum())
    df.loc[bad, "ret"] = np.nan
    df["range"] = df["high"] - df["low"]
    df["range_pct"] = np.where(df["open"] > 0, df["range"] / df["open"] * 100, np.nan)
    df["typical"] = (df["high"] + df["low"] + df["close"]) / 3
    df["year"], df["month"] = df["date"].dt.year, df["date"].dt.month
    df["quarter"], df["dow"] = df["date"].dt.quarter, df["date"].dt.day_name()
    q["rows"] = len(df)
    q["high_below_low"] = int((df["high"] < df["low"]).sum())
    q["close_outside_range"] = int(((df["close"] > df["high"]) | (df["close"] < df["low"])).sum())
    q["non_positive_close"] = int((df["close"] <= 0).sum())
    q["missing_volume"] = int(df["volume"].isna().sum())
    q["negative_volume"] = int((df["volume"] < 0).sum())
    q["commodities"] = int(df["name"].nunique())
    q["date_min"], q["date_max"] = df["date"].min(), df["date"].max()
    return df, q


def preset_range(preset: str, dmin, dmax):
    years = {"Last 1 Year": 1, "Last 3 Years": 3, "Last 5 Years": 5, "Last 10 Years": 10}.get(preset)
    if years is None:
        return dmin, dmax
    return max(dmin, dmax - pd.DateOffset(years=years)), dmax


def filter_df(df, names, start, end):
    m = (df["date"] >= pd.Timestamp(start)) & (df["date"] <= pd.Timestamp(end))
    if names:
        m &= df["name"].isin(names)
    return df[m]


@st.cache_data(show_spinner=False)
def to_csv_bytes(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False).encode()


def agg(one: pd.DataFrame, interval: str) -> pd.DataFrame:
    """OHLCV for ONE commodity at the requested interval (open=first, high=max, low=min, close=last, volume=sum)."""
    s = one.sort_values("date").set_index("date")[["open", "high", "low", "close", "volume"]]
    if interval == "Daily":
        return s
    out = s.resample(FREQ[interval]).agg(
        open=("open", "first"), high=("high", "max"), low=("low", "min"), close=("close", "last"),
        volume=("volume", lambda v: v.sum(min_count=1)))
    return out.dropna(subset=["close"])


def pick_interval(dmin, dmax, interval, max_n):
    """Coarsen the interval (never refine it) until the range fits in max_n periods."""
    i = ORDER.index(interval)
    while i < len(ORDER) - 1 and len(pd.date_range(dmin, dmax, freq=FREQ[ORDER[i]])) + 1 > max_n:
        i += 1
    return ORDER[i]


def period_labels(idx, interval):
    if interval == "Yearly":
        return [d.strftime("%Y") for d in idx]
    if interval == "Quarterly":
        return [f"Q{(d.month - 1) // 3 + 1} {d.year}" for d in idx]
    if interval == "Monthly":
        return [d.strftime("%b %Y") for d in idx]
    return [d.strftime("%d %b %Y") for d in idx]


def summarize(one: pd.DataFrame):
    """Latest close, change over the range (first close -> last close), period high/low."""
    if one.empty:
        return None
    one = one.sort_values("date")
    first, last = one["close"].iloc[0], one["close"].iloc[-1]
    return dict(latest=last, latest_date=one["date"].iloc[-1], first=first,
                change=last - first, change_pct=(last / first - 1) * 100 if first > 0 else np.nan,
                high=one["high"].max(), low=one["low"].min(), n=len(one))


def performance_table(d: pd.DataFrame) -> pd.DataFrame:
    """% change of close (first -> last observation in range) for every commodity in d."""
    rows = []
    for nm, g in d.groupby("name"):
        s = summarize(g)
        if s and np.isfinite(s["change_pct"]):
            rows.append((nm, g["symbol"].iloc[0], s["latest"], s["change_pct"]))
    return pd.DataFrame(rows, columns=["name", "symbol", "latest", "change_pct"]).sort_values("change_pct", ascending=False)


def fmt_price(v):
    if v is None or not np.isfinite(v):
        return "—"
    return f"{v:,.2f}" if abs(v) >= 100 else f"{v:,.3f}"
