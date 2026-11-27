import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

BASE = Path(__file__).resolve().parent

INPUT_FILE = BASE / "part_j_before_after_summary.csv"
OUTPUT_FILE = BASE / "part_j_before_after_comparison.png"

df = pd.read_csv(INPUT_FILE)

# Use the actual measured percentages
plot_df = df[
    ["condition", "relevant_information_percent",
     "complete_information_percent"]
].copy()

plot_df = plot_df.set_index("condition")

ax = plot_df.plot(
    kind="bar",
    figsize=(10, 6)
)

ax.set_title("Before vs After API/Fusion")
ax.set_xlabel("System condition")
ax.set_ylabel("Percentage (%)")
ax.set_ylim(0, 100)

plt.xticks(rotation=0)
plt.legend(
    ["Relevant information", "Complete information"],
    title="Evaluation"
)

plt.tight_layout()
plt.savefig(OUTPUT_FILE, dpi=300)
plt.show()

print("=" * 60)
print("PART J VISUALIZATION CREATED")
print("=" * 60)
print("Output:")
print(OUTPUT_FILE)