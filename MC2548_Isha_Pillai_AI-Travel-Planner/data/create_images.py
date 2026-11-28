import sys
import os

sys.path.append(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)

import pandas as pd
from services.pexels_service import search_destination_image


# --------------------------------------------------
# 1. Read original travel dataset
# --------------------------------------------------

input_file = "data/Travel details dataset.csv"

df = pd.read_csv(
    input_file,
    sep="\t"
)


image_records = []


# --------------------------------------------------
# 2. Process every trip
# --------------------------------------------------

for _, row in df.iterrows():

    trip_id = int(row["Trip ID"])

    destination = str(
        row["Destination"]
    ).strip()

    # Skip missing destinations
    if destination.lower() == "nan" or destination == "":
        print(
            f"Skipping Trip {trip_id} - "
            f"destination is missing"
        )
        continue

    print(
        f"Getting image for Trip {trip_id}: "
        f"{destination}"
    )


    # --------------------------------------------------
    # 3. Call Pexels API
    # --------------------------------------------------

    result = search_destination_image(
        destination
    )


    if result is None:

        print(
            f"Skipping Trip {trip_id} - "
            f"image data unavailable"
        )

        continue


    # --------------------------------------------------
    # 4. Check for complete data
    # --------------------------------------------------

    required_fields = [
        "photo_id",
        "photographer",
        "image_url",
        "pexels_url"
    ]


    missing_data = False

    for field in required_fields:

        if not result.get(field):

            missing_data = True
            break


    if missing_data:

        print(
            f"Skipping Trip {trip_id} - "
            f"incomplete image data"
        )

        continue


    # --------------------------------------------------
    # 5. Add clean record
    # --------------------------------------------------

    image_records.append({

        # Primary Key
        "Image_ID": (
            f"IMG{trip_id:03d}"
        ),

        # Foreign Key
        "Trip_ID": trip_id,

        "Destination": destination,

        "Photo_ID": result[
            "photo_id"
        ],

        "Photographer": result[
            "photographer"
        ],

        "Image_URL": result[
            "image_url"
        ],

        "Pexels_URL": result[
            "pexels_url"
        ]
    })


# --------------------------------------------------
# 6. Create DataFrame
# --------------------------------------------------

images_df = pd.DataFrame(
    image_records
)


# --------------------------------------------------
# 7. Remove NULL values
# --------------------------------------------------

if not images_df.empty:

    images_df = images_df.dropna()


    # Remove empty strings
    for column in images_df.columns:

        images_df = images_df[
            images_df[column]
            .astype(str)
            .str.strip()
            .ne("")
        ]


# --------------------------------------------------
# 8. Save clean dataset
# --------------------------------------------------

output_file = "data/images.csv"

images_df.to_csv(
    output_file,
    index=False
)


# --------------------------------------------------
# 9. Display results
# --------------------------------------------------

print("\n--------------------------------")
print("Clean images.csv created!")
print("--------------------------------")

print(
    "Number of records:",
    len(images_df)
)

print("\nColumns:")

print(
    list(images_df.columns)
)

print("\nImage Data:")

print(
    images_df.to_string(
        index=False
    )
)