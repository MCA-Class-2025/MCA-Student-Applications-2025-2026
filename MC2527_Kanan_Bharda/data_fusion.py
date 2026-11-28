
"""
ScamShield AI - Data Fusion
Combines the five external API results into one Excel workbook.
"""

from pathlib import Path
import pandas as pd

# Project folders
ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
DATA.mkdir(exist_ok=True)

SOURCE = DATA / "scamshield_dataset.xlsx"
OUTPUT_XLSX = DATA / "ScamShield_Fused_Dataset.xlsx"
OUTPUT_CSV = DATA / "fused_dataset.csv"
API_CSV = DATA / "api_dataset.csv"

# API status and detail columns in the original application workbook
API_FIELDS = {
    "Safe Browsing": [
        "SafeBrowsing_Status",
        "SafeBrowsing_Details"
    ],
    "VirusTotal": [
        "VirusTotal_Status",
        "VirusTotal_Detections",
        "VirusTotal_Reputation"
    ],
    "AbuseIPDB": [
        "AbuseIPDB_Status",
        "AbuseIPDB_IP",
        "AbuseIPDB_Score",
        "AbuseIPDB_Reports"
    ],
    "PhishTank": [
        "PhishTank_Status",
        "PhishTank_InDatabase",
        "PhishTank_Verified"
    ],
    "URLhaus": [
        "URLhaus_Status",
        "URLhaus_Threat",
        "URLhaus_URL_Status"
    ]
}


def load_data():
    if not SOURCE.exists():
        raise FileNotFoundError(
            f"Source Excel file not found: {SOURCE}\n"
            "Check that data/scamshield_dataset.xlsx exists."
        )

    df = pd.read_excel(SOURCE)

    if df.empty:
        raise ValueError("The source Excel file has no analysis records.")

    return df


def create_fusion(df):
    fused = df.copy()

    # Count API checks for every analysis
    status_columns = [
        fields[0] for fields in API_FIELDS.values()
        if fields[0] in fused.columns
    ]

    fused["APIs_Checked_Count"] = 0
    fused["APIs_With_Usable_Response"] = 0

    for column in status_columns:
        status = fused[column].fillna("").astype(str).str.lower()

        fused["APIs_Checked_Count"] += (
            ~status.isin(["", "not_checked", "not checked", "none"])
        ).astype(int)

        fused["APIs_With_Usable_Response"] += (
            status.isin(["found", "no_match", "no_results", "no_results"])
        ).astype(int)

    fused["Fusion_Record_Status"] = fused[
        "APIs_Checked_Count"
    ].apply(
        lambda count: "APIs checked" if count > 0
        else "No APIs checked"
    )

    return fused


def create_api_evidence(df):
    records = []

    for index, row in df.iterrows():
        record_id = row.get("ID", index + 1)

        for api_name, columns in API_FIELDS.items():
            status_column = columns[0]

            status = row.get(status_column, "not_checked")
            if pd.isna(status) or str(status).strip() == "":
                status = "not_checked"

            details = {}

            for column in columns[1:]:
                value = row.get(column, "")

                if pd.isna(value):
                    value = ""

                details[column] = value

            records.append({
                "ID": record_id,
                "API_Name": api_name,
                "API_Status": status,
                "API_Details": str(details),
                "LLM_Classification": row.get(
                    "LLM_Classification", ""
                ),
                "LLM_Risk_Score": row.get(
                    "LLM_Risk_Score", ""
                )
            })

    return pd.DataFrame(records)


def create_quality_report(df, evidence):
    quality = pd.DataFrame({
        "Metric": [
            "Total analysis records",
            "Total API evidence rows",
            "Expected API rows",
            "Duplicate analysis records",
            "Missing values in source",
            "API responses not checked"
        ],
        "Value": [
            len(df),
            len(evidence),
            len(df) * len(API_FIELDS),
            int(df.duplicated().sum()),
            int(df.isna().sum().sum()),
            int(
                evidence["API_Status"]
                .astype(str)
                .str.lower()
                .isin(["not_checked", "not checked", ""])
                .sum()
            )
        ]
    })

    return quality


def create_dictionary():
    rows = [
        ["ID", "Unique analysis record identifier"],
        ["Message", "SMS, email or message submitted for analysis"],
        ["URL", "Suspicious URL provided or extracted"],
        ["SafeBrowsing_Status", "Google Safe Browsing result"],
        ["VirusTotal_Status", "VirusTotal URL scan result"],
        ["AbuseIPDB_Status", "IP reputation check result"],
        ["PhishTank_Status", "PhishTank phishing database result"],
        ["URLhaus_Status", "URLhaus malware URL result"],
        ["LLM_Classification", "Gemini classification of the message"],
        ["LLM_Risk_Score", "LLM-generated risk score"],
        ["APIs_Checked_Count", "Number of APIs that were checked"],
        ["APIs_With_Usable_Response", "Number of APIs with a usable response"],
        ["Fusion_Record_Status", "Whether API checks were performed"]
    ]

    return pd.DataFrame(rows, columns=["Column", "Description"])


def main():
    print("Starting ScamShield data fusion...")

    original = load_data()
    print(f"Original analysis records: {len(original)}")

    fused = create_fusion(original)
    evidence = create_api_evidence(original)
    quality = create_quality_report(original, evidence)
    dictionary = create_dictionary()

    # Save CSV files
    fused.to_csv(OUTPUT_CSV, index=False)
    evidence.to_csv(API_CSV, index=False)

    # Save all sheets in one Excel workbook
    with pd.ExcelWriter(OUTPUT_XLSX, engine="openpyxl") as writer:
        fused.to_excel(
            writer, sheet_name="Fused_Data", index=False
        )
        evidence.to_excel(
            writer, sheet_name="API_Evidence", index=False
        )
        quality.to_excel(
            writer, sheet_name="Data_Quality", index=False
        )
        dictionary.to_excel(
            writer, sheet_name="Data_Dictionary", index=False
        )

    print("\nDATA FUSION COMPLETED SUCCESSFULLY")
    print(f"Fused Excel: {OUTPUT_XLSX}")
    print(f"Fused CSV: {OUTPUT_CSV}")
    print(f"API evidence CSV: {API_CSV}")
    print(f"Analysis records: {len(fused)}")
    print(f"API evidence rows: {len(evidence)}")
    print("\nData quality summary:")
    print(quality.to_string(index=False))


if __name__ == "__main__":
    main()
