from pathlib import Path
import cv2
import numpy as np
import pandas as pd


# ============================================================
# PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

TRAIN_DIR = PROJECT_ROOT / "data" / "train"
TEST_DIR = PROJECT_ROOT / "data" / "test"

OUTPUT_FILE = PROJECT_ROOT / "data" / "fusion_metadata.csv"


# ============================================================
# IMAGE FEATURES
# ============================================================

def get_image_features(image_path):

    img = cv2.imread(str(image_path))

    if img is None:
        return None

    # Resize
    img = cv2.resize(img, (224, 224))

    # OpenCV = BGR
    b, g, r = cv2.split(img)

    # RGB statistics
    mean_r = np.mean(r)
    mean_g = np.mean(g)
    mean_b = np.mean(b)

    std_r = np.std(r)
    std_g = np.std(g)
    std_b = np.std(b)

    # Grayscale
    gray = cv2.cvtColor(
        img,
        cv2.COLOR_BGR2GRAY
    )

    # Brightness
    brightness = np.mean(gray)

    # Contrast
    contrast = np.std(gray)

    # Edges
    edges = cv2.Canny(
        gray,
        100,
        200
    )

    edge_density = np.mean(
        edges > 0
    )

    # Texture
    texture = cv2.Laplacian(
        gray,
        cv2.CV_64F
    ).var()

    # Shape
    height, width = gray.shape

    aspect_ratio = width / height

    return {
        "mean_r": mean_r,
        "mean_g": mean_g,
        "mean_b": mean_b,

        "std_r": std_r,
        "std_g": std_g,
        "std_b": std_b,

        "brightness": brightness,
        "contrast": contrast,

        "edge_density": edge_density,

        "texture": texture,

        "aspect_ratio": aspect_ratio
    }


# ============================================================
# SCAN ONE DATASET SPLIT
# ============================================================

def scan_dataset(folder, split):

    rows = []

    print()
    print("=" * 60)
    print(split.upper(), "DATASET")
    print("=" * 60)

    if not folder.exists():

        print("ERROR: Folder not found:")
        print(folder)

        return rows

    class_folders = [
        x for x in folder.iterdir()
        if x.is_dir()
    ]

    print(
        "Classes found:",
        len(class_folders)
    )

    for class_folder in sorted(class_folders):

        species = class_folder.name

        print(
            "\nProcessing:",
            species
        )

        image_files = []

        for file in class_folder.rglob("*"):

            if file.suffix.lower() in [
                ".jpg",
                ".jpeg",
                ".png",
                ".bmp",
                ".webp"
            ]:

                image_files.append(file)

        print(
            "Images:",
            len(image_files)
        )

        for image_path in image_files:

            features = get_image_features(
                image_path
            )

            if features is None:

                print(
                    "Could not read:",
                    image_path
                )

                continue

            relative_path = image_path.relative_to(
                PROJECT_ROOT
            )

            row = {

                "image_path":
                    str(relative_path).replace(
                        "\\",
                        "/"
                    ),

                "species":
                    species,

                "split":
                    split
            }

            row.update(features)

            rows.append(row)

    return rows


# ============================================================
# MAIN
# ============================================================

def main():

    print()
    print("=" * 60)
    print("FISH FUSION METADATA GENERATOR")
    print("=" * 60)

    print()
    print("Project folder:")
    print(PROJECT_ROOT)

    print()
    print("Train folder:")
    print(TRAIN_DIR)

    print()
    print("Test folder:")
    print(TEST_DIR)

    # Train
    train_rows = scan_dataset(
        TRAIN_DIR,
        "train"
    )

    # Test
    test_rows = scan_dataset(
        TEST_DIR,
        "test"
    )

    # Combine
    rows = train_rows + test_rows

    if len(rows) == 0:

        print()
        print("ERROR: No images were found.")

        return

    # Create dataframe
    df = pd.DataFrame(rows)

    # Save
    df.to_csv(
        OUTPUT_FILE,
        index=False
    )

    # Summary
    print()
    print("=" * 60)
    print("SUCCESS!")
    print("=" * 60)

    print()
    print("CSV created at:")

    print(OUTPUT_FILE)

    print()
    print("Total images:", len(df))

    print()
    print("Train images:")

    print(
        len(
            df[df["split"] == "train"]
        )
    )

    print()
    print("Test images:")

    print(
        len(
            df[df["split"] == "test"]
        )
    )

    print()
    print("Classes:")

    print(
        df["species"].unique()
    )

    print()
    print("CSV columns:")

    print(
        list(df.columns)
    )

    print()
    print("First 5 rows:")

    print(
        df.head()
    )

    print()
    print("DONE!")


# ============================================================
# START PROGRAM
# ============================================================

if __name__ == "__main__":
    main()