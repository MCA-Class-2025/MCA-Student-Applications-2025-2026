import os
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler


# ============================================================
# STEP 5 - PREPARE TRAINING AND TESTING DATA
# ============================================================

print("=" * 80)
print("STEP 5 - PREPARING TRAINING AND TESTING DATA")
print("=" * 80)


# ============================================================
# 1. PATHS
# ============================================================

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

INPUT_FILE = os.path.join(
    BASE_DIR,
    "ml_assignment",
    "results",
    "ml_ready_dataset.csv"
)

OUTPUT_DIR = os.path.join(
    BASE_DIR,
    "ml_assignment",
    "results"
)

os.makedirs(OUTPUT_DIR, exist_ok=True)


print("\nInput dataset:")
print(INPUT_FILE)


# ============================================================
# 2. LOAD DATASET
# ============================================================

print("\n" + "=" * 80)
print("1. LOADING ML-READY DATASET")
print("=" * 80)

if not os.path.exists(INPUT_FILE):
    raise FileNotFoundError(
        f"Dataset not found:\n{INPUT_FILE}"
    )

df = pd.read_csv(INPUT_FILE)

print("Dataset loaded successfully.")
print(f"Rows: {df.shape[0]}")
print(f"Columns: {df.shape[1]}")


# ============================================================
# 3. CHECK REQUIRED COLUMNS
# ============================================================

required_columns = [
    "source_type",
    "content_length",
    "title_length",
    "content_word_count",
    "title_word_count",
    "metadata_length",
    "has_url",
    "modified_year",
    "modified_month",
    "modified_day",
    "language_encoded"
]

missing_columns = [
    column for column in required_columns
    if column not in df.columns
]

if missing_columns:
    raise ValueError(
        f"The following required columns are missing:\n"
        f"{missing_columns}"
    )


# ============================================================
# 4. HANDLE MISSING VALUES
# ============================================================

print("\n" + "=" * 80)
print("2. HANDLING MISSING VALUES")
print("=" * 80)

numeric_columns = [
    "content_length",
    "title_length",
    "content_word_count",
    "title_word_count",
    "metadata_length",
    "has_url",
    "modified_year",
    "modified_month",
    "modified_day",
    "language_encoded"
]

for column in numeric_columns:
    df[column] = pd.to_numeric(
        df[column],
        errors="coerce"
    )

    df[column] = df[column].fillna(0)


print("Missing numeric values handled successfully.")


# ============================================================
# 5. DEFINE FEATURES (X)
# ============================================================

print("\n" + "=" * 80)
print("3. DEFINING FEATURES")
print("=" * 80)

feature_columns = [
    "content_length",
    "title_length",
    "content_word_count",
    "title_word_count",
    "metadata_length",
    "has_url",
    "modified_year",
    "modified_month",
    "modified_day",
    "language_encoded"
]

X = df[feature_columns].copy()

print("\nFeatures used for machine learning:")

for number, column in enumerate(feature_columns, start=1):
    print(f"{number}. {column}")


# ============================================================
# 6. DEFINE TARGET (Y)
# ============================================================

print("\n" + "=" * 80)
print("4. DEFINING TARGET VARIABLE")
print("=" * 80)

# Target = source_type
#
# The model will learn to predict whether a record
# belongs to Google Drive, GitHub, DuckDuckGo, etc.

y = df["source_type"].copy()

print("Target variable: source_type")

print("\nTarget classes:")
print(y.value_counts())


# ============================================================
# 7. ENCODE TARGET
# ============================================================

print("\n" + "=" * 80)
print("5. ENCODING TARGET VARIABLE")
print("=" * 80)

target_mapping = {
    class_name: number
    for number, class_name
    in enumerate(sorted(y.unique()))
}

print("\nTarget encoding:")

for class_name, number in target_mapping.items():
    print(f"{class_name} -> {number}")

y_encoded = y.map(target_mapping)


# ============================================================
# 8. TRAIN / TEST SPLIT
# ============================================================

print("\n" + "=" * 80)
print("6. TRAIN / TEST SPLIT")
print("=" * 80)

print("\nUsing:")
print("Training data = 80%")
print("Testing data  = 20%")

# Stratification is used so that each class is
# represented as fairly as possible in both datasets.

try:
    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y_encoded,
        test_size=0.20,
        random_state=42,
        stratify=y_encoded
    )

except ValueError:
    print(
        "\nWarning: Stratified split could not be performed "
        "because one or more classes contain too few records."
    )

    print("Using normal train/test split instead.")

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y_encoded,
        test_size=0.20,
        random_state=42
    )


print("\nTraining set:")
print(f"X_train: {X_train.shape}")
print(f"y_train: {y_train.shape}")

print("\nTesting set:")
print(f"X_test: {X_test.shape}")
print(f"y_test: {y_test.shape}")


# ============================================================
# 9. FEATURE SCALING
# ============================================================

print("\n" + "=" * 80)
print("7. FEATURE SCALING")
print("=" * 80)

scaler = StandardScaler()

X_train_scaled = scaler.fit_transform(X_train)

X_test_scaled = scaler.transform(X_test)

print("StandardScaler applied successfully.")

print(f"\nScaled X_train shape: {X_train_scaled.shape}")
print(f"Scaled X_test shape:  {X_test_scaled.shape}")


# ============================================================
# 10. SAVE TRAINING AND TESTING DATA
# ============================================================

print("\n" + "=" * 80)
print("8. SAVING PREPARED DATA")
print("=" * 80)


# Unscaled training data
train_data = X_train.copy()
train_data["target"] = y_train.values

train_file = os.path.join(
    OUTPUT_DIR,
    "train_data.csv"
)

train_data.to_csv(
    train_file,
    index=False
)


# Unscaled testing data
test_data = X_test.copy()
test_data["target"] = y_test.values

test_file = os.path.join(
    OUTPUT_DIR,
    "test_data.csv"
)

test_data.to_csv(
    test_file,
    index=False
)


# Scaled training data
scaled_train_data = pd.DataFrame(
    X_train_scaled,
    columns=feature_columns
)

scaled_train_data["target"] = y_train.values

scaled_train_file = os.path.join(
    OUTPUT_DIR,
    "train_data_scaled.csv"
)

scaled_train_data.to_csv(
    scaled_train_file,
    index=False
)


# Scaled testing data
scaled_test_data = pd.DataFrame(
    X_test_scaled,
    columns=feature_columns
)

scaled_test_data["target"] = y_test.values

scaled_test_file = os.path.join(
    OUTPUT_DIR,
    "test_data_scaled.csv"
)

scaled_test_data.to_csv(
    scaled_test_file,
    index=False
)


# ============================================================
# 11. SAVE TARGET MAPPING
# ============================================================

mapping_file = os.path.join(
    OUTPUT_DIR,
    "target_mapping.csv"
)

mapping_df = pd.DataFrame(
    list(target_mapping.items()),
    columns=["source_type", "target_value"]
)

mapping_df.to_csv(
    mapping_file,
    index=False
)


# ============================================================
# 12. FINAL SUMMARY
# ============================================================

print("\n" + "=" * 80)
print("STEP 5 COMPLETED SUCCESSFULLY")
print("=" * 80)

print("\nOriginal dataset:")
print(f"Rows: {df.shape[0]}")
print(f"Features: {len(feature_columns)}")

print("\nTraining data:")
print(f"Rows: {len(X_train)}")
print(f"Columns: {X_train.shape[1]}")

print("\nTesting data:")
print(f"Rows: {len(X_test)}")
print(f"Columns: {X_test.shape[1]}")

print("\nGenerated files:")

print(f"1. {train_file}")
print(f"2. {test_file}")
print(f"3. {scaled_train_file}")
print(f"4. {scaled_test_file}")
print(f"5. {mapping_file}")

print("\nTarget variable:")
print("source_type")

print("\nTarget classes:")
for class_name, number in target_mapping.items():
    print(f"{number} = {class_name}")

print("\n" + "=" * 80)
print("READY FOR MACHINE LEARNING ALGORITHMS")
print("=" * 80)