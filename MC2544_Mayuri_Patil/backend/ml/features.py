FEATURE_COLUMNS = [
    "age",
    "gender",
    "height",
    "weight",
    "ap_hi",
    "ap_lo",
    "cholesterol",
    "gluc",
    "smoke",
    "alco",
    "active",
]
TARGET_COLUMN = "cardio"
FUSION_KEY_COLUMN = "patient_id"

# These features fuse the raw data 
FUSED_FEATURE_COLUMNS = FEATURE_COLUMNS + [
    "bmi",
    "pulse_pressure",
    "mean_arterial_pressure",
]


def build_feature_frame(data):
    """Return raw clinical features combined with derived feature-level inputs."""
    missing_columns = set(FEATURE_COLUMNS).difference(data.columns)
    if missing_columns:
        raise ValueError(f"Missing clinical features: {sorted(missing_columns)}")

    fused = data.loc[:, FEATURE_COLUMNS].copy()
    height_in_metres = fused["height"] / 100
    fused["bmi"] = fused["weight"] / height_in_metres.pow(2)
    fused["pulse_pressure"] = fused["ap_hi"] - fused["ap_lo"]
    fused["mean_arterial_pressure"] = fused["ap_lo"] + fused["pulse_pressure"] / 3
    return fused.loc[:, FUSED_FEATURE_COLUMNS]


def build_keyed_fusion_frame(data):
    """Attach a unique patient key to the fused feature record."""
    if FUSION_KEY_COLUMN not in data.columns:
        raise ValueError(f"Missing fusion key: {FUSION_KEY_COLUMN}")
    if data[FUSION_KEY_COLUMN].isna().any() or data[FUSION_KEY_COLUMN].duplicated().any():
        raise ValueError("The fusion key must be present and unique for every patient record.")

    fused_features = build_feature_frame(data)
    return data.loc[:, [FUSION_KEY_COLUMN]].join(fused_features)
