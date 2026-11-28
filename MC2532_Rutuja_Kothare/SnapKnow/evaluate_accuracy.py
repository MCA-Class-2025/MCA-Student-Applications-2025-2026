"""
evaluate_accuracy.py: how often is the vision model right?

Reads snapknow_ml_dataset.csv (made by build_ml_dataset.py with --folder) and prints:
  - overall accuracy
  - accuracy per class
  - every mistake
  - average confidence when the AI was right vs. wrong

Run:  python evaluate_accuracy.py
"""

import os
import sys

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
CSV = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "snapknow_ml_dataset.csv")


def main():
    df = pd.read_csv(CSV)
    if "ai_correct" not in df.columns:
        sys.exit(
            "No 'ai_correct' column. Run first:\n"
            "  python build_ml_dataset.py --folder sample_images --provider gemini --no-history"
        )
    df = df[df["true_label"].notna() & (df["true_label"] != "")]
    n, right = len(df), int(df["ai_correct"].sum())
    print(f"Photos with a known true label: {n}")
    print(f"Overall accuracy: {right}/{n} = {right / n:.1%}\n")

    print("Accuracy per class:")
    per = df.groupby("true_label")["ai_correct"].agg(["sum", "count"])
    for label, row in per.iterrows():
        print(f"  {label:<10} {int(row['sum'])}/{int(row['count'])} = {row['sum'] / row['count']:.0%}")

    wrong = df[df["ai_correct"] == 0]
    print(f"\nMistakes ({len(wrong)}):")
    if wrong.empty:
        print("  none")
    for _, r in wrong.iterrows():
        print(f"  {r['image_filename']}: real = {r['true_label']}, AI said = {r['category']} ({r['name']})")

    print("\nAverage confidence:")
    for flag, text in [(1, "when AI was right"), (0, "when AI was wrong")]:
        sub = df[df["ai_correct"] == flag]["confidence"]
        print(f"  {text}: {sub.mean():.1f}" if len(sub) else f"  {text}: (no cases)")


if __name__ == "__main__":
    main()