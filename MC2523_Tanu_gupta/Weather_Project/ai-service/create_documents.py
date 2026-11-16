import pandas as pd
import os


# ==========================================
# CONFIGURATION
# ==========================================

INPUT_FILE = "data/weather_cleaned.csv"

OUTPUT_FOLDER = "data/weather_documents"


# ==========================================
# CREATE OUTPUT FOLDER
# ==========================================

os.makedirs(
    OUTPUT_FOLDER,
    exist_ok=True
)


# ==========================================
# LOAD CLEANED DATASET
# ==========================================

print("Loading cleaned dataset...")

df = pd.read_csv(INPUT_FILE)

print(
    "Records loaded:",
    len(df)
)


# ==========================================
# CREATE DOCUMENTS
# ==========================================

documents = []


for index, row in df.iterrows():

    document = f"""
Historical Weather Record

City: {row['city']}

Date: {row['date']}

Weather condition: {row['weather_description']}

Maximum temperature: {row['temperature_2m_max']}°C

Minimum temperature: {row['temperature_2m_min']}°C

Maximum apparent temperature: {row['apparent_temperature_max']}°C

Minimum apparent temperature: {row['apparent_temperature_min']}°C

Total precipitation: {row['precipitation_sum']} mm

Total rainfall: {row['rain_sum']} mm

Maximum wind speed: {row['wind_speed_10m_max']} km/h

Maximum wind gust: {row['wind_gusts_10m_max']} km/h

Dominant wind direction: {row['wind_direction_10m_dominant']} degrees.
""".strip()


    documents.append(document)


# ==========================================
# SAVE ALL DOCUMENTS
# ==========================================

output_file = os.path.join(
    OUTPUT_FOLDER,
    "weather_documents.txt"
)


with open(
    output_file,
    "w",
    encoding="utf-8"
) as file:

    for document in documents:

        file.write(document)

        file.write(
            "\n\n==============================\n\n"
        )


# ==========================================
# COMPLETION MESSAGE
# ==========================================

print("\n====================================")

print("DOCUMENT CREATION COMPLETED")

print("====================================")

print(
    "Total documents:",
    len(documents)
)

print(
    "Output file:",
    output_file
)

print("====================================")