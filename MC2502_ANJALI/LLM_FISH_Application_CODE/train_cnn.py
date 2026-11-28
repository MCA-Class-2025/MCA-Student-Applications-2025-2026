"""
train_cnn.py
------------
Trains a fish-species classifier on the Indian Seafood Fish Dataset using
transfer learning (MobileNetV2 backbone, pretrained on ImageNet).

Expected folder layout (created by split_dataset.py):
    data/
        train/
            Pomfret/*.jpg
            Black_Pomfret/*.jpg
            ...
        test/
            Pomfret/*.jpg
            ...

Outputs:
    models/fish_classifier.h5     - trained Keras model
    models/class_indices.json     - mapping {class_name: index}
    models/training_history.png   - accuracy/loss curves

Usage:
    python train_cnn.py --data_dir ../data --epochs 15 --batch_size 32
"""

import argparse
import json
import os

import matplotlib.pyplot as plt
import tensorflow as tf
from tensorflow.keras.applications import MobileNetV2
from tensorflow.keras.applications.mobilenet_v2 import preprocess_input
from tensorflow.keras.layers import Dense, GlobalAveragePooling2D, Dropout
from tensorflow.keras.models import Model
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint

IMG_SIZE = (224, 224)


def build_model(num_classes: int) -> Model:
    base_model = MobileNetV2(
        input_shape=IMG_SIZE + (3,),
        include_top=False,
        weights="imagenet",
    )
    base_model.trainable = False  # freeze backbone for the first training pass

    x = base_model.output
    x = GlobalAveragePooling2D()(x)
    x = Dense(256, activation="relu")(x)
    x = Dropout(0.4)(x)
    outputs = Dense(num_classes, activation="softmax")(x)

    model = Model(inputs=base_model.input, outputs=outputs)
    model.compile(
        optimizer=Adam(learning_rate=1e-4),
        loss="categorical_crossentropy",
        metrics=["accuracy"],
    )
    return model


def get_generators(data_dir: str, batch_size: int):
    train_datagen = ImageDataGenerator(
        preprocessing_function=preprocess_input,
        rotation_range=20,
        width_shift_range=0.15,
        height_shift_range=0.15,
        shear_range=0.1,
        zoom_range=0.2,
        horizontal_flip=True,
        brightness_range=(0.7, 1.3),  # dataset has varied lighting conditions
    )
    test_datagen = ImageDataGenerator(preprocessing_function=preprocess_input)

    train_gen = train_datagen.flow_from_directory(
        os.path.join(data_dir, "train"),
        target_size=IMG_SIZE,
        batch_size=batch_size,
        class_mode="categorical",
    )
    test_gen = test_datagen.flow_from_directory(
        os.path.join(data_dir, "test"),
        target_size=IMG_SIZE,
        batch_size=batch_size,
        class_mode="categorical",
        shuffle=False,
    )
    return train_gen, test_gen


def plot_history(history, out_path: str):
    fig, axes = plt.subplots(1, 2, figsize=(12, 4))

    axes[0].plot(history.history["accuracy"], label="train_acc")
    axes[0].plot(history.history["val_accuracy"], label="val_acc")
    axes[0].set_title("Accuracy")
    axes[0].set_xlabel("Epoch")
    axes[0].legend()

    axes[1].plot(history.history["loss"], label="train_loss")
    axes[1].plot(history.history["val_loss"], label="val_loss")
    axes[1].set_title("Loss")
    axes[1].set_xlabel("Epoch")
    axes[1].legend()

    plt.tight_layout()
    plt.savefig(out_path)
    print(f"Saved training curves to {out_path}")


def main(args):
    os.makedirs(args.model_dir, exist_ok=True)

    train_gen, test_gen = get_generators(args.data_dir, args.batch_size)
    num_classes = train_gen.num_classes
    print(f"Detected {num_classes} classes: {train_gen.class_indices}")

    # Save class index mapping so predict.py / app.py can decode predictions later
    with open(os.path.join(args.model_dir, "class_indices.json"), "w") as f:
        json.dump(train_gen.class_indices, f, indent=2)

    model = build_model(num_classes)
    model.summary()

    checkpoint_path = os.path.join(args.model_dir, "fish_classifier.h5")
    callbacks = [
        EarlyStopping(monitor="val_accuracy", patience=4, restore_best_weights=True),
        ModelCheckpoint(checkpoint_path, monitor="val_accuracy", save_best_only=True),
    ]

    print("\n--- Stage 1: training classification head (backbone frozen) ---")
    history = model.fit(
        train_gen,
        validation_data=test_gen,
        epochs=args.epochs,
        callbacks=callbacks,
    )

    # Fine-tune: unfreeze the top layers of the backbone for a few more epochs
    print("\n--- Stage 2: fine-tuning top backbone layers ---")
    base_model = model.layers[0] if isinstance(model.layers[0], Model) else None
    # find the MobileNetV2 submodel by name
    for layer in model.layers:
        if layer.name.startswith("mobilenetv2"):
            base_model = layer
            break

    if base_model is not None:
        base_model.trainable = True
        for layer in base_model.layers[:-30]:
            layer.trainable = False

        model.compile(
            optimizer=Adam(learning_rate=1e-5),
            loss="categorical_crossentropy",
            metrics=["accuracy"],
        )

        fine_tune_history = model.fit(
            train_gen,
            validation_data=test_gen,
            epochs=args.fine_tune_epochs,
            callbacks=callbacks,
        )

        for key in history.history:
            history.history[key] += fine_tune_history.history[key]

    model.save(checkpoint_path)
    print(f"\nSaved trained model to {checkpoint_path}")

    plot_history(history, os.path.join(args.model_dir, "training_history.png"))

    loss, acc = model.evaluate(test_gen)
    print(f"\nFinal test accuracy: {acc:.4f} | test loss: {loss:.4f}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data_dir", type=str, default="../data")
    parser.add_argument("--model_dir", type=str, default="../models")
    parser.add_argument("--batch_size", type=int, default=32)
    parser.add_argument("--epochs", type=int, default=15)
    parser.add_argument("--fine_tune_epochs", type=int, default=5)
    args = parser.parse_args()

    main(args)
