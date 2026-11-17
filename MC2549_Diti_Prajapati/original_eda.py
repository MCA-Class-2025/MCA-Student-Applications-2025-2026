import pandas as pd
import matplotlib.pyplot as plt

# ==========================================
# 1. LOAD ORIGINAL DATASET
# ==========================================

file_path = "amazon_products.csv"

df = pd.read_csv(file_path)

print("\n========== DATASET OVERVIEW ==========")

print("Number of Records:", df.shape[0])
print("Number of Attributes:", df.shape[1])

print("\nColumns:")
print(df.columns.tolist())


# ==========================================
# 2. DATA TYPES
# ==========================================

print("\n========== DATA TYPES ==========")

print(df.dtypes)


# ==========================================
# 3. MISSING VALUES
# ==========================================

print("\n========== MISSING VALUES ==========")

missing = df.isnull().sum()

print(missing[missing > 0])


# ==========================================
# 4. DUPLICATE RECORDS
# ==========================================

print("\n========== DUPLICATES ==========")

print("Complete duplicate rows:", df.duplicated().sum())

print("Duplicate product IDs:",
      df["product_id"].duplicated().sum())


# ==========================================
# 5. CLEAN PRICE COLUMNS
# ==========================================

df["discounted_price_num"] = (
    df["discounted_price"]
    .astype(str)
    .str.replace("₹", "", regex=False)
    .str.replace(",", "", regex=False)
    .astype(float)
)

df["actual_price_num"] = (
    df["actual_price"]
    .astype(str)
    .str.replace("₹", "", regex=False)
    .str.replace(",", "", regex=False)
    .astype(float)
)

df["discount_percentage_num"] = (
    df["discount_percentage"]
    .astype(str)
    .str.replace("%", "", regex=False)
    .astype(float)
)

df["rating_num"] = pd.to_numeric(
    df["rating"],
    errors="coerce"
)

df["rating_count_num"] = (
    df["rating_count"]
    .astype(str)
    .str.replace(",", "", regex=False)
    .replace("nan", None)
)

df["rating_count_num"] = pd.to_numeric(
    df["rating_count_num"],
    errors="coerce"
)


# ==========================================
# 6. STATISTICAL SUMMARY
# ==========================================

print("\n========== STATISTICAL SUMMARY ==========")

numeric_columns = [
    "discounted_price_num",
    "actual_price_num",
    "discount_percentage_num",
    "rating_num",
    "rating_count_num"
]

print(df[numeric_columns].describe())


# ==========================================
# 7. PRICE DISTRIBUTION
# ==========================================

plt.figure(figsize=(8, 5))

plt.hist(
    df["discounted_price_num"].dropna(),
    bins=30
)

plt.xlabel("Discounted Price")
plt.ylabel("Number of Products")
plt.title("Distribution of Discounted Product Prices")

plt.tight_layout()
plt.show()


# ==========================================
# 8. RATING DISTRIBUTION
# ==========================================

plt.figure(figsize=(8, 5))

plt.hist(
    df["rating_num"].dropna(),
    bins=10
)

plt.xlabel("Rating")
plt.ylabel("Number of Products")
plt.title("Distribution of Product Ratings")

plt.tight_layout()
plt.show()


# ==========================================
# 9. TOP PRODUCT CATEGORIES
# ==========================================

# Extract the first category from the hierarchical category field

df["main_category"] = (
    df["category"]
    .astype(str)
    .str.split("|")
    .str[0]
)

category_counts = df["main_category"].value_counts().head(10)

plt.figure(figsize=(10, 6))

category_counts.plot(kind="bar")

plt.xlabel("Product Category")
plt.ylabel("Number of Products")
plt.title("Top 10 Product Categories")

plt.xticks(rotation=45, ha="right")

plt.tight_layout()
plt.show()


# ==========================================
# 10. RATING VS REVIEW COUNT
# ==========================================

plt.figure(figsize=(8, 5))

plt.scatter(
    df["rating_num"],
    df["rating_count_num"],
    alpha=0.5
)

plt.xlabel("Product Rating")
plt.ylabel("Rating Count")
plt.title("Relationship Between Rating and Rating Count")

plt.tight_layout()
plt.show()


# ==========================================
# 11. DISCOUNT VS RATING
# ==========================================

plt.figure(figsize=(8, 5))

plt.scatter(
    df["discount_percentage_num"],
    df["rating_num"],
    alpha=0.5
)

plt.xlabel("Discount Percentage")
plt.ylabel("Product Rating")
plt.title("Relationship Between Discount and Rating")

plt.tight_layout()
plt.show()


# ==========================================
# 12. CORRELATION MATRIX
# ==========================================

correlation_columns = [
    "discounted_price_num",
    "actual_price_num",
    "discount_percentage_num",
    "rating_num",
    "rating_count_num"
]

correlation = df[correlation_columns].corr()

print("\n========== CORRELATION MATRIX ==========")

print(correlation)


# ==========================================
# 13. DATASET SUMMARY
# ==========================================

print("\n========== FINAL SUMMARY ==========")

print("Records:", len(df))
print("Attributes:", 16)
print("Complete duplicate rows:", df.duplicated().sum())
print("Unique product IDs:", df["product_id"].nunique())

print("\nOriginal Dataset EDA Completed Successfully!")