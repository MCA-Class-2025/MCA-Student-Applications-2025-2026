"""
split_dataset.py
-----------------
The Mendeley "Indian Seafood Fish Dataset" download gives you ONE folder per
fish class, e.g.:

    raw_data/
        Pomfret/
        Black_Pomfret/
        Rohu/
        Mackerel/
        Tilapia/
        Prawn/
        Rani_Fish/
        Bhetki/

Keras' ImageDataGenerator (used in train_cnn.py) expects a train/ and test/
split, each containing the same class subfolders. This script does that
split for you (80% train / 20% test by default) by COPYING files, so your
original raw_data/ folder is left untouched.

Usage:
    python split_dataset.py --raw_dir ../raw_data --out_dir ../data --split 0.2
"""

import argparse
import shutil
import random
from pathlib import Path


def split_dataset(raw_dir: str, out_dir: str, split: float = 0.2, seed: int = 42):
    raw_path = Path(raw_dir)
    out_path = Path(out_dir)
    train_path = out_path / "train"
    test_path = out_path / "test"

    if not raw_path.exists():
        raise FileNotFoundError(f"Raw data folder not found: {raw_path}")

    class_dirs = [d for d in raw_path.iterdir() if d.is_dir()]
    if not class_dirs:
        raise ValueError(f"No class subfolders found inside {raw_path}")

    random.seed(seed)
    summary = {}

    for class_dir in class_dirs:
        images = [
            f for f in class_dir.iterdir()
            if f.suffix.lower() in (".jpg", ".jpeg", ".png")
        ]
        random.shuffle(images)

        n_test = max(1, int(len(images) * split))
        test_images = images[:n_test]
        train_images = images[n_test:]

        train_class_dir = train_path / class_dir.name
        test_class_dir = test_path / class_dir.name
        train_class_dir.mkdir(parents=True, exist_ok=True)
        test_class_dir.mkdir(parents=True, exist_ok=True)

        for f in train_images:
            shutil.copy2(f, train_class_dir / f.name)
        for f in test_images:
            shutil.copy2(f, test_class_dir / f.name)

        summary[class_dir.name] = (len(train_images), len(test_images))

    print("\nSplit complete:")
    print(f"{'Class':<20}{'Train':<10}{'Test':<10}")
    for cls, (n_train, n_test) in summary.items():
        print(f"{cls:<20}{n_train:<10}{n_test:<10}")
    print(f"\nSaved to: {out_path.resolve()}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw_dir", type=str, required=True,
                         help="Path to folder containing one subfolder per fish class")
    parser.add_argument("--out_dir", type=str, default="../data",
                         help="Where to write train/ and test/ folders")
    parser.add_argument("--split", type=float, default=0.2,
                         help="Fraction of images per class to use for testing")
    args = parser.parse_args()

    split_dataset(args.raw_dir, args.out_dir, args.split)
