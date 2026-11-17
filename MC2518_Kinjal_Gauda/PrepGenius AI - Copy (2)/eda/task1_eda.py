import os
import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# ---------------------------------------------------------
# PATH SETUP & DIRECTORY CREATION
# ---------------------------------------------------------
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR) if os.path.basename(SCRIPT_DIR) == 'eda' else SCRIPT_DIR

DATA_FILENAME = "PrepGenius_FUSED_DATASET_50000.csv"
DATA_PATH = os.path.join(PROJECT_ROOT, "data", "fused", DATA_FILENAME)

if not os.path.exists(DATA_PATH):
    DATA_PATH = os.path.join("data", "fused", DATA_FILENAME)

EDA_RESULTS_DIR = os.path.join(PROJECT_ROOT, "ml_results", "task1_eda")
os.makedirs(EDA_RESULTS_DIR, exist_ok=True)

print("=" * 80)
print(" PREPGENIUS AI - TASK 1 EXPLORATORY DATA ANALYSIS (EDA)")
print("=" * 80)

# ---------------------------------------------------------
# 1. LOAD & INSPECT DATASET
# ---------------------------------------------------------
print(f"\n[STEP 1] Loading Fused Dataset from: {DATA_PATH}")

df = pd.read_csv(DATA_PATH)

num_rows, num_cols = df.shape
missing_series = df.isnull().sum()
total_missing = missing_series.sum()
duplicate_count = df.duplicated().sum()

print("\n--- DATASET PROFILE SUMMARY ---")
print(f"Dataset Filename: {DATA_FILENAME}")
print(f"Number of Rows  : {num_rows:,}")
print(f"Number of Cols  : {num_cols}")
print(f"Total Missing   : {total_missing:,}")
print(f"Duplicate Count : {duplicate_count:,}")

# ---------------------------------------------------------
# 2. PRINT DESCRIPTIVE STATISTIC & TOPIC COUNTS
# ---------------------------------------------------------
corr_cols = [
    'CGPA',
    'Programming_Skill',
    'Projects_Completed',
    'Study_Hours_Per_Week',
    'Interview_Score',
    'Employability_Score',
    'Starting_Salary_USD'
]

print("\n--- DESCRIPTIVE STATISTICS (KEY NUMERICAL VARIABLES) ---")
desc_stats = df[corr_cols].describe().T
print(desc_stats[['count', 'mean', 'std', 'min', '25%', '50%', '75%', 'max']].to_string())

print("\n--- TOPIC DISTRIBUTION COUNTS ---")
topic_counts = df['topic_name'].value_counts()
for topic, count in topic_counts.items():
    print(f" - {topic:<45}: {count:,} ({count/num_rows:.2%})")

print("\n--- CORRELATION MATRIX FOR REPORT ---")
corr_matrix = df[corr_cols].corr()
print(corr_matrix.round(4).to_string())

# ---------------------------------------------------------
# 3. GENERATE VISUALIZATIONS
# ---------------------------------------------------------
print("\n[STEP 2] Generating EDA Visualizations...")
sns.set_theme(style="whitegrid")

# 1. CGPA Histogram
plt.figure(figsize=(8, 5))
sns.histplot(df['CGPA'], kde=True, color='royalblue', bins=30)
plt.title("Distribution of Student CGPA", fontsize=13, fontweight='bold')
plt.xlabel("CGPA (0.00 - 4.00)")
plt.ylabel("Frequency / Count")
plt.tight_layout()
cgpa_path = os.path.join(EDA_RESULTS_DIR, "cgpa_histogram.png")
plt.savefig(cgpa_path, dpi=300)
plt.close()
print(f"Saved: {cgpa_path}")

# 2. Employability_Score Histogram
plt.figure(figsize=(8, 5))
sns.histplot(df['Employability_Score'], kde=True, color='teal', bins=30)
plt.title("Distribution of Employability Score", fontsize=13, fontweight='bold')
plt.xlabel("Employability Score (0.0 - 100.0)")
plt.ylabel("Frequency / Count")
plt.tight_layout()
emp_path = os.path.join(EDA_RESULTS_DIR, "employability_score_histogram.png")
plt.savefig(emp_path, dpi=300)
plt.close()
print(f"Saved: {emp_path}")

# 3. Starting_Salary_USD Histogram
plt.figure(figsize=(8, 5))
sns.histplot(df['Starting_Salary_USD'], kde=True, color='darkgreen', bins=30)
plt.title("Distribution of Starting Salary (USD)", fontsize=13, fontweight='bold')
plt.xlabel("Starting Salary (USD)")
plt.ylabel("Frequency / Count")
plt.tight_layout()
sal_path = os.path.join(EDA_RESULTS_DIR, "starting_salary_histogram.png")
plt.savefig(sal_path, dpi=300)
plt.close()
print(f"Saved: {sal_path}")

# 4. Topic Distribution Bar Chart
plt.figure(figsize=(10, 6))
ax = sns.barplot(x=topic_counts.values, y=topic_counts.index, palette="mako")
plt.title("Topic Distribution in PrepGenius Fused Dataset", fontsize=13, fontweight='bold')
plt.xlabel("Count of Students / Records")
plt.ylabel("Topic Name")

for p in ax.patches:
    width = p.get_width()
    ax.annotate(f'{int(width):,} ({width/num_rows:.1%})',
                (width + 300, p.get_y() + p.get_height() / 2.),
                ha='left', va='center', fontsize=9, fontweight='bold')

plt.xlim(0, max(topic_counts.values) * 1.15)
plt.tight_layout()
topic_path = os.path.join(EDA_RESULTS_DIR, "topic_distribution.png")
plt.savefig(topic_path, dpi=300)
plt.close()
print(f"Saved: {topic_path}")

# 5. Boxplots for Important Numerical Variables
fig, axes = plt.subplots(2, 3, figsize=(15, 9))
axes = axes.flatten()

box_vars = ['CGPA', 'Employability_Score', 'Starting_Salary_USD', 'Interview_Score', 'Programming_Skill', 'Study_Hours_Per_Week']
colors = ['skyblue', 'lightseagreen', 'mediumseagreen', 'coral', 'mediumpurple', 'gold']

for idx, var in enumerate(box_vars):
    sns.boxplot(y=df[var], ax=axes[idx], color=colors[idx])
    axes[idx].set_title(f"Boxplot: {var}", fontsize=11, fontweight='bold')
    axes[idx].set_ylabel(var)

plt.tight_layout()
box_path = os.path.join(EDA_RESULTS_DIR, "numerical_boxplots.png")
plt.savefig(box_path, dpi=300)
plt.close()
print(f"Saved: {box_path}")

# 6. Correlation Heatmap
plt.figure(figsize=(9, 7))
sns.heatmap(corr_matrix, annot=True, fmt=".3f", cmap="coolwarm", vmin=-1, vmax=1, square=True, linewidths=0.5)
plt.title("Correlation Heatmap of Key Academic & Career Metrics", fontsize=13, fontweight='bold')
plt.xticks(rotation=45, ha='right')
plt.yticks(rotation=0)
plt.tight_layout()
corr_path = os.path.join(EDA_RESULTS_DIR, "correlation_heatmap.png")
plt.savefig(corr_path, dpi=300)
plt.close()
print(f"Saved: {corr_path}")

# ---------------------------------------------------------
# 4. FINAL VERIFICATION SUMMARY
# ---------------------------------------------------------
print("\n" + "=" * 80)
print(" TASK 1 EDA EXECUTION COMPLETE - VERIFICATION SUMMARY")
print("=" * 80)
print(f"1. CGPA Histogram             : {cgpa_path}")
print(f"2. Employability Score Hist   : {emp_path}")
print(f"3. Starting Salary Histogram  : {sal_path}")
print(f"4. Topic Distribution Plot    : {topic_path}")
print(f"5. Numerical Boxplots         : {box_path}")
print(f"6. Correlation Heatmap        : {corr_path}")
print("=" * 80)
