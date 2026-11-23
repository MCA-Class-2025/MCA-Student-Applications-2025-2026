"""Spatial statistics implemented with NumPy/SciPy/scikit-learn.

Distances are great-circle (haversine) distances, which is the appropriate measure for
a global dataset (a single projected CRS would distort a worldwide study area). Where a
planar projection is required (study-area size, standard deviational ellipse) a
Lambert azimuthal equal-area projection centred on the data centroid is used.
Moran's I / LISA / Gi* are computed on grid cells (mean log10 value per cell) so that
densely sampled sites do not dominate and replicated points do not create pseudo-replication.
"""
import numpy as np
import pandas as pd
from scipy import sparse, stats
from scipy.spatial import ConvexHull, cKDTree
from sklearn.neighbors import BallTree

R = 6371.0088
MIN_CELLS = 30


def cell_table(d, cell_deg=2.0):
    """Mean log10(value) per cell for ONE unit (d must already be unit-specific)."""
    d = d[d.log_value.notna()]
    if d.empty:
        return pd.DataFrame(columns=["lat", "lon", "x", "n"])
    cy = np.floor((d.lat + 90) / cell_deg).astype(int)
    cx = np.floor((d.lon + 180) / cell_deg).astype(int)
    g = d.assign(cy=cy, cx=cx).groupby(["cy", "cx"])
    t = g.agg(lat=("lat", "mean"), lon=("lon", "mean"), x=("log_value", "mean"), n=("lat", "size"))
    return t.reset_index(drop=True)


def _knn(lat, lon, k):
    pts = np.radians(np.c_[lat, lon])
    dist, idx = BallTree(pts, metric="haversine").query(pts, k=k + 1)
    return idx[:, 1:], dist[:, 1:] * R


def _w_rowstd(idx):
    n, k = idx.shape
    return sparse.csr_matrix((np.full(n * k, 1.0 / k), (np.repeat(np.arange(n), k), idx.ravel())), shape=(n, n))


def prepare(cells, k):
    n = len(cells)
    if n < MIN_CELLS:
        return {"ok": False, "reason": f"Only {n} grid cells with valid values (minimum {MIN_CELLS}). Widen the filters or use a smaller cell size."}
    if cells["x"].std() == 0:
        return {"ok": False, "reason": "All cell values are identical; spatial autocorrelation is undefined."}
    k = int(min(k, n - 1))
    idx, _ = _knn(cells.lat.values, cells.lon.values, k)
    return {"ok": True, "idx": idx, "k": k, "W": _w_rowstd(idx), "n": n}


def global_moran(cells, k=8, perms=999, seed=1):
    p = prepare(cells, k)
    if not p["ok"]:
        return p
    x = cells.x.values.astype(float)
    z = x - x.mean()
    W, n = p["W"], p["n"]
    den = z @ z
    I = float(z @ (W @ z) / den)
    rng = np.random.default_rng(seed)
    sim = np.array([(zp @ (W @ zp)) / den for zp in (rng.permutation(z) for _ in range(perms))])
    mu, sd = sim.mean(), sim.std(ddof=1)
    zs = (I - mu) / sd
    c = int((np.abs(sim - mu) >= abs(I - mu)).sum())
    return {"ok": True, "I": I, "E_I": -1 / (n - 1), "z": float(zs), "p": (c + 1) / (perms + 1),
            "n": n, "k": p["k"], "perms": perms, "lag": W @ z, "zval": z}


def local_moran(cells, k=8, perms=499, seed=2, alpha=0.05):
    p = prepare(cells, k)
    if not p["ok"]:
        return p
    x = cells.x.values.astype(float)
    z = (x - x.mean()) / x.std()
    idx, n = p["idx"], p["n"]
    lag = z[idx].mean(1)
    Ii = z * lag
    rng = np.random.default_rng(seed)
    ge = np.zeros(n)
    done, chunk = 0, 50
    ar = np.arange(n)[None, :, None]
    while done < perms:
        m = min(chunk, perms - done)
        j = rng.integers(0, n - 1, size=(m, n, p["k"]))
        j = j + (j >= ar)                                   # exclude the focal cell
        Ip = z[None, :] * z[j].mean(-1)
        ge += np.where(Ii >= 0, (Ip >= Ii).sum(0), (Ip <= Ii).sum(0))
        done += m
    pv = (ge + 1) / (perms + 1)
    quad = np.where(z > 0, np.where(lag > 0, "High-High", "High-Low"),
                    np.where(lag > 0, "Low-High", "Low-Low"))
    quad = np.where(pv < alpha, quad, "Not significant")
    out = cells.copy()
    out["z"], out["lag"], out["Ii"], out["p"], out["cluster"] = z, lag, Ii, pv, quad
    return {"ok": True, "cells": out, "alpha": alpha, "perms": perms, "k": p["k"]}


def getis_ord(cells, k=8, alpha=0.05):
    """Gi* (self included, binary KNN weights), analytic z-scores, plus Benjamini-Hochberg FDR."""
    n = len(cells)
    if n < MIN_CELLS:
        return {"ok": False, "reason": f"Only {n} grid cells with valid values (minimum {MIN_CELLS})."}
    x = cells.x.values.astype(float)
    S = x.std()
    if S == 0:
        return {"ok": False, "reason": "All cell values are identical; Gi* is undefined."}
    k = int(min(k, n - 1))
    idx, _ = _knn(cells.lat.values, cells.lon.values, k)
    Wi = k + 1
    s = x + x[idx].sum(1)
    z = (s - x.mean() * Wi) / (S * np.sqrt((n * Wi - Wi ** 2) / (n - 1)))
    p = 2 * stats.norm.sf(np.abs(z))
    order = np.argsort(p)
    q = np.empty(n)
    q[order] = np.minimum.accumulate((p[order] * n / (np.arange(n) + 1))[::-1])[::-1]
    out = cells.copy()
    out["gi_z"], out["p"], out["p_fdr"] = z, p, np.minimum(q, 1)
    out["class"] = np.where(out.p_fdr < alpha, np.where(z > 0, "Hotspot", "Coldspot"), "Not significant")
    out["class_raw"] = np.where(out.p < alpha, np.where(z > 0, "Hotspot (unadjusted)", "Coldspot (unadjusted)"), "Not significant")
    return {"ok": True, "cells": out, "alpha": alpha, "k": k}


# ---------- projection helpers -------------------------------------------------------------
def _laea(lat, lon, lat0, lon0):
    la, lo, la0, lo0 = map(np.radians, (lat, lon, lat0, lon0))
    kp = np.sqrt(2 / (1 + np.sin(la0) * np.sin(la) + np.cos(la0) * np.cos(la) * np.cos(lo - lo0)))
    x = R * kp * np.cos(la) * np.sin(lo - lo0)
    y = R * kp * (np.cos(la0) * np.sin(la) - np.sin(la0) * np.cos(la) * np.cos(lo - lo0))
    return x, y


def _laea_inv(x, y, lat0, lon0):
    la0, lo0 = np.radians(lat0), np.radians(lon0)
    rho = np.hypot(x, y)
    c = 2 * np.arcsin(np.clip(rho / (2 * R), -1, 1))
    rho = np.where(rho == 0, 1e-9, rho)
    lat = np.arcsin(np.cos(c) * np.sin(la0) + y * np.sin(c) * np.cos(la0) / rho)
    lon = lo0 + np.arctan2(x * np.sin(c), rho * np.cos(la0) * np.cos(c) - y * np.sin(la0) * np.sin(c))
    return np.degrees(lat), (np.degrees(lon) + 180) % 360 - 180


def _centre(lat, lon):
    la, lo = np.radians(lat), np.radians(lon)
    v = np.c_[np.cos(la) * np.cos(lo), np.cos(la) * np.sin(lo), np.sin(la)].mean(0)
    return float(np.degrees(np.arctan2(v[2], np.hypot(v[0], v[1])))), float(np.degrees(np.arctan2(v[1], v[0])))


def nearest_neighbour(df):
    """Clark-Evans nearest-neighbour index on UNIQUE sampling locations."""
    u = df.drop_duplicates("loc_key")
    n = len(u)
    if n < 20:
        return {"ok": False, "reason": f"Only {n} unique locations (minimum 20)."}
    lat, lon = u.lat.values, u.lon.values
    _, d = _knn(lat, lon, 1)
    nn = d[:, 0]
    lat0, lon0 = _centre(lat, lon)
    x, y = _laea(lat, lon, lat0, lon0)
    try:
        A = ConvexHull(np.c_[x, y]).volume
    except Exception:
        return {"ok": False, "reason": "Locations are collinear; study-area cannot be computed."}
    exp = 0.5 / np.sqrt(n / A)
    se = 0.26136 / np.sqrt(n * n / A)
    z = (nn.mean() - exp) / se
    return {"ok": True, "n": n, "mean_nn_km": float(nn.mean()), "median_nn_km": float(np.median(nn)),
            "expected_km": float(exp), "R": float(nn.mean() / exp), "z": float(z),
            "p": float(2 * stats.norm.sf(abs(z))), "area_km2": float(A), "nn": nn}


def std_ellipse(df):
    """Standard deviational ellipse (1 SD) in a local equal-area projection."""
    n = len(df)
    if n < 10:
        return {"ok": False, "reason": f"Only {n} points (minimum 10)."}
    lat0, lon0 = _centre(df.lat.values, df.lon.values)
    x, y = _laea(df.lat.values, df.lon.values, lat0, lon0)
    mx, my = x.mean(), y.mean()
    cov = np.cov(np.c_[x - mx, y - my].T, bias=True)
    ev, evec = np.linalg.eigh(cov)
    a, b = np.sqrt(2 * ev[1]), np.sqrt(2 * ev[0])           # SDE axes (major, minor)
    major = evec[:, 1]
    ang = float((np.degrees(np.arctan2(major[0], major[1]))) % 180)  # bearing clockwise from north
    t = np.linspace(0, 2 * np.pi, 120)
    ex = mx + a * np.cos(t) * major[0] + b * np.sin(t) * evec[0, 0]
    ey = my + a * np.cos(t) * major[1] + b * np.sin(t) * evec[1, 0]
    elat, elon = _laea_inv(ex, ey, lat0, lon0)
    clat, clon = _laea_inv(np.array([mx]), np.array([my]), lat0, lon0)
    return {"ok": True, "n": n, "centre_lat": float(clat[0]), "centre_lon": float(clon[0]),
            "major_km": float(a), "minor_km": float(b), "rotation_deg": ang,
            "ratio": float(b / a), "poly_lat": elat, "poly_lon": elon}
