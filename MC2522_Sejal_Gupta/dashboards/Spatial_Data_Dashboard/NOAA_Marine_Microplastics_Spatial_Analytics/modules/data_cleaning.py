"""Cleaning: the raw CSV is never modified; a separate analysis dataframe is built."""
import re
import numpy as np
import pandas as pd
from config.settings import NOT_RECORDED, CLASS_ORDER

RENAME = {
    "Unique ID": "id", "Sample Date": "date", "Latitude (degree)": "lat",
    "Longitude (degree)": "lon", "Ocean": "ocean", "Region": "region",
    "Subregion": "subregion", "Country": "country", "State": "state",
    "Beach Location": "beach", "Marine Setting": "setting",
    "Ocean Bottom Depth (m)": "depth_bottom", "Water Sample Depth (m)": "depth_water",
    "Sediment Sample Depth (m)": "depth_sediment", "Sampling Method": "method",
    "Mesh Size (mm)": "mesh_mm", "Volunteers Number": "volunteers",
    "Collecting Time (min)": "collect_min", "Standardized Nurdle Amount": "nurdle_amount",
    "Microplastics Measurement": "measurement", "Unit": "unit",
    "Concentration Class Range": "class_range", "Concentration Class": "conc_class",
    "Short Reference": "reference", "DOI": "doi", "Organization": "organization",
    "NCEI Accession Number": "accession", "ObjectId": "object_id",
}
CAT_COLS = ["ocean", "region", "subregion", "country", "state", "setting", "method"]


def clean_data(raw: pd.DataFrame):
    """Return (clean_df, cleaning_log). Invalid coordinates are removed and counted."""
    df = raw.copy()
    df.columns = [re.sub(r"\s+", " ", c).strip() for c in df.columns]
    df = df.rename(columns=RENAME)
    log = {"raw_rows": len(raw)}

    for c in ("lat", "lon"):
        df[c] = pd.to_numeric(df[c], errors="coerce")
    ok = df.lat.between(-90, 90) & df.lon.between(-180, 180)
    log["invalid_coordinates_removed"] = int((~ok).sum())
    df = df[ok].copy()

    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    log["unparseable_dates"] = int(df["date"].isna().sum())
    df["year"] = df["date"].dt.year

    for c in CAT_COLS + ["beach", "unit", "organization", "reference"]:
        df[c] = df[c].astype("object").where(df[c].notna(), None)
        df[c] = df[c].map(lambda v: v.strip() if isinstance(v, str) else v)
    for c in CAT_COLS:
        df[c] = df[c].fillna(NOT_RECORDED)

    # One measurement column per record; the unit always travels with it.
    # Nurdle Patrol rows (unit "pieces/10 mins") hold their value in the standardized nurdle column.
    df["value"] = df["measurement"].fillna(df["nurdle_amount"])
    df["log_value"] = np.where(df["value"] > 0, np.log10(df["value"].where(df["value"] > 0)), np.nan)
    df["conc_class"] = pd.Categorical(df["conc_class"], categories=CLASS_ORDER, ordered=True)

    key = [c for c in df.columns if c not in ("id", "object_id", "GlobalID")]
    df["duplicate_flag"] = df.duplicated(subset=key, keep="first")
    df["loc_key"] = df.lat.round(4).astype(str) + "," + df.lon.round(4).astype(str)
    df = df.reset_index(drop=True)
    log["clean_rows"] = len(df)
    return df, log
