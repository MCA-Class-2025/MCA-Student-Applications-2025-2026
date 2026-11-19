from pathlib import Path

import joblib
import pandas as pd

from ml.features import FEATURE_COLUMNS, FUSION_KEY_COLUMN, build_keyed_fusion_frame
from models.schemas import PatientData, PredictionResponse

MODEL_PATH = Path(__file__).resolve().parent.parent / "ml" / "model.joblib"


class ModelNotReadyError(RuntimeError):
    """Raised when a trained model artifact is not available."""


def predict(patient: PatientData) -> PredictionResponse:
    if not MODEL_PATH.exists():
        raise ModelNotReadyError(
            "Prediction model is not trained yet. Train it with backend/ml/train.py "
            "after adding the final dataset."
        )

    artifact = joblib.load(MODEL_PATH)
    model, expected_features = _resolve_prediction_model(artifact)
    if patient.ap_lo >= patient.ap_hi:
        raise ValueError("Diastolic blood pressure must be lower than systolic blood pressure.")

    fused_values = _build_keyed_fusion_frame(patient).drop(columns=FUSION_KEY_COLUMN)
    unsupported_features = set(expected_features).difference(fused_values.columns)
    if unsupported_features:
        raise ModelNotReadyError(
            "Prediction model uses unsupported features. Retrain it with backend/ml/train.py."
        )
    values = fused_values.loc[:, expected_features]
    probability = float(model.predict_proba(values)[0][1])
    return PredictionResponse(
        risk_label="High Risk" if probability >= 0.5 else "Low Risk",
        risk_probability=probability,
    )


def get_model_evaluation() -> dict[str, object]:
    """Return the selected model and held-out metrics after five-model training."""
    if not MODEL_PATH.exists():
        raise ModelNotReadyError(
            "Prediction model is not trained yet. Train it with backend/ml/train.py."
        )
    artifact = joblib.load(MODEL_PATH)
    if not isinstance(artifact, dict) or not isinstance(artifact.get("metrics"), dict):
        raise ModelNotReadyError(
            "Model comparison is unavailable for the legacy artifact. Retrain with backend/ml/train.py."
        )
    selected_model_name = artifact.get("selected_model_name")
    metrics = artifact["metrics"]
    if not isinstance(selected_model_name, str):
        raise ModelNotReadyError("The model artifact is invalid. Retrain with backend/ml/train.py.")
    return {"selected_model_name": selected_model_name, "metrics": metrics}


def _resolve_prediction_model(artifact: object) -> tuple[object, list[str]]:
    """Read either the multi-model artifact or the legacy single-model artifact."""
    if isinstance(artifact, dict):
        selected_model_name = artifact.get("selected_model_name")
        models = artifact.get("models")
        feature_columns = artifact.get("feature_columns")
        if (
            not isinstance(selected_model_name, str)
            or not isinstance(models, dict)
            or selected_model_name not in models
            or not isinstance(feature_columns, list)
            or not all(isinstance(feature, str) for feature in feature_columns)
        ):
            raise ModelNotReadyError("The model artifact is invalid. Retrain with backend/ml/train.py.")
        return models[selected_model_name], feature_columns
    return artifact, list(getattr(artifact, "feature_names_in_", FEATURE_COLUMNS))


# build the persisted, patient-keyed feature record used for prediction.
def build_fused_record(patient: PatientData) -> dict[str, float | int | str]:
    """Build the persisted, patient-keyed feature record used for prediction."""
    fused_record = _build_keyed_fusion_frame(patient).iloc[0].to_dict()
    return {
        feature: value.item() if hasattr(value, "item") else value
        for feature, value in fused_record.items()
    }


def _build_keyed_fusion_frame(patient: PatientData) -> pd.DataFrame:
    raw_values = pd.DataFrame(
        [[patient.patient_id, *[getattr(patient, feature) for feature in FEATURE_COLUMNS]]],
        columns=[FUSION_KEY_COLUMN, *FEATURE_COLUMNS],
    )
    return build_keyed_fusion_frame(raw_values)
