import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

# ============================================================
# PHASE 1 - PART A
# EXPLORATORY DATA ANALYSIS
# ORIGINAL ISOT FAKE/REAL NEWS DATASET
# ============================================================

print("=" * 75)
print("PHASE 1 - PART A : EXPLORATORY DATA ANALYSIS")
print("=" * 75)

# ============================================================
# 1. PROJECT PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[2]

FAKE_PATH = (
    BASE_DIR
    / "data"
    / "raw"
    / "ISOT_Fake_Real_News"
    / "Fake.csv"
)

REAL_PATH = (
    BASE_DIR
    / "data"
    / "raw"
    / "ISOT_Fake_Real_News"
    / "True.csv"
)

OUTPUT_DIR = (
    BASE_DIR
    / "data"
    / "processed"
    / "eda_phase1"
)

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ============================================================
# 2. CHECK FILES
# ============================================================

if not FAKE_PATH.exists():
    raise FileNotFoundError(
        f"Fake dataset not found:\n{FAKE_PATH}"
    )

if not REAL_PATH.exists():
    raise FileNotFoundError(
        f"Real dataset not found:\n{REAL_PATH}"
    )

# ============================================================
# 3. LOAD DATA
# ============================================================

print("\nLoading dataset...")

fake_df = pd.read_csv(
    FAKE_PATH,
    low_memory=False
)

real_df = pd.read_csv(
    REAL_PATH,
    low_memory=False
)

# Add labels
fake_df["label"] = "Fake"
real_df["label"] = "Real"

# Combine datasets
df = pd.concat(
    [fake_df, real_df],
    ignore_index=True
)

print("Dataset loaded successfully.")

# ============================================================
# 4. BASIC DATASET INFORMATION
# ============================================================

print("\n" + "=" * 75)
print("DATASET INFORMATION")
print("=" * 75)

print(f"Fake records       : {len(fake_df)}")
print(f"Real records       : {len(real_df)}")
print(f"Total records      : {len(df)}")
print(f"Attributes         : {len(df.columns)}")
print(f"Attributes         : {list(df.columns)}")

# Save dataset information
dataset_info = pd.DataFrame({
    "Parameter": [
        "Fake Records",
        "Real Records",
        "Total Records",
        "Number of Attributes"
    ],
    "Value": [
        len(fake_df),
        len(real_df),
        len(df),
        len(df.columns)
    ]
})

dataset_info.to_csv(
    OUTPUT_DIR / "dataset_information.csv",
    index=False
)

# ============================================================
# 5. DATA TYPES
# ============================================================

print("\n" + "=" * 75)
print("DATA TYPES")
print("=" * 75)

print(df.dtypes)

dtype_table = pd.DataFrame({
    "Attribute": df.columns,
    "Data Type": df.dtypes.astype(str).values
})

dtype_table.to_csv(
    OUTPUT_DIR / "data_types.csv",
    index=False
)

# ============================================================
# 6. MISSING VALUE ANALYSIS
# ============================================================

print("\n" + "=" * 75)
print("MISSING VALUES")
print("=" * 75)

missing_values = df.isnull().sum()

missing_percentage = (
    missing_values / len(df)
) * 100

missing_table = pd.DataFrame({
    "Attribute": missing_values.index,
    "Missing Values": missing_values.values,
    "Missing Percentage": missing_percentage.round(2).values
})

print(
    missing_table.to_string(index=False)
)

missing_table.to_csv(
    OUTPUT_DIR / "missing_values.csv",
    index=False
)

# ============================================================
# 7. DUPLICATE ANALYSIS
# ============================================================

print("\n" + "=" * 75)
print("DUPLICATE RECORDS")
print("=" * 75)

fake_duplicates = fake_df.duplicated().sum()
real_duplicates = real_df.duplicated().sum()
total_duplicates = df.duplicated().sum()

print(f"Fake duplicates      : {fake_duplicates}")
print(f"Real duplicates      : {real_duplicates}")
print(f"Total duplicates     : {total_duplicates}")

duplicate_summary = pd.DataFrame({
    "Dataset": [
        "Fake",
        "Real",
        "Combined"
    ],
    "Duplicate Records": [
        fake_duplicates,
        real_duplicates,
        total_duplicates
    ]
})

duplicate_summary.to_csv(
    OUTPUT_DIR / "duplicate_summary.csv",
    index=False
)

# ============================================================
# 8. GRAPH 1
# FAKE VS REAL DISTRIBUTION
# ============================================================

print("\nCreating Graph 1: Fake vs Real distribution...")

label_counts = (
    df["label"]
    .value_counts()
    .reindex(["Fake", "Real"])
)

plt.figure(figsize=(9, 6))

bars = plt.bar(
    label_counts.index,
    label_counts.values
)

plt.title(
    "Distribution of Fake and Real News",
    fontsize=16
)

plt.xlabel(
    "News Label",
    fontsize=12
)

plt.ylabel(
    "Number of Articles",
    fontsize=12
)

# Add values on bars
for bar, value in zip(
    bars,
    label_counts.values
):
    plt.text(
        bar.get_x() + bar.get_width() / 2,
        bar.get_height() + 400,
        f"{value:,}",
        ha="center",
        fontsize=11
    )

plt.tight_layout()

plt.savefig(
    OUTPUT_DIR / "01_fake_real_distribution.png",
    dpi=300,
    bbox_inches="tight"
)

plt.show()
plt.close()

# ============================================================
# 9. GRAPH 2
# SUBJECT DISTRIBUTION
# ============================================================

print("\nCreating Graph 2: Subject distribution...")

subject_counts = (
    df["subject"]
    .value_counts()
)

plt.figure(figsize=(12, 7))

bars = plt.bar(
    subject_counts.index,
    subject_counts.values
)

plt.title(
    "News Articles by Subject",
    fontsize=16
)

plt.xlabel(
    "Subject",
    fontsize=12
)

plt.ylabel(
    "Number of Articles",
    fontsize=12
)

plt.xticks(
    rotation=45,
    ha="right"
)

for bar, value in zip(
    bars,
    subject_counts.values
):
    plt.text(
        bar.get_x() + bar.get_width() / 2,
        bar.get_height() + 150,
        f"{value:,}",
        ha="center",
        fontsize=9
    )

plt.tight_layout()

plt.savefig(
    OUTPUT_DIR / "02_subject_distribution.png",
    dpi=300,
    bbox_inches="tight"
)

plt.show()
plt.close()

# ============================================================
# 10. GRAPH 3
# FAKE VS REAL BY SUBJECT
# ============================================================

print("\nCreating Graph 3: Fake vs Real by subject...")

subject_label = pd.crosstab(
    df["subject"],
    df["label"]
)

# Ensure both labels exist
for column in ["Fake", "Real"]:
    if column not in subject_label.columns:
        subject_label[column] = 0

subject_label = subject_label[
    ["Fake", "Real"]
]

ax = subject_label.plot(
    kind="bar",
    figsize=(13, 7)
)

ax.set_title(
    "Fake vs Real News by Subject",
    fontsize=16
)

ax.set_xlabel(
    "Subject",
    fontsize=12
)

ax.set_ylabel(
    "Number of Articles",
    fontsize=12
)

plt.xticks(
    rotation=45,
    ha="right"
)

plt.legend(
    title="News Label"
)

plt.tight_layout()

plt.savefig(
    OUTPUT_DIR / "03_fake_real_by_subject.png",
    dpi=300,
    bbox_inches="tight"
)

plt.show()
plt.close()

# ============================================================
# 11. TITLE AND TEXT LENGTH
# ============================================================

print("\nCalculating title and text lengths...")

df["title_length"] = (
    df["title"]
    .astype(str)
    .str.len()
)

df["text_length"] = (
    df["text"]
    .astype(str)
    .str.len()
)

# ============================================================
# 12. NUMERICAL STATISTICS
# ============================================================

print("\n" + "=" * 75)
print("TITLE AND TEXT LENGTH STATISTICS")
print("=" * 75)

length_statistics = (
    df[
        [
            "title_length",
            "text_length"
        ]
    ]
    .describe()
)

print(length_statistics)

length_statistics.to_csv(
    OUTPUT_DIR / "text_title_statistics.csv"
)

# ============================================================
# 13. GRAPH 4
# TITLE LENGTH DISTRIBUTION
# ============================================================

print("\nCreating Graph 4: Title length distribution...")

plt.figure(figsize=(11, 6))

plt.hist(
    df["title_length"],
    bins=50
)

plt.title(
    "Distribution of News Title Length",
    fontsize=16
)

plt.xlabel(
    "Title Length (Characters)",
    fontsize=12
)

plt.ylabel(
    "Number of Articles",
    fontsize=12
)

plt.tight_layout()

plt.savefig(
    OUTPUT_DIR / "04_title_length_distribution.png",
    dpi=300,
    bbox_inches="tight"
)

plt.show()
plt.close()

# ============================================================
# 14. GRAPH 5
# TEXT LENGTH DISTRIBUTION
# ============================================================

print("\nCreating Graph 5: Text length distribution...")

# Remove extreme 1% values only for visualization
text_limit = (
    df["text_length"]
    .quantile(0.99)
)

plot_text = df.loc[
    df["text_length"] <= text_limit,
    "text_length"
]

plt.figure(figsize=(11, 6))

plt.hist(
    plot_text,
    bins=50
)

plt.title(
    "Distribution of News Article Text Length",
    fontsize=16
)

plt.xlabel(
    "Text Length (Characters)",
    fontsize=12
)

plt.ylabel(
    "Number of Articles",
    fontsize=12
)

plt.tight_layout()

plt.savefig(
    OUTPUT_DIR / "05_text_length_distribution.png",
    dpi=300,
    bbox_inches="tight"
)

plt.show()
plt.close()

# ============================================================
# 15. GRAPH 6
# FAKE VS REAL TEXT LENGTH BOXPLOT
# ============================================================

print("\nCreating Graph 6: Fake vs Real text length...")

fake_text = df.loc[
    df["label"] == "Fake",
    "text_length"
]

real_text = df.loc[
    df["label"] == "Real",
    "text_length"
]

# Remove extreme values only for visualization
fake_limit = fake_text.quantile(0.99)
real_limit = real_text.quantile(0.99)

fake_text_plot = fake_text[
    fake_text <= fake_limit
]

real_text_plot = real_text[
    real_text <= real_limit
]

plt.figure(figsize=(9, 6))

plt.boxplot(
    [
        fake_text_plot,
        real_text_plot
    ],
    tick_labels=[
        "Fake",
        "Real"
    ]
)

plt.title(
    "Article Text Length: Fake vs Real",
    fontsize=16
)

plt.xlabel(
    "News Label",
    fontsize=12
)

plt.ylabel(
    "Text Length (Characters)",
    fontsize=12
)

plt.tight_layout()

plt.savefig(
    OUTPUT_DIR / "06_fake_real_text_length_boxplot.png",
    dpi=300,
    bbox_inches="tight"
)

plt.show()
plt.close()

# ============================================================
# 16. DATE ANALYSIS
# ============================================================

print("\nProcessing publication dates...")

df["date_parsed"] = pd.to_datetime(
    df["date"],
    errors="coerce"
)

valid_dates = (
    df["date_parsed"]
    .notna()
    .sum()
)

invalid_dates = (
    df["date_parsed"]
    .isna()
    .sum()
)

print(f"Valid dates          : {valid_dates}")
print(f"Invalid dates        : {invalid_dates}")

df["year"] = (
    df["date_parsed"]
    .dt.year
)

year_counts = (
    df["year"]
    .dropna()
    .astype(int)
    .value_counts()
    .sort_index()
)

print("\nArticles by year:")
print(year_counts)

year_table = pd.DataFrame({
    "Year": year_counts.index,
    "Number of Articles": year_counts.values
})

year_table.to_csv(
    OUTPUT_DIR / "articles_by_year.csv",
    index=False
)

# ============================================================
# 17. GRAPH 7
# ARTICLES BY YEAR
# ============================================================

if not year_counts.empty:

    print("\nCreating Graph 7: Articles by publication year...")

    plt.figure(figsize=(12, 6))

    bars = plt.bar(
        year_counts.index.astype(str),
        year_counts.values
    )

    plt.title(
        "News Articles by Publication Year",
        fontsize=16
    )

    plt.xlabel(
        "Publication Year",
        fontsize=12
    )

    plt.ylabel(
        "Number of Articles",
        fontsize=12
    )

    plt.xticks(
        rotation=45
    )

    for bar, value in zip(
        bars,
        year_counts.values
    ):
        plt.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 100,
            f"{value:,}",
            ha="center",
            fontsize=9
        )

    plt.tight_layout()

    plt.savefig(
        OUTPUT_DIR / "07_articles_by_year.png",
        dpi=300,
        bbox_inches="tight"
    )

    plt.show()
    plt.close()

# ============================================================
# 18. LABEL PERCENTAGE
# ============================================================

print("\n" + "=" * 75)
print("LABEL PERCENTAGE")
print("=" * 75)

label_percentage = (
    df["label"]
    .value_counts(normalize=True)
    * 100
).round(2)

print(label_percentage)

label_percentage_table = pd.DataFrame({
    "Label": label_percentage.index,
    "Percentage": label_percentage.values
})

label_percentage_table.to_csv(
    OUTPUT_DIR / "label_percentage.csv",
    index=False
)

# ============================================================
# 19. SUBJECT SUMMARY
# ============================================================

subject_summary = (
    df["subject"]
    .value_counts()
    .reset_index()
)

subject_summary.columns = [
    "Subject",
    "Number of Articles"
]

subject_summary.to_csv(
    OUTPUT_DIR / "subject_summary.csv",
    index=False
)

# ============================================================
# 20. OUTLIER ANALYSIS USING IQR
# ============================================================

print("\n" + "=" * 75)
print("OUTLIER ANALYSIS USING IQR")
print("=" * 75)


def calculate_iqr_outliers(series, name):

    q1 = series.quantile(0.25)
    q3 = series.quantile(0.75)

    iqr = q3 - q1

    lower_bound = q1 - (1.5 * iqr)
    upper_bound = q3 + (1.5 * iqr)

    outliers = series[
        (series < lower_bound)
        |
        (series > upper_bound)
    ]

    print(f"\n{name}")
    print(f"Q1              : {q1:.2f}")
    print(f"Q3              : {q3:.2f}")
    print(f"IQR             : {iqr:.2f}")
    print(f"Lower Bound     : {lower_bound:.2f}")
    print(f"Upper Bound     : {upper_bound:.2f}")
    print(f"Outliers        : {len(outliers)}")

    return {
        "Attribute": name,
        "Q1": q1,
        "Q3": q3,
        "IQR": iqr,
        "Lower Bound": lower_bound,
        "Upper Bound": upper_bound,
        "Outlier Count": len(outliers)
    }


outlier_results = []

outlier_results.append(
    calculate_iqr_outliers(
        df["title_length"],
        "Title Length"
    )
)

outlier_results.append(
    calculate_iqr_outliers(
        df["text_length"],
        "Text Length"
    )
)

outlier_table = pd.DataFrame(
    outlier_results
)

outlier_table.to_csv(
    OUTPUT_DIR / "outlier_analysis.csv",
    index=False
)

# ============================================================
# 21. COMPLETE EDA SUMMARY
# ============================================================

summary = pd.DataFrame({
    "Parameter": [
        "Total Records",
        "Fake Records",
        "Real Records",
        "Number of Attributes",
        "Duplicate Records",
        "Total Missing Values",
        "Valid Dates",
        "Invalid Dates",
        "Average Title Length",
        "Median Title Length",
        "Average Text Length",
        "Median Text Length"
    ],
    "Value": [
        len(df),
        len(fake_df),
        len(real_df),
        len(df.columns),
        total_duplicates,
        int(df.isnull().sum().sum()),
        valid_dates,
        invalid_dates,
        round(df["title_length"].mean(), 2),
        round(df["title_length"].median(), 2),
        round(df["text_length"].mean(), 2),
        round(df["text_length"].median(), 2)
    ]
})

summary.to_csv(
    OUTPUT_DIR / "eda_summary.csv",
    index=False
)

# ============================================================
# 22. SAVE ANALYSIS DATA
# ============================================================

analysis_columns = [
    "title",
    "text",
    "subject",
    "date",
    "label",
    "title_length",
    "text_length"
]

df[
    analysis_columns
].to_csv(
    OUTPUT_DIR / "original_dataset_eda.csv",
    index=False
)

# ============================================================
# 23. FINAL OUTPUT
# ============================================================

print("\n" + "=" * 75)
print("PART A EDA COMPLETED SUCCESSFULLY")
print("=" * 75)

print("\nOutput directory:")
print(OUTPUT_DIR)

print("\nGenerated graphs:")

for file in sorted(
    OUTPUT_DIR.glob("*.png")
):
    print(" -", file.name)

print("\nGenerated analysis files:")

for file in sorted(
    OUTPUT_DIR.glob("*.csv")
):
    print(" -", file.name)

print("\n" + "=" * 75)
print("READY FOR PHASE 1 REPORT - PART A")
print("=" * 75)