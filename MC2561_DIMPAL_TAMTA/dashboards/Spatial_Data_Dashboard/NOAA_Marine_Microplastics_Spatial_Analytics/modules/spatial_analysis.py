"""Density, grid and clustering helpers (no Streamlit)."""
import numpy as np
import pandas as pd
from sklearn.cluster import DBSCAN
from sklearn.neighbors import KernelDensity

R_KM = 6371.0088


def grid_cells(df, cell_deg=2.0, value_col=None):
    """Aggregate points into square lat/lon cells. Returns one row per non-empty cell."""
    d = df.dropna(subset=["lat", "lon"]).copy()
    d["cy"] = np.floor((d.lat + 90) / cell_deg).astype(int)
    d["cx"] = np.floor((d.lon + 180) / cell_deg).astype(int)
    g = d.groupby(["cy", "cx"])
    out = g.agg(lat=("lat", "mean"), lon=("lon", "mean"), n=("lat", "size")).reset_index()
    if value_col is not None:
        v = g[value_col].agg(["mean", "median", "count"]).reset_index()
        v.columns = ["cy", "cx", f"{value_col}_mean", f"{value_col}_median", f"{value_col}_n"]
        out = out.merge(v, on=["cy", "cx"], how="left")
    return out


def dbscan_clusters(df, eps_km=100.0, min_samples=10):
    """DBSCAN on great-circle (haversine) distance. Label -1 = noise."""
    if len(df) < max(min_samples, 2):
        return None
    X = np.radians(df[["lat", "lon"]].to_numpy())
    lab = DBSCAN(eps=eps_km / R_KM, min_samples=min_samples, metric="haversine",
                 algorithm="ball_tree").fit_predict(X)
    out = df.copy()
    out["cluster"] = lab
    return out


def kde_grid(df, bandwidth_km=200.0, weights=None, step_deg=2.0, max_points=15000, seed=0):
    """Gaussian KDE with haversine metric, evaluated on a regular lat/lon grid
    covering the data extent. Returns DataFrame(lat, lon, density) or None."""
    if len(df) < 10:
        return None
    d = df
    w = None if weights is None else np.asarray(weights, float)
    if len(d) > max_points:
        idx = np.random.default_rng(seed).choice(len(d), max_points, replace=False)
        d = d.iloc[idx]
        w = None if w is None else w[idx]
    X = np.radians(d[["lat", "lon"]].to_numpy())
    kde = KernelDensity(bandwidth=bandwidth_km / R_KM, metric="haversine",
                        kernel="gaussian", algorithm="ball_tree", rtol=0.02)
    kde.fit(X, sample_weight=w)
    la0, la1 = max(d.lat.min() - step_deg, -90), min(d.lat.max() + step_deg, 90)
    lo0, lo1 = max(d.lon.min() - step_deg, -180), min(d.lon.max() + step_deg, 180)
    # keep grid size bounded
    while ((la1 - la0) / step_deg) * ((lo1 - lo0) / step_deg) > 12000:
        step_deg *= 1.5
    glat, glon = np.meshgrid(np.arange(la0, la1 + 1e-9, step_deg), np.arange(lo0, lo1 + 1e-9, step_deg))
    G = np.radians(np.c_[glat.ravel(), glon.ravel()])
    dens = np.exp(kde.score_samples(G))
    out = pd.DataFrame({"lat": glat.ravel(), "lon": glon.ravel(), "density": dens})
    cut = out.density.quantile(0.5)           # hide the empty/low background
    out = out[out.density > cut].copy()
    out["density"] = out.density / out.density.max()
    return out
