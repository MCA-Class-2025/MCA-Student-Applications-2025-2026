
import pandas as pd
import os

files = {
    "Original WDI Baseline": "wdi_country_baseline_multiyear.csv",
    "Fused Dataset": "data/fused_country_intelligence.csv",
    "REST Countries": "data/rest_countries.csv",
    "Open-Meteo": "data/open_meteo_weather.csv",
    "Frankfurter": "data/frankfurter_rates.csv",
    "OpenAQ": "data/openaq_air_quality.csv",
    "Nager.Date": "data/nager_holidays.csv"
}

print("\n========== PART F: DATASET INSPECTION ==========\n")

for name, path in files.items():
    print(f"\n--- {name} ---")

    if os.path.exists(path):
        df = pd.read_csv(path)

        print("Rows:", df.shape[0])
        print("Columns:", df.shape[1])
        print("Column names:")
        print(list(df.columns))
    else:
        print("FILE NOT FOUND:", path)

print("\n========== INSPECTION COMPLETE ==========")
