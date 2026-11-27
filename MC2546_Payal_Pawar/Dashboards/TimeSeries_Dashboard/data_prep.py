"""Generate a realistic synthetic daily retail time-series dataset -> data.xlsx"""
import numpy as np, pandas as pd

def build(seed=42):
    rng = np.random.default_rng(seed)
    days = pd.date_range("2023-01-01", "2026-10-31", freq="D")
    stores = {"Mumbai": 1.25, "Delhi": 1.10, "Bengaluru": 1.00}
    cats = {"Electronics": 1.5, "Grocery": 1.0, "Fashion": 0.8, "Home": 0.6}
    rows = []
    t = np.arange(len(days))
    weekly = np.array([0.90, 0.88, 0.92, 0.97, 1.08, 1.25, 1.20])[days.dayofweek]
    annual = np.asarray(1 + 0.18 * np.sin(2 * np.pi * (days.dayofyear - 80) / 365.25))
    festive = np.where((days.month == 10) & (days.day >= 10), 1.35, 1) * np.where((days.month == 11) & (days.day <= 15), 1.30, 1) \
              * np.where((days.month == 12) & (days.day >= 20), 1.15, 1)
    for s, sm in stores.items():
        for c, cm in cats.items():
            trend = 1 + 0.0007 * t * (1.2 if c == "Electronics" else 1)
            promo = (rng.random(len(days)) < 0.07).astype(int)
            base = 20000 * sm * cm * trend * weekly * annual * festive * (1 + 0.28 * promo)
            rev = np.asarray(base * rng.normal(1, 0.06, len(days)))
            idx = rng.choice(len(days), 6, replace=False)          # injected anomalies
            rev[idx] *= rng.choice([0.45, 1.7], 6)
            aov = np.asarray(650 * cm * rng.normal(1, 0.04, len(days)))
            temp = 27 + 7 * np.sin(2 * np.pi * (days.dayofyear - 100) / 365.25) + rng.normal(0, 1.5, len(days))
            rows.append(pd.DataFrame({"date": days, "store": s, "category": c, "revenue": rev.round(0),
                "orders": (rev / aov).round(0), "avg_order_value": aov.round(1), "promo": promo, "temperature_c": temp.round(1)}))
    return pd.concat(rows, ignore_index=True)

if __name__ == "__main__":
    df = build(); df.to_excel("data.xlsx", index=False, sheet_name="Fused")
    print(f"data.xlsx written: {df.shape[0]:,} rows, {df.date.min().date()} -> {df.date.max().date()}")
