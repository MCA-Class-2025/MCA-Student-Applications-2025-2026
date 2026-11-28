import pandas as pd
import os

# ==========================================================
# PATHS
# ==========================================================

INTERIOR_FILE = "dataset/interior_design_dataset.csv"
DECOR_FILE = "dataset/cleaned_decor.csv"

OUTPUT_DIR = "processed_dataset"

os.makedirs(OUTPUT_DIR, exist_ok=True)


# ==========================================================
# LOAD INTERIOR DESIGN DATASET
# ==========================================================

print("Loading interior design dataset...")

interior_df = pd.read_csv(INTERIOR_FILE)

print("Interior records:", len(interior_df))


# Remove completely empty rows
interior_df = interior_df.dropna(how="all")


# Fill missing text values
text_columns = [
    "style_tags",
    "design_description",
    "user_preference",
    "material_type",
    "color_palette"
]

for column in text_columns:
    if column in interior_df.columns:
        interior_df[column] = (
            interior_df[column]
            .fillna("")
            .astype(str)
        )


# ==========================================================
# CREATE RAG TEXT FOR INTERIOR DATA
# ==========================================================

interior_documents = []

for _, row in interior_df.iterrows():

    text = f"""
Interior Design Information

Style:
{row.get('style_tags', '')}

Design Description:
{row.get('design_description', '')}

User Preference:
{row.get('user_preference', '')}

Material:
{row.get('material_type', '')}

Colour Palette:
{row.get('color_palette', '')}
""".strip()

    interior_documents.append(text)


interior_output = pd.DataFrame({
    "document_id": range(1, len(interior_documents) + 1),
    "text": interior_documents
})


interior_output.to_csv(
    f"{OUTPUT_DIR}/interior_rag_documents.csv",
    index=False
)


# ==========================================================
# LOAD DECOR DATASET
# ==========================================================

print("Loading decor dataset...")

decor_df = pd.read_csv(DECOR_FILE)

print("Decor records:", len(decor_df))


# Remove completely empty rows
decor_df = decor_df.dropna(how="all")


# Fill missing values
for column in decor_df.columns:
    decor_df[column] = (
        decor_df[column]
        .fillna("")
        .astype(str)
    )


# ==========================================================
# CREATE RAG TEXT FOR DECOR DATA
# ==========================================================

decor_documents = []

for _, row in decor_df.iterrows():

    text = f"""
Furniture / Home Decor Product

Product:
{row.get('name', '')}

Brand:
{row.get('brand', '')}

Rating:
{row.get('rating', '')}

Price:
₹{row.get('price', '')}

Actual Price:
₹{row.get('actual price', '')}

Discount:
{row.get('discount', '')}%

Shipping:
{row.get('shipping', '')}

Category:
{row.get('category', '')}

Deal:
{row.get('deals', '')}

EMI:
{row.get('emi', '')}
""".strip()

    decor_documents.append(text)


decor_output = pd.DataFrame({
    "document_id": range(1, len(decor_documents) + 1),
    "text": decor_documents
})


decor_output.to_csv(
    f"{OUTPUT_DIR}/decor_rag_documents.csv",
    index=False
)


# ==========================================================
# FINISHED
# ==========================================================

print("\n======================================")
print("DATASET PREPARATION COMPLETED")
print("======================================")

print(
    f"Interior RAG documents: {len(interior_output)}"
)

print(
    f"Decor RAG documents: {len(decor_output)}"
)

print("\nCreated files:")

print(
    "processed_dataset/interior_rag_documents.csv"
)

print(
    "processed_dataset/decor_rag_documents.csv"
)