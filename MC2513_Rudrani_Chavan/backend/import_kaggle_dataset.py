"""
backend/import_kaggle_dataset.py
---------------------------------
One-shot importer: reads data/datasets/Indian_Food_Nutrition_Processed.csv
and inserts each row into the SQLite `meals` table as source_type="kaggle".

Rules
-----
* Only maps columns that genuinely exist in the CSV.
* Does NOT invent ingredients, diet types, meal types, goals, or health benefits.
  Those fields are left NULL / empty for kaggle rows.
* Skips rows that:
    - have a blank Dish Name
    - have an unparseable / negative calorie value
    - already exist in the database (same name, any source_type)
* Preserves all existing curated/api_analysis records.
* Never modifies RAG pipeline, ChromaDB, existing APIs, or Streamlit UI.

CSV columns mapped
------------------
  Dish Name          -> name
  Calories (kcal)    -> calories
  Carbohydrates (g)  -> carbohydrates
  Protein (g)        -> protein
  Fats (g)           -> fat
  Fibre (g)          -> fiber
  Free Sugar (g)     -> stored in minerals JSON as {"Free Sugar (g)": <val>}
  Sodium (mg)        -> stored in minerals JSON as {"Sodium (mg)": <val>}
  Calcium (mg)       -> stored in minerals JSON as {"Calcium (mg)": <val>}
  Iron (mg)          -> stored in minerals JSON as {"Iron (mg)": <val>}
  Vitamin C (mg)     -> stored in vitamins JSON as {"Vitamin C (mg)": <val>}
  Folate (ug)        -> stored in vitamins JSON as {"Folate (ug)": <val>}
"""

import csv
import json
import os
import sys

# ── Allow running from project root: python -m backend.import_kaggle_dataset ──
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from backend.database import engine, SessionLocal, Base
from backend.models import Meal

CSV_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data", "datasets", "Indian_Food_Nutrition_Processed.csv"
)

# ── helper ──────────────────────────────────────────────────────────────────
def _safe_float(val: str, field: str) -> float | None:
    """Parse a float; return None on blank, raise ValueError on bad value."""
    val = val.strip()
    if val == "" or val.lower() in ("nan", "null", "none", "-"):
        return None
    return float(val)


def import_kaggle_dataset() -> None:
    # Ensure tables exist (idempotent)
    Base.metadata.create_all(bind=engine)

    if not os.path.isfile(CSV_PATH):
        print(f"[ERROR] CSV not found: {CSV_PATH}")
        sys.exit(1)

    print("=" * 60)
    print("KAGGLE DATASET IMPORTER")
    print("=" * 60)
    print(f"CSV : {CSV_PATH}")

    # Read CSV
    with open(CSV_PATH, encoding="utf-8", errors="replace") as fh:
        reader = csv.DictReader(fh)
        rows = list(reader)

    total_csv_rows = len(rows)
    print(f"CSV rows read  : {total_csv_rows}")

    db: Session = SessionLocal()
    try:
        inserted = 0
        skipped_dup = 0
        skipped_inv = 0

        for row in rows:
            dish_name = row.get("Dish Name", "").strip()

            # ── Validation ──────────────────────────────────────────────
            if not dish_name:
                skipped_inv += 1
                continue

            # Parse required numeric fields
            try:
                cal = _safe_float(row.get("Calories (kcal)", ""), "Calories (kcal)")
                if cal is not None and cal < 0:
                    raise ValueError("negative calories")
            except ValueError as exc:
                print(f"  [SKIP-INVALID] '{dish_name}': {exc}")
                skipped_inv += 1
                continue

            # ── Duplicate check ─────────────────────────────────────────
            existing = db.query(Meal).filter(Meal.name == dish_name).first()
            if existing:
                skipped_dup += 1
                continue

            # ── Parse remaining numeric fields (non-fatal if blank) ──────
            def sf(key):
                try:
                    return _safe_float(row.get(key, ""), key)
                except ValueError:
                    return None

            carbs  = sf("Carbohydrates (g)")
            protein = sf("Protein (g)")
            fat    = sf("Fats (g)")
            fiber  = sf("Fibre (g)")

            # Micro-nutrients stored as JSON dicts
            minerals_dict = {}
            vitamins_dict = {}

            for col, store in [
                ("Free Sugar (g)",  minerals_dict),
                ("Sodium (mg)",     minerals_dict),
                ("Calcium (mg)",    minerals_dict),
                ("Iron (mg)",       minerals_dict),
            ]:
                v = sf(col)
                if v is not None:
                    store[col] = v

            for col, store in [
                ("Vitamin C (mg)",  vitamins_dict),
                ("Folate (\ufffdg)", vitamins_dict),   # BOM-mangled variant
                ("Folate (µg)",     vitamins_dict),    # proper mu
                ("Folate (ug)",     vitamins_dict),    # plain ascii
            ]:
                raw = row.get(col, "").strip()
                if raw:
                    v = sf(col)
                    if v is not None:
                        vitamins_dict["Folate (ug)"] = v
                        break  # only store once regardless of column name variant

            # Vitamin C separately
            vc = sf("Vitamin C (mg)")
            if vc is not None:
                vitamins_dict["Vitamin C (mg)"] = vc

            # ── Insert ───────────────────────────────────────────────────
            meal = Meal(
                name=dish_name,
                source_type="kaggle",
                # diet flags — unknown, leave False
                diet_veg=False,
                diet_egg=False,
                diet_nv=False,
                # goal flags — unknown, leave False
                goal_wl=False,
                goal_wg=False,
                goal_mg=False,
                goal_m=False,
                goal_db=False,
                # meal classification — unknown
                meal_type=None,
                # macros
                calories=cal,
                protein=protein,
                carbohydrates=carbs,
                fat=fat,
                fiber=fiber,
                # micronutrients as JSON
                vitamins=json.dumps(vitamins_dict) if vitamins_dict else json.dumps([]),
                minerals=json.dumps(minerals_dict) if minerals_dict else json.dumps([]),
                # no ingredients / health benefits available in CSV
                ingredients=json.dumps([]),
                health_benefits=None,
            )
            db.add(meal)
            inserted += 1

        db.commit()

    except Exception as exc:
        db.rollback()
        print(f"[ERROR] Import failed: {exc}")
        raise
    finally:
        db.close()

    # ── Final counts ─────────────────────────────────────────────────────────
    count_db: Session = SessionLocal()
    try:
        total_meals = count_db.query(Meal).count()
        kaggle_count = count_db.query(Meal).filter(Meal.source_type == "kaggle").count()
        curated_count = count_db.query(Meal).filter(Meal.source_type == "curated").count()
    finally:
        count_db.close()

    print()
    print("-" * 60)
    print(f"CSV rows             : {total_csv_rows}")
    print(f"Imported (kaggle)    : {inserted}")
    print(f"Duplicate rows skipped: {skipped_dup}")
    print(f"Invalid rows skipped  : {skipped_inv}")
    print("-" * 60)
    print(f"Final meals table    : {total_meals} total")
    print(f"  curated            : {curated_count}")
    print(f"  kaggle             : {kaggle_count}")
    print("-" * 60)
    print("Import complete. Run GET /api/foods to verify.")
    print("=" * 60)


if __name__ == "__main__":
    import_kaggle_dataset()
