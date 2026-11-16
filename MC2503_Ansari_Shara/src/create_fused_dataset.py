import os

from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill
from openpyxl.utils import get_column_letter

from database import Database
from virus_total import VirusTotal
from malware_bazaar import MalwareBazaar
from url_scanner import URLScanner
from nvd_api import NVD
from mitre_attack import MITREAttack


# ==========================================================
# CONFIGURATION
# ==========================================================

OUTPUT_FILE = "SecureShare_API_Dataset_v2.xlsx"

# NVD search used for the project
NVD_KEYWORD = "Microsoft Windows"

# MITRE ATT&CK search used for the project
MITRE_KEYWORD = "command and scripting"


# ==========================================================
# INITIALIZE COMPONENTS
# ==========================================================

print("=" * 60)
print("INITIALIZING API DATA COLLECTION")
print("=" * 60)

db = Database()

vt = VirusTotal()

mb = MalwareBazaar()

urlhaus_key = os.getenv("URLHAUS_AUTH_KEY")

if not urlhaus_key:
    raise ValueError(
        "URLHAUS_AUTH_KEY not found in .env file."
    )

url_scanner = URLScanner(urlhaus_key)

nvd = NVD()

mitre = MITREAttack()


# ==========================================================
# GET USERNAMES
# ==========================================================

user_input = input(
    "\nEnter SecureShare usernames to scan separated by comma: "
)

usernames = [
    username.strip()
    for username in user_input.split(",")
    if username.strip()
]

if not usernames:

    print("No usernames entered.")

    exit()


print("\nUsers selected:")

for username in usernames:

    print("-", username)


# ==========================================================
# CREATE EXCEL WORKBOOK
# ==========================================================

workbook = Workbook()

sheet = workbook.active

sheet.title = "API Dataset"


# ==========================================================
# EXCEL COLUMNS
# ==========================================================

headers = [

    # -----------------------------
    # SecureShare Information
    # -----------------------------

    "Username",
    "File Name",
    "File Path",
    "File SHA-256",

    # -----------------------------
    # VirusTotal
    # -----------------------------

    "VT Found",
    "VT Malicious",
    "VT Suspicious",
    "VT Harmless",
    "VT Undetected",
    "VT Error",

    # -----------------------------
    # MalwareBazaar
    # -----------------------------

    "MB Found",
    "MB Malicious",
    "MB Query Status",
    "MB Error",

    # -----------------------------
    # URLhaus
    # -----------------------------

    "URLs Found",
    "URLhaus Malicious Count",
    "URLhaus Not Found Count",
    "URLhaus Error Count",
    "Malicious URLs",
    "URL Threats",
    "URL Hosts",

    # -----------------------------
    # Combined File Result
    # -----------------------------

    "Combined File Result",

    # -----------------------------
    # NVD
    # -----------------------------

    "NVD Search Keyword",
    "NVD Matching CVEs",
    "NVD CVE IDs",
    "NVD Descriptions",

    # -----------------------------
    # MITRE ATT&CK
    # -----------------------------

    "MITRE Search Keyword",
    "MITRE Matching Techniques",
    "MITRE Technique IDs",
    "MITRE Technique Names",
    "MITRE Descriptions"

]


# ==========================================================
# WRITE HEADER
# ==========================================================

for column_number, header in enumerate(headers, start=1):

    cell = sheet.cell(
        row=1,
        column=column_number,
        value=header
    )

    cell.font = Font(
        bold=True,
        color="FFFFFF"
    )

    cell.fill = PatternFill(
        fill_type="solid",
        fgColor="2563EB"
    )

    cell.alignment = Alignment(
        horizontal="center",
        vertical="center"
    )


sheet.freeze_panes = "A2"

sheet.auto_filter.ref = (
    f"A1:{get_column_letter(len(headers))}1"
)


# ==========================================================
# COLLECT NVD DATA
# ==========================================================

print("\n" + "=" * 60)
print("COLLECTING NVD DATA")
print("=" * 60)

nvd_result = nvd.search_cve(NVD_KEYWORD)

nvd_cve_ids = []

nvd_descriptions = []

nvd_total = 0


if "error" not in nvd_result:

    nvd_total = nvd_result.get(
        "totalResults",
        0
    )

    for item in nvd_result.get(
        "vulnerabilities",
        []
    )[:5]:

        cve = item.get(
            "cve",
            {}
        )

        cve_id = cve.get(
            "id",
            ""
        )

        descriptions = cve.get(
            "descriptions",
            []
        )

        description = ""

        if descriptions:

            description = descriptions[0].get(
                "value",
                ""
            )

        if cve_id:

            nvd_cve_ids.append(
                cve_id
            )

        if description:

            nvd_descriptions.append(
                description
            )


print(
    f"NVD matching CVEs: {nvd_total}"
)


# ==========================================================
# COLLECT MITRE ATT&CK DATA
# ==========================================================

print("\n" + "=" * 60)
print("COLLECTING MITRE ATT&CK DATA")
print("=" * 60)

mitre_results = mitre.search_technique(
    MITRE_KEYWORD
)

mitre_ids = []

mitre_names = []

mitre_descriptions = []


for technique in mitre_results[:5]:

    technique_id = technique.get(
        "id",
        ""
    )

    technique_name = technique.get(
        "name",
        ""
    )

    description = technique.get(
        "description",
        ""
    )

    if technique_id:

        mitre_ids.append(
            technique_id
        )

    if technique_name:

        mitre_names.append(
            technique_name
        )

    if description:

        mitre_descriptions.append(
            description
        )


print(
    f"MITRE matching techniques: "
    f"{len(mitre_results)}"
)


# ==========================================================
# SCAN USERS
# ==========================================================

total_rows = 0


for username in usernames:

    print("\n" + "=" * 60)

    print(
        f"SCANNING USER: {username}"
    )

    print("=" * 60)


    # ------------------------------------------------------
    # Get user's files
    # ------------------------------------------------------

    files = db.get_user_files(
        username
    )

    if not files:

        print(
            f"No files found for user: {username}"
        )

        continue


    # ------------------------------------------------------
    # URLhaus scan
    # ------------------------------------------------------

    print(
        f"\nCollecting URLhaus data for {username}..."
    )

    url_results = url_scanner.scan_files(
        files
    )


    # Create mapping:

    # file name -> URLhaus result

    url_result_map = {}

    for result in url_results:

        url_result_map[
            result["file_name"]
        ] = result


    # ------------------------------------------------------
    # Scan each file
    # ------------------------------------------------------

    for file in files:

        file_name = file["file_name"]

        database_path = file["file_path"]

        upload_folder = (
            r"C:\xampp\htdocs\zero_trust_system\uploads"
        )

        full_path = os.path.join(
            upload_folder,
            os.path.basename(database_path)
        )


        print(
            f"\nProcessing: {file_name}"
        )


        # ==================================================
        # FILE HASH
        # ==================================================

        file_hash = ""

        if os.path.exists(full_path):

            try:

                file_hash = vt.calculate_hash(
                    full_path
                )

            except Exception as error:

                print(
                    f"Hash error: {error}"
                )


        # ==================================================
        # VIRUSTOTAL
        # ==================================================

        print(
            f"  Checking VirusTotal: {file_name}"
        )

        if file_hash:

            vt_result = vt.check_hash(
                file_hash
            )

        else:

            vt_result = {
                "found": False,
                "malicious": 0,
                "suspicious": 0,
                "harmless": 0,
                "undetected": 0,
                "error": "File not found"
            }


        # ==================================================
        # MALWAREBAZAAR
        # ==================================================

        print(
            f"  Checking MalwareBazaar: {file_name}"
        )

        if file_hash:

            mb_result = mb.check_hash(
                file_hash
            )

        else:

            mb_result = {
                "found": False,
                "malicious": False,
                "query_status": "file_not_found",
                "error": "File not found"
            }


        # ==================================================
        # URLHAUS
        # ==================================================

        url_result = url_result_map.get(
            file_name,
            {}
        )

        urls = url_result.get(
            "urls",
            []
        )

        malicious_url_items = (
            url_result.get(
                "malicious_urls",
                []
            )
        )

        not_found_urls = (
            url_result.get(
                "not_found_urls",
                []
            )
        )

        error_urls = (
            url_result.get(
                "error_urls",
                []
            )
        )


        malicious_url_values = []

        url_threat_values = []

        url_host_values = []


        for item in malicious_url_items:

            malicious_url_values.append(
                item.get(
                    "url",
                    ""
                )
            )

            url_threat_values.append(
                item.get(
                    "threat",
                    ""
                )
            )

            url_host_values.append(
                item.get(
                    "host",
                    ""
                )
            )


        # ==================================================
        # COMBINED FILE RESULT
        # ==================================================

        vt_malicious = (
            vt_result.get(
                "malicious",
                0
            ) > 0
        )

        vt_suspicious = (
            vt_result.get(
                "suspicious",
                0
            ) > 0
        )

        mb_malicious = (
            mb_result.get(
                "malicious",
                False
            )
        )

        url_malicious = (
            len(malicious_url_items) > 0
        )


        if vt_malicious or mb_malicious:

            combined_result = "MALICIOUS"

        elif vt_suspicious:

            combined_result = "SUSPICIOUS"

        elif not vt_result.get(
            "found",
            False
        ):

            combined_result = "UNKNOWN"

        else:

            combined_result = (
                "NO_KNOWN_THREAT"
            )


        # ==================================================
        # ADD ROW TO EXCEL
        # ==================================================

        row = [

            # SecureShare
            username,
            file_name,
            full_path,
            file_hash,

            # VirusTotal
            vt_result.get(
                "found",
                False
            ),
            vt_result.get(
                "malicious",
                0
            ),
            vt_result.get(
                "suspicious",
                0
            ),
            vt_result.get(
                "harmless",
                0
            ),
            vt_result.get(
                "undetected",
                0
            ),
            vt_result.get(
                "error",
                ""
            ),

            # MalwareBazaar
            mb_result.get(
                "found",
                False
            ),
            mb_result.get(
                "malicious",
                False
            ),
            mb_result.get(
                "query_status",
                ""
            ),
            mb_result.get(
                "error",
                ""
            ),

            # URLhaus
            len(urls),
            len(malicious_url_items),
            len(not_found_urls),
            len(error_urls),
            "\n".join(
                malicious_url_values
            ),
            "\n".join(
                url_threat_values
            ),
            "\n".join(
                url_host_values
            ),

            # Combined result
            combined_result,

            # NVD
            NVD_KEYWORD,
            nvd_total,
            "\n".join(
                nvd_cve_ids
            ),
            "\n".join(
                nvd_descriptions
            ),

            # MITRE
            MITRE_KEYWORD,
            len(mitre_results),
            "\n".join(
                mitre_ids
            ),
            "\n".join(
                mitre_names
            ),
            "\n".join(
                mitre_descriptions
            )

        ]


        sheet.append(row)

        total_rows += 1


# ==========================================================
# FORMAT EXCEL
# ==========================================================

print("\n" + "=" * 60)

print(
    "FORMATTING EXCEL FILE"
)

print("=" * 60)


for row in sheet.iter_rows():

    for cell in row:

        cell.alignment = Alignment(
            vertical="top",
            wrap_text=True
        )


# ----------------------------------------------------------
# Set reasonable column widths
# ----------------------------------------------------------

column_widths = {

    "A": 15,
    "B": 35,
    "C": 50,
    "D": 70,

    "E": 12,
    "F": 15,
    "G": 15,
    "H": 15,
    "I": 15,
    "J": 25,

    "K": 12,
    "L": 15,
    "M": 20,
    "N": 25,

    "O": 12,
    "P": 20,
    "Q": 20,
    "R": 18,
    "S": 45,
    "T": 25,
    "U": 30,

    "V": 22,

    "W": 25,
    "X": 18,
    "Y": 45,
    "Z": 70,

    "AA": 30,
    "AB": 25,
    "AC": 25,
    "AD": 40,
    "AE": 70

}


for column, width in column_widths.items():

    sheet.column_dimensions[
        column
    ].width = width


# ----------------------------------------------------------
# Row height
# ----------------------------------------------------------

for row_number in range(
    2,
    sheet.max_row + 1
):

    sheet.row_dimensions[
        row_number
    ].height = 100


# ----------------------------------------------------------
# Header row height
# ----------------------------------------------------------

sheet.row_dimensions[1].height = 35


# ==========================================================
# SAVE FILE
# ==========================================================

workbook.save(
    OUTPUT_FILE
)


# ==========================================================
# FINAL MESSAGE
# ==========================================================

print("\n" + "=" * 60)

print(
    "API DATASET CREATED SUCCESSFULLY"
)

print("=" * 60)

print(
    f"Excel file: {OUTPUT_FILE}"
)

print(
    f"Users scanned: {len(usernames)}"
)

print(
    f"Total file rows collected: {total_rows}"
)

print(
    "\nOpen the Excel file and check the columns."
)

print("=" * 60)