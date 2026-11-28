"""Statistics helpers for page 6 (descriptive stats, outliers, validation, gaps, Excel export)."""
from io import BytesIO
import numpy as np
import pandas as pd
from .data import METRICS


def describe_table(dU, metric):
    col = METRICS[metric]
    g = dU.groupby("name")[col]
    t = g.agg(count="count", mean="mean", std="std", min="min", p25=lambda s: s.quantile(.25), median="median",
              p75=lambda s: s.quantile(.75), max="max")
    t["skew"] = g.skew()
    t["kurtosis"] = g.apply(lambda s: s.kurt())
    t = t.join(dU.groupby("name")["ret"].agg(ret_mean_pct="mean", ret_std_pct="std"))
    t["cv_pct"] = t["std"] / t["mean"] * 100
    return t.round(3).reset_index()


def outliers(dU, z=4.0):
    x = dU.dropna(subset=["ret"]).copy()
    g = x.groupby("name")["ret"]
    sd = g.transform("std")
    x["z"] = (x["ret"] - g.transform("mean")) / sd.where(sd > 0)
    out = x[x["z"].abs() > z][["date", "name", "symbol", "close", "ret", "z"]]
    out = out.sort_values("z", key=lambda s: s.abs(), ascending=False)
    return out.assign(ret=out["ret"].round(3), z=out["z"].round(2))


def validation_table(df, q):
    hi_bad = int((df["high"] < df[["open", "close", "low"]].max(axis=1)).sum())
    lo_bad = int((df["low"] > df[["open", "close", "high"]].min(axis=1)).sum())
    rows = [
        ("Date parsed as datetime", q["bad_dates"], "rows with unreadable dates"),
        ("Duplicate Date + Symbol combinations", q["duplicate_keys_removed"], "last row kept"),
        ("Non-positive Open/High/Low/Close", int((df[["open", "high", "low", "close"]] <= 0).any(axis=1).sum()), "kept; returns around them left blank"),
        ("High below Open, Close or Low", hi_bad, "kept as in source"),
        ("Low above Open, Close or High", lo_bad, "kept as in source"),
        ("Missing volume", q["missing_volume"], "shown as gaps, never 0"),
        ("Negative volume", q["negative_volume"], ""),
    ]
    return pd.DataFrame([(a, b, "OK" if b == 0 else "Review", c) for a, b, c in rows], columns=["Check", "Rows", "Status", "Handling"])


def gaps(df, min_days=7, top=25):
    x = df.sort_values(["symbol", "date"]).copy()
    x["prev_date"] = x.groupby("symbol")["date"].shift()
    x["gap_days"] = (x["date"] - x["prev_date"]).dt.days
    g = x[x["gap_days"] > min_days][["name", "prev_date", "date", "gap_days"]].sort_values("gap_days", ascending=False)
    return g.head(top).rename(columns={"prev_date": "last_date_before_gap", "date": "next_date"})


def to_excel_bytes(data: pd.DataFrame, desc: pd.DataFrame) -> bytes:
    buf = BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as xw:
        data.to_excel(xw, sheet_name="Filtered data", index=False)
        desc.to_excel(xw, sheet_name="Summary statistics", index=False)
    return buf.getvalue()
