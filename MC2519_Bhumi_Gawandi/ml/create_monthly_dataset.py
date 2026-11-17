import pandas as pd
import os

# ==========================================
# 1. Load original dataset
# ==========================================

DATASET_PATH = "dataset/personal_finance.csv"

df = pd.read_csv(DATASET_PATH)

# Convert Date
df["Date"] = pd.to_datetime(df["Date"])


# ==========================================
# 2. Separate Income and Expense
# ==========================================

df["Income_Amount"] = df.apply(
    lambda row: row["Amount"] if row["Type"] == "Income" else 0,
    axis=1
)

df["Expense_Amount"] = df.apply(
    lambda row: row["Amount"] if row["Type"] == "Expense" else 0,
    axis=1
)


# ==========================================
# 3. Create Year and Month
# ==========================================

df["Year"] = df["Date"].dt.year
df["Month"] = df["Date"].dt.month

df["YearMonth"] = df["Date"].dt.to_period("M")


# ==========================================
# 4. Group by Month
# ==========================================

monthly = df.groupby("YearMonth").agg(
    Total_Income=("Income_Amount", "sum"),
    Total_Expense=("Expense_Amount", "sum"),
    Transaction_Count=("Amount", "count"),
    Average_Transaction=("Amount", "mean")
).reset_index()


# ==========================================
# 5. Convert YearMonth to string
# ==========================================

monthly["YearMonth"] = monthly["YearMonth"].astype(str)


# ==========================================
# 6. Add Year and Month columns
# ==========================================

monthly["Year"] = pd.to_datetime(
    monthly["YearMonth"]
).dt.year

monthly["Month"] = pd.to_datetime(
    monthly["YearMonth"]
).dt.month


# ==========================================
# 7. Sort by date
# ==========================================

monthly = monthly.sort_values("YearMonth")


# ==========================================
# 8. Save dataset
# ==========================================

os.makedirs("dataset", exist_ok=True)

OUTPUT_PATH = "dataset/monthly_expenses.csv"

monthly.to_csv(
    OUTPUT_PATH,
    index=False
)


# ==========================================
# 9. Display result
# ==========================================

print("\n========== MONTHLY DATASET CREATED ==========\n")

print("Number of months:", len(monthly))

print("\nColumns:")
print(monthly.columns.tolist())

print("\nFirst 10 months:")
print(monthly.head(10))

print("\nLast 10 months:")
print(monthly.tail(10))

print("\nDataset shape:")
print(monthly.shape)

print("\nSaved to:")
print(OUTPUT_PATH)