import numpy as np
import tensorflow as tf
from PIL import Image


MODEL_PATH = "models/waste_classifier.keras"
CLASS_PATH = "models/class_names.txt"


# ==========================================
# LOAD MODEL
# ==========================================

model = tf.keras.models.load_model(
    MODEL_PATH
)


# ==========================================
# LOAD CLASS NAMES
# ==========================================

with open(
    CLASS_PATH,
    "r"
) as file:

    class_names = [
        line.strip()
        for line in file.readlines()
    ]


# ==========================================
# PREDICT WASTE
# ==========================================

def predict_waste(uploaded_file):

    # Convert Streamlit UploadedFile
    # into PIL Image

    image = Image.open(
        uploaded_file
    ).convert("RGB")

    # Resize image
    image = image.resize(
        (224, 224)
    )

    # Convert to NumPy
    image_array = np.array(
        image
    )

    # Add batch dimension
    image_array = np.expand_dims(
        image_array,
        axis=0
    )

    # MobileNetV2 preprocessing
    image_array = tf.keras.applications.mobilenet_v2.preprocess_input(
        image_array
    )

    # Prediction
    predictions = model.predict(
        image_array,
        verbose=0
    )[0]

    # Highest probability class
    predicted_index = np.argmax(
        predictions
    )

    predicted_class = class_names[
        predicted_index
    ]

    confidence = float(
        predictions[predicted_index] * 100
    )

    return predicted_class, confidence