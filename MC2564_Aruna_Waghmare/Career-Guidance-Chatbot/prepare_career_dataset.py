import pandas as pd
import os

# ==============================
# File Paths
# ==============================
GPT_PATH = "dataset/gpt_dataset.csv"
JOB_PATH = "dataset/IT_Job_Roles_Skills.csv"

# ==============================
# Load Datasets
# ==============================
gpt_df = pd.read_csv(GPT_PATH, encoding="utf-8")
job_df = pd.read_csv(JOB_PATH, encoding="cp1252")

# ==============================
# Display Dataset Information
# ==============================
print("GPT Dataset:", gpt_df.shape)
print("Job Dataset:", job_df.shape)

print("\nGPT columns:")
print(gpt_df.columns.tolist())

print("\nJob dataset columns:")
print(job_df.columns.tolist())

# ==============================
# Prepare Job Dataset
# ==============================
job_df["text"] = (
    "Job Title: "
    + job_df["Job Title"].fillna("").astype(str)
    + "\nJob Description: "
    + job_df["Job Description"].fillna("").astype(str)
    + "\nSkills: "
    + job_df["Skills"].fillna("").astype(str)
    + "\nCertifications: "
    + job_df["Certifications"].fillna("").astype(str)
)

# ==============================
# Prepare GPT Dataset
# ==============================
gpt_df["text"] = (
    "Category: "
    + gpt_df["Category"].fillna("").astype(str)
    + "\nResume: "
    + gpt_df["Resume"].fillna("").astype(str)
)

# ==============================
# Add Source Information
# ==============================
job_df["source"] = "IT Job Roles Dataset"
gpt_df["source"] = "GPT Career Dataset"

# ==============================
# Combine Datasets
# ==============================
combined_df = pd.concat(
    [
        job_df[["text", "source"]],
        gpt_df[["text", "source"]]
    ],
    ignore_index=True
)

# ==============================
# Remove Empty Records
# ==============================
combined_df = combined_df.dropna(
    subset=["text"]
)

combined_df = combined_df[
    combined_df["text"].str.strip() != ""
]

# ==============================
# Remove Duplicate Records
# ==============================
combined_df = combined_df.drop_duplicates(
    subset=["text"]
)

# ==============================
# Reset Index
# ==============================
combined_df = combined_df.reset_index(
    drop=True
)

# ==============================
# Create Output Directory
# ==============================
os.makedirs(
    "processed_data",
    exist_ok=True
)

# ==============================
# Save Cleaned Dataset
# ==============================
output_path = "processed_data/career_data_cleaned.csv"

combined_df.to_csv(
    output_path,
    index=False
)

# ==============================
# Final Information
# ==============================
print(f"\nSaved successfully: {output_path}")

print(
    "Final dataset shape:",
    combined_df.shape
)