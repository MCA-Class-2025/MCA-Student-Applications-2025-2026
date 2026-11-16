
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

# --------------------------------------------------
# PATHS AND DATA
# --------------------------------------------------

BASE = Path(__file__).resolve().parent.parent
DATA = BASE / "SecureShare_Fused_Dataset.csv"
OUT = BASE / "outputs" / "eda"

OUT.mkdir(parents=True, exist_ok=True)

if not DATA.exists():
    raise FileNotFoundError(f"Fused dataset not found: {DATA}")

df = pd.read_csv(DATA, low_memory=False)

print("=" * 60)
print("PART E: EXPLORATORY DATA ANALYSIS OF FUSED DATASET")
print("=" * 60)
print(f"Rows: {len(df)}")
print(f"Columns: {len(df.columns)}")


# --------------------------------------------------
# NUMERIC VARIABLES
# --------------------------------------------------

original_numeric = [
    "failed_attempts",
    "session_duration",
    "privilege_level"
]

api_numeric = [
    "AbuseIPDB Abuse Confidence Score",
    "AbuseIPDB Total Reports"
]

numeric_cols = [
    col for col in original_numeric + api_numeric
    if col in df.columns
]

for col in numeric_cols:
    df[col] = pd.to_numeric(df[col], errors="coerce")

api_cols = [col for col in api_numeric if col in df.columns]


# --------------------------------------------------
# 1. UNIVARIATE ANALYSIS
# --------------------------------------------------

print("\n1. UNIVARIATE ANALYSIS")

# Descriptive statistics
if numeric_cols:
    df[numeric_cols].describe().T.to_csv(
        OUT / "part_e_descriptive_statistics.csv"
    )

# API variable histograms and boxplots
for col in api_cols:

    values = df[col].dropna()

    if values.empty:
        continue

    safe_name = col.replace(" ", "_")

    # Histogram
    plt.figure(figsize=(8, 5))
    plt.hist(values, bins=20, edgecolor="black")
    plt.title(f"Distribution of {col}")
    plt.xlabel(col)
    plt.ylabel("Frequency")
    plt.tight_layout()
    plt.savefig(
        OUT / f"part_e_histogram_{safe_name}.png",
        dpi=200
    )
    plt.close()

    # Boxplot
    plt.figure(figsize=(7, 5))
    plt.boxplot(values, showfliers=True)
    plt.title(f"Boxplot of {col}")
    plt.ylabel(col)
    plt.tight_layout()
    plt.savefig(
        OUT / f"part_e_boxplot_{safe_name}.png",
        dpi=200
    )
    plt.close()


# --------------------------------------------------
# 2. BIVARIATE ANALYSIS
# --------------------------------------------------

print("\n2. BIVARIATE ANALYSIS")

# A. Session duration by failed attempts
# Boxplot is more suitable because failed_attempts
# contains discrete values.

if (
    "failed_attempts" in df.columns
    and "session_duration" in df.columns
):

    plot_df = df[
        ["failed_attempts", "session_duration"]
    ].dropna()

    groups = []
    labels = []

    for value, group in plot_df.groupby("failed_attempts"):

        durations = group["session_duration"].dropna()

        if not durations.empty:
            groups.append(durations.values)
            labels.append(str(value))

    if groups:
        plt.figure(figsize=(10, 6))

        plt.boxplot(
            groups,
            tick_labels=labels,
            showfliers=False
        )

        plt.title(
            "Session Duration Distribution by Failed Attempts"
        )
        plt.xlabel("Failed Attempts")
        plt.ylabel("Session Duration")
        plt.tight_layout()

        plt.savefig(
            OUT / "07_boxplot_session_duration_by_failed_attempts.png",
            dpi=200
        )
        plt.close()


# B. API confidence score by suspicious activity

if (
    "AbuseIPDB Abuse Confidence Score" in df.columns
    and "suspicious_activity" in df.columns
):

    plot_df = df[
        [
            "AbuseIPDB Abuse Confidence Score",
            "suspicious_activity"
        ]
    ].dropna()

    groups = []
    labels = []

    for value, group in plot_df.groupby("suspicious_activity"):

        scores = group[
            "AbuseIPDB Abuse Confidence Score"
        ].dropna()

        if not scores.empty:
            groups.append(scores.values)
            labels.append(str(value))

    if groups:
        plt.figure(figsize=(8, 5))

        plt.boxplot(
            groups,
            tick_labels=labels,
            showfliers=False
        )

        plt.title("API Confidence Score by Suspicious Activity")
        plt.xlabel("Suspicious Activity")
        plt.ylabel("AbuseIPDB Abuse Confidence Score")
        plt.tight_layout()

        plt.savefig(
            OUT / "part_e_api_confidence_by_suspicious_activity.png",
            dpi=200
        )
        plt.close()


# C. API confidence score by failed attempts

if (
    "AbuseIPDB Abuse Confidence Score" in df.columns
    and "failed_attempts" in df.columns
):

    plot_df = df[
        [
            "failed_attempts",
            "AbuseIPDB Abuse Confidence Score"
        ]
    ].dropna()

    groups = []
    labels = []

    for value, group in plot_df.groupby("failed_attempts"):

        scores = group[
            "AbuseIPDB Abuse Confidence Score"
        ].dropna()

        if not scores.empty:
            groups.append(scores.values)
            labels.append(str(value))

    if groups:
        plt.figure(figsize=(10, 6))

        plt.boxplot(
            groups,
            tick_labels=labels,
            showfliers=False
        )

        plt.title("API Abuse Confidence Score by Failed Attempts")
        plt.xlabel("Failed Attempts")
        plt.ylabel("AbuseIPDB Abuse Confidence Score")
        plt.tight_layout()

        plt.savefig(
            OUT / "part_e_api_confidence_vs_failed_attempts.png",
            dpi=200
        )
        plt.close()


# --------------------------------------------------
# 3. MULTIVARIATE ANALYSIS
# --------------------------------------------------

print("\n3. MULTIVARIATE ANALYSIS")

# A. Correlation matrix and heatmap

if len(numeric_cols) >= 2:

    correlation = df[numeric_cols].corr(
        method="pearson"
    )

    correlation.to_csv(
        OUT / "part_e_correlation_matrix.csv"
    )

    plt.figure(figsize=(10, 8))

    image = plt.imshow(
        correlation,
        cmap="coolwarm",
        vmin=-1,
        vmax=1
    )

    plt.colorbar(
        image,
        label="Pearson Correlation Coefficient"
    )

    plt.xticks(
        range(len(correlation.columns)),
        correlation.columns,
        rotation=45,
        ha="right"
    )

    plt.yticks(
        range(len(correlation.index)),
        correlation.index
    )

    for i in range(len(correlation.index)):
        for j in range(len(correlation.columns)):

            value = correlation.iloc[i, j]

            if pd.notna(value):
                plt.text(
                    j,
                    i,
                    f"{value:.2f}",
                    ha="center",
                    va="center",
                    fontsize=9
                )

    plt.title("Correlation Heatmap: Original and API Variables")
    plt.tight_layout()

    plt.savefig(
        OUT / "part_e_correlation_heatmap.png",
        dpi=200
    )
    plt.close()


# B. Suspicious activity vs blocked status

if (
    "suspicious_activity" in df.columns
    and "blocked" in df.columns
):

    cross_tab = pd.crosstab(
        df["suspicious_activity"],
        df["blocked"],
        margins=True
    )

    cross_tab.to_csv(
        OUT / "part_e_suspicious_vs_blocked.csv"
    )


# --------------------------------------------------
# CLEAN UP OLD PNG 7
# --------------------------------------------------

old_scatter = OUT / "07_scatter_failed_attempts_session.png"

if old_scatter.exists():
    old_scatter.unlink()


# --------------------------------------------------
# COMPLETION
# --------------------------------------------------

print("\n" + "=" * 60)
print("PART E ANALYSIS COMPLETED")
print("=" * 60)

print(f"API variables analysed: {api_cols}")
print(f"Numeric variables analysed: {numeric_cols}")
print(f"Output folder: {OUT}")

print("\nGenerated analyses:")
print("- Descriptive statistics")
print("- API variable histograms")
print("- API variable boxplots")
print("- Session duration by failed attempts")
print("- API confidence score by suspicious activity")
print("- API confidence score by failed attempts")
print("- Correlation heatmap")
print("- Suspicious activity vs blocked status")

print("\nReview all generated charts before finalising Part E.")
