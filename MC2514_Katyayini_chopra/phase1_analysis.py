import pandas as pd
import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt

BASE = Path(__file__).resolve().parent
DATA_FILE = BASE / "data" / "fixai_fused_dataset.csv"
OUT_DIR = BASE / "analysis"
OUT_DIR.mkdir(exist_ok=True)

df = pd.read_csv(DATA_FILE)

print("=" * 70)
print("FIXAI PHASE 1 — DATA QUALITY + EDA")
print("=" * 70)

print(f"\nDataset shape: {df.shape[0]} rows x {df.shape[1]} columns")

# ---------------------------------------------------------
# STRUCTURAL CHECKS
# ---------------------------------------------------------
structural = pd.DataFrame({
    "check": [
        "rows",
        "columns",
        "duplicate_rows",
        "duplicate_service_types",
    ],
    "value": [
        len(df),
        len(df.columns),
        int(df.duplicated().sum()),
        int(df["service_type"].duplicated().sum()) if "service_type" in df.columns else None,
    ]
})
structural.to_csv(OUT_DIR / "structural_checks.csv", index=False)

print("\nData types:")
print(df.dtypes.to_string())

# ---------------------------------------------------------
# MISSING VALUES
# ---------------------------------------------------------
missing = pd.DataFrame({
    "attribute": df.columns,
    "missing_values": [int(df[c].isna().sum()) for c in df.columns],
})
missing["missing_percentage"] = (missing["missing_values"] / len(df) * 100).round(2)
missing = missing.sort_values("missing_percentage", ascending=False)
missing.to_csv(OUT_DIR / "missing_values.csv", index=False)

print("\nMissing values:")
print(missing[missing["missing_values"] > 0].to_string(index=False))

# ---------------------------------------------------------
# CATEGORICAL CONSISTENCY
# ---------------------------------------------------------
categorical_rows = []
for c in df.select_dtypes(include=["object"]).columns:
    vals = df[c].dropna().astype(str).str.strip()
    categorical_rows.append({
        "attribute": c,
        "unique_values": vals.nunique(),
        "blank_values": int((vals == "").sum()),
        "example_values": " | ".join(vals.drop_duplicates().head(10).tolist())
    })

pd.DataFrame(categorical_rows).to_csv(
    OUT_DIR / "categorical_consistency.csv", index=False
)

# ---------------------------------------------------------
# OUTLIERS — IQR
# ---------------------------------------------------------
numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()

outlier_rows = []

for c in numeric_cols:
    s = df[c].dropna()

    if len(s) < 4:
        continue

    q1 = s.quantile(0.25)
    q3 = s.quantile(0.75)
    iqr = q3 - q1

    if iqr == 0:
        lower = q1
        upper = q3
    else:
        lower = q1 - 1.5 * iqr
        upper = q3 + 1.5 * iqr

    count = int(((s < lower) | (s > upper)).sum())

    outlier_rows.append({
        "attribute": c,
        "q1": q1,
        "q3": q3,
        "iqr": iqr,
        "lower_bound": lower,
        "upper_bound": upper,
        "outlier_count": count
    })

outliers = pd.DataFrame(outlier_rows)
outliers.to_csv(OUT_DIR / "outlier_report.csv", index=False)

print("\nOutlier report:")
print(outliers.to_string(index=False))

# ---------------------------------------------------------
# NUMERICAL SUMMARY
# ---------------------------------------------------------
summary = df[numeric_cols].describe().T.reset_index()
summary = summary.rename(columns={"index": "attribute"})
summary.to_csv(OUT_DIR / "numerical_summary.csv", index=False)

print("\nNumerical summary:")
print(summary.to_string(index=False))

# ---------------------------------------------------------
# SERVICE SUMMARY
# ---------------------------------------------------------
if "service_type" in df.columns:
    service_summary = (
        df.groupby("service_type")
        .size()
        .reset_index(name="record_count")
        .sort_values("record_count", ascending=False)
    )
    service_summary.to_csv(
        OUT_DIR / "service_type_summary.csv",
        index=False
    )

# ---------------------------------------------------------
# CHART 1 — MISSING VALUES
# ---------------------------------------------------------
m = missing[missing["missing_values"] > 0]

if not m.empty:
    plt.figure(figsize=(10, 5))
    plt.bar(m["attribute"], m["missing_percentage"])
    plt.xticks(rotation=75, ha="right")
    plt.ylabel("Missing values (%)")
    plt.title("Missing Values in Fused Dataset")
    plt.tight_layout()
    plt.savefig(OUT_DIR / "01_missing_values.png", dpi=160)
    plt.close()

# ---------------------------------------------------------
# CHART 2 — TEMPERATURE
# ---------------------------------------------------------
temperature_candidates = [
    "weather_temperature",
    "temperature",
    "weather_temp"
]

temperature_col = next(
    (c for c in temperature_candidates if c in df.columns),
    None
)

if temperature_col and df[temperature_col].notna().any():
    plt.figure(figsize=(8, 5))
    df[temperature_col].dropna().plot(kind="hist", bins=8)
    plt.xlabel("Temperature")
    plt.title("Temperature Distribution")
    plt.tight_layout()
    plt.savefig(OUT_DIR / "02_temperature_distribution.png", dpi=160)
    plt.close()

# ---------------------------------------------------------
# CHART 3 — HUMIDITY
# ---------------------------------------------------------
humidity_col = next(
    (c for c in ["weather_humidity", "humidity"] if c in df.columns),
    None
)

if humidity_col and df[humidity_col].notna().any():
    plt.figure(figsize=(8, 5))
    df[humidity_col].dropna().plot(kind="hist", bins=8)
    plt.xlabel("Humidity (%)")
    plt.title("Humidity Distribution")
    plt.tight_layout()
    plt.savefig(OUT_DIR / "03_humidity_distribution.png", dpi=160)
    plt.close()

# ---------------------------------------------------------
# CHART 4 — PROFESSIONAL RATING
# ---------------------------------------------------------
rating_col = next(
    (c for c in ["professional_rating", "rating"] if c in df.columns),
    None
)

if rating_col and df[rating_col].notna().any():
    plt.figure(figsize=(8, 5))
    df[rating_col].dropna().plot(kind="hist", bins=8)
    plt.xlabel("Professional Rating")
    plt.title("Professional Rating Distribution")
    plt.tight_layout()
    plt.savefig(OUT_DIR / "04_professional_rating_distribution.png", dpi=160)
    plt.close()

# ---------------------------------------------------------
# CHART 5 — BIVARIATE: HUMIDITY VS RAINFALL
# ---------------------------------------------------------
rain_col = next(
    (c for c in ["weather_daily_rainfall", "weather_rainfall", "rainfall"] if c in df.columns),
    None
)

if humidity_col and rain_col:
    tmp = df[[humidity_col, rain_col]].dropna()

    if len(tmp) >= 2 and tmp[humidity_col].nunique() > 1 and tmp[rain_col].nunique() > 1:
        plt.figure(figsize=(8, 5))
        plt.scatter(tmp[humidity_col], tmp[rain_col])
        plt.xlabel("Humidity (%)")
        plt.ylabel("Rainfall")
        plt.title("Humidity vs Rainfall")
        plt.tight_layout()
        plt.savefig(OUT_DIR / "05_humidity_vs_rainfall.png", dpi=160)
        plt.close()

# ---------------------------------------------------------
# CHART 6 — BIVARIATE: RATING VS EXPERIENCE
# ---------------------------------------------------------
experience_col = next(
    (c for c in ["professional_experience", "experience"] if c in df.columns),
    None
)

if rating_col and experience_col:
    tmp = df[[rating_col, experience_col]].dropna()

    if len(tmp) >= 2 and tmp[rating_col].nunique() > 1 and tmp[experience_col].nunique() > 1:
        plt.figure(figsize=(8, 5))
        plt.scatter(tmp[experience_col], tmp[rating_col])
        plt.xlabel("Professional Experience (years)")
        plt.ylabel("Professional Rating")
        plt.title("Professional Experience vs Rating")
        plt.tight_layout()
        plt.savefig(OUT_DIR / "06_experience_vs_rating.png", dpi=160)
        plt.close()

# ---------------------------------------------------------
# MULTIVARIATE CORRELATION
# ---------------------------------------------------------
corr_cols = []

preferred = [
    "weather_temperature",
    "weather_humidity",
    "weather_precipitation",
    "weather_daily_rainfall",
    "weather_daily_max_temperature",
    "weather_daily_min_temperature",
    "air_pm2_5",
    "air_pm10",
    "air_us_aqi",
    "professional_rating",
    "professional_experience"
]

for c in preferred:
    if c in df.columns and pd.api.types.is_numeric_dtype(df[c]):
        if df[c].notna().sum() >= 2 and df[c].nunique(dropna=True) > 1:
            corr_cols.append(c)

if len(corr_cols) >= 2:
    corr = df[corr_cols].corr()

    corr.to_csv(
        OUT_DIR / "correlation_matrix.csv"
    )

    fig, ax = plt.subplots(figsize=(10, 8))
    matrix = corr.to_numpy()
    image = ax.imshow(matrix, aspect="auto")
    ax.set_xticks(range(len(corr_cols)))
    ax.set_yticks(range(len(corr_cols)))
    ax.set_xticklabels(corr_cols, rotation=75, ha="right")
    ax.set_yticklabels(corr_cols)
    ax.set_title("Correlation Heatmap — Fused Dataset")
    fig.colorbar(image, ax=ax)
    fig.tight_layout()
    fig.savefig(OUT_DIR / "07_correlation_heatmap.png", dpi=160)
    plt.close()

print("\nEDA files and charts saved in:")
print(OUT_DIR)

print("\nDONE.")


# matrices, dashboard, 6 algoo,