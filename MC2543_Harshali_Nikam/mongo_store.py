import os
from pathlib import Path
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

def store_in_mongodb():
    from pymongo import MongoClient

    uri = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
    db_name = os.getenv("MONGO_DB", "cityfusion")

    path = Path("data/processed/fused_dataset.csv")
    if not path.exists():
        raise FileNotFoundError("Run python collect_data.py first.")

    df = pd.read_csv(path)
    records = df.where(pd.notnull(df), None).to_dict("records")

    client = MongoClient(uri, serverSelectionTimeoutMS=5000)
    client.admin.command("ping")

    db = client[db_name]
    collection = db["raw_fused_data"]

    collection.delete_many({})
    if records:
        collection.insert_many(records)

    print(f"Inserted {len(records):,} records into MongoDB: {db_name}.raw_fused_data")

if __name__ == "__main__":
    store_in_mongodb()
