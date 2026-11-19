import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os


# ============================================================
# CONFIGURATION
# ============================================================

INPUT_FILE = "processed_data/career_fused_dataset.csv"

OUTPUT_DIR = "eda_output"

os.makedirs(OUTPUT_DIR, exist_ok=True)


# ============================================================
# 1. LOAD DATASET
# ============================================================

print("\n========================================")
print("LOADING FUSED DATASET")
print("========================================")

df = pd.read_csv(
    INPUT_FILE,
    encoding="utf-8-sig"
)

print("Dataset loaded successfully.")
print("Shape:", df.shape)


# ============================================================
# 2. BASIC DATASET INFORMATION
# ============================================================

print("\n========================================")
print("BASIC INFORMATION")
print("========================================")

rows, columns = df.shape

print("Number of records:", rows)
print("Number of attributes:", columns)

print("\nColumns:")

for i, column in enumerate(df.columns, 1):
    print(i, ".", column)


with open(
    os.path.join(OUTPUT_DIR, "dataset_summary.txt"),
    "w",
    encoding="utf-8"
) as f:

    f.write("FUSED DATASET SUMMARY\n")
    f.write("=====================\n\n")

    f.write(f"Number of records: {rows}\n")
    f.write(f"Number of attributes: {columns}\n\n")

    f.write("Columns:\n")

    for i, column in enumerate(df.columns, 1):
        f.write(f"{i}. {column}\n")


# ============================================================
# 3. DATA TYPES
# ============================================================

print("\n========================================")
print("DATA TYPES")
print("========================================")

print(df.dtypes)

df.dtypes.astype(str).to_csv(
    os.path.join(OUTPUT_DIR, "data_types.csv")
)


# ============================================================
# 4. UNIQUE VALUES
# ============================================================

print("\n========================================")
print("UNIQUE VALUES")
print("========================================")

unique_values = df.nunique()

print(unique_values)

unique_values.to_csv(
    os.path.join(OUTPUT_DIR, "unique_values.csv")
)


# ============================================================
# 5. DUPLICATE RECORDS
# ============================================================

print("\n========================================")
print("DUPLICATE RECORDS")
print("========================================")

duplicate_count = df.duplicated().sum()

print("Duplicate records:", duplicate_count)

duplicate_rows = df[
    df.duplicated(keep=False)
]

duplicate_rows.to_csv(
    os.path.join(
        OUTPUT_DIR,
        "duplicate_records.csv"
    ),
    index=False
)


# ============================================================
# 6. DUPLICATE JOB TITLES
# ============================================================

print("\n========================================")
print("DUPLICATE JOB TITLES")
print("========================================")

if "Job Title" in df.columns:

    duplicate_job_titles = (
        df["Job Title"]
        .fillna("Unknown")
        .value_counts()
    )

    duplicate_job_titles = duplicate_job_titles[
        duplicate_job_titles > 1
    ]

    print(duplicate_job_titles)

    duplicate_job_titles.to_csv(
        os.path.join(
            OUTPUT_DIR,
            "duplicate_job_titles.csv"
        )
    )


# ============================================================
# 7. MISSING VALUES
# ============================================================

print("\n========================================")
print("MISSING VALUES")
print("========================================")

missing_count = df.isnull().sum()

missing_percentage = (
    df.isnull().mean() * 100
)

missing_table = pd.DataFrame({

    "Missing Count": missing_count,

    "Missing Percentage":
        missing_percentage.round(2)

})

print(missing_table)

missing_table.to_csv(
    os.path.join(
        OUTPUT_DIR,
        "missing_values.csv"
    )
)


# ============================================================
# 8. MISSING DATA BAR CHART
# ============================================================

plt.figure(figsize=(12, 6))

missing_percentage.sort_values(
    ascending=False
).plot(
    kind="bar"
)

plt.title(
    "Missing Data Percentage by Attribute"
)

plt.xlabel("Attributes")

plt.ylabel(
    "Missing Percentage (%)"
)

plt.xticks(
    rotation=45,
    ha="right"
)

plt.tight_layout()

plt.savefig(
    os.path.join(
        OUTPUT_DIR,
        "missing_data.png"
    ),
    dpi=300
)

plt.close()


# ============================================================
# 9. API RESOURCE AVAILABILITY
# ============================================================

print("\n========================================")
print("API RESOURCE AVAILABILITY")
print("========================================")


resource_columns = [

    "resume_samples",

    "remotive_jobs",

    "youtube_resources",

    "github_projects",

    "technical_books",

    "research_papers"

]


resource_counts = {}


for column in resource_columns:

    if column in df.columns:

        count = (
            df[column]
            .fillna("")
            .astype(str)
            .str.strip()
            .replace("nan", "")
            .ne("")
            .sum()
        )

        resource_counts[column] = count

        print(
            column,
            ":",
            count
        )


resource_df = pd.DataFrame(
    list(resource_counts.items()),
    columns=[
        "Resource",
        "Available Records"
    ]
)


resource_df.to_csv(
    os.path.join(
        OUTPUT_DIR,
        "api_resource_availability.csv"
    ),
    index=False
)


# ============================================================
# 10. API RESOURCE CHART
# ============================================================

if not resource_df.empty:

    plt.figure(figsize=(12, 6))

    plt.bar(
        resource_df["Resource"],
        resource_df["Available Records"]
    )

    plt.title(
        "Availability of External API / Resource Data"
    )

    plt.xlabel("Resource")

    plt.ylabel(
        "Number of Records"
    )

    plt.xticks(
        rotation=45,
        ha="right"
    )

    plt.tight_layout()

    plt.savefig(
        os.path.join(
            OUTPUT_DIR,
            "api_resource_availability.png"
        ),
        dpi=300
    )

    plt.close()


# ============================================================
# 11. CAREER ROLE DISTRIBUTION
# ============================================================

print("\n========================================")
print("CAREER ROLE ANALYSIS")
print("========================================")


if "career_role" in df.columns:

    career_counts = (
        df["career_role"]
        .fillna("Unknown")
        .value_counts()
    )

    print("\nTop 20 Career Roles:")

    print(
        career_counts.head(20)
    )

    career_counts.head(20).to_csv(
        os.path.join(
            OUTPUT_DIR,
            "top_career_roles.csv"
        )
    )


# ============================================================
# 12. TOP CAREER ROLE CHART
# ============================================================

if "career_role" in df.columns:

    top_roles = (
        df["career_role"]
        .fillna("Unknown")
        .value_counts()
        .head(15)
    )

    plt.figure(figsize=(12, 7))

    top_roles.sort_values().plot(
        kind="barh"
    )

    plt.title(
        "Top 15 Career Roles"
    )

    plt.xlabel(
        "Number of Records"
    )

    plt.ylabel(
        "Career Role"
    )

    plt.tight_layout()

    plt.savefig(
        os.path.join(
            OUTPUT_DIR,
            "top_career_roles.png"
        ),
        dpi=300
    )

    plt.close()


# ============================================================
# 13. CREATE RESOURCE COUNT VARIABLES
# ============================================================

print("\n========================================")
print("CREATING RESOURCE COUNTS")
print("========================================")


for column in resource_columns:

    if column in df.columns:

        df[column + "_count"] = (

            df[column]
            .fillna("")
            .astype(str)
            .apply(
                lambda x:
                0 if x.strip() == ""
                else len(
                    [
                        item
                        for item in x.split("|")
                        if item.strip()
                    ]
                )
            )
        )


# ============================================================
# 14. NUMERICAL DATA ANALYSIS
# ============================================================

print("\n========================================")
print("NUMERICAL ANALYSIS")
print("========================================")

numeric_columns = df.select_dtypes(
    include=np.number
).columns

print(
    "Numerical columns:",
    list(numeric_columns)
)


if len(numeric_columns) > 0:

    numerical_summary = df[
        numeric_columns
    ].describe().T

    numerical_summary[
        [
            "count",
            "mean",
            "std",
            "min",
            "25%",
            "50%",
            "75%",
            "max"
        ]
    ].to_csv(
        os.path.join(
            OUTPUT_DIR,
            "numerical_summary.csv"
        )
    )

    print(
        numerical_summary
    )


# ============================================================
# 15. RESOURCE COUNT SUMMARY
# ============================================================

print("\n========================================")
print("RESOURCE COUNT SUMMARY")
print("========================================")


count_columns = [

    column
    for column in df.columns
    if column.endswith("_count")

]


if count_columns:

    resource_count_summary = (
        df[count_columns]
        .describe()
        .T
    )

    print(
        resource_count_summary
    )

    resource_count_summary.to_csv(
        os.path.join(
            OUTPUT_DIR,
            "resource_count_summary.csv"
        )
    )


# ============================================================
# 16. OUTLIER DETECTION USING IQR
# ============================================================

print("\n========================================")
print("OUTLIER ANALYSIS")
print("========================================")


outlier_results = []


for column in count_columns:

    Q1 = df[column].quantile(0.25)

    Q3 = df[column].quantile(0.75)

    IQR = Q3 - Q1

    lower_limit = Q1 - 1.5 * IQR

    upper_limit = Q3 + 1.5 * IQR

    outliers = df[
        (df[column] < lower_limit) |
        (df[column] > upper_limit)
    ]

    outlier_count = len(outliers)

    outlier_results.append({

        "Attribute": column,

        "Q1": Q1,

        "Q3": Q3,

        "IQR": IQR,

        "Lower Limit": lower_limit,

        "Upper Limit": upper_limit,

        "Outlier Count": outlier_count

    })

    print(
        column,
        "-> Outliers:",
        outlier_count
    )


outlier_df = pd.DataFrame(
    outlier_results
)


outlier_df.to_csv(
    os.path.join(
        OUTPUT_DIR,
        "outlier_analysis.csv"
    ),
    index=False
)


# ============================================================
# 17. BOXPLOTS
# ============================================================

for column in count_columns:

    plt.figure(figsize=(8, 5))

    plt.boxplot(
        df[column].dropna()
    )

    plt.title(
        f"Boxplot - {column}"
    )

    plt.ylabel("Count")

    plt.tight_layout()

    safe_name = (
        column
        .replace("/", "_")
        .replace(" ", "_")
    )

    plt.savefig(
        os.path.join(
            OUTPUT_DIR,
            f"boxplot_{safe_name}.png"
        ),
        dpi=300
    )

    plt.close()


# ============================================================
# 18. HISTOGRAMS
# ============================================================

for column in count_columns:

    plt.figure(figsize=(8, 5))

    plt.hist(
        df[column].dropna(),
        bins=10
    )

    plt.title(
        f"Distribution - {column}"
    )

    plt.xlabel("Count")

    plt.ylabel("Frequency")

    plt.tight_layout()

    safe_name = (
        column
        .replace("/", "_")
        .replace(" ", "_")
    )

    plt.savefig(
        os.path.join(
            OUTPUT_DIR,
            f"histogram_{safe_name}.png"
        ),
        dpi=300
    )

    plt.close()


# ============================================================
# 19. RESOURCE COMPARISON
# ============================================================

print("\n========================================")
print("RESOURCE COMPARISON")
print("========================================")


if count_columns:

    average_resources = (
        df[count_columns]
        .mean()
        .sort_values(
            ascending=False
        )
    )

    print(
        average_resources
    )

    average_resources.to_csv(
        os.path.join(
            OUTPUT_DIR,
            "average_resource_counts.csv"
        )
    )


# ============================================================
# 20. MULTIVARIATE CORRELATION
# ============================================================

print("\n========================================")
print("CORRELATION ANALYSIS")
print("========================================")


if len(count_columns) >= 2:

    correlation = df[
        count_columns
    ].corr()

    print(
        correlation
    )

    correlation.to_csv(
        os.path.join(
            OUTPUT_DIR,
            "resource_correlation.csv"
        )
    )

    plt.figure(
        figsize=(10, 8)
    )

    plt.imshow(
        correlation,
        interpolation="nearest"
    )

    plt.title(
        "Correlation Between Resource Variables"
    )

    plt.xticks(
        range(len(correlation.columns)),
        correlation.columns,
        rotation=45,
        ha="right"
    )

    plt.yticks(
        range(len(correlation.columns)),
        correlation.columns
    )

    plt.colorbar()

    plt.tight_layout()

    plt.savefig(
        os.path.join(
            OUTPUT_DIR,
            "correlation_heatmap.png"
        ),
        dpi=300
    )

    plt.close()


# ============================================================
# 21. BIVARIATE ANALYSIS
# CAREER ROLE VS API RESOURCES
# ============================================================

print("\n========================================")
print("BIVARIATE ANALYSIS")
print("CAREER ROLE VS API RESOURCES")
print("========================================")


if "career_role" in df.columns and count_columns:

    # Create a temporary dataframe
    role_resource = (
        df.groupby("career_role")[count_columns]
        .sum()
    )

    # Add total resources
    role_resource["total_resources"] = (
        role_resource[count_columns]
        .sum(axis=1)
    )

    # Select top 10 career roles based on total resources
    top_role_resource = (
        role_resource
        .sort_values(
            "total_resources",
            ascending=False
        )
        .head(10)
    )

    # Remove total column before saving
    top_role_resource[count_columns].to_csv(
        os.path.join(
            OUTPUT_DIR,
            "career_role_resource_analysis.csv"
        )
    )

    print("\nTop Career Roles by API Resource Availability:")

    print(
        top_role_resource[count_columns]
    )


    # --------------------------------------------------------
    # GROUPED BAR CHART
    # --------------------------------------------------------

    chart_data = top_role_resource[count_columns]

    plt.figure(
        figsize=(16, 9)
    )

    x = np.arange(
        len(chart_data.index)
    )

    number_of_resources = len(
        count_columns
    )

    bar_width = (
        0.8 / number_of_resources
    )


    for i, column in enumerate(count_columns):

        plt.bar(
            x + i * bar_width,
            chart_data[column],
            width=bar_width,
            label=column.replace(
                "_count",
                ""
            )
        )


    plt.title(
        "Career Role vs API Resource Availability",
        fontsize=16
    )

    plt.xlabel(
        "Career Role",
        fontsize=12
    )

    plt.ylabel(
        "Number of Resources",
        fontsize=12
    )

    plt.xticks(
        x + (bar_width * (number_of_resources - 1) / 2),
        chart_data.index,
        rotation=45,
        ha="right"
    )

    plt.legend(
        title="API Resources",
        bbox_to_anchor=(1.02, 1),
        loc="upper left"
    )

    plt.tight_layout()

    plt.savefig(
        os.path.join(
            OUTPUT_DIR,
            "career_role_vs_api_resources.png"
        ),
        dpi=300,
        bbox_inches="tight"
    )

    plt.close()

    print(
        "\nBivariate graph created successfully:"
    )

    print(
        "career_role_vs_api_resources.png"
    )


# ============================================================
# 22. CAREER ROLE VS RESOURCES DATA
# ============================================================

print("\n========================================")
print("CAREER ROLE VS RESOURCES")
print("========================================")


if "career_role" in df.columns and count_columns:

    role_resource = (
        df.groupby("career_role")[count_columns]
        .sum()
        .sort_values(
            by=count_columns[0],
            ascending=False
        )
        .head(20)
    )

    print(
        role_resource
    )

    role_resource.to_csv(
        os.path.join(
            OUTPUT_DIR,
            "career_role_resource_analysis_top20.csv"
        )
    )


# ============================================================
# 23. FINAL DATASET STRUCTURE
# ============================================================

print("\n========================================")
print("FINAL DATA QUALITY SUMMARY")
print("========================================")


print(
    "Rows:",
    len(df)
)

print(
    "Columns:",
    len(df.columns)
)

print(
    "Duplicate rows:",
    df.duplicated().sum()
)

print(
    "Total missing values:",
    df.isnull().sum().sum()
)

print(
    "Unique Job Titles:",
    df["Job Title"].nunique()
    if "Job Title" in df.columns
    else "Column not found"
)


# ============================================================
# 24. SAVE CLEAN EDA COPY
# ============================================================

eda_copy_path = os.path.join(
    OUTPUT_DIR,
    "career_fused_eda_copy.csv"
)

df.to_csv(
    eda_copy_path,
    index=False,
    encoding="utf-8-sig"
)


# ============================================================
# 25. COMPLETED
# ============================================================

print("\n========================================")
print("EDA COMPLETED SUCCESSFULLY")
print("========================================")

print(
    "All output files are available inside:"
)

print(
    OUTPUT_DIR
)

print("\nImportant files:")

print(
    "1. dataset_summary.txt"
)

print(
    "2. missing_values.csv"
)

print(
    "3. missing_data.png"
)

print(
    "4. api_resource_availability.csv"
)

print(
    "5. api_resource_availability.png"
)

print(
    "6. duplicate_records.csv"
)

print(
    "7. duplicate_job_titles.csv"
)

print(
    "8. numerical_summary.csv"
)

print(
    "9. resource_count_summary.csv"
)

print(
    "10. outlier_analysis.csv"
)

print(
    "11. correlation_heatmap.png"
)

print(
    "12. career_role_resource_analysis.csv"
)

print(
    "13. career_role_vs_api_resources.png"
)

print(
    "\nOriginal dataset was NOT modified."
)