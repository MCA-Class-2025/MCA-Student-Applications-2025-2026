
import os
import pandas as pd
from dotenv import load_dotenv
from groq import Groq

# ==========================================================
# LOAD ENVIRONMENT VARIABLES
# ==========================================================

load_dotenv()

api_key = os.getenv("GROQ_API_KEY")

print("API key found:", bool(api_key))

if not api_key:
    print("ERROR: GROQ_API_KEY is not set.")
    exit()


# ==========================================================
# CREATE GROQ CLIENT
# ==========================================================

client = Groq(api_key=api_key)


# ==========================================================
# LOAD DATASET
# ==========================================================

df = pd.read_csv(
    "fused_dataset/fused_interior_decor.csv"
)

# Take first record
row = df.iloc[0]


# ==========================================================
# CREATE API QUERY
# ==========================================================

style = str(row.get("style_tags", ""))
material = str(row.get("material_type", ""))
color = str(row.get("color_palette", ""))
category = str(row.get("category", ""))
description = str(row.get("design_description", ""))

query = f"""
You are an expert interior designer.

Interior design style:
{style}

Material:
{material}

Colour palette:
{color}

Category:
{category}

Design description:
{description}

Give a short practical interior design recommendation.
"""


# ==========================================================
# DISPLAY API REQUEST
# ==========================================================

print("\n" + "=" * 60)
print("API REQUEST")
print("=" * 60)

print(query)

print("\nSending request to Groq...")


# ==========================================================
# SEND REQUEST TO GROQ
# ==========================================================

try:

    response = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[
            {
                "role": "user",
                "content": query
            }
        ]
    )


    # ======================================================
    # EXTRACT API RESPONSE
    # ======================================================

    groq_answer = response.choices[0].message.content


    # ======================================================
    # DISPLAY API RESPONSE
    # ======================================================

    print("\n" + "=" * 60)
    print("API RESPONSE")
    print("=" * 60)

    print(groq_answer)


    print("\n" + "=" * 60)
    print("GROQ API TEST SUCCESSFUL")
    print("=" * 60)


except Exception as e:

    print("\n" + "=" * 60)
    print("GROQ API ERROR")
    print("=" * 60)

    print(e)
