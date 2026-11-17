from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt


# ============================================================
# PATHS
# ============================================================

ML_ROOT = Path(__file__).resolve().parents[1]

DATASET_DIR = ML_ROOT / "dataset"

PROCESSED_DIR = DATASET_DIR / "processed"

RESULTS_DIR = (
    ML_ROOT
    / "eda"
    / "results"
    / "price_analysis"
)

RESULTS_DIR.mkdir(
    parents=True,
    exist_ok=True
)


GROCERY_FILE = (
    PROCESSED_DIR
    / "grocery_price_history.csv"
)

ELECTRONICS_FILE = (
    PROCESSED_DIR
    / "electronics_price_history.csv"
)


# ============================================================
# LOAD DATA
# ============================================================

def load_data():

    print("\n========================================")
    print("LOADING PRICE DATASETS")
    print("========================================")

    grocery = pd.read_csv(
        GROCERY_FILE
    )

    electronics = pd.read_csv(
        ELECTRONICS_FILE
    )

    grocery["Date"] = pd.to_datetime(
        grocery["Date"]
    )

    electronics["Date"] = pd.to_datetime(
        electronics["Date"]
    )

    print(
        "Grocery:",
        grocery.shape
    )

    print(
        "Electronics:",
        electronics.shape
    )

    return grocery, electronics


# ============================================================
# GROCERY ANALYSIS
# ============================================================

def grocery_analysis(
    df
):

    print("\n========================================")
    print("GROCERY EDA")
    print("========================================")

    # --------------------------------------------------------
    # Basic information
    # --------------------------------------------------------

    print("\nRows:", len(df))

    print(
        "Columns:",
        len(df.columns)
    )

    print(
        "\nProducts:"
    )

    print(
        df["Product"]
        .unique()
    )

    # --------------------------------------------------------
    # Statistics
    # --------------------------------------------------------

    print(
        "\nGrocery price statistics:"
    )

    print(
        df["Price"].describe()
    )

    # --------------------------------------------------------
    # Average price by product
    # --------------------------------------------------------

    average_price = (
        df.groupby("Product")["Price"]
        .mean()
        .sort_values(
            ascending=False
        )
    )

    print(
        "\nAverage price by product:"
    )

    print(
        average_price
    )

    average_price.to_csv(
        RESULTS_DIR
        / "grocery_average_price.csv"
    )

    # --------------------------------------------------------
    # Minimum and maximum price
    # --------------------------------------------------------

    price_summary = (
        df.groupby("Product")["Price"]
        .agg(
            [
                "min",
                "max",
                "mean"
            ]
        )
        .reset_index()
    )

    price_summary.columns = [
        "Product",
        "MinimumPrice",
        "MaximumPrice",
        "AveragePrice"
    ]

    price_summary.to_csv(
        RESULTS_DIR
        / "grocery_price_summary.csv",
        index=False
    )

    print(
        "\nPrice summary:"
    )

    print(
        price_summary
    )

    # ========================================================
    # GRAPH 1
    # GROCERY PRICE TREND
    # ========================================================

    plt.figure(
        figsize=(12, 6)
    )

    for product in (
        df["Product"]
        .unique()
    ):

        product_data = (
            df[
                df["Product"]
                == product
            ]
            .sort_values("Date")
        )

        plt.plot(
            product_data["Date"],
            product_data["Price"],
            label=product
        )

    plt.title(
        "Historical Grocery Price Trends"
    )

    plt.xlabel(
        "Date"
    )

    plt.ylabel(
        "Price"
    )

    plt.legend(
        bbox_to_anchor=(
            1.05,
            1
        ),
        loc="upper left"
    )

    plt.grid(
        True,
        alpha=0.3
    )

    plt.tight_layout()

    plt.savefig(
        RESULTS_DIR
        / "grocery_price_trends.png",
        dpi=150
    )

    plt.close()

    # ========================================================
    # GRAPH 2
    # AVERAGE PRICE BY PRODUCT
    # ========================================================

    plt.figure(
        figsize=(12, 6)
    )

    average_price.sort_values().plot(
        kind="barh"
    )

    plt.title(
        "Average Grocery Price by Product"
    )

    plt.xlabel(
        "Average Price"
    )

    plt.ylabel(
        "Product"
    )

    plt.tight_layout()

    plt.savefig(
        RESULTS_DIR
        / "grocery_average_price.png",
        dpi=150
    )

    plt.close()

    # ========================================================
    # GRAPH 3
    # YEARLY GROCERY PRICE
    # ========================================================

    yearly_price = (
        df.groupby(
            [
                "Year",
                "Product"
            ]
        )["Price"]
        .mean()
        .reset_index()
    )

    plt.figure(
        figsize=(12, 6)
    )

    for product in (
        yearly_price["Product"]
        .unique()
    ):

        product_data = (
            yearly_price[
                yearly_price["Product"]
                == product
            ]
        )

        plt.plot(
            product_data["Year"],
            product_data["Price"],
            marker="o",
            label=product
        )

    plt.title(
        "Yearly Average Grocery Prices"
    )

    plt.xlabel(
        "Year"
    )

    plt.ylabel(
        "Average Price"
    )

    plt.legend(
        bbox_to_anchor=(
            1.05,
            1
        ),
        loc="upper left"
    )

    plt.grid(
        True,
        alpha=0.3
    )

    plt.tight_layout()

    plt.savefig(
        RESULTS_DIR
        / "grocery_yearly_prices.png",
        dpi=150
    )

    plt.close()


# ============================================================
# ELECTRONICS ANALYSIS
# ============================================================

def electronics_analysis(
    df
):

    print("\n========================================")
    print("ELECTRONICS EDA")
    print("========================================")

    # --------------------------------------------------------
    # Basic information
    # --------------------------------------------------------

    print(
        "\nRows:",
        len(df)
    )

    print(
        "Columns:",
        len(df.columns)
    )

    print(
        "\nUnique products:",
        df["Product"].nunique()
    )

    print(
        "Unique brands:",
        df["Brand"].nunique()
    )

    print(
        "Unique categories:",
        df["Category"].nunique()
    )

    # --------------------------------------------------------
    # Statistics
    # --------------------------------------------------------

    print(
        "\nElectronics price statistics:"
    )

    print(
        df["Price"].describe()
    )

    # --------------------------------------------------------
    # Average price by category
    # --------------------------------------------------------

    category_price = (
        df.groupby(
            "Category"
        )["Price"]
        .mean()
        .sort_values(
            ascending=False
        )
    )

    print(
        "\nAverage price by category:"
    )

    print(
        category_price
    )

    category_price.to_csv(
        RESULTS_DIR
        / "electronics_category_average_price.csv"
    )

    # ========================================================
    # GRAPH 1
    # CATEGORY PRICE
    # ========================================================

    plt.figure(
        figsize=(12, 6)
    )

    category_price.sort_values().plot(
        kind="barh"
    )

    plt.title(
        "Average Electronics Price by Category"
    )

    plt.xlabel(
        "Average Price"
    )

    plt.ylabel(
        "Category"
    )

    plt.tight_layout()

    plt.savefig(
        RESULTS_DIR
        / "electronics_category_price.png",
        dpi=150
    )

    plt.close()

    # --------------------------------------------------------
    # Average price by brand
    # --------------------------------------------------------

    brand_price = (
        df.groupby(
            "Brand"
        )["Price"]
        .agg(
            [
                "count",
                "mean"
            ]
        )
        .sort_values(
            "mean",
            ascending=False
        )
    )

    print(
        "\nTop brands by average price:"
    )

    print(
        brand_price.head(20)
    )

    brand_price.to_csv(
        RESULTS_DIR
        / "electronics_brand_price.csv"
    )

    # ========================================================
    # GRAPH 2
    # TOP BRANDS
    # ========================================================

    top_brands = (
        df["Brand"]
        .value_counts()
        .head(15)
        .index
    )

    top_brand_data = (
        df[
            df["Brand"]
            .isin(top_brands)
        ]
        .groupby("Brand")["Price"]
        .mean()
        .sort_values()
    )

    plt.figure(
        figsize=(12, 6)
    )

    top_brand_data.plot(
        kind="barh"
    )

    plt.title(
        "Average Price of Top Electronics Brands"
    )

    plt.xlabel(
        "Average Price"
    )

    plt.ylabel(
        "Brand"
    )

    plt.tight_layout()

    plt.savefig(
        RESULTS_DIR
        / "electronics_brand_price.png",
        dpi=150
    )

    plt.close()

    # ========================================================
    # GRAPH 3
    # YEARLY PRICE TREND
    # ========================================================

    yearly_price = (
        df.groupby(
            "Year"
        )["Price"]
        .mean()
        .reset_index()
    )

    plt.figure(
        figsize=(12, 6)
    )

    plt.plot(
        yearly_price["Year"],
        yearly_price["Price"],
        marker="o"
    )

    plt.title(
        "Average Electronics Price by Year"
    )

    plt.xlabel(
        "Year"
    )

    plt.ylabel(
        "Average Price"
    )

    plt.grid(
        True,
        alpha=0.3
    )

    plt.tight_layout()

    plt.savefig(
        RESULTS_DIR
        / "electronics_yearly_price.png",
        dpi=150
    )

    plt.close()

    # ========================================================
    # GRAPH 4
    # PRICE DISTRIBUTION
    # ========================================================

    plt.figure(
        figsize=(10, 6)
    )

    plt.hist(
        df["Price"],
        bins=50
    )

    plt.title(
        "Electronics Price Distribution"
    )

    plt.xlabel(
        "Price"
    )

    plt.ylabel(
        "Number of Records"
    )

    plt.grid(
        True,
        alpha=0.3
    )

    plt.tight_layout()

    plt.savefig(
        RESULTS_DIR
        / "electronics_price_distribution.png",
        dpi=150
    )

    plt.close()


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    print(
        "\n"
        "========================================\n"
        "AI SMART EXPENSE TRACKER\n"
        "PRICE DATA EDA\n"
        "========================================"
    )

    grocery, electronics = load_data()

    grocery_analysis(
        grocery
    )

    electronics_analysis(
        electronics
    )

    print(
        "\n========================================"
    )

    print(
        "EDA COMPLETED SUCCESSFULLY"
    )

    print(
        "========================================"
    )

    print(
        "\nResults saved in:"
    )

    print(
        RESULTS_DIR
    )