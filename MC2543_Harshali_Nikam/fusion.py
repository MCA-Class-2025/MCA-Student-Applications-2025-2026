from pathlib import Path
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler

PROCESSED_DIR = Path("data/processed")
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

def load_data():
    path = PROCESSED_DIR / "fused_dataset.csv"
    if not path.exists():
        raise FileNotFoundError("Run: python collect_data.py first")
    return pd.read_csv(path, parse_dates=["time"])

def clean_data(df):
    df = df.copy()

    numeric_cols = [
        "temperature_2m", "relative_humidity_2m", "precipitation",
        "wind_speed_10m", "pm2_5", "pm10",
        "nitrogen_dioxide", "ozone", "lat", "lon",
        "population", "gdp_usd", "urban_population_pct", "usd_to_local"
    ]

    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
            df[col] = df[col].replace([np.inf, -np.inf], np.nan)
            df[col] = df[col].fillna(df[col].median())

    return df

def add_features(df):
    df = df.copy()

    # Derived features: feature engineering before feature fusion.
    df["temp_humidity_interaction"] = (
        df["temperature_2m"] * df["relative_humidity_2m"] / 100.0
    )
    df["pollution_index"] = (
        0.45 * df["pm2_5"] +
        0.30 * df["pm10"] +
        0.15 * df["nitrogen_dioxide"] +
        0.10 * df["ozone"]
    )

    # Day/hour features
    df["hour"] = df["time"].dt.hour
    df["day_of_week"] = df["time"].dt.dayofweek

    return df

def feature_fusion(df):
    """
    Feature Fusion:
    Combine numerical features originating from Weather, Air Quality,
    World Bank, REST Countries/currency metadata and geographic data
    into one standardized feature matrix.
    """
    feature_cols = [
        "temperature_2m",
        "relative_humidity_2m",
        "precipitation",
        "wind_speed_10m",
        "pm10",
        "nitrogen_dioxide",
        "ozone",
        "lat",
        "lon",
        "population",
        "gdp_usd",
        "urban_population_pct",
        "usd_to_local",
        "temp_humidity_interaction",
        "hour",
        "day_of_week",
    ]

    X = df[feature_cols].copy()

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    X_scaled = pd.DataFrame(X_scaled, columns=feature_cols, index=df.index)
    X_scaled.to_csv(PROCESSED_DIR / "feature_fusion_matrix.csv", index=False)

    return X_scaled, scaler, feature_cols

def run_fusion_pipeline():
    df = load_data()
    df = clean_data(df)
    df = add_features(df)
    X_scaled, scaler, feature_cols = feature_fusion(df)

    df.to_csv(PROCESSED_DIR / "cleaned_dataset.csv", index=False)

    return df, X_scaled, scaler, feature_cols

if __name__ == "__main__":
    df, X, _, cols = run_fusion_pipeline()
    print("Feature Fusion complete.")
    print("Rows:", len(df))
    print("Features:", len(cols))
    print("Saved:", PROCESSED_DIR / "feature_fusion_matrix.csv")
