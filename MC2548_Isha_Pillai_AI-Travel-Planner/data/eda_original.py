import pandas as pd
import matplotlib.pyplot as plt
import os


# =========================================================
# 1. FILE PATH
# =========================================================

FILE_PATH = "data/Travel details dataset.csv"

# Folder to save EDA graphs
OUTPUT_FOLDER = "data/eda_outputs"
os.makedirs(OUTPUT_FOLDER, exist_ok=True)


# =========================================================
# 2. LOAD ORIGINAL DATASET
# =========================================================

df = pd.read_csv(
    FILE_PATH,
    sep="\t"
)


# =========================================================
# 3. BASIC INFORMATION
# =========================================================

print("\n======================================")
print("       ORIGINAL DATASET EDA")
print("======================================")

print("\nDataset Shape:")
print(df.shape)

print("\nNumber of Records:")
print(len(df))

print("\nNumber of Attributes:")
print(len(df.columns))

print("\nColumn Names:")
print(list(df.columns))


# =========================================================
# 4. MISSING VALUES
# =========================================================

print("\n======================================")
print("       MISSING VALUE ANALYSIS")
print("======================================")

missing = df.isnull().sum()

print(missing)


# =========================================================
# 5. DUPLICATE RECORDS
# =========================================================

print("\n======================================")
print("       DUPLICATE ANALYSIS")
print("======================================")

duplicates = df.duplicated().sum()

print("Duplicate records:", duplicates)


# =========================================================
# 6. DESTINATION ANALYSIS
# =========================================================

print("\n======================================")
print("       DESTINATION ANALYSIS")
print("======================================")

destination_counts = (
    df["Destination"]
    .dropna()
    .value_counts()
)

print(destination_counts.head(10))


plt.figure(figsize=(10, 6))

destination_counts.head(10).plot(
    kind="bar"
)

plt.title("Top 10 Destinations")
plt.xlabel("Destination")
plt.ylabel("Number of Trips")
plt.xticks(rotation=45, ha="right")
plt.tight_layout()

plt.savefig(
    os.path.join(
        OUTPUT_FOLDER,
        "destination_analysis.png"
    ),
    dpi=150
)

plt.show()


# =========================================================
# 7. TRIP DURATION ANALYSIS
# =========================================================

print("\n======================================")
print("       TRIP DURATION ANALYSIS")
print("======================================")

duration = pd.to_numeric(
    df["Duration (days)"],
    errors="coerce"
)

print("\nAverage trip duration:")
print(round(duration.mean(), 2), "days")

print("\nMinimum trip duration:")
print(duration.min(), "days")

print("\nMaximum trip duration:")
print(duration.max(), "days")


plt.figure(figsize=(9, 6))

plt.hist(
    duration.dropna(),
    bins=10
)

plt.title("Distribution of Trip Duration")
plt.xlabel("Duration (days)")
plt.ylabel("Number of Trips")
plt.tight_layout()

plt.savefig(
    os.path.join(
        OUTPUT_FOLDER,
        "trip_duration.png"
    ),
    dpi=150
)

plt.show()


# =========================================================
# 8. TRAVELER AGE ANALYSIS
# =========================================================

print("\n======================================")
print("       TRAVELER AGE ANALYSIS")
print("======================================")

age = pd.to_numeric(
    df["Traveler age"],
    errors="coerce"
)

print("\nAverage traveler age:")
print(round(age.mean(), 2))

print("\nMinimum traveler age:")
print(age.min())

print("\nMaximum traveler age:")
print(age.max())


plt.figure(figsize=(9, 6))

plt.hist(
    age.dropna(),
    bins=10
)

plt.title("Distribution of Traveler Age")
plt.xlabel("Traveler Age")
plt.ylabel("Number of Travelers")
plt.tight_layout()

plt.savefig(
    os.path.join(
        OUTPUT_FOLDER,
        "traveler_age.png"
    ),
    dpi=150
)

plt.show()


# =========================================================
# 9. ACCOMMODATION ANALYSIS
# =========================================================

print("\n======================================")
print("       ACCOMMODATION ANALYSIS")
print("======================================")

accommodation_counts = (
    df["Accommodation type"]
    .dropna()
    .value_counts()
)

print(accommodation_counts)


plt.figure(figsize=(8, 6))

accommodation_counts.plot(
    kind="bar"
)

plt.title("Accommodation Type Distribution")
plt.xlabel("Accommodation Type")
plt.ylabel("Number of Trips")
plt.xticks(rotation=45, ha="right")
plt.tight_layout()

plt.savefig(
    os.path.join(
        OUTPUT_FOLDER,
        "accommodation_analysis.png"
    ),
    dpi=150
)

plt.show()


# =========================================================
# 10. TRANSPORTATION ANALYSIS
# =========================================================

print("\n======================================")
print("       TRANSPORTATION ANALYSIS")
print("======================================")

transport_counts = (
    df["Transportation type"]
    .dropna()
    .value_counts()
)

print(transport_counts)


plt.figure(figsize=(8, 6))

transport_counts.plot(
    kind="bar"
)

plt.title("Transportation Type Distribution")
plt.xlabel("Transportation Type")
plt.ylabel("Number of Trips")
plt.xticks(rotation=45, ha="right")
plt.tight_layout()

plt.savefig(
    os.path.join(
        OUTPUT_FOLDER,
        "transportation_analysis.png"
    ),
    dpi=150
)

plt.show()


# =========================================================
# 11. ACCOMMODATION COST ANALYSIS
# =========================================================

print("\n======================================")
print("       ACCOMMODATION COST ANALYSIS")
print("======================================")

accommodation_cost = pd.to_numeric(
    df["Accommodation cost"],
    errors="coerce"
)

print("\nAverage accommodation cost:")
print(round(accommodation_cost.mean(), 2))

print("\nMinimum accommodation cost:")
print(accommodation_cost.min())

print("\nMaximum accommodation cost:")
print(accommodation_cost.max())


plt.figure(figsize=(9, 6))

plt.hist(
    accommodation_cost.dropna(),
    bins=10
)

plt.title("Distribution of Accommodation Cost")
plt.xlabel("Accommodation Cost")
plt.ylabel("Number of Trips")
plt.tight_layout()

plt.savefig(
    os.path.join(
        OUTPUT_FOLDER,
        "accommodation_cost.png"
    ),
    dpi=150
)

plt.show()


# =========================================================
# 12. TRANSPORTATION COST ANALYSIS
# =========================================================

print("\n======================================")
print("       TRANSPORTATION COST ANALYSIS")
print("======================================")

transport_cost = pd.to_numeric(
    df["Transportation cost"],
    errors="coerce"
)

print("\nAverage transportation cost:")
print(round(transport_cost.mean(), 2))

print("\nMinimum transportation cost:")
print(transport_cost.min())

print("\nMaximum transportation cost:")
print(transport_cost.max())


plt.figure(figsize=(9, 6))

plt.hist(
    transport_cost.dropna(),
    bins=10
)

plt.title("Distribution of Transportation Cost")
plt.xlabel("Transportation Cost")
plt.ylabel("Number of Trips")
plt.tight_layout()

plt.savefig(
    os.path.join(
        OUTPUT_FOLDER,
        "transportation_cost.png"
    ),
    dpi=150
)

plt.show()


# =========================================================
# 13. SUMMARY
# =========================================================

print("\n======================================")
print("          EDA SUMMARY")
print("======================================")

print("Records:", len(df))
print("Attributes:", len(df.columns))
print("Duplicate records:", duplicates)
print("Missing values:", df.isnull().sum().sum())

print(
    "\nEDA graphs saved in:",
    OUTPUT_FOLDER
)

print("\n======================================")
print("       EDA COMPLETED")
print("======================================")