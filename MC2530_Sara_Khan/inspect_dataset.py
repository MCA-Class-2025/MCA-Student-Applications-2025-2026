from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parent
sample_file = ROOT / "data" / "travel_attractions_1500.csv"
report_file = ROOT / "reports" / "dataset_inspection.txt"

if not sample_file.exists():
    raise FileNotFoundError("Run setup_project.py first.")

df = pd.read_csv(sample_file, low_memory=False)
print("Rows:", len(df))
print("Columns:", len(df.columns))
print("Countries:", df["country_iso2"].nunique())
print("Country-city pairs:", df[["country_iso2", "city_en"]].drop_duplicates().shape[0])
print("Categories:", df["category"].nunique())
print("\nMissing values:\n", df.isna().sum().sort_values(ascending=False))
print("\nTop countries:\n", df["country_en"].value_counts().head(15))
print("\nTop categories:\n", df["category"].value_counts().head(15))
print("\nTop cities:\n", df.groupby(["country_en", "city_en"]).size().sort_values(ascending=False).head(15))
if report_file.exists():
    print(f"\nFull report: {report_file}")
