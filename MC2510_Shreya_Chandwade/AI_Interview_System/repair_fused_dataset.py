import csv
from pathlib import Path

INPUT_FILE = Path("fused_interview_dataset_all_rows_1939.csv")
OUTPUT_FILE = Path("fused_interview_dataset_clean.csv")

EXPECTED_COLUMNS = 15

with INPUT_FILE.open("r", encoding="utf-8", newline="") as f:
    rows = list(csv.reader(f))

header = rows[0]
data = rows[1:]

clean_rows = []
repaired = 0

for row in data:

    # Normal row
    if len(row) == EXPECTED_COLUMNS:
        clean_rows.append(row)
        continue

    # The known malformed record contains two student_interview
    # records merged into one CSV record.
    if len(row) == 23 and row[0] == "1942":

        # ---------- RECORD 1942 ----------
        record_1942 = [
            row[0],   # master_row_id
            row[1],   # source_dataset
            row[2],   # source_id
            row[3],   # job_role
            row[4],   # category
            row[5],   # skill
            "",       # programming_language
            "",       # difficulty
            row[8],   # question
            row[9],   # answer
            row[10],  # expected_topics
            "",       # ai_generated_solution - repaired below
            "",       # time_complexity
            "",       # explanation
            ""        # date
        ]

        # The malformed field contains the beginning of the first
        # record's AI-generated solution followed by record 1943.
        combined = row[11]

        marker = "\n\n1943,student_interview,"

        if marker in combined:
            first_solution, second_start = combined.split(marker, 1)

            record_1942[11] = first_solution

            # ---------- RECORD 1943 ----------
            second_fields = [
                "1943",
                "student_interview," + second_start
            ]

            # Reconstruct the second CSV record using the remaining
            # fields that were split incorrectly.
            second_raw = (
                "1943,student_interview,"
                + second_start
            )

            # The remaining malformed fields belong to record 1943.
            # Reconstruct them from the observed structure.
            record_1943 = [
                "1943",
                "student_interview",
                "interview-dc9b77c5-3cec-441a-9917-1c9df5e81871-q-1",
                "Backend Developer",
                "Student Interview",
                "Python, Linux, Cybersecurity",
                "",
                "",
                "Walk me through a project on your resume where you used Python. What challenges did you face?",
                "cc",
                "",
                "",
                "",
                "",
                ""
            ]

            # The actual remaining fields in the malformed row are
            # mapped according to the 15-column schema.
            record_1942[12] = row[12]
            record_1942[13] = row[13]
            record_1942[14] = row[22]

            record_1943[11] = row[19]
            record_1943[12] = row[20]
            record_1943[13] = row[21]
            record_1943[14] = row[22]

            clean_rows.append(record_1942)
            clean_rows.append(record_1943)

            repaired += 1

        else:
            print("WARNING: Could not identify embedded record in row 1942.")
            clean_rows.append(row)

    else:
        print(
            f"WARNING: Unexpected row with {len(row)} columns: "
            f"{row[:3]}"
        )
        clean_rows.append(row)


# Write clean dataset
with OUTPUT_FILE.open(
    "w",
    encoding="utf-8",
    newline=""
) as f:

    writer = csv.writer(f, quoting=csv.QUOTE_MINIMAL)
    writer.writerow(header)
    writer.writerows(clean_rows)


# Verify
with OUTPUT_FILE.open(
    "r",
    encoding="utf-8",
    newline=""
) as f:

    check_rows = list(csv.reader(f))

bad_rows = [
    (i + 1, len(row))
    for i, row in enumerate(check_rows)
    if len(row) != EXPECTED_COLUMNS
]

print("\n===================================")
print("DATASET REPAIR COMPLETED")
print("===================================")
print("Original CSV data rows:", len(data))
print("Repaired malformed records:", repaired)
print("Clean CSV data rows:", len(check_rows) - 1)
print("Bad rows remaining:", len(bad_rows))

if bad_rows:
    print("Bad row details:", bad_rows[:10])
else:
    print("SUCCESS: Every data row has exactly 15 columns.")

print("\nCreated:")
print(OUTPUT_FILE)