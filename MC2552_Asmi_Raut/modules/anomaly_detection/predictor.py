from modules.anomaly_detection.model_loader import load_resources
from modules.anomaly_detection.preprocess import preprocess


def predict(df):

    model, _, _, _ = load_resources()

    processed_df = preprocess(df)

    prediction = model.predict(processed_df)

    result = []

    for value in prediction:

        if value == -1:
            result.append("Anomaly")
        else:
            result.append("Normal")

    return result