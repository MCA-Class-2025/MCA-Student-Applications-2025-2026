"""
predict.py
----------
Loads the trained CNN and classifies a single fish image.

Usage as a script:
    python predict.py --image path/to/fish.jpg

Usage as a module (used by app.py):
    from predict import FishClassifier
    clf = FishClassifier()
    label, confidence, top3 = clf.predict("path/to/fish.jpg")
"""

import argparse
import json
import os

import numpy as np
from tensorflow.keras.applications.mobilenet_v2 import preprocess_input
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing import image

IMG_SIZE = (224, 224)


class FishClassifier:
    def __init__(self, model_path: str = "../models/fish_classifier.h5",
                 class_indices_path: str = "../models/class_indices.json"):
        if not os.path.exists(model_path):
            raise FileNotFoundError(
                f"Model not found at {model_path}. Run train_cnn.py first."
            )
        self.model = load_model(model_path)

        with open(class_indices_path, "r") as f:
            class_indices = json.load(f)
        # invert {class_name: index} -> {index: class_name}
        self.idx_to_class = {v: k for k, v in class_indices.items()}

    def predict(self, img_path: str, top_k: int = 3):
        img = image.load_img(img_path, target_size=IMG_SIZE)
        arr = image.img_to_array(img)
        arr = np.expand_dims(arr, axis=0)
        arr = preprocess_input(arr)

        preds = self.model.predict(arr, verbose=0)[0]

        top_indices = preds.argsort()[-top_k:][::-1]
        top_predictions = [
            (self.idx_to_class[i], float(preds[i])) for i in top_indices
        ]

        best_label, best_confidence = top_predictions[0]
        return best_label, best_confidence, top_predictions


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--image", type=str, required=True)
    parser.add_argument("--model_path", type=str, default="../models/fish_classifier.h5")
    parser.add_argument("--class_indices_path", type=str, default="../models/class_indices.json")
    args = parser.parse_args()

    clf = FishClassifier(args.model_path, args.class_indices_path)
    label, confidence, top3 = clf.predict(args.image)

    print(f"\nPredicted fish: {label}  (confidence: {confidence:.2%})")
    print("\nTop 3 predictions:")
    for cls, conf in top3:
        print(f"  {cls:<20} {conf:.2%}")
