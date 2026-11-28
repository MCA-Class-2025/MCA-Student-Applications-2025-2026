
import os
import pandas as pd
import matplotlib.pyplot as plt

# ==========================================================
# LOAD DATASET
# ==========================================================

file_path = "fused_dataset/fused_interior_decor.csv"

df = pd.read_csv(file_path)

print("=" * 60)
print("FUSED DATASET EDA")
print("=" * 60)

print("Rows:", len(df))
print("Columns:", len(df.columns))

print("\nColumns:")
print(df.columns.tolist())


# ==========================================================
# CREATE OUTPUT FOLDER
# ==========================================================

os.makedirs("eda_figures", exist_ok=True)


# ==========================================================
# CONVERT NUMERICAL COLUMNS
# ==========================================================

numeric_columns = [
    "price",
    "actual_price",
    "discount",
    "rating",
    "match_score"
]

for col in numeric_columns:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")


# ==========================================================
# E1 – PRODUCT PRICE HISTOGRAM
# ==========================================================

if "price" in df.columns:

    plt.figure(figsize=(8, 5))

    df["price"].dropna().plot(
        kind="hist",
        bins=30
    )

    plt.title("E1 – Product Price Distribution")
    plt.xlabel("Product Price")
    plt.ylabel("Number of Products")
    plt.tight_layout()

    plt.savefig(
        "eda_figures/E1_product_price.png",
        dpi=300
    )

    plt.show()


# ==========================================================
# E2 – PRODUCT RATING BOXPLOT
# ==========================================================

if "rating" in df.columns:

    plt.figure(figsize=(7, 5))

    plt.boxplot(
        df["rating"].dropna()
    )

    plt.title("E2 – Product Rating Distribution")
    plt.ylabel("Rating")

    plt.tight_layout()

    plt.savefig(
        "eda_figures/E2_product_rating.png",
        dpi=300
    )

    plt.show()


# ==========================================================
# E3 – PRODUCT CATEGORY DISTRIBUTION
# ==========================================================

if "category" in df.columns:

    category_counts = (
        df["category"]
        .fillna("Unknown")
        .value_counts()
        .head(15)
    )

    plt.figure(figsize=(10, 6))

    category_counts.plot(
        kind="bar"
    )

    plt.title("E3 – Product Category Distribution")
    plt.xlabel("Product Category")
    plt.ylabel("Number of Products")

    plt.xticks(
        rotation=45,
        ha="right"
    )

    plt.tight_layout()

    plt.savefig(
        "eda_figures/E3_product_category.png",
        dpi=300
    )

    plt.show()


# ==========================================================
# E4 – INTERIOR STYLE DISTRIBUTION
# ==========================================================

if "style_tags" in df.columns:

    style_counts = (
        df["style_tags"]
        .fillna("Unknown")
        .value_counts()
        .head(15)
    )

    plt.figure(figsize=(10, 6))

    style_counts.plot(
        kind="bar"
    )

    plt.title("E4 – Interior Style Distribution")
    plt.xlabel("Interior Style")
    plt.ylabel("Number of Records")

    plt.xticks(
        rotation=45,
        ha="right"
    )

    plt.tight_layout()

    plt.savefig(
        "eda_figures/E4_interior_style.png",
        dpi=300
    )

    plt.show()


# ==========================================================
# E5 – MATCH SCORE DISTRIBUTION
# ==========================================================

if "match_score" in df.columns:

    plt.figure(figsize=(8, 5))

    df["match_score"].dropna().plot(
        kind="hist",
        bins=20
    )

    plt.title("E5 – Match Score Distribution")
    plt.xlabel("Match Score")
    plt.ylabel("Number of Records")

    plt.tight_layout()

    plt.savefig(
        "eda_figures/E5_match_score.png",
        dpi=300
    )

    plt.show()


# ==========================================================
# E6 – API FUSION STATUS
# ==========================================================

if "api_fusion_status" in df.columns:

    status_counts = (
        df["api_fusion_status"]
        .fillna("Missing")
        .value_counts()
    )

    plt.figure(figsize=(8, 5))

    status_counts.plot(
        kind="bar"
    )

    plt.title("E6 – API Fusion Status")
    plt.xlabel("API Status")
    plt.ylabel("Number of Records")

    plt.xticks(
        rotation=45,
        ha="right"
    )

    plt.tight_layout()

    plt.savefig(
        "eda_figures/E6_api_fusion_status.png",
        dpi=300
    )

    plt.show()


# ==========================================================
# E7 – PRICE VS RATING
# ==========================================================

if "price" in df.columns and "rating" in df.columns:

    data = df[
        ["price", "rating"]
    ].dropna()

    plt.figure(figsize=(8, 5))

    plt.scatter(
        data["price"],
        data["rating"],
        alpha=0.6
    )

    plt.title("E7 – Product Price vs Rating")
    plt.xlabel("Product Price")
    plt.ylabel("Product Rating")

    plt.tight_layout()

    plt.savefig(
        "eda_figures/E7_price_vs_rating.png",
        dpi=300
    )

    plt.show()


# ==========================================================
# E8 – PRICE VS DISCOUNT
# ==========================================================

if "price" in df.columns and "discount" in df.columns:

    data = df[
        ["price", "discount"]
    ].dropna()

    plt.figure(figsize=(8, 5))

    plt.scatter(
        data["price"],
        data["discount"],
        alpha=0.6
    )

    plt.title("E8 – Product Price vs Discount")
    plt.xlabel("Product Price")
    plt.ylabel("Discount")

    plt.tight_layout()

    plt.savefig(
        "eda_figures/E8_price_vs_discount.png",
        dpi=300
    )

    plt.show()


# ==========================================================
# E9 – INTERIOR STYLE VS AVERAGE RATING
# ==========================================================

if "style_tags" in df.columns and "rating" in df.columns:

    style_rating = (
        df.groupby("style_tags")["rating"]
        .mean()
        .sort_values(ascending=False)
        .head(15)
    )

    plt.figure(figsize=(10, 6))

    style_rating.plot(
        kind="bar"
    )

    plt.title(
        "E9 – Interior Style vs Average Product Rating"
    )

    plt.xlabel("Interior Style")
    plt.ylabel("Average Rating")

    plt.xticks(
        rotation=45,
        ha="right"
    )

    plt.tight_layout()

    plt.savefig(
        "eda_figures/E9_style_vs_rating.png",
        dpi=300
    )

    plt.show()


# ==========================================================
# E10 – MATCH SCORE VS RATING
# ==========================================================

if "match_score" in df.columns and "rating" in df.columns:

    data = df[
        ["match_score", "rating"]
    ].dropna()

    plt.figure(figsize=(8, 5))

    plt.scatter(
        data["match_score"],
        data["rating"],
        alpha=0.6
    )

    plt.title(
        "E10 – Match Score vs Product Rating"
    )

    plt.xlabel("Match Score")
    plt.ylabel("Product Rating")

    plt.tight_layout()

    plt.savefig(
        "eda_figures/E10_match_score_vs_rating.png",
        dpi=300
    )

    plt.show()


# ==========================================================
# E11 – CORRELATION HEATMAP
# ==========================================================

available_numeric = [
    col for col in numeric_columns
    if col in df.columns
]

correlation = df[
    available_numeric
].corr()

plt.figure(figsize=(8, 6))

plt.imshow(
    correlation,
    interpolation="nearest"
)

plt.title("E11 – Numerical Correlation Heatmap")

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

plt.colorbar(
    label="Correlation"
)

plt.tight_layout()

plt.savefig(
    "eda_figures/E11_correlation_heatmap.png",
    dpi=300
)

plt.show()


# ==========================================================
# SUMMARY
# ==========================================================

print("\n" + "=" * 60)
print("EDA COMPLETED")
print("=" * 60)

print("\nFigures saved in:")

print("eda_figures/")
