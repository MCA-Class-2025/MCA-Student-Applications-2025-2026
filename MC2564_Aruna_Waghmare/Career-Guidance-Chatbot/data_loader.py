import pandas as pd
import os


DATA_PATH = "dataset"



# Function to load CSV

def load_csv(file_name):

    path = os.path.join(DATA_PATH, file_name)

    try:
        df = pd.read_csv(
            path,
            encoding="latin1"
        )

        print("\nLoaded:", file_name)
        print("Shape:", df.shape)
        print("Columns:", list(df.columns))

        return df

    except Exception as e:
        print("Error loading", file_name, ":", e)
        return None



# Function to load Excel

def load_excel(file_name):

    path = os.path.join(DATA_PATH, file_name)

    try:
        df = pd.read_excel(path)

        print("\nLoaded:", file_name)
        print("Shape:", df.shape)
        print("Columns:", list(df.columns))

        return df

    except Exception as e:
        print("Error loading", file_name, ":", e)
        return None



# Load your datasets

dataset1 = load_csv(
    "IT_Job_Roles_Skills.csv"
)


dataset2 = load_csv(
    "gpt_dataset.csv"
)





# Store available datasets

datasets = [
    dataset1,
    dataset2,
    dataset3
]


# Remove failed loads

datasets = [
    df for df in datasets 
    if df is not None
]



# Cleaning function

def clean_data(df):

    # remove duplicate rows
    df = df.drop_duplicates()


    # fill missing values
    df = df.fillna("Not Available")


    # clean column names

    df.columns = (
        df.columns
        .astype(str)
        .str.strip()
        .str.lower()
        .str.replace(" ", "_")
    )


    return df



cleaned_datasets = []


for df in datasets:

    cleaned_datasets.append(
        clean_data(df)
    )



# Check datasets

if len(cleaned_datasets) == 0:

    raise Exception(
        "No dataset loaded. Check files."
    )



# Combine all datasets

combined_data = pd.concat(
    cleaned_datasets,
    ignore_index=True,
    sort=False
)



# Save processed file

os.makedirs(
    "processed_data",
    exist_ok=True
)


combined_data.to_csv(
    "processed_data/career_data_cleaned.csv",
    index=False
)



print("\n==========================")
print("DATA PROCESSING COMPLETED")
print("==========================")

print(
    "Final Shape:",
    combined_data.shape
)

print(
    "Saved: processed_data/career_data_cleaned.csv"
)