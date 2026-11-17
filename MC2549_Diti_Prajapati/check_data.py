import pandas as pd

# Load dataset
df = pd.read_csv("data/amazon_products.csv")

print("Columns in dataset:")
print(df.columns.tolist())

print("\nFirst row sample:")
print(df.head(1))