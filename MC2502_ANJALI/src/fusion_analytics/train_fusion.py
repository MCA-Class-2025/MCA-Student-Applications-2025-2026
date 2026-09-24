
"""
Train the two Fusion Analytics experiments:

1. RAW/DATA-LEVEL FUSION
   32x32 RGB raw pixels + 13 raw API-derived numerical/indicator values.

2. FEATURE-LEVEL FUSION
   MobileNetV2 visual embedding -> PCA 256 dimensions
   + the same 13 API-derived features.

Model fusion is intentionally NOT included.

Run from project root:
    python src/fusion_analytics/train_fusion.py
"""

import sys
from pathlib import Path
import json
import warnings

import joblib
import numpy as np
import pandas as pd
from PIL import Image

from sklearn.decomposition import PCA
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    precision_recall_fscore_support,
    confusion_matrix,
)
from sklearn.preprocessing import StandardScaler
from tensorflow.keras.applications.mobilenet_v2 import (
    MobileNetV2,
    preprocess_input,
)
from tensorflow.keras.models import Model
from tensorflow.keras.preprocessing import image as keras_image

warnings.filterwarnings("ignore")

HERE = Path(__file__).resolve().parent
SRC = HERE.parents[0]

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from fusion_analytics.config import (
    API_METADATA,
    CNN_FEATURES,
    CNN_PATHS,
    RESULTS,
    MODEL_DIR,
    API_FEATURE_COLUMNS,
)

PROJECT_ROOT = HERE.parents[1]

IMAGE_SIZE_RAW = (32, 32)
CNN_SIZE = (224, 224)
BATCH_SIZE = 32
RANDOM_STATE = 42


def resolve_image_path(image_path):
    """
    fusion_metadata.csv stores paths like:
        data/train/Type 1 Pomfret/Pomfret001.jpg

    Resolve them relative to project root.
    """
    p = Path(str(image_path))

    if p.is_absolute() and p.exists():
        return p

    candidate = PROJECT_ROOT / p
    if candidate.exists():
        return candidate

    # A useful fallback if the CSV used a different slash style.
    candidate = PROJECT_ROOT / str(image_path).replace("\\", "/")
    if candidate.exists():
        return candidate

    raise FileNotFoundError(f"Image not found: {image_path}")


def load_api_data():
    if not API_METADATA.exists():
        raise FileNotFoundError(
            f"{API_METADATA} does not exist. "
            "Run build_api_metadata.py first."
        )

    df = pd.read_csv(API_METADATA)

    missing = set(API_FEATURE_COLUMNS) - set(df.columns)
    if missing:
        raise ValueError(
            f"API metadata is missing required features: {sorted(missing)}"
        )

    return df


def load_rgb_raw(path):
    with Image.open(path) as img:
        img = img.convert("RGB")
        img = img.resize(IMAGE_SIZE_RAW)
        arr = np.asarray(img, dtype=np.float32) / 255.0
    return arr.reshape(-1)


def load_cnn_model():
    """
    MobileNetV2 is used only as a visual feature extractor.
    The final 1280-D pooled embedding is later reduced to 256-D
    with PCA fitted on the training set only.
    """
    base = MobileNetV2(
        weights="imagenet",
        include_top=False,
        pooling="avg",
        input_shape=(224, 224, 3),
    )
    return base


def extract_cnn_features(df):
    if CNN_FEATURES.exists() and CNN_PATHS.exists():
        cached_paths = pd.read_csv(CNN_PATHS)["image_path"].tolist()

        if cached_paths == df["image_path"].tolist():
            print("Using cached CNN features.")
            return np.load(CNN_FEATURES)

    model = load_cnn_model()

    features = []
    paths = df["image_path"].tolist()

    batch_images = []
    batch_paths = []

    def flush():
        if not batch_images:
            return

        arr = np.stack(batch_images)
        arr = preprocess_input(arr)
        emb = model.predict(
            arr,
            verbose=0,
        )
        features.extend(emb.tolist())
        batch_images.clear()
        batch_paths.clear()

    for i, path in enumerate(paths, start=1):
        full = resolve_image_path(path)

        img = keras_image.load_img(
            full,
            target_size=CNN_SIZE,
        )
        arr = keras_image.img_to_array(img)

        batch_images.append(arr)
        batch_paths.append(path)

        if len(batch_images) == BATCH_SIZE:
            flush()

        if i % 100 == 0 or i == len(paths):
            print(f"CNN features: {i}/{len(paths)}")

    flush()

    features = np.asarray(features, dtype=np.float32)

    if len(features) != len(df):
        raise RuntimeError(
            f"CNN feature count {len(features)} != metadata rows {len(df)}"
        )

    np.save(CNN_FEATURES, features)
    pd.DataFrame({"image_path": paths}).to_csv(
        CNN_PATHS,
        index=False,
    )

    print(f"Saved CNN embeddings: {features.shape}")
    return features


def api_matrix(df):
    x = df[API_FEATURE_COLUMNS].copy()

    for col in API_FEATURE_COLUMNS:
        x[col] = pd.to_numeric(
            x[col],
            errors="coerce",
        )

    return x.to_numpy(dtype=np.float32)


def evaluate(name, y_true, y_pred):
    precision, recall, f1, _ = precision_recall_fscore_support(
        y_true,
        y_pred,
        average="weighted",
        zero_division=0,
    )

    acc = accuracy_score(y_true, y_pred)

    print()
    print("=" * 70)
    print(name)
    print("=" * 70)
    print(f"Accuracy : {acc:.4f}")
    print(f"Precision: {precision:.4f}")
    print(f"Recall   : {recall:.4f}")
    print(f"F1       : {f1:.4f}")

    return {
        "experiment": name,
        "accuracy": acc,
        "precision_weighted": precision,
        "recall_weighted": recall,
        "f1_weighted": f1,
        "confusion_matrix": confusion_matrix(
            y_true,
            y_pred,
        ).tolist(),
    }


def fit_classifier(X_train, y_train):
    imputer = SimpleImputer(strategy="median")
    scaler = StandardScaler()

    X_train_imp = imputer.fit_transform(X_train)
    X_train_scaled = scaler.fit_transform(X_train_imp)

    clf = LogisticRegression(
        max_iter=2000,
        random_state=RANDOM_STATE,
        solver="lbfgs",
    )

    clf.fit(
        X_train_scaled,
        y_train,
    )

    return imputer, scaler, clf


def transform(imputer, scaler, X):
    return scaler.transform(
        imputer.transform(X)
    )


def main():
    df = load_api_data()

    print(f"API metadata rows: {len(df)}")

    # ---------------------------------------------------------
    # Extract image data
    # ---------------------------------------------------------

    print()
    print("Loading raw 32x32 RGB pixels...")

    raw_pixels = np.asarray(
        [load_rgb_raw(resolve_image_path(p)) for p in df["image_path"]],
        dtype=np.float32,
    )

    print("Raw pixel matrix:", raw_pixels.shape)

    # ---------------------------------------------------------
    # Extract CNN features
    # ---------------------------------------------------------

    print()
    print("Preparing MobileNetV2 features...")

    cnn_1280 = extract_cnn_features(df)

    # ---------------------------------------------------------
    # API features
    # ---------------------------------------------------------

    api = api_matrix(df)

    print("API feature matrix:", api.shape)

    # ---------------------------------------------------------
    # Split
    # ---------------------------------------------------------

    train_mask = (
        df["split"].astype(str).str.lower() == "train"
    ).to_numpy()

    test_mask = (
        df["split"].astype(str).str.lower() == "test"
    ).to_numpy()

    y = df["species"].to_numpy()

    y_train = y[train_mask]
    y_test = y[test_mask]

    print()
    print(f"Train rows: {train_mask.sum()}")
    print(f"Test rows : {test_mask.sum()}")

    results = []

    # =========================================================
    # EXPERIMENT 1: IMAGE ONLY BASELINE
    # =========================================================

    print()
    print("Training IMAGE-ONLY baseline...")

    # Use PCA to make the raw image baseline manageable.
    raw_pca = PCA(
        n_components=100,
        random_state=RANDOM_STATE,
    )

    raw_train_reduced = raw_pca.fit_transform(
        raw_pixels[train_mask]
    )

    raw_test_reduced = raw_pca.transform(
        raw_pixels[test_mask]
    )

    imp, scaler, clf = fit_classifier(
        raw_train_reduced,
        y_train,
    )

    pred = clf.predict(
        transform(
            imp,
            scaler,
            raw_test_reduced,
        )
    )

    results.append(
        evaluate(
            "Image Only Baseline",
            y_test,
            pred,
        )
    )

    joblib.dump(
        {
            "pca": raw_pca,
            "imputer": imp,
            "scaler": scaler,
            "classifier": clf,
        },
        MODEL_DIR / "image_only.joblib",
    )

    # =========================================================
    # EXPERIMENT 2: RAW/DATA-LEVEL FUSION
    # =========================================================

    print()
    print("Training RAW/DATA-LEVEL FUSION...")

    raw_train = np.hstack(
        [
            raw_pixels[train_mask],
            api[train_mask],
        ]
    )

    raw_test = np.hstack(
        [
            raw_pixels[test_mask],
            api[test_mask],
        ]
    )

    print("Raw fused matrix:", raw_train.shape)

    imp, scaler, clf = fit_classifier(
        raw_train,
        y_train,
    )

    pred = clf.predict(
        transform(
            imp,
            scaler,
            raw_test,
        )
    )

    results.append(
        evaluate(
            "Raw/Data-Level Fusion",
            y_test,
            pred,
        )
    )

    joblib.dump(
        {
            "imputer": imp,
            "scaler": scaler,
            "classifier": clf,
        },
        MODEL_DIR / "raw_fusion.joblib",
    )

    # =========================================================
    # EXPERIMENT 3: FEATURE-LEVEL FUSION
    # =========================================================

    print()
    print("Training FEATURE-LEVEL FUSION...")

    # PCA is fitted ONLY on training visual features.
    cnn_pca = PCA(
        n_components=256,
        random_state=RANDOM_STATE,
    )

    cnn_train_256 = cnn_pca.fit_transform(
        cnn_1280[train_mask]
    )

    cnn_test_256 = cnn_pca.transform(
        cnn_1280[test_mask]
    )

    feature_train = np.hstack(
        [
            cnn_train_256,
            api[train_mask],
        ]
    )

    feature_test = np.hstack(
        [
            cnn_test_256,
            api[test_mask],
        ]
    )

    print(
        "Feature-fused matrix:",
        feature_train.shape,
    )

    imp, scaler, clf = fit_classifier(
        feature_train,
        y_train,
    )

    pred = clf.predict(
        transform(
            imp,
            scaler,
            feature_test,
        )
    )

    results.append(
        evaluate(
            "Feature-Level Fusion",
            y_test,
            pred,
        )
    )

    joblib.dump(
        {
            "pca_256": cnn_pca,
            "imputer": imp,
            "scaler": scaler,
            "classifier": clf,
            "api_features": API_FEATURE_COLUMNS,
        },
        MODEL_DIR / "feature_fusion.joblib",
    )

    # ---------------------------------------------------------
    # Save results
    # ---------------------------------------------------------

    result_rows = []

    for item in results:
        row = {
            "experiment": item["experiment"],
            "accuracy": item["accuracy"],
            "precision_weighted": item["precision_weighted"],
            "recall_weighted": item["recall_weighted"],
            "f1_weighted": item["f1_weighted"],
            "confusion_matrix": json.dumps(
                item["confusion_matrix"]
            ),
        }
        result_rows.append(row)

    results_df = pd.DataFrame(result_rows)

    results_df.to_csv(
        RESULTS,
        index=False,
    )

    print()
    print("=" * 70)
    print("FINAL COMPARISON")
    print("=" * 70)
    print(
        results_df[
            [
                "experiment",
                "accuracy",
                "precision_weighted",
                "recall_weighted",
                "f1_weighted",
            ]
        ].to_string(index=False)
    )

    print()
    print(f"Results saved to: {RESULTS}")


if __name__ == "__main__":
    main()
