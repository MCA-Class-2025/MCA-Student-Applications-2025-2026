"""Data-quality summary used by the Explorer and the report."""
import pandas as pd
from config.settings import NOT_RECORDED


def quality_report(df: pd.DataFrame, log: dict) -> dict:
    n = len(df)
    pct = lambda k: round(100 * k / n, 1) if n else 0.0
    miss = {
        "country": int((df.country == NOT_RECORDED).sum()),
        "ocean": int((df.ocean == NOT_RECORDED).sum()),
        "region": int((df.region == NOT_RECORDED).sum()),
        "measurement/value": int(df.value.isna().sum()),
        "date": int(df.date.isna().sum()),
    }
    return {
        "rows": n, "raw_rows": log.get("raw_rows", n),
        "invalid_coordinates_removed": log.get("invalid_coordinates_removed", 0),
        "duplicate_records": int(df.duplicate_flag.sum()),
        "unique_locations": int(df.loc_key.nunique()),
        "missing": {k: (v, pct(v)) for k, v in miss.items()},
        "units": df.unit.value_counts().to_dict(),
    }


def missing_table(df: pd.DataFrame) -> pd.DataFrame:
    m = df.isna().sum().to_frame("missing")
    m["missing %"] = (100 * m["missing"] / max(len(df), 1)).round(1)
    m["dtype"] = df.dtypes.astype(str)
    return m.reset_index(names="column")
