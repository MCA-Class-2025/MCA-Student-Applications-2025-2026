# -*- coding: utf-8 -*-
"""
Inspect all datasets, databases, configuration files, RAG pipeline, FastAPI backend, Streamlit frontend,
and calculate exact statistical properties for NutriMate complete EDA and Technical Analysis.
"""

import csv
import sqlite3
import os
import glob
import json
import re
from pathlib import Path

BASE_DIR = Path(r"C:\nutrimate")

def inspect_all():
    print("=========================================================")
    print("NUTRIMATE PROJECT COMPLETE INSPECTION")
    print("=========================================================")

    # 1. Dataset 1: Kaggle dataset
    ds1_path = BASE_DIR / "data/datasets/Indian_Food_Nutrition_Processed.csv"
    if ds1_path.exists():
        ds1 = list(csv.DictReader(open(ds1_path, encoding="utf-8")))
        print(f"\n[1] DATASET 1: Indian_Food_Nutrition_Processed.csv")
        print(f"    Path: {ds1_path}")
        print(f"    Size: {os.path.getsize(ds1_path)} bytes")
        print(f"    Rows: {len(ds1)}")
        print(f"    Cols: {len(ds1[0].keys())}")
        print(f"    Columns: {list(ds1[0].keys())}")

    # 2. Dataset 2: API records
    ds2_path = BASE_DIR / "data/datasets/nutrimate_api_records.csv"
    if ds2_path.exists():
        ds2 = list(csv.DictReader(open(ds2_path, encoding="utf-8")))
        print(f"\n[2] DATASET 2: nutrimate_api_records.csv")
        print(f"    Path: {ds2_path}")
        print(f"    Size: {os.path.getsize(ds2_path)} bytes")
        print(f"    Rows: {len(ds2)}")
        print(f"    Cols: {len(ds2[0].keys())}")
        print(f"    Columns: {list(ds2[0].keys())}")

    # 3. Dataset 3: Fused dataset
    ds3_path = BASE_DIR / "data/datasets/nutrimate_fused_dataset.csv"
    if ds3_path.exists():
        ds3 = list(csv.DictReader(open(ds3_path, encoding="utf-8")))
        print(f"\n[3] DATASET 3: nutrimate_fused_dataset.csv")
        print(f"    Path: {ds3_path}")
        print(f"    Size: {os.path.getsize(ds3_path)} bytes")
        print(f"    Rows: {len(ds3)}")
        print(f"    Cols: {len(ds3[0].keys())}")
        print(f"    Columns: {list(ds3[0].keys())}")

    # 4. SQLite DB: nutrimate.db
    db_path = BASE_DIR / "data/nutrimate.db"
    if db_path.exists():
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        c.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [t[0] for t in c.fetchall()]
        print(f"\n[4] SQLITE DATABASE: data/nutrimate.db")
        print(f"    Path: {db_path}")
        print(f"    Size: {os.path.getsize(db_path)} bytes")
        print(f"    Tables: {tables}")
        for t in tables:
            c.execute(f"SELECT count(*) FROM {t}")
            cnt = c.fetchone()[0]
            c.execute(f"PRAGMA table_info({t})")
            cols = [col[1] for col in c.fetchall()]
            print(f"      Table '{t}': {cnt} rows | Columns: {cols}")
        conn.close()

    # 5. Vector DB: ChromaDB
    chroma_path = BASE_DIR / "data/db/chroma.sqlite3"
    if chroma_path.exists():
        conn = sqlite3.connect(chroma_path)
        c = conn.cursor()
        c.execute("SELECT name FROM sqlite_master WHERE type='table'")
        ctables = [t[0] for t in c.fetchall()]
        print(f"\n[5] CHROMADB VECTOR STORE: data/db/chroma.sqlite3")
        print(f"    Path: {chroma_path}")
        print(f"    Size: {os.path.getsize(chroma_path)} bytes")
        if "collections" in ctables:
            c.execute("SELECT id, name FROM collections")
            colls = c.fetchall()
            print(f"    Collections: {colls}")
        if "embeddings" in ctables:
            c.execute("SELECT count(*) FROM embeddings")
            emb_cnt = c.fetchone()[0]
            print(f"    Embeddings Count: {emb_cnt}")
        conn.close()

    # 6. Document files
    doc_dir = BASE_DIR / "data/documents"
    if doc_dir.exists():
        docs = list(doc_dir.glob("*"))
        print(f"\n[6] DOCUMENTS DIRECTORY: data/documents")
        print(f"    Total Documents: {len(docs)}")
        for d in docs:
            print(f"      - {d.name} ({os.path.getsize(d)} bytes)")

    # 7. Config & LLM / Ollama settings
    config_path = BASE_DIR / "config.py"
    if config_path.exists():
        print(f"\n[7] CONFIGURATION FILE: config.py")
        print(open(config_path, encoding="utf-8").read())

    # 8. RAG Pipeline inspect
    rag_path = BASE_DIR / "rag_pipeline.py"
    if rag_path.exists():
        print(f"\n[8] RAG PIPELINE FILE: rag_pipeline.py")
        code = open(rag_path, encoding="utf-8").read()
        print(f"    File Size: {os.path.getsize(rag_path)} bytes")
        # Extract key imports and model definitions
        for line in code.split("\n"):
            if "Ollama" in line or "Embeddings" in line or "Chroma" in line or "MODEL" in line or "model" in line.lower() or "base_url" in line.lower():
                if len(line.strip()) < 120 and not line.strip().startswith("#"):
                    print(f"    > {line.strip()}")

    # 9. FastAPI Backend inspect
    main_path = BASE_DIR / "backend/main.py"
    if main_path.exists():
        print(f"\n[9] FASTAPI BACKEND: backend/main.py")
        code = open(main_path, encoding="utf-8").read()
        print(f"    File Size: {os.path.getsize(main_path)} bytes")
        endpoints = [line.strip() for line in code.split("\n") if line.strip().startswith("@app.")]
        print(f"    Total Endpoints: {len(endpoints)}")
        for ep in endpoints:
            print(f"      {ep}")

    # 10. Streamlit App inspect
    app_path = BASE_DIR / "app.py"
    if app_path.exists():
        print(f"\n[10] STREAMLIT FRONTEND: app.py")
        code = open(app_path, encoding="utf-8").read()
        print(f"    File Size: {os.path.getsize(app_path)} bytes")
        tabs = [line.strip() for line in code.split("\n") if "st.tabs" in line or "st.sidebar" in line or "st.navigation" in line]
        print(f"    Navigation / UI references:")
        for t in tabs[:15]:
            print(f"      {t}")

if __name__ == "__main__":
    inspect_all()
