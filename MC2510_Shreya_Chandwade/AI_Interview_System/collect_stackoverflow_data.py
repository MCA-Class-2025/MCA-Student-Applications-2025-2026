import pandas as pd
import requests
import time
import re
from datetime import datetime

INPUT_FILE = "stackoverflow_api_strong_candidates.csv"
OUTPUT_FILE = "stackoverflow_api_results.csv"

API_URL = "https://api.stackexchange.com/2.3/search/advanced"

df = pd.read_csv(INPUT_FILE)

results = []

def clean_query(question):
    """
    Clean the interview question before sending it
    to Stack Overflow.
    """
    question = str(question)

    # Remove excessive whitespace
    question = re.sub(r"\s+", " ", question).strip()

    # Limit query length
    return question[:180]


for index, row in df.iterrows():

    question = clean_query(row["question"])

    print(f"[{index + 1}/{len(df)}] Searching: {question}")

    params = {
        "site": "stackoverflow",
        "q": question,
        "sort": "relevance",
        "order": "desc",
        "pagesize": 5
    }

    try:

        response = requests.get(
            API_URL,
            params=params,
            timeout=20
        )

        response.raise_for_status()

        data = response.json()

        items = data.get("items", [])

        if len(items) == 0:

            results.append({
                "master_row_id": row["master_row_id"],
                "question": row["question"],
                "stackoverflow_question_id": None,
                "stackoverflow_title": None,
                "stackoverflow_tags": None,
                "stackoverflow_score": None,
                "stackoverflow_answer_count": None,
                "stackoverflow_is_answered": None,
                "stackoverflow_view_count": None,
                "stackoverflow_accepted_answer": None,
                "stackoverflow_link": None,
                "api_match_status": "NO_MATCH",
                "api_match_score": 0,
                "api_retrieved_date": datetime.now().date()
            })

        else:

            # Take the most relevant result
            best = items[0]

            results.append({
                "master_row_id": row["master_row_id"],
                "question": row["question"],

                "stackoverflow_question_id":
                    best.get("question_id"),

                "stackoverflow_title":
                    best.get("title"),

                "stackoverflow_tags":
                    ", ".join(best.get("tags", [])),

                "stackoverflow_score":
                    best.get("score", 0),

                "stackoverflow_answer_count":
                    best.get("answer_count", 0),

                "stackoverflow_is_answered":
                    best.get("is_answered", False),

                "stackoverflow_view_count":
                    best.get("view_count", 0),

                "stackoverflow_accepted_answer":
                    best.get("accepted_answer_id"),

                "stackoverflow_link":
                    best.get("link"),

                "api_match_status":
                    "MATCHED",

                "api_match_score":
                    best.get("score", 0),

                "api_retrieved_date":
                    datetime.now().date()
            })

        # Small delay to respect API limits
        time.sleep(0.3)

    except Exception as e:

        print("API ERROR:", e)

        results.append({
            "master_row_id": row["master_row_id"],
            "question": row["question"],
            "stackoverflow_question_id": None,
            "stackoverflow_title": None,
            "stackoverflow_tags": None,
            "stackoverflow_score": None,
            "stackoverflow_answer_count": None,
            "stackoverflow_is_answered": None,
            "stackoverflow_view_count": None,
            "stackoverflow_accepted_answer": None,
            "stackoverflow_link": None,
            "api_match_status": "ERROR",
            "api_match_score": 0,
            "api_retrieved_date": datetime.now().date()
        })


# Convert results to DataFrame
result_df = pd.DataFrame(results)

# Save
result_df.to_csv(
    OUTPUT_FILE,
    index=False
)

print("\n===================================")
print("API COLLECTION COMPLETED")
print("===================================")

print("Total records:", len(result_df))

print("\nMatch status:")
print(
    result_df["api_match_status"]
    .value_counts()
)

print("\nSaved file:")
print(OUTPUT_FILE)