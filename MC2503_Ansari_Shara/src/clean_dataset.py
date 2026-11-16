import pandas as pd

# ============================
# Load Original Dataset
# ============================

file_path = "data/raw/auth_authz_failures_dataset.csv"

df = pd.read_csv(file_path)

print("=" * 50)
print("ORIGINAL DATASET")
print("=" * 50)

print(f"Rows : {len(df)}")
print(f"Columns : {len(df.columns)}")

# ============================
# Keep Required Columns
# ============================

required_columns = [
    "user_id",
    "ip_address",
    "device_type",
    "os_type",
    "browser",
    "success",
    "account_status",
    "failed_attempts",
    "session_duration",
    "role",
    "privilege_level",
    "suspicious_activity",
    "blocked"
]

df = df[required_columns]

print("\nColumns selected successfully.")

# ============================
# Replace Guest with User
# ============================

df["role"] = df["role"].replace("Guest", "User")

print("\nRole Distribution:")
print(df["role"].value_counts())

# ============================
# Missing Values
# ============================

print("\nMissing Values:")
print(df.isnull().sum())

# ============================
# Remove Duplicates
# ============================

duplicates = df.duplicated().sum()

print(f"\nDuplicate Rows : {duplicates}")

df = df.drop_duplicates()

print(f"Rows after removing duplicates : {len(df)}")

# ============================
# Random Sample
# ============================

df = df.sample(n=5000, random_state=42)
df = df.reset_index(drop=True)

print(f"\nFinal Dataset Rows : {len(df)}")

# ============================
# Save
# ============================

output_file = "data/processed/authentication_dataset_cleaned.csv"

df.to_csv(output_file, index=False)

print("\nDataset saved successfully!")
print(output_file)