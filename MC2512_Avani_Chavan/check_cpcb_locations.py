from pathlib import Path
import pandas as pd

files = list(Path(".").rglob("raw_data_hourly*"))

print("=" * 70)
print("CPCB DATA LOCATION CHECK")
print("=" * 70)

print(f"\nTotal CPCB files found: {len(files)}")

all_columns = set()
cities = set()
stations = set()

for file in files:
    try:
        # Most CPCB downloaded files are Excel files
        df = pd.read_excel(file)

        all_columns.update(map(str, df.columns))

        for col in df.columns:
            name = str(col).lower()

            if "city" in name:
                cities.update(
                    df[col].dropna().astype(str).str.strip()
                )

            if "station" in name:
                stations.update(
                    df[col].dropna().astype(str).str.strip()
                )

    except Exception:
        # Try CSV if it isn't Excel
        try:
            df = pd.read_csv(file)

            all_columns.update(map(str, df.columns))

            for col in df.columns:
                name = str(col).lower()

                if "city" in name:
                    cities.update(
                        df[col].dropna().astype(str).str.strip()
                    )

                if "station" in name:
                    stations.update(
                        df[col].dropna().astype(str).str.strip()
                    )

        except Exception:
            pass

print("\nColumns detected:")
for column in sorted(all_columns):
    print(" -", column)

print("\n" + "=" * 70)
print(f"UNIQUE CITIES: {len(cities)}")
print(f"UNIQUE STATIONS: {len(stations)}")
print("=" * 70)

print("\nCITIES:")
for number, city in enumerate(sorted(cities), 1):
    print(f"{number}. {city}")

print("\n" + "=" * 70)