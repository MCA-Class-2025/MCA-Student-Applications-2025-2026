
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

# Load Excel dataset
file_path = r"data/original/Food_Dataset.xlsx"
df = pd.read_excel(file_path, engine="openpyxl")

# Create output folder
output_dir = "analysis/eda_charts"
os.makedirs(output_dir, exist_ok=True)

# Visualization style
sns.set_theme(style="whitegrid")

print("Dataset loaded successfully!")
print("Shape:", df.shape)

# ------------------------------------------------
# 1. Cuisine Distribution
# ------------------------------------------------
plt.figure(figsize=(8, 5))
sns.countplot(data=df, x="cuisine", order=df["cuisine"].value_counts().index)
plt.title("Food Distribution by Cuisine")
plt.xlabel("Cuisine")
plt.ylabel("Number of Food Records")
plt.tight_layout()
plt.savefig(f"{output_dir}/cuisine_distribution.png")
plt.show()

# ------------------------------------------------
# 2. Meal Type Distribution
# ------------------------------------------------
plt.figure(figsize=(8, 5))
sns.countplot(data=df, x="meal_type",
              order=df["meal_type"].value_counts().index)
plt.title("Distribution of Meal Types")
plt.xlabel("Meal Type")
plt.ylabel("Number of Records")
plt.xticks(rotation=20)
plt.tight_layout()
plt.savefig(f"{output_dir}/meal_type_distribution.png")
plt.show()

# ------------------------------------------------
# 3. Calorie Distribution
# ------------------------------------------------
plt.figure(figsize=(8, 5))
sns.histplot(df["calories"], bins=15, kde=True)
plt.title("Calorie Distribution of Food Items")
plt.xlabel("Calories")
plt.ylabel("Frequency")
plt.tight_layout()
plt.savefig(f"{output_dir}/calorie_distribution.png")
plt.show()

# ------------------------------------------------
# 4. Nutritional Comparison
# ------------------------------------------------
nutrition = ["protein_g", "carbs_g", "fat_g", "fiber_g"]

plt.figure(figsize=(9, 5))
df[nutrition].mean().plot(kind="bar")
plt.title("Average Nutritional Values")
plt.xlabel("Nutritional Components")
plt.ylabel("Average Quantity (g)")
plt.xticks(rotation=0)
plt.tight_layout()
plt.savefig(f"{output_dir}/average_nutrition.png")
plt.show()

# ------------------------------------------------
# 5. Cooking Time Distribution
# ------------------------------------------------
plt.figure(figsize=(8, 5))
sns.histplot(df["cooking_time_min"], bins=15, kde=True)
plt.title("Distribution of Cooking Time")
plt.xlabel("Cooking Time (Minutes)")
plt.ylabel("Frequency")
plt.tight_layout()
plt.savefig(f"{output_dir}/cooking_time_distribution.png")
plt.show()

# ------------------------------------------------
# 6. Correlation Heatmap
# ------------------------------------------------
plt.figure(figsize=(9, 6))
correlation = df[nutrition + ["calories", "cooking_time_min"]].corr()

sns.heatmap(correlation, annot=True, cmap="coolwarm",
            fmt=".2f", linewidths=0.5)

plt.title("Food Nutrition Correlation Heatmap")
plt.tight_layout()
plt.savefig(f"{output_dir}/correlation_heatmap.png")
plt.show()

# ------------------------------------------------
# 7. Health Category Distribution
# ------------------------------------------------
plt.figure(figsize=(9, 5))
sns.countplot(data=df, x="health_category",
              order=df["health_category"].value_counts().index)

plt.title("Food Distribution by Health Category")
plt.xlabel("Health Category")
plt.ylabel("Number of Records")
plt.xticks(rotation=25)
plt.tight_layout()
plt.savefig(f"{output_dir}/health_category_distribution.png")
plt.show()

print("\nAll EDA visualizations generated successfully!")
print("Charts saved inside:", output_dir)
