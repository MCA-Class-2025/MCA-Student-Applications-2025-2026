from modules.anomaly_detection.model_loader import load_resources


def preprocess(df):

    _, protocol_encoder, service_encoder, flag_encoder = load_resources()

    df["protocol_type"] = protocol_encoder.transform(df["protocol_type"])
    df["service"] = service_encoder.transform(df["service"])
    df["flag"] = flag_encoder.transform(df["flag"])

    return df