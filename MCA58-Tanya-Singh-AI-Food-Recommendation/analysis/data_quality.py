
import os
import pandas as pd

from config import FUSED_DATA_DIR


def main():

    file_path = os.path.join(
        FUSED_DATA_DIR,
        "fused_food_dataset.csv"
    )

    if not os.path.exists(file_path):
        print("Fused dataset not found!")
        return

    df = pd.read_csv(file_path)

    print("\n========== DATA QUALITY REPORT ==========")

    print("Rows:", df.shape[0])
    print("Columns:", df.shape[1])

    quality = pd.DataFrame({
        "Data_Type": df.dtypes.astype(str),
        "Missing_Count": df.isnull().sum(),
        "Missing_Percentage": (
            df.isnull().mean() * 100
        ).round(2),
        "Unique_Values": df.nunique()
    })

    print("\n========== COLUMN QUALITY ==========")
    print(quality)

    print("\nDuplicate rows:", df.duplicated().sum())

    numerical = df.select_dtypes(include="number")

    print("\n========== NUMERICAL OUTLIERS (IQR) ==========")

    outlier_results = []

    for column in numerical.columns:

        q1 = numerical[column].quantile(0.25)
        q3 = numerical[column].quantile(0.75)
        iqr = q3 - q1

        lower = q1 - 1.5 * iqr
        upper = q3 + 1.5 * iqr

        count = (
            (numerical[column] < lower) |
            (numerical[column] > upper)
        ).sum()

        outlier_results.append({
            "Column": column,
            "Lower_Bound": lower,
            "Upper_Bound": upper,
            "Outlier_Count": count
        })

    outliers = pd.DataFrame(outlier_results)
    print(outliers)

    os.makedirs("analysis/reports", exist_ok=True)

    quality.to_csv(
        "analysis/reports/data_quality_report.csv"
    )

    outliers.to_csv(
        "analysis/reports/outlier_report.csv",
        index=False
    )

    print("\nReports saved in analysis/reports/")


if __name__ == "__main__":
    main()
