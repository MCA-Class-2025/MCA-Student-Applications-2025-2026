import pandas as pd
import os


# =========================================================
# CONFIGURATION
# =========================================================

ORIGINAL_FILE = "data_fusion/cleaned_waste_dataset.csv"

GEOAPIFY_FILE = "api_data/geoapify_recycling.csv"
OPENMETEO_FILE = "api_data/openmeteo_air_quality.csv"
OPENWEATHER_FILE = "api_data/openweather_api.csv"
WEATHERAPI_FILE = "api_data/weather_api.csv"

OUTPUT_FILE = "api_data/final_fused_waste_dataset.csv"


# =========================================================
# CITY NORMALIZATION
# =========================================================

def normalize_city(value):

    if pd.isna(value):
        return ""

    return (
        str(value)
        .strip()
        .lower()
        .replace(" ", "")
    )


# =========================================================
# LOAD DATASETS
# =========================================================

print("\n==============================================")
print("       SMART WASTE DATA FUSION")
print("==============================================")

print("\nLoading datasets...")

original = pd.read_csv(ORIGINAL_FILE)

geoapify = pd.read_csv(GEOAPIFY_FILE)
openmeteo = pd.read_csv(OPENMETEO_FILE)
openweather = pd.read_csv(OPENWEATHER_FILE)
weatherapi = pd.read_csv(WEATHERAPI_FILE)


print("\nDatasets loaded successfully!")

print("\n--- ORIGINAL DATASET ---")
print(f"Records   : {len(original)}")
print(f"Attributes: {len(original.columns)}")

print("\n--- API DATASETS ---")
print(f"Geoapify    : {len(geoapify)} records, {len(geoapify.columns)} attributes")
print(f"Open-Meteo  : {len(openmeteo)} records, {len(openmeteo.columns)} attributes")
print(f"OpenWeather : {len(openweather)} records, {len(openweather.columns)} attributes")
print(f"WeatherAPI  : {len(weatherapi)} records, {len(weatherapi.columns)} attributes")


# =========================================================
# CREATE CITY KEYS
# =========================================================

print("\nNormalizing city names...")

original["City_Key"] = original["City"].apply(normalize_city)

geoapify["City_Key"] = geoapify["Search_City"].apply(normalize_city)
openmeteo["City_Key"] = openmeteo["City"].apply(normalize_city)
openweather["City_Key"] = openweather["City"].apply(normalize_city)
weatherapi["City_Key"] = weatherapi["City"].apply(normalize_city)


# =========================================================
# ORIGINAL DATASET VALIDATION
# =========================================================

print("\n==============================================")
print("       ORIGINAL DATASET VALIDATION")
print("==============================================")

print(f"\nOriginal records       : {len(original)}")
print(f"Original attributes    : {len(original.columns) - 1}")

print(
    f"Original duplicate rows: "
    f"{original.drop(columns=['City_Key']).duplicated().sum()}"
)

if "Record_ID" in original.columns:
    print(
        f"Duplicate Record_IDs   : "
        f"{original['Record_ID'].duplicated().sum()}"
    )


# =========================================================
# API DUPLICATE KEY VALIDATION
# =========================================================

print("\n==============================================")
print("          API KEY VALIDATION")
print("==============================================")

print(
    f"Geoapify duplicate city keys   : "
    f"{geoapify['City_Key'].duplicated().sum()}"
)

print(
    f"Open-Meteo duplicate city keys : "
    f"{openmeteo['City_Key'].duplicated().sum()}"
)

print(
    f"OpenWeather duplicate city keys: "
    f"{openweather['City_Key'].duplicated().sum()}"
)

print(
    f"WeatherAPI duplicate city keys : "
    f"{weatherapi['City_Key'].duplicated().sum()}"
)


# =========================================================
# API MATCHING WITH ORIGINAL DATASET
# =========================================================

original_cities = set(
    original["City_Key"].dropna()
)

geo_cities = set(
    geoapify["City_Key"].dropna()
)

openmeteo_cities = set(
    openmeteo["City_Key"].dropna()
)

openweather_cities = set(
    openweather["City_Key"].dropna()
)

weatherapi_cities = set(
    weatherapi["City_Key"].dropna()
)


print("\n==============================================")
print("             MATCHING ANALYSIS")
print("==============================================")


def print_match(api_name, api_cities):

    matching = original_cities & api_cities
    unmatched = original_cities - api_cities

    print(f"\n{api_name}")
    print(f"Matching cities   : {len(matching)}")
    print(f"Unmatched cities  : {len(unmatched)}")


print_match("Geoapify", geo_cities)
print_match("Open-Meteo", openmeteo_cities)
print_match("OpenWeather", openweather_cities)
print_match("WeatherAPI", weatherapi_cities)


# =========================================================
# PREPARE GEOAPIFY
# =========================================================

geoapify_agg = (
    geoapify
    .groupby("City_Key")
    .agg(
        Recycling_Facility_Count=(
            "Name",
            "count"
        ),

        Recycling_Facility_Names=(
            "Name",
            lambda x: " | ".join(
                x.dropna()
                .astype(str)
                .unique()
            )
        ),

        Recycling_Categories=(
            "Categories",
            lambda x: " | ".join(
                x.dropna()
                .astype(str)
                .unique()
            )
        ),

        Average_Facility_Distance_Meters=(
            "Distance_Meters",
            "mean"
        ),

        Sample_Place_ID=(
            "Place_ID",
            "first"
        ),

        Waste_API_Source=(
            "API_Source",
            "first"
        )
    )
    .reset_index()
)

geoapify_agg[
    "Average_Facility_Distance_Meters"
] = geoapify_agg[
    "Average_Facility_Distance_Meters"
].round(2)


# =========================================================
# REMOVE API DUPLICATES
# =========================================================

openmeteo = openmeteo.drop_duplicates(
    subset=["City_Key"]
)

openweather = openweather.drop_duplicates(
    subset=["City_Key"]
)

weatherapi = weatherapi.drop_duplicates(
    subset=["City_Key"]
)


# =========================================================
# OPEN-METEO
# =========================================================

openmeteo_selected = openmeteo[
    [
        "City_Key",
        "PM10",
        "PM2_5",
        "Carbon_Monoxide",
        "Carbon_Dioxide",
        "Nitrogen_Dioxide",
        "Sulphur_Dioxide",
        "Ozone",
        "Dust",
        "UV_Index",
        "European_AQI",
        "US_AQI",
        "Observation_Time",
        "API_Source"
    ]
].copy()

openmeteo_selected = openmeteo_selected.rename(
    columns={
        "PM10": "OpenMeteo_PM10",
        "PM2_5": "OpenMeteo_PM2_5",
        "Carbon_Monoxide": "OpenMeteo_CO",
        "Carbon_Dioxide": "OpenMeteo_CO2",
        "Nitrogen_Dioxide": "OpenMeteo_NO2",
        "Sulphur_Dioxide": "OpenMeteo_SO2",
        "Ozone": "OpenMeteo_O3",
        "Dust": "OpenMeteo_Dust",
        "UV_Index": "OpenMeteo_UV_Index",
        "European_AQI": "European_AQI",
        "US_AQI": "OpenMeteo_US_AQI",
        "Observation_Time": "OpenMeteo_Observation_Time",
        "API_Source": "OpenMeteo_API_Source"
    }
)


# =========================================================
# OPENWEATHER
# =========================================================

openweather_selected = openweather[
    [
        "City_Key",
        "Temperature_C",
        "Feels_Like_C",
        "Minimum_Temperature_C",
        "Maximum_Temperature_C",
        "Pressure_hPa",
        "Humidity_Percent",
        "Visibility_Meters",
        "Wind_Speed_mps",
        "Wind_Direction_Degrees",
        "Wind_Gust_mps",
        "Cloudiness_Percent",
        "Rain_1h_MM",
        "Weather_ID",
        "Weather_Main",
        "Weather_Description",
        "Weather_Icon",
        "Country",
        "Sunrise",
        "Sunset",
        "Observation_Time",
        "Timezone_Seconds",
        "API_Source"
    ]
].copy()

openweather_selected = openweather_selected.rename(
    columns={
        "Temperature_C": "OpenWeather_Temperature_C",
        "Feels_Like_C": "OpenWeather_Feels_Like_C",
        "Minimum_Temperature_C": "OpenWeather_Min_Temperature_C",
        "Maximum_Temperature_C": "OpenWeather_Max_Temperature_C",
        "Pressure_hPa": "OpenWeather_Pressure_hPa",
        "Humidity_Percent": "OpenWeather_Humidity_Percent",
        "Visibility_Meters": "OpenWeather_Visibility_Meters",
        "Wind_Speed_mps": "OpenWeather_Wind_Speed_mps",
        "Wind_Direction_Degrees": "OpenWeather_Wind_Direction_Degrees",
        "Wind_Gust_mps": "OpenWeather_Wind_Gust_mps",
        "Cloudiness_Percent": "OpenWeather_Cloudiness_Percent",
        "Rain_1h_MM": "OpenWeather_Rain_1h_MM",
        "Weather_ID": "OpenWeather_Weather_ID",
        "Weather_Main": "OpenWeather_Weather_Main",
        "Weather_Description": "OpenWeather_Weather_Description",
        "Weather_Icon": "OpenWeather_Weather_Icon",
        "Country": "OpenWeather_Country",
        "Sunrise": "OpenWeather_Sunrise",
        "Sunset": "OpenWeather_Sunset",
        "Observation_Time": "OpenWeather_Observation_Time",
        "Timezone_Seconds": "OpenWeather_Timezone_Seconds",
        "API_Source": "OpenWeather_API_Source"
    }
)


# =========================================================
# WEATHER API
# =========================================================

weatherapi_selected = weatherapi[
    [
        "City_Key",
        "Last_Updated",
        "Temperature_C",
        "Feels_Like_C",
        "Humidity_Percent",
        "Wind_KPH",
        "Wind_Direction",
        "Pressure_MB",
        "Precipitation_MM",
        "Cloud_Percent",
        "Visibility_KM",
        "UV_Index",
        "Gust_KPH",
        "Weather_Condition",
        "US_EPA_AQI",
        "PM2_5",
        "PM10",
        "CO",
        "NO2",
        "SO2",
        "O3",
        "API_Source"
    ]
].copy()

weatherapi_selected = weatherapi_selected.rename(
    columns={
        "Last_Updated": "WeatherAPI_Last_Updated",
        "Temperature_C": "WeatherAPI_Temperature_C",
        "Feels_Like_C": "WeatherAPI_Feels_Like_C",
        "Humidity_Percent": "WeatherAPI_Humidity_Percent",
        "Wind_KPH": "WeatherAPI_Wind_KPH",
        "Wind_Direction": "WeatherAPI_Wind_Direction",
        "Pressure_MB": "WeatherAPI_Pressure_MB",
        "Precipitation_MM": "WeatherAPI_Precipitation_MM",
        "Cloud_Percent": "WeatherAPI_Cloud_Percent",
        "Visibility_KM": "WeatherAPI_Visibility_KM",
        "UV_Index": "WeatherAPI_UV_Index",
        "Gust_KPH": "WeatherAPI_Gust_KPH",
        "Weather_Condition": "WeatherAPI_Condition",
        "US_EPA_AQI": "WeatherAPI_US_EPA_AQI",
        "PM2_5": "WeatherAPI_PM2_5",
        "PM10": "WeatherAPI_PM10",
        "CO": "WeatherAPI_CO",
        "NO2": "WeatherAPI_NO2",
        "SO2": "WeatherAPI_SO2",
        "O3": "WeatherAPI_O3",
        "API_Source": "WeatherAPI_Source"
    }
)


# =========================================================
# API FUSION
# =========================================================

print("\n==============================================")
print("             FUSING API DATA")
print("==============================================")

api_fused = openweather_selected.copy()

api_fused = api_fused.merge(
    weatherapi_selected,
    on="City_Key",
    how="left"
)

api_fused = api_fused.merge(
    openmeteo_selected,
    on="City_Key",
    how="left"
)

api_fused = api_fused.merge(
    geoapify_agg,
    on="City_Key",
    how="left"
)

print(f"\nAPI fused records    : {len(api_fused)}")
print(f"API fused attributes : {len(api_fused.columns)}")


# =========================================================
# ORIGINAL + API FUSION
# =========================================================

print("\n==============================================")
print("       ORIGINAL + API DATA FUSION")
print("==============================================")

original_records_before = len(original)

fused = original.merge(
    api_fused,
    on="City_Key",
    how="left",
    suffixes=("", "_API")
)

print(
    f"Original records before fusion : "
    f"{original_records_before}"
)

print(
    f"Records after fusion           : "
    f"{len(fused)}"
)

print(
    f"Final attributes               : "
    f"{len(fused.columns)}"
)


# =========================================================
# MISSING API RESPONSES
# =========================================================

print("\n==============================================")
print("          MISSING API RESPONSES")
print("==============================================")

api_columns = [
    col for col in api_fused.columns
    if col != "City_Key"
]

missing_api_rows = fused[api_columns].isna().all(axis=1)

print(
    f"Records with no API response : "
    f"{missing_api_rows.sum()}"
)

for source, column in [
    ("OpenWeather", "OpenWeather_Temperature_C"),
    ("WeatherAPI", "WeatherAPI_Temperature_C"),
    ("Open-Meteo", "OpenMeteo_PM10"),
    ("Geoapify", "Recycling_Facility_Count")
]:

    if column in fused.columns:

        print(
            f"{source} missing responses : "
            f"{fused[column].isna().sum()}"
        )


# =========================================================
# RECORDS LOST / ADDED
# =========================================================

print("\n==============================================")
print("        RECORD LOSS / ADDITION")
print("==============================================")

records_lost = original_records_before - len(fused)

print(f"Original records : {original_records_before}")
print(f"Fused records    : {len(fused)}")
print(f"Records lost     : {records_lost}")

print(
    f"API source records added as attributes: "
    f"{len(fused) - original_records_before}"
)


# =========================================================
# CONFLICTING VALUES
# =========================================================

print("\n==============================================")
print("           CONFLICTING VALUES")
print("==============================================")

conflict_count = 0

# Latitude comparison
if "Latitude" in fused.columns and "Latitude_API" in fused.columns:

    lat_conflicts = (
        fused["Latitude"].notna()
        & fused["Latitude_API"].notna()
        & (
            abs(
                fused["Latitude"]
                - fused["Latitude_API"]
            ) > 0.01
        )
    )

    print(
        f"Latitude conflicts : "
        f"{lat_conflicts.sum()}"
    )

    conflict_count += lat_conflicts.sum()


# Longitude comparison
if "Longitude" in fused.columns and "Longitude_API" in fused.columns:

    lon_conflicts = (
        fused["Longitude"].notna()
        & fused["Longitude_API"].notna()
        & (
            abs(
                fused["Longitude"]
                - fused["Longitude_API"]
            ) > 0.01
        )
    )

    print(
        f"Longitude conflicts: "
        f"{lon_conflicts.sum()}"
    )

    conflict_count += lon_conflicts.sum()


print(
    f"Total coordinate conflicts: "
    f"{conflict_count}"
)


# =========================================================
# FINAL DUPLICATE CHECK
# =========================================================

print("\n==============================================")
print("           FINAL DATASET CHECK")
print("==============================================")

print(
    f"Duplicate complete records: "
    f"{fused.drop(columns=['City_Key']).duplicated().sum()}"
)

if "Record_ID" in fused.columns:

    print(
        f"Duplicate Record_IDs      : "
        f"{fused['Record_ID'].duplicated().sum()}"
    )


# =========================================================
# REMOVE CITY KEY
# =========================================================

if "City_Key" in fused.columns:

    fused = fused.drop(
        columns=["City_Key"]
    )


# =========================================================
# SAVE FINAL DATASET
# =========================================================

os.makedirs(
    "api_data",
    exist_ok=True
)

fused.to_csv(
    OUTPUT_FILE,
    index=False
)


# =========================================================
# FINAL RESULT
# =========================================================

print("\n==============================================")
print("          DATA FUSION COMPLETED")
print("==============================================")

print(
    f"Final records    : {len(fused)}"
)

print(
    f"Final attributes : {len(fused.columns)}"
)

print(
    f"Saved file       : {OUTPUT_FILE}"
)

print("\nFirst 5 fused records:")
print(
    fused.head().to_string()
)

print("\n==============================================")
print("       ALL API DATA SUCCESSFULLY FUSED")
print("==============================================")