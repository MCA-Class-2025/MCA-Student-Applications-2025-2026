"""
03_fusion.py -- Part C: Data Fusion
=====================================
Common attribute : city name (extracted from the "place" / "to" fields)
Fusion method     : LEFT JOIN (original travel data -> API climate data)
                    + INNER JOIN (fused data -> users, on userCode)
"""
import pandas as pd
import numpy as np
import re
import json

RAW = "/home/claude/FinSightAI/data/original"
API = "/home/claude/FinSightAI/data/api"
OUT = "/home/claude/FinSightAI/data/fused"

CITY_RE = re.compile(r"^\s*([A-Za-z\u00C0-\u00FF ]+?)\s*\(")

def extract_city(raw_place):
    """Standardize messy place strings -> clean city key for joining.
    Handles casing issues, extra spaces, and missing parentheses spacing
    (e.g. 'salvador (bh)', 'Recife(PE)', 'Sao Paulo  (SP)')."""
    if pd.isna(raw_place):
        return np.nan
    s = str(raw_place).strip()
    m = CITY_RE.match(s)
    city = m.group(1).strip() if m else s
    return city.title()

def parse_mixed_dates(series):
    """Original export mixes MM/DD/YYYY and MM-DD-YYYY formats -- normalize
    both to a single datetime dtype."""
    def _parse(x):
        for fmt in ("%m/%d/%Y", "%m-%d-%Y"):
            try:
                return pd.to_datetime(x, format=fmt)
            except (ValueError, TypeError):
                continue
        return pd.NaT
    return series.apply(_parse)

def clean_common(df):
    df = df.drop_duplicates().copy()
    return df

def main():
    users   = pd.read_csv(f"{RAW}/users.csv")
    hotels  = pd.read_csv(f"{RAW}/hotels.csv")
    flights = pd.read_csv(f"{RAW}/flights.csv")
    weather = pd.read_csv(f"{API}/weather_climate_api.csv")

    n_dupe_users, n_dupe_hotels, n_dupe_flights = (
        users.duplicated().sum(), hotels.duplicated().sum(), flights.duplicated().sum())

    users   = clean_common(users)
    hotels  = clean_common(hotels)
    flights = clean_common(flights)

    users["name"] = users["name"].str.strip()
    users["company"] = users["company"].str.strip().str.title()

    hotels["date"] = parse_mixed_dates(hotels["date"])
    flights["date"] = parse_mixed_dates(flights["date"])

    hotels["city_key"]  = hotels["place"].apply(extract_city)
    flights["dest_city_key"] = flights["to"].apply(extract_city)
    flights["orig_city_key"] = flights["from"].apply(extract_city)
    weather["city_key"] = weather["city"].apply(lambda c: c.title())

    # ---------- Fusion #1: hotels (original) <- weather (API), on city ----------
    n_hotels_before = len(hotels)
    hotels_fused = hotels.merge(
        weather.drop(columns=["city"]), on="city_key", how="left", indicator=True
    )
    unmatched_hotels = (hotels_fused["_merge"] == "left_only").sum()
    hotels_fused = hotels_fused.drop(columns=["_merge"])

    # enrich with employee/company info (inner join: every booking must map to a real employee)
    fused = hotels_fused.merge(users, left_on="userCode", right_on="code", how="inner", suffixes=("", "_user"))
    fused = fused.rename(columns={"name": "hotel_name", "name_user": "employee_name"})

    # ---------- Fusion #2: flights (original) <- weather (API), on destination city ----------
    n_flights_before = len(flights)
    flights_fused = flights.merge(
        weather.drop(columns=["city"]), left_on="dest_city_key", right_on="city_key", how="left", indicator=True
    )
    unmatched_flights = (flights_fused["_merge"] == "left_only").sum()
    flights_fused = flights_fused.drop(columns=["_merge"])
    flights_fused = flights_fused.merge(users, left_on="userCode", right_on="code", how="inner", suffixes=("", "_user"))
    flights_fused = flights_fused.rename(columns={"name": "employee_name"})

    fused.to_csv(f"{OUT}/fused_hotels_weather_employee.csv", index=False)
    flights_fused.to_csv(f"{OUT}/fused_flights_weather_employee.csv", index=False)

    # ---------- Validation summary ----------
    validation = {
        "hotels_records_before_fusion": int(n_hotels_before),
        "hotels_records_after_fusion": int(len(fused)),
        "hotels_matched_with_weather": int(n_hotels_before - unmatched_hotels),
        "hotels_unmatched_with_weather": int(unmatched_hotels),
        "flights_records_before_fusion": int(n_flights_before),
        "flights_records_after_fusion": int(len(flights_fused)),
        "flights_matched_with_weather": int(n_flights_before - unmatched_flights),
        "flights_unmatched_with_weather": int(unmatched_flights),
        "duplicate_rows_removed_users": int(n_dupe_users),
        "duplicate_rows_removed_hotels": int(n_dupe_hotels),
        "duplicate_rows_removed_flights": int(n_dupe_flights),
        "unique_cities_in_original_hotels": int(hotels["city_key"].nunique()),
        "unique_cities_in_api_dataset": int(weather["city_key"].nunique()),
        "cities_in_hotels_missing_from_api": sorted(set(hotels["city_key"].dropna().unique()) - set(weather["city_key"].unique())),
    }
    with open(f"{OUT}/fusion_validation.json", "w") as f:
        json.dump(validation, f, indent=2)

    print(json.dumps(validation, indent=2))
    print("\nFused hotel dataset shape :", fused.shape)
    print("Fused flight dataset shape:", flights_fused.shape)

if __name__ == "__main__":
    main()
