import joblib
import os

MODEL_DIR = "models"

model = None
protocol_encoder = None
service_encoder = None
flag_encoder = None


def load_resources():
    global model
    global protocol_encoder
    global service_encoder
    global flag_encoder

    if model is None:
        model = joblib.load(os.path.join(MODEL_DIR, "isolation_forest_final.pkl"))

    if protocol_encoder is None:
        protocol_encoder = joblib.load(os.path.join(MODEL_DIR, "protocol_encoder.pkl"))

    if service_encoder is None:
        service_encoder = joblib.load(os.path.join(MODEL_DIR, "service_encoder.pkl"))

    if flag_encoder is None:
        flag_encoder = joblib.load(os.path.join(MODEL_DIR, "flag_encoder.pkl"))

    return model, protocol_encoder, service_encoder, flag_encoder