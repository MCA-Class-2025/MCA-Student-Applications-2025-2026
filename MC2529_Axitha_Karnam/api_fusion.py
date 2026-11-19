import os
import csv
from datetime import datetime


# ============================================================
# CONFIGURATION
# ============================================================

API_OUTPUT_FOLDER = "api_outputs"

os.makedirs(
    API_OUTPUT_FOLDER,
    exist_ok=True
)


# ============================================================
# API-SPECIFIC CSV FILES
# ============================================================

API_FILES = {

    "Alpha Vantage":
        "alpha_vantage_answers.csv",

    "Frankfurter":
        "frankfurter_answers.csv",

    "CoinGecko":
        "coingecko_answers.csv",

    "FRED":
        "fred_answers.csv",

    "Twelve Data":
        "twelve_data_answers.csv"
}


# ============================================================
# GET CSV FILE PATH
# ============================================================

def get_api_csv_path(api_name):

    filename = API_FILES.get(
        api_name
    )

    if filename is None:

        raise ValueError(
            f"Unknown API: {api_name}"
        )

    return os.path.join(
        API_OUTPUT_FOLDER,
        filename
    )


# ============================================================
# SAVE API ANSWER
# ============================================================

def save_api_answer(
    api_name,
    question,
    api_result,
    gemma_answer,
    data_type="API",
    source=None
):

    file_path = get_api_csv_path(
        api_name
    )

    if source is None:

        source = api_name

    timestamp = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    # --------------------------------------------------------
    # CSV COLUMNS
    # --------------------------------------------------------

    fieldnames = [

        "Timestamp",

        "Question",

        "Type",

        "API",

        "Source",

        "API_Result",

        "Gemma_Answer"
    ]

    file_exists = os.path.exists(
        file_path
    )

    try:

        with open(
            file_path,
            "a",
            newline="",
            encoding="utf-8"
        ) as file:

            writer = csv.DictWriter(
                file,
                fieldnames=fieldnames
            )

            # Write header only once
            if not file_exists:

                writer.writeheader()

            writer.writerow({

                "Timestamp":
                    timestamp,

                "Question":
                    question,

                "Type":
                    data_type,

                "API":
                    api_name,

                "Source":
                    source,

                "API_Result":
                    str(api_result),

                "Gemma_Answer":
                    str(gemma_answer)
            })

        print(
            f"Saved {api_name} result to:"
        )

        print(
            file_path
        )

        return file_path

    except Exception as error:

        print(
            "Error saving API answer:",
            error
        )

        return None


# ============================================================
# GET API OUTPUT FILE
# ============================================================

def get_api_output_file(
    api_name
):

    return get_api_csv_path(
        api_name
    )


# ============================================================
# GET ALL API OUTPUT FILES
# ============================================================

def get_all_api_output_files():

    output_files = {}

    for api_name in API_FILES:

        output_files[api_name] = (
            get_api_csv_path(api_name)
        )

    return output_files