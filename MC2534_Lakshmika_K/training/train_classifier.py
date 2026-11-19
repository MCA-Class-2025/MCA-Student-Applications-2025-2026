import os
import tensorflow as tf
from tensorflow.keras import layers, models
from tensorflow.keras.applications import MobileNetV2
from tensorflow.keras.applications.mobilenet_v2 import preprocess_input


# ==========================================
# SETTINGS
# ==========================================

DATASET_DIR = "dataset/garbage"
MODEL_DIR = "models"

IMG_SIZE = (224, 224)
BATCH_SIZE = 32
EPOCHS = 10

os.makedirs(MODEL_DIR, exist_ok=True)


# ==========================================
# LOAD DATASET
# ==========================================

print("\nLoading garbage image dataset...")

train_dataset = tf.keras.utils.image_dataset_from_directory(
    DATASET_DIR,
    validation_split=0.20,
    subset="training",
    seed=42,
    image_size=IMG_SIZE,
    batch_size=BATCH_SIZE
)

validation_dataset = tf.keras.utils.image_dataset_from_directory(
    DATASET_DIR,
    validation_split=0.20,
    subset="validation",
    seed=42,
    image_size=IMG_SIZE,
    batch_size=BATCH_SIZE
)


# ==========================================
# CLASS NAMES
# ==========================================

class_names = train_dataset.class_names

print("\nWaste Categories:")
for i, name in enumerate(class_names):
    print(f"{i}: {name}")


# ==========================================
# PERFORMANCE
# ==========================================

AUTOTUNE = tf.data.AUTOTUNE

train_dataset = train_dataset.prefetch(
    AUTOTUNE
)

validation_dataset = validation_dataset.prefetch(
    AUTOTUNE
)


# ==========================================
# DATA AUGMENTATION
# ==========================================

data_augmentation = tf.keras.Sequential([
    layers.RandomFlip("horizontal"),
    layers.RandomRotation(0.1),
    layers.RandomZoom(0.1),
])


# ==========================================
# MOBILE NET V2
# ==========================================

base_model = MobileNetV2(
    input_shape=(224, 224, 3),
    include_top=False,
    weights="imagenet"
)

base_model.trainable = False


# ==========================================
# BUILD MODEL
# ==========================================

inputs = layers.Input(
    shape=(224, 224, 3)
)

x = data_augmentation(inputs)

x = preprocess_input(x)

x = base_model(
    x,
    training=False
)

x = layers.GlobalAveragePooling2D()(x)

x = layers.Dropout(0.2)(x)

outputs = layers.Dense(
    len(class_names),
    activation="softmax"
)(x)

model = models.Model(
    inputs,
    outputs
)


# ==========================================
# COMPILE
# ==========================================

model.compile(
    optimizer="adam",
    loss="sparse_categorical_crossentropy",
    metrics=["accuracy"]
)


# ==========================================
# TRAIN
# ==========================================

print("\nStarting training...\n")

history = model.fit(
    train_dataset,
    validation_data=validation_dataset,
    epochs=EPOCHS
)


# ==========================================
# SAVE MODEL
# ==========================================

model_path = os.path.join(
    MODEL_DIR,
    "waste_classifier.keras"
)

model.save(model_path)


# ==========================================
# SAVE CLASS NAMES
# ==========================================

classes_path = os.path.join(
    MODEL_DIR,
    "class_names.txt"
)

with open(
    classes_path,
    "w"
) as file:

    for class_name in class_names:
        file.write(class_name + "\n")


# ==========================================
# FINAL RESULT
# ==========================================

print("\n" + "=" * 60)
print("       WASTE CLASSIFICATION MODEL READY")
print("=" * 60)

print("\nCategories:")

for name in class_names:
    print("-", name)

print("\nModel saved at:")
print(model_path)

print("\nClasses saved at:")
print(classes_path)

print("\nTraining completed successfully!")