import pandas as pd

# Load the new dataset
df = pd.read_csv("AI_Event_Planner_Dataset.csv")

# Display basic information
print("===== FIRST 5 ROWS =====")
print(df.head())

print("\n===== DATASET SHAPE =====")
print("Rows:", df.shape[0])
print("Columns:", df.shape[1])

print("\n===== COLUMN NAMES =====")
print(df.columns.tolist())

print("\n===== DATA TYPES =====")
print(df.dtypes)

print("\n===== MISSING VALUES =====")
print(df.isnull().sum())

print("\n===== DUPLICATE ROWS =====")
print(df.duplicated().sum())

print("\n===== STATISTICAL SUMMARY =====")
print(df.describe(include="all"))

import matplotlib.pyplot as plt

# ==============================
# EDA VISUALIZATION
# ==============================

# 1. Event Type Distribution
plt.figure(figsize=(10, 5))
df["event_type"].value_counts().plot(kind="bar")
plt.title("Event Type Distribution")
plt.xlabel("Event Type")
plt.ylabel("Number of Events")
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()


# 2. City Distribution
plt.figure(figsize=(10, 5))
df["city"].value_counts().plot(kind="bar")
plt.title("Event Distribution by City")
plt.xlabel("City")
plt.ylabel("Number of Events")
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()


# 3. Budget Distribution
plt.figure(figsize=(8, 5))
plt.hist(df["budget_inr"], bins=20)
plt.title("Event Budget Distribution")
plt.xlabel("Budget (INR)")
plt.ylabel("Number of Events")
plt.tight_layout()
plt.show()


# 4. Total Estimated Cost Distribution
plt.figure(figsize=(8, 5))
plt.hist(df["total_estimated_cost_inr"], bins=20)
plt.title("Total Estimated Event Cost Distribution")
plt.xlabel("Total Estimated Cost (INR)")
plt.ylabel("Number of Events")
plt.tight_layout()
plt.show()


# 5. Success Score Distribution
plt.figure(figsize=(8, 5))
plt.hist(df["success_score"], bins=15)
plt.title("Event Success Score Distribution")
plt.xlabel("Success Score")
plt.ylabel("Number of Events")
plt.tight_layout()
plt.show()


# 6. Within Budget
plt.figure(figsize=(6, 5))
df["within_budget"].value_counts().plot(kind="bar")
plt.title("Events Within Budget")
plt.xlabel("Within Budget")
plt.ylabel("Number of Events")
plt.xticks(rotation=0)
plt.tight_layout()
plt.show()


# 7. Guests vs Total Cost
plt.figure(figsize=(8, 5))
plt.scatter(
    df["guests"],
    df["total_estimated_cost_inr"]
)
plt.title("Guests vs Total Estimated Cost")
plt.xlabel("Number of Guests")
plt.ylabel("Total Estimated Cost (INR)")
plt.tight_layout()
plt.show()


# 8. Budget vs Total Estimated Cost
plt.figure(figsize=(8, 5))
plt.scatter(
    df["budget_inr"],
    df["total_estimated_cost_inr"]
)
plt.title("Budget vs Total Estimated Cost")
plt.xlabel("Budget (INR)")
plt.ylabel("Total Estimated Cost (INR)")
plt.tight_layout()
plt.show()


# 9. Correlation Matrix
numeric_df = df.select_dtypes(include="number")

plt.figure(figsize=(12, 8))
plt.imshow(numeric_df.corr(), aspect="auto")
plt.colorbar()

plt.xticks(
    range(len(numeric_df.columns)),
    numeric_df.columns,
    rotation=90
)

plt.yticks(
    range(len(numeric_df.columns)),
    numeric_df.columns
)

plt.title("Correlation Matrix")
plt.tight_layout()
plt.savefig("correlation_matrix.png")
plt.show()
plt.close()

# ==========================================
# ADDITIONAL EDA GRAPHS
# ==========================================

# 1. Events by Event Type
plt.figure(figsize=(10, 5))
df["event_type"].value_counts().plot(kind="bar")
plt.title("Number of Events by Event Type")
plt.xlabel("Event Type")
plt.ylabel("Number of Events")
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()


# 2. Events by City
plt.figure(figsize=(10, 5))
df["city"].value_counts().plot(kind="bar")
plt.title("Number of Events by City")
plt.xlabel("City")
plt.ylabel("Number of Events")
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()


# 3. Within Budget
plt.figure(figsize=(6, 5))
df["within_budget"].value_counts().plot(kind="bar")
plt.title("Events Within Budget vs Over Budget")
plt.xlabel("Within Budget")
plt.ylabel("Number of Events")
plt.xticks(rotation=0)
plt.tight_layout()
plt.show()


# 4. Success Score Distribution
plt.figure(figsize=(8, 5))
plt.hist(df["success_score"], bins=15)
plt.title("Event Success Score Distribution")
plt.xlabel("Success Score")
plt.ylabel("Number of Events")
plt.tight_layout()
plt.show()


# 5. Guests vs Budget
plt.figure(figsize=(8, 5))
plt.scatter(df["guests"], df["budget_inr"])
plt.title("Number of Guests vs Budget")
plt.xlabel("Number of Guests")
plt.ylabel("Budget (INR)")
plt.tight_layout()
plt.show()


# 6. Budget vs Total Estimated Cost
plt.figure(figsize=(8, 5))
plt.scatter(
    df["budget_inr"],
    df["total_estimated_cost_inr"]
)
plt.title("Budget vs Total Estimated Cost")
plt.xlabel("Budget (INR)")
plt.ylabel("Total Estimated Cost (INR)")
plt.tight_layout()
plt.show()


print("\n========== ADDITIONAL EDA COMPLETED ==========")