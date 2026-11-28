"""Rule-based insights. Every sentence is computed from the filtered data - nothing is hard-coded."""
from collections import OrderedDict
import numpy as np
from config.settings import NOT_RECORDED, DEFAULT_UNIT
from modules import calculations as calc, spatial_statistics as ss, spatial_analysis as sa


def run_spatial(df, unit, cell=2.0, k=8, perms=499):
    d = calc.unit_subset(df, unit)
    cells = ss.cell_table(d, cell)
    return {"unit": unit, "cells": cells, "n": len(d),
            "moran": ss.global_moran(cells, k, perms), "lisa": ss.local_moran(cells, k, min(perms, 299)),
            "gi": ss.getis_ord(cells, k), "nn": ss.nearest_neighbour(d), "sde": ss.std_ellipse(d),
            "cell": cell, "k": k}


def _top(df, col, n=3):
    s = df.loc[df[col] != NOT_RECORDED, col].value_counts()
    tot = len(df)
    return [(i, int(v), 100 * v / tot) for i, v in s.head(n).items()]


def _fmt(items):
    return ", ".join(f"{a} ({b:,} records, {c:.1f}%)" for a, b, c in items)


def build_insights(df, quality, spatial=None):
    S = OrderedDict()
    n = len(df)
    k = calc.kpis(df)
    yrs = df.year.dropna()
    S["Executive Summary"] = [
        f"The selection contains {n:,} sampling records at {df.loc_key.nunique():,} distinct coordinates, collected between {int(yrs.min())} and {int(yrs.max())}." if len(yrs) else f"The selection contains {n:,} sampling records.",
        f"Records with a stated country cover {k['countries']} countries; {k['countries_missing_pct']}% of records have no country and are excluded from country comparisons.",
        f"{k['oceans']} oceans are represented. {k['top_ocean']} has the highest sampling coverage ({k['top_ocean_pct']}% of records).",
        "Measurements use " + str(df.unit.nunique()) + " different units (" + ", ".join(sorted(df.unit.unique())) + "); they are analysed separately and never averaged together.",
    ]
    g = []
    for col, lab in [("ocean", "oceans"), ("country", "countries"), ("region", "regions")]:
        t = _top(df, col)
        if t:
            g.append(f"Most sampled {lab}: {_fmt(t)}.")
    lat = df.lat
    g.append(f"Latitudes range from {lat.min():.1f}° to {lat.max():.1f}°; {100 * (lat > 0).mean():.1f}% of records are in the Northern Hemisphere and {100 * (lat.abs() < 23.5).mean():.1f}% lie in the tropics.")
    S["Geographic Findings"] = g
    S["Regional Findings"] = _regional(df)
    S["Concentration Findings"] = _concentration(df)
    S["Spatial Findings"], S["Statistical Findings"] = _spatial(df, spatial)
    q = quality
    dq = [f"{q['duplicate_records']:,} records are exact duplicates of another record apart from their IDs (flagged, not removed).",
          f"{q['invalid_coordinates_removed']} records had invalid coordinates and were removed before analysis."]
    for kname, (cnt, pct) in q["missing"].items():
        if cnt:
            dq.append(f"Missing {kname}: {cnt:,} records ({pct}%).")
    dq.append("Records without country, region or ocean values are excluded only from analyses that need them; no values were imputed or guessed.")
    S["Data Quality Findings"] = dq
    S["Conclusion"] = _conclusion(df, k, spatial)
    return S


def _regional(df):
    out = []
    rec = df[df.region != NOT_RECORDED]
    if rec.empty:
        return ["No region information is available in the current selection."]
    out.append(f"{rec.region.nunique()} named regions are present, covering {100 * len(rec) / len(df):.1f}% of records.")
    for u in calc.available_units(rec)[:3]:
        d = calc.unit_subset(rec, u)
        gs = calc.group_stats(d[d.value > 0], "region", 50)
        gs = gs[gs.n >= 20]
        if len(gs) >= 2:
            hi, lo = gs.sort_values("median").iloc[-1], gs.sort_values("median").iloc[0]
            out.append(f"For {u} (regions with at least 20 records): highest median in {hi.region} ({hi['median']:.4g}), lowest in {lo.region} ({lo['median']:.4g}). "
                       "Differences partly reflect methods and survey design.")
    return out


def _concentration(df):
    out = []
    for u in calc.available_units(df):
        d = calc.unit_subset(df, u)
        if d.empty:
            continue
        v = d.value
        out.append(f"{u}: {len(d):,} records; median {v.median():.4g}, mean {v.mean():.4g}, maximum {v.max():.4g}; {100 * (v == 0).mean():.1f}% are zero values.")
        cc = d.conc_class.value_counts(normalize=True)
        if len(cc):
            out.append(f"{u}: most common concentration class is '{cc.index[0]}' ({100 * cc.iloc[0]:.1f}% of its records).")
        sm = calc.group_stats(d[d.value > 0], "setting", 6)
        sm = sm[sm.n >= 20]
        if len(sm) >= 2:
            s2 = sm.sort_values("median")
            out.append(f"{u}: median by marine setting ranges from {s2.iloc[0]['median']:.4g} ({s2.iloc[0].setting}) to {s2.iloc[-1]['median']:.4g} ({s2.iloc[-1].setting}).")
    return out or ["No measurements in the current selection."]


def _spatial(df, sp):
    spat, stat = [], []
    db = sa.dbscan_clusters(df, 100, 10)
    if db is not None and (db.cluster >= 0).any():
        nc = db.cluster.max() + 1
        big = db[db.cluster >= 0].cluster.value_counts()
        spat.append(f"DBSCAN (radius 100 km, minimum 10 records) finds {nc} geographic sampling clusters; the largest holds {big.iloc[0]:,} records. {100 * (db.cluster < 0).mean():.1f}% of records are isolated (noise).")
    else:
        spat.append("DBSCAN found no clusters with a 100 km radius and a minimum of 10 records.")
    spat.append("Clusters of records describe sampling EFFORT; they are not evidence of pollution hotspots.")
    if sp is None:
        return spat, ["Spatial statistics were not computed for this selection."]
    u = sp["unit"]
    gi = sp["gi"]
    if gi["ok"]:
        c = gi["cells"]["class"].value_counts()
        spat.append(f"Getis-Ord Gi* on {u} ({sp['cell']}° cells, FDR-adjusted): {c.get('Hotspot', 0)} statistically significant hotspot cells and {c.get('Coldspot', 0)} coldspot cells out of {len(gi['cells']):,}.")
        stat.append(f"Gi* hotspot/coldspot counts above use Benjamini-Hochberg FDR at 5%; without adjustment {int((gi['cells'].p < .05).sum())} cells are individually significant.")
    else:
        spat.append(f"Gi* not computed: {gi['reason']}")
    m = sp["moran"]
    if m["ok"]:
        p = "p < " + f"{1 / (m['perms'] + 1):.3f}" if m["p"] <= 1 / (m["perms"] + 1) + 1e-12 else f"p = {m['p']:.3f}"
        stat.append(f"Global Moran's I for mean log10 {u} per {sp['cell']}° cell: I = {m['I']:.3f} (expected {m['E_I']:.3f}), z = {m['z']:.1f}, {p} ({m['perms']} permutations, k = {m['k']}, n = {m['n']} cells) - "
                    + ("significant positive spatial autocorrelation: nearby cells tend to have similar values." if m["p"] < .05 and m["I"] > 0 else "significant negative autocorrelation." if m["p"] < .05 else "no significant spatial autocorrelation."))
    else:
        stat.append(f"Global Moran's I not computed: {m['reason']}")
    l = sp["lisa"]
    if l["ok"]:
        c = l["cells"]["cluster"].value_counts()
        stat.append(f"Local Moran's I (LISA, p < 0.05, unadjusted): High-High {c.get('High-High', 0)}, Low-Low {c.get('Low-Low', 0)}, High-Low {c.get('High-Low', 0)}, Low-High {c.get('Low-High', 0)} cells.")
    nn = sp["nn"]
    if nn["ok"]:
        stat.append(f"Nearest-neighbour analysis of {nn['n']:,} unique locations: mean distance {nn['mean_nn_km']:.1f} km versus {nn['expected_km']:.1f} km expected under randomness (R = {nn['R']:.2f}); "
                    + ("locations are more clustered than random, reflecting survey design." if nn["R"] < 1 else "locations are not more clustered than random."))
    e = sp["sde"]
    if e["ok"]:
        stat.append(f"The standard deviational ellipse is centred near {e['centre_lat']:.1f}°, {e['centre_lon']:.1f}° with semi-axes {e['major_km']:,.0f} km and {e['minor_km']:,.0f} km.")
    return spat, stat or ["No spatial statistics could be computed."]


def _conclusion(df, k, sp):
    c = [f"The selected data describe {len(df):,} sampling records concentrated in {k['top_ocean']} ({k['top_ocean_pct']}% of records); coverage is geographically uneven."]
    if sp and sp["moran"]["ok"] and sp["moran"]["p"] < .05:
        c.append(f"Measured {sp['unit']} values show statistically significant spatial structure (Moran's I = {sp['moran']['I']:.2f}).")
    c.append("Findings describe the sampled locations only. Differences between regions mix real variation with differences in sampling method, mesh size, survey era and effort, and should not be read as global pollution estimates.")
    return c
