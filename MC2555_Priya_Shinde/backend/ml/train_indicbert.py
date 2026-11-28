from pathlib import Path

import numpy as np
import pandas as pd
import torch

from datasets import Dataset
from sklearn.metrics import (
    accuracy_score,
    precision_recall_fscore_support,
    classification_report,
    confusion_matrix
)

from transformers import (
    AutoTokenizer,
    AutoModelForSequenceClassification,
    TrainingArguments,
    Trainer
)


# ============================================================
# PROJECT PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

TRAIN_FILE = (
    PROJECT_ROOT
    / "data"
    / "indicbert"
    / "train.csv"
)

VALIDATION_FILE = (
    PROJECT_ROOT
    / "data"
    / "indicbert"
    / "validation.csv"
)

MODEL_OUTPUT_DIR = (
    PROJECT_ROOT
    / "models"
    / "indicbert_fake_news"
)


# ============================================================
# MODEL
# ============================================================

MODEL_NAME = (
    "ai4bharat/IndicBERTv2-MLM-Sam-TLM"
)


# ============================================================
# SETTINGS
# ============================================================

MAX_LENGTH = 128

# CPU-safe settings
TRAIN_BATCH_SIZE = 2
EVAL_BATCH_SIZE = 2

GRADIENT_ACCUMULATION_STEPS = 8

NUM_EPOCHS = 2

LEARNING_RATE = 2e-5

RANDOM_SEED = 42


# ============================================================
# DEVICE
# ============================================================

DEVICE = (
    "cuda"
    if torch.cuda.is_available()
    else "cpu"
)


# ============================================================
# HEADER
# ============================================================

print("\n")
print("=" * 60)
print(" MULTILINGUAL FAKE NEWS - INDICBERT V2")
print("=" * 60)

print(
    f"\nDevice: {DEVICE}"
)

print(
    f"Model: {MODEL_NAME}"
)


# ============================================================
# CHECK DATA FILES
# ============================================================

if not TRAIN_FILE.exists():

    raise FileNotFoundError(
        f"Training file not found:\n{TRAIN_FILE}"
    )


if not VALIDATION_FILE.exists():

    raise FileNotFoundError(
        f"Validation file not found:\n{VALIDATION_FILE}"
    )


# ============================================================
# LOAD DATA
# ============================================================

print("\nLoading training data...")

train_df = pd.read_csv(
    TRAIN_FILE
)

print(
    "Training records:",
    len(train_df)
)


print("\nLoading validation data...")

validation_df = pd.read_csv(
    VALIDATION_FILE
)

print(
    "Validation records:",
    len(validation_df)
)


# ============================================================
# CLEAN DATA
# ============================================================

required_columns = [
    "text",
    "label"
]

for column in required_columns:

    if column not in train_df.columns:

        raise ValueError(
            f"Missing column in training data: {column}"
        )

    if column not in validation_df.columns:

        raise ValueError(
            f"Missing column in validation data: {column}"
        )


train_df = train_df[
    [
        "text",
        "label",
        "language"
    ]
].copy()


validation_df = validation_df[
    [
        "text",
        "label",
        "language"
    ]
].copy()


train_df["text"] = (
    train_df["text"]
    .fillna("")
    .astype(str)
    .str.strip()
)


validation_df["text"] = (
    validation_df["text"]
    .fillna("")
    .astype(str)
    .str.strip()
)


# ============================================================
# LABEL ENCODING
# ============================================================

# IMPORTANT:
#
# 0 = Fake
# 1 = Real
#
# This mapping will also be used during prediction.

label_map = {
    "Fake": 0,
    "Real": 1
}


train_df["label"] = (
    train_df["label"]
    .map(label_map)
)


validation_df["label"] = (
    validation_df["label"]
    .map(label_map)
)


# Remove invalid labels

train_df = train_df.dropna(
    subset=["label"]
).copy()

validation_df = validation_df.dropna(
    subset=["label"]
).copy()


train_df["label"] = (
    train_df["label"]
    .astype(int)
)

validation_df["label"] = (
    validation_df["label"]
    .astype(int)
)


# ============================================================
# DISTRIBUTION
# ============================================================

print("\nTraining label distribution:")

print(
    train_df["label"]
    .value_counts()
    .sort_index()
)


print("\nValidation label distribution:")

print(
    validation_df["label"]
    .value_counts()
    .sort_index()
)


print("\nTraining language distribution:")

print(
    train_df["language"]
    .value_counts()
)


# ============================================================
# CONVERT TO HUGGING FACE DATASETS
# ============================================================

print("\nConverting data...")

train_dataset = Dataset.from_pandas(
    train_df[
        [
            "text",
            "label"
        ]
    ],
    preserve_index=False
)


validation_dataset = Dataset.from_pandas(
    validation_df[
        [
            "text",
            "label"
        ]
    ],
    preserve_index=False
)


# ============================================================
# LOAD TOKENIZER
# ============================================================

print("\nLoading IndicBERT v2 tokenizer...")

tokenizer = AutoTokenizer.from_pretrained(
    MODEL_NAME
)

print(
    "Tokenizer loaded successfully."
)


# ============================================================
# TOKENIZATION
# ============================================================

def tokenize_function(batch):

    return tokenizer(
        batch["text"],
        truncation=True,
        max_length=MAX_LENGTH,
        padding="max_length"
    )


print("\nTokenizing training data...")

train_dataset = train_dataset.map(
    tokenize_function,
    batched=True,
    desc="Tokenizing training"
)


print("\nTokenizing validation data...")

validation_dataset = validation_dataset.map(
    tokenize_function,
    batched=True,
    desc="Tokenizing validation"
)


# ============================================================
# REMOVE ORIGINAL TEXT
# ============================================================

train_dataset = train_dataset.remove_columns(
    ["text"]
)

validation_dataset = validation_dataset.remove_columns(
    ["text"]
)


# ============================================================
# FORMAT
# ============================================================

train_dataset.set_format(
    "torch"
)

validation_dataset.set_format(
    "torch"
)


# ============================================================
# LOAD MODEL
# ============================================================

print("\nLoading IndicBERT v2 classification model...")

model = AutoModelForSequenceClassification.from_pretrained(
    MODEL_NAME,
    num_labels=2,
    id2label={
        0: "Fake",
        1: "Real"
    },
    label2id={
        "Fake": 0,
        "Real": 1
    },
    ignore_mismatched_sizes=True
)

print(
    "IndicBERT v2 classification model loaded successfully."
)


# ============================================================
# METRICS
# ============================================================

def compute_metrics(
    eval_prediction
):

    predictions = (
        eval_prediction.predictions
    )

    labels = (
        eval_prediction.label_ids
    )

    predicted_labels = np.argmax(
        predictions,
        axis=1
    )

    accuracy = accuracy_score(
        labels,
        predicted_labels
    )

    precision, recall, f1, _ = (
        precision_recall_fscore_support(
            labels,
            predicted_labels,
            average="binary",
            zero_division=0
        )
    )

    return {
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "f1": f1
    }


# ============================================================
# TRAINING ARGUMENTS
# ============================================================

training_args = TrainingArguments(
    output_dir=str(MODEL_OUTPUT_DIR),

    num_train_epochs=NUM_EPOCHS,

    per_device_train_batch_size=TRAIN_BATCH_SIZE,
    per_device_eval_batch_size=EVAL_BATCH_SIZE,

    gradient_accumulation_steps=GRADIENT_ACCUMULATION_STEPS,

    learning_rate=LEARNING_RATE,

    logging_steps=100,

    eval_strategy="epoch",
    save_strategy="epoch",

    load_best_model_at_end=True,

    metric_for_best_model="f1",
    greater_is_better=True,

    save_total_limit=2,

    report_to="none",

    seed=RANDOM_SEED,

    dataloader_num_workers=0,

    fp16=False
)


# ============================================================
# TRAINER
# ============================================================

trainer = Trainer(

    model=model,

    args=training_args,

    train_dataset=train_dataset,

    eval_dataset=validation_dataset,

    processing_class=tokenizer,

    compute_metrics=compute_metrics
)


# ============================================================
# TRAIN
# ============================================================

print("\n")
print("=" * 60)
print(" STARTING INDICBERT V2 TRAINING")
print("=" * 60)

print(
    "\nThis may take time because the system is using CPU."
)


trainer.train()


# ============================================================
# FINAL EVALUATION
# ============================================================

print("\n")
print("=" * 60)
print(" FINAL VALIDATION")
print("=" * 60)


evaluation_result = (
    trainer.evaluate()
)


print(
    "\nValidation metrics:"
)

for key, value in evaluation_result.items():

    if isinstance(value, float):

        print(
            f"{key}: {value:.4f}"
        )

    else:

        print(
            f"{key}: {value}"
        )


# ============================================================
# DETAILED PREDICTIONS
# ============================================================

print("\nGenerating validation predictions...")

prediction_output = (
    trainer.predict(
        validation_dataset
    )
)

logits = (
    prediction_output.predictions
)

true_labels = (
    prediction_output.label_ids
)

predicted_labels = np.argmax(
    logits,
    axis=1
)


# ============================================================
# CLASSIFICATION REPORT
# ============================================================

print("\n")
print("=" * 60)
print(" CLASSIFICATION REPORT")
print("=" * 60)

print(
    classification_report(
        true_labels,
        predicted_labels,
        target_names=[
            "Fake",
            "Real"
        ],
        digits=4,
        zero_division=0
    )
)


# ============================================================
# CONFUSION MATRIX
# ============================================================

print("\nConfusion Matrix:")

print(
    confusion_matrix(
        true_labels,
        predicted_labels
    )
)


# ============================================================
# SAVE MODEL
# ============================================================

print("\n")
print("=" * 60)
print(" SAVING INDICBERT V2 MODEL")
print("=" * 60)


MODEL_OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)


trainer.save_model(
    MODEL_OUTPUT_DIR
)

tokenizer.save_pretrained(
    MODEL_OUTPUT_DIR
)


# ============================================================
# SAVE LABEL MAP
# ============================================================

label_map_file = (
    MODEL_OUTPUT_DIR
    / "label_map.txt"
)

with open(
    label_map_file,
    "w",
    encoding="utf-8"
) as file:

    file.write(
        "0=Fake\n"
    )

    file.write(
        "1=Real\n"
    )


# ============================================================
# COMPLETE
# ============================================================

print("\n")
print("=" * 60)
print(" INDICBERT V2 TRAINING COMPLETED")
print("=" * 60)

print(
    "\nModel saved at:"
)

print(
    MODEL_OUTPUT_DIR
)

print(
    "\nLabel mapping:"
)

print(
    "0 = Fake"
)

print(
    "1 = Real"
)

print("\n")