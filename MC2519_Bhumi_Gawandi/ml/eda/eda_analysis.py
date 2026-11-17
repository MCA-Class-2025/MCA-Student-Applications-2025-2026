from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt


# ============================================================
# PROJECT PATH
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

# FUSED DATASET
DATASET_PATH = (
    PROJECT_ROOT
    / "ml"
    / "data_fusion"
    / "results"
    / "fused_financial_data.csv"

)

# EDA RESULTS
RESULTS_DIR = (
    PROJECT_ROOT
    / "eda"
    / "results"
)

CHARTS_DIR = (
    RESULTS_DIR
    / "charts"
)

RESULTS_DIR.mkdir(
    parents=True,
    exist_ok=True
)

CHARTS_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# ============================================================
# START
# ============================================================

print()
print("=" * 60)
print("EDA ANALYSIS ON FUSED DATASET")
print("=" * 60)


# ============================================================
# CHECK DATASET
# ============================================================

print()
print("Dataset path:")
print(DATASET_PATH)


if not DATASET_PATH.exists():

    print()
    print("ERROR: Fused dataset not found.")
    print()
    print("Expected:")
    print(DATASET_PATH)
    print()

    exit()


# ============================================================
# LOAD DATASET
# ============================================================

df = pd.read_csv(
    DATASET_PATH
)


print()
print("=" * 60)
print("DATASET OVERVIEW")
print("=" * 60)

print(
    "Total records:",
    len(df)
)

print(
    "Total columns:",
    len(df.columns)
)

print()
print("Columns:")

print(
    df.columns.tolist()
)


# ============================================================
# DATA TYPES
# ============================================================

print()
print("=" * 60)
print("DATA TYPES")
print("=" * 60)

print(
    df.dtypes
)

df.dtypes.astype(str).to_csv(
    RESULTS_DIR / "data_types.csv",
    header=["Data Type"]
)


# ============================================================
# MISSING VALUES
# ============================================================

print()
print("=" * 60)
print("MISSING VALUES")
print("=" * 60)

missing_values = (
    df.isnull()
    .sum()
    .sort_values(
        ascending=False
    )
)

print(
    missing_values
)

missing_values.to_csv(
    RESULTS_DIR / "missing_values.csv",
    header=["Missing Values"]
)


# ============================================================
# DUPLICATES
# ============================================================

print()
print("=" * 60)
print("DUPLICATES")
print("=" * 60)

duplicate_count = (
    df.duplicated()
    .sum()
)

print(
    "Duplicate records:",
    duplicate_count
)


duplicate_df = pd.DataFrame({

    "Metric": [
        "Duplicate Records"
    ],

    "Value": [
        duplicate_count
    ]

})

duplicate_df.to_csv(
    RESULTS_DIR / "duplicates.csv",
    index=False
)


# ============================================================
# DATE PROCESSING
# ============================================================

df["date"] = pd.to_datetime(
    df["date"],
    errors="coerce"
)

df["Year"] = (
    df["date"]
    .dt.year
)

df["Month"] = (
    df["date"]
    .dt.month
)

df["YearMonth"] = (
    df["date"]
    .dt.to_period("M")
    .astype(str)
)


# ============================================================
# AMOUNT CONVERSION
# ============================================================

df["amount"] = pd.to_numeric(
    df["amount"],
    errors="coerce"
)


# ============================================================
# BASIC STATISTICS
# ============================================================

print()
print("=" * 60)
print("AMOUNT STATISTICS")
print("=" * 60)

amount_statistics = (
    df["amount"]
    .describe()
)

print(
    amount_statistics
)

amount_statistics.to_csv(
    RESULTS_DIR / "amount_statistics.csv",
    header=["Value"]
)


# ============================================================
# DATA SOURCE ANALYSIS
# ============================================================

print()
print("=" * 60)
print("DATA SOURCE ANALYSIS")
print("=" * 60)

source_counts = (
    df["source"]
    .value_counts()
)

print(
    source_counts
)

source_counts.to_csv(
    RESULTS_DIR / "source_distribution.csv",
    header=["Count"]
)


# ============================================================
# SOURCE AMOUNT
# ============================================================

source_amount = (
    df.groupby("source")["amount"]
    .sum()
    .sort_values(
        ascending=False
    )
)

print()
print("=" * 60)
print("AMOUNT BY DATA SOURCE")
print("=" * 60)

print(
    source_amount
)

source_amount.to_csv(
    RESULTS_DIR / "source_amount.csv",
    header=["Total Amount"]
)


# ============================================================
# CATEGORY ANALYSIS
# ============================================================

print()
print("=" * 60)
print("CATEGORY ANALYSIS")
print("=" * 60)

category_counts = (
    df["category"]
    .value_counts()
)

print(
    category_counts
)

category_counts.to_csv(
    RESULTS_DIR / "category_distribution.csv",
    header=["Count"]
)


# ============================================================
# CATEGORY AMOUNT
# ============================================================

category_amount = (
    df.groupby("category")["amount"]
    .sum()
    .sort_values(
        ascending=False
    )
)

print()
print("=" * 60)
print("CATEGORY-WISE AMOUNT")
print("=" * 60)

print(
    category_amount
)

category_amount.to_csv(
    RESULTS_DIR / "category_amount.csv",
    header=["Total Amount"]
)


# ============================================================
# TYPE ANALYSIS
# ============================================================

print()
print("=" * 60)
print("TYPE ANALYSIS")
print("=" * 60)

type_counts = (
    df["type"]
    .value_counts()
)

print(
    type_counts
)

type_counts.to_csv(
    RESULTS_DIR / "type_distribution.csv",
    header=["Count"]
)


# ============================================================
# INCOME
# ============================================================

income_total = (
    df.loc[
        df["type"] == "Income",
        "amount"
    ]
    .sum()
)


# ============================================================
# EXPENSE
# ============================================================

expense_total = (
    df.loc[
        df["type"] == "Expense",
        "amount"
    ]
    .sum()
)


print()
print("=" * 60)
print("TOTAL AMOUNTS")
print("=" * 60)

print(
    "Total Income :",
    round(
        income_total,
        2
    )
)

print(
    "Total Expense:",
    round(
        expense_total,
        2
    )
)


# ============================================================
# AVERAGE EXPENSE
# ============================================================

expense_values = (
    df.loc[
        df["type"] == "Expense",
        "amount"
    ]
    .dropna()
)

if len(expense_values) > 0:

    average_expense = (
        expense_values.mean()
    )

else:

    average_expense = 0


print()
print(
    "Average Expense:",
    round(
        average_expense,
        2
    )
)


# ============================================================
# MONTHLY EXPENSE
# ============================================================

monthly_expense = (
    df[
        df["type"] == "Expense"
    ]
    .groupby(
        "YearMonth"
    )["amount"]
    .sum()
    .reset_index()
)

monthly_expense.columns = [
    "YearMonth",
    "Total_Expense"
]


print()
print("=" * 60)
print("MONTHLY EXPENSE")
print("=" * 60)

print(
    monthly_expense.head(10)
)


monthly_expense.to_csv(
    RESULTS_DIR
    / "monthly_expense_eda.csv",
    index=False
)


# ============================================================
# YEARLY EXPENSE
# ============================================================

yearly_expense = (
    df[
        df["type"] == "Expense"
    ]
    .groupby(
        "Year"
    )["amount"]
    .sum()
    .reset_index()
)

yearly_expense.columns = [
    "Year",
    "Total_Expense"
]


print()
print("=" * 60)
print("YEARLY EXPENSE")
print("=" * 60)

print(
    yearly_expense
)


yearly_expense.to_csv(
    RESULTS_DIR
    / "yearly_expense_eda.csv",
    index=False
)


# ============================================================
# ANOMALY ANALYSIS
# ============================================================

print()
print("=" * 60)
print("ANOMALY ANALYSIS")
print("=" * 60)


if "anomaly_status" in df.columns:

    anomaly_counts = (
        df["anomaly_status"]
        .replace(
            "",
            "Not Available"
        )
        .fillna(
            "Not Available"
        )
        .value_counts()
    )

    print(
        anomaly_counts
    )

    anomaly_counts.to_csv(
        RESULTS_DIR
        / "anomaly_distribution.csv",
        header=["Count"]
    )

else:

    print(
        "Anomaly column not found."
    )

    anomaly_counts = pd.Series(
        dtype="int64"
    )


# ============================================================
# ANOMALY AMOUNT
# ============================================================

if (
    "anomaly_status" in df.columns
):

    anomaly_amount = (
        df[
            df["anomaly_status"]
            == "Anomaly"
        ]
        .groupby(
            "category"
        )["amount"]
        .sum()
        .sort_values(
            ascending=False
        )
    )

    anomaly_amount.to_csv(
        RESULTS_DIR
        / "anomaly_category_amount.csv",
        header=["Total Amount"]
    )


# ============================================================
# API ANALYSIS
# ============================================================

print()
print("=" * 60)
print("API DATA ANALYSIS")
print("=" * 60)


api_sources = [

    "Groq AI",

    "Financial News API",

    "Currency API",

    "Exchange Rate API",

    "Receipt OCR"

]


api_records = []


for source in api_sources:

    count = (
        df[
            df["source"] == source
        ]
        .shape[0]
    )

    api_records.append({

        "Source":
            source,

        "Records":
            count

    })


api_df = pd.DataFrame(
    api_records
)


print(
    api_df
)


api_df.to_csv(
    RESULTS_DIR
    / "api_data_summary.csv",
    index=False
)


# ============================================================
# FINANCIAL TRANSACTION SUMMARY
# ============================================================

financial_df = df[
    df["type"].isin(
        [
            "Income",
            "Expense"
        ]
    )
].copy()


financial_summary = pd.DataFrame({

    "Metric": [

        "Total Financial Transactions",

        "Total Income",

        "Total Expense",

        "Average Expense",

        "Highest Expense",

        "Lowest Expense"

    ],

    "Value": [

        len(
            financial_df
        ),

        round(
            income_total,
            2
        ),

        round(
            expense_total,
            2
        ),

        round(
            average_expense,
            2
        ),

        round(
            expense_values.max()
            if len(expense_values) > 0
            else 0,
            2
        ),

        round(
            expense_values.min()
            if len(expense_values) > 0
            else 0,
            2
        )

    ]

})


financial_summary.to_csv(
    RESULTS_DIR
    / "financial_summary.csv",
    index=False
)


# ============================================================
# CHART 1
# DATA SOURCE DISTRIBUTION
# ============================================================

plt.figure(
    figsize=(10, 6)
)

source_counts.plot(
    kind="bar"
)

plt.title(
    "Data Records by Source"
)

plt.xlabel(
    "Data Source"
)

plt.ylabel(
    "Number of Records"
)

plt.xticks(
    rotation=45,
    ha="right"
)

plt.tight_layout()

plt.savefig(
    CHARTS_DIR
    / "source_distribution.png",
    dpi=150
)

plt.close()


# ============================================================
# CHART 2
# CATEGORY DISTRIBUTION
# ============================================================

plt.figure(
    figsize=(10, 6)
)

category_counts.plot(
    kind="bar"
)

plt.title(
    "Transaction Distribution by Category"
)

plt.xlabel(
    "Category"
)

plt.ylabel(
    "Number of Records"
)

plt.xticks(
    rotation=45,
    ha="right"
)

plt.tight_layout()

plt.savefig(
    CHARTS_DIR
    / "category_distribution.png",
    dpi=150
)

plt.close()


# ============================================================
# CHART 3
# CATEGORY AMOUNT
# ============================================================

plt.figure(
    figsize=(10, 6)
)

category_amount.plot(
    kind="bar"
)

plt.title(
    "Total Amount by Category"
)

plt.xlabel(
    "Category"
)

plt.ylabel(
    "Total Amount"
)

plt.xticks(
    rotation=45,
    ha="right"
)

plt.tight_layout()

plt.savefig(
    CHARTS_DIR
    / "category_amount.png",
    dpi=150
)

plt.close()


# ============================================================
# CHART 4
# INCOME VS EXPENSE
# ============================================================

income_expense = pd.Series({

    "Income":
        income_total,

    "Expense":
        expense_total

})


plt.figure(
    figsize=(7, 5)
)

income_expense.plot(
    kind="bar"
)

plt.title(
    "Total Income vs Total Expense"
)

plt.xlabel(
    "Type"
)

plt.ylabel(
    "Amount"
)

plt.xticks(
    rotation=0
)

plt.tight_layout()

plt.savefig(
    CHARTS_DIR
    / "income_vs_expense_amount.png",
    dpi=150
)

plt.close()


# ============================================================
# CHART 5
# TRANSACTION TYPE
# ============================================================

plt.figure(
    figsize=(7, 5)
)

type_counts.plot(
    kind="bar"
)

plt.title(
    "Income vs Expense Transactions"
)

plt.xlabel(
    "Type"
)

plt.ylabel(
    "Number of Transactions"
)

plt.xticks(
    rotation=0
)

plt.tight_layout()

plt.savefig(
    CHARTS_DIR
    / "transaction_type.png",
    dpi=150
)

plt.close()


# ============================================================
# CHART 6
# MONTHLY EXPENSE TREND
# ============================================================

if not monthly_expense.empty:

    plt.figure(
        figsize=(14, 6)
    )

    plt.plot(
        monthly_expense[
            "YearMonth"
        ],
        monthly_expense[
            "Total_Expense"
        ],
        marker="o"
    )

    plt.title(
        "Monthly Expense Trend"
    )

    plt.xlabel(
        "Month"
    )

    plt.ylabel(
        "Total Expense"
    )

    plt.xticks(
        rotation=90
    )

    plt.tight_layout()

    plt.savefig(
        CHARTS_DIR
        / "monthly_expense_trend.png",
        dpi=150
    )

    plt.close()


# ============================================================
# CHART 7
# YEARLY EXPENSE
# ============================================================

if not yearly_expense.empty:

    plt.figure(
        figsize=(8, 5)
    )

    plt.plot(
        yearly_expense[
            "Year"
        ],
        yearly_expense[
            "Total_Expense"
        ],
        marker="o"
    )

    plt.title(
        "Yearly Expense Trend"
    )

    plt.xlabel(
        "Year"
    )

    plt.ylabel(
        "Total Expense"
    )

    plt.tight_layout()

    plt.savefig(
        CHARTS_DIR
        / "yearly_expense_trend.png",
        dpi=150
    )

    plt.close()


# ============================================================
# CHART 8
# AMOUNT DISTRIBUTION
# ============================================================

amount_values = (
    df["amount"]
    .dropna()
)

if not amount_values.empty:

    plt.figure(
        figsize=(10, 6)
    )

    plt.hist(
        amount_values,
        bins=30
    )

    plt.title(
        "Transaction Amount Distribution"
    )

    plt.xlabel(
        "Amount"
    )

    plt.ylabel(
        "Frequency"
    )

    plt.tight_layout()

    plt.savefig(
        CHARTS_DIR
        / "amount_distribution.png",
        dpi=150
    )

    plt.close()


# ============================================================
# CHART 9
# ANOMALY DISTRIBUTION
# ============================================================

if not anomaly_counts.empty:

    plt.figure(
        figsize=(7, 5)
    )

    anomaly_counts.plot(
        kind="bar"
    )

    plt.title(
        "Anomaly Distribution"
    )

    plt.xlabel(
        "Anomaly Status"
    )

    plt.ylabel(
        "Number of Records"
    )

    plt.xticks(
        rotation=0
    )

    plt.tight_layout()

    plt.savefig(
        CHARTS_DIR
        / "anomaly_distribution.png",
        dpi=150
    )

    plt.close()


# ============================================================
# CHART 10
# API DATA
# ============================================================

plt.figure(
    figsize=(10, 6)
)

plt.bar(
    api_df["Source"],
    api_df["Records"]
)

plt.title(
    "API Data Records"
)

plt.xlabel(
    "API Source"
)

plt.ylabel(
    "Number of Records"
)

plt.xticks(
    rotation=45,
    ha="right"
)

plt.tight_layout()

plt.savefig(
    CHARTS_DIR
    / "api_data_summary.png",
    dpi=150
)

plt.close()


# ============================================================
# EDA SUMMARY
# ============================================================

start_date = (
    df["date"].min()
)

end_date = (
    df["date"].max()
)


summary = {

    "Total Records":
        len(df),

    "Total Columns":
        len(df.columns),

    "Total Categories":
        df["category"]
        .nunique(),

    "Total Data Sources":
        df["source"]
        .nunique(),

    "Total Income":
        round(
            income_total,
            2
        ),

    "Total Expense":
        round(
            expense_total,
            2
        ),

    "Average Expense":
        round(
            average_expense,
            2
        ),

    "Missing Values":
        int(
            df.isnull()
            .sum()
            .sum()
        ),

    "Duplicate Records":
        int(
            duplicate_count
        ),

    "Start Date":
        str(
            start_date.date()
        )
        if pd.notna(start_date)
        else "",

    "End Date":
        str(
            end_date.date()
        )
        if pd.notna(end_date)
        else ""

}


# ============================================================
# ANOMALY SUMMARY
# ============================================================

if (
    "anomaly_status" in df.columns
):

    anomaly_count = (
        (
            df["anomaly_status"]
            == "Anomaly"
        )
        .sum()
    )

else:

    anomaly_count = 0


summary[
    "Anomalies"
] = int(
    anomaly_count
)


summary_df = pd.DataFrame(
    list(
        summary.items()
    ),
    columns=[
        "Metric",
        "Value"
    ]
)


summary_df.to_csv(
    RESULTS_DIR
    / "eda_summary.csv",
    index=False
)


# ============================================================
# SAVE CLEAN EDA DATASET
# ============================================================

df.to_csv(
    RESULTS_DIR
    / "eda_dataset.csv",
    index=False
)


# ============================================================
# COMPLETE
# ============================================================

print()
print("=" * 60)
print("EDA COMPLETED SUCCESSFULLY")
print("=" * 60)

print()
print(
    "EDA results saved at:"
)

print(
    RESULTS_DIR
)

print()
print(
    "Charts saved at:"
)

print(
    CHARTS_DIR
)

print()
print(
    "Generated EDA files:"
)

for file in sorted(
    RESULTS_DIR.iterdir()
):

    if file.is_file():

        print(
            " -",
            file.name
        )

print()
print(
    "Generated charts:"
)

for file in sorted(
    CHARTS_DIR.iterdir()
):

    if file.is_file():

        print(
            " -",
            file.name
        )

print()
print("=" * 60)