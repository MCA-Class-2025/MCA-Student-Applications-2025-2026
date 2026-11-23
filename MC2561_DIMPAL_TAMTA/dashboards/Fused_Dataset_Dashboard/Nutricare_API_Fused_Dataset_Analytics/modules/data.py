"""Loading, parsing, filtering and exporting the fused dataset (nothing is invented or dropped)."""
import io, json
from collections import Counter
from pathlib import Path
import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = ROOT / "data" / "API_Fusion_Dataset.csv"
GEO_PATH = ROOT / "data" / "india_states.geojson"

MACROS = ["Calories (kcal)", "Protein (g)", "Carbohydrates (g)", "Fat (g)", "Fiber (g)"]
MICROS = ["Calcium (mg)", "Iron (mg)", "Potassium (mg)", "Sodium (mg)", "Vitamin C (mg)"]
NUTR = MACROS + MICROS
GLOB, IND = "Total Global Production (tonnes)", "India Total Production (tonnes)"
SHARE = "India's share in global production(%)"
SUPPORT, RISK_TXT = "Cancer_Patient_Support_Category", "Cancer_Risk_Classification"
BAD = {"Unknown", "Not produced in India", "", "nan"}
GRADES = ["A", "B", "C", "D", "E", "-"]
EXTRA = ["NOVA Group", "Risk Group"]          # helper columns, hidden from exports


@st.cache_data
def load_data():
    d = pd.read_csv(DATA_PATH)
    d["NOVA Group"] = d["nova_group"].astype(str)
    d["Risk Group"] = d[RISK_TXT].str.split(" - ").str[0].str.strip()
    q = dict(rows=len(d), cols=d.shape[1], missing_cells=int(d.isna().sum().sum()),
             rows_missing=int(d.drop(columns=EXTRA).isna().any(axis=1).sum()),
             unknown_country=int((d["Top Producing Country"] == "Unknown").sum()),
             not_in_india=int((d["Top Producing Indian State"] == "Not produced in India").sum()),
             no_score=int((d["Nutri-Score Grade"] == "-").sum()), zero_cal=int((d["Calories (kcal)"] == 0).sum()),
             dup_rows=int(d.drop(columns=EXTRA).duplicated().sum()), dup_names=int(d["Food Name"].duplicated().sum()),
             assumptions=int(d["Assumption"].notna().sum()), no_image=int(d["Image URL"].isna().sum()))
    return d, q


@st.cache_data
def geojson():
    return json.load(open(GEO_PATH, encoding="utf-8"))


def split(v):
    return [x.strip() for x in str(v).split(",") if x.strip() not in BAD]


def counts(series):
    return Counter(x for v in series.dropna() for x in split(v))


def filter_df(df, nutri=(), nova=(), risk=(), support=(), countries=(), states=(), text="", foods=(), hindi=(), marathi=()):
    m = pd.Series(True, index=df.index)
    if foods: m &= df["Food Name"].isin(foods)
    if hindi: m &= df["Hindi Name"].isin(hindi)
    if marathi: m &= df["Marathi Name"].isin(marathi)
    if nutri: m &= df["Nutri-Score Grade"].isin(nutri)
    if nova: m &= df["NOVA Group"].isin(nova)
    if risk: m &= df["Risk Group"].isin(risk)
    if support: m &= df[SUPPORT].isin(support)
    if countries: m &= df["Top 3 Producing Countries"].map(lambda v: bool(set(split(v)) & set(countries)))
    if states: m &= df["Top 3 Producing Indian States"].map(lambda v: bool(set(split(v)) & set(states)))
    if text:
        t = df.drop(columns=EXTRA).astype(str)
        m &= t.apply(lambda s: s.str.contains(text, case=False, regex=False)).any(axis=1)
    return df[m]


def export_view(d):
    return d.drop(columns=EXTRA)


def to_csv_bytes(d):
    return export_view(d).to_csv(index=False).encode("utf-8-sig")


def to_excel_bytes(d):
    b = io.BytesIO()
    export_view(d).to_excel(b, index=False, engine="openpyxl")
    return b.getvalue()


@st.cache_data
def state_centroids():
    """Label position for each Indian state = centre of its bounding box."""
    out = {}
    def pts(c):
        return [p for x in c for p in pts(x)] if isinstance(c[0][0], (list, tuple)) else list(c)
    for f in geojson()["features"]:
        p = pts(f["geometry"]["coordinates"]); xs, ys = [a[0] for a in p], [a[1] for a in p]
        out[f["properties"]["state"]] = ((min(ys) + max(ys)) / 2, (min(xs) + max(xs)) / 2)
    return out


def loc_info(d, col, n=6):
    """{location: (food count, 'a, b, c…')} for the Top-3 columns."""
    acc = {}
    for name, v in zip(d["Food Name"], d[col]):
        for loc in split(v): acc.setdefault(loc, []).append(name)
    return {k: (len(v), ", ".join(v[:n]) + ("…" if len(v) > n else "")) for k, v in acc.items()}
