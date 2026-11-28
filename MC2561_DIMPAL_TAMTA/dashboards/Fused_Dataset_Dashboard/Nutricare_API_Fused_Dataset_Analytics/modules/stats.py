"""Statistical tables for the Statistics & Data Explorer page."""
import numpy as np
import pandas as pd
from .data import EXTRA, GLOB, IND, NUTR, SHARE


def describe_table(d):
    x = d[NUTR + [GLOB, IND, SHARE]]
    t = x.describe().T
    t["median"] = x.median(); t["skew"] = x.skew(); t["kurtosis"] = x.kurt()
    t["cv_pct"] = (x.std() / x.mean() * 100).replace([np.inf, -np.inf], np.nan)
    t["missing"] = x.isna().sum()
    return t.round(2).reset_index().rename(columns={"index": "column"})


def missing_table(d):
    c = d.drop(columns=EXTRA)
    m = c.isna().sum().rename("Missing").reset_index()
    m.columns = ["Column", "Missing"]
    m["% Missing"] = (m["Missing"] / max(len(c), 1) * 100).round(2)
    return m


def duplicates(d):
    c = d.drop(columns=EXTRA)
    return c[c.duplicated(keep=False)], c[c["Food Name"].duplicated(keep=False)].sort_values("Food Name")


def outliers(d, z=3.0):
    x = d[NUTR]
    zs = (x - x.mean()) / x.std()
    rows = [(n, int((zs[n].abs() > z).sum())) for n in NUTR]
    return pd.DataFrame(rows, columns=["Nutrient", f"|z| > {z:g}"])


def quality_report(q, n_filtered):
    items = [("Rows in file", q["rows"]), ("Rows in current filter", n_filtered), ("Columns (source)", q["cols"] - 2),
             ("Rows with any missing value", q["rows_missing"]), ("Missing cells", q["missing_cells"]),
             ("Fully duplicated rows", q["dup_rows"]), ("Repeated Food Names", q["dup_names"]),
             ("Top country 'Unknown'", q["unknown_country"]), ("'Not produced in India'", q["not_in_india"]),
             ("Nutri-Score '-' (not scored)", q["no_score"]), ("Zero-calorie foods", q["zero_cal"]),
             ("Rows with an Assumption note", q["assumptions"]), ("Missing image URLs", q["no_image"])]
    return pd.DataFrame(items, columns=["Check", "Value"])
