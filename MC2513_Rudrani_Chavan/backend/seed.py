import os
import json
from sqlalchemy.orm import Session
from backend.database import engine, SessionLocal, Base, DATABASE_URL
from backend.models import Meal
from backend.seed_data import MEAL_DB

def seed_database():
    # Initialize / Create tables if they do not exist
    print("Initializing SQLite database tables...")
    Base.metadata.create_all(bind=engine)

    db: Session = SessionLocal()
    
    total_records = len(MEAL_DB)
    inserted_count = 0
    skipped_count = 0
    
    print(f"Beginning seeding process for {total_records} meals...")
    
    try:
        for item in MEAL_DB:
            # Check if meal already exists to enforce idempotency
            existing_meal = db.query(Meal).filter(Meal.name == item["name"]).first()
            if existing_meal:
                skipped_count += 1
                continue
            
            # Map diets list to distinct flags
            diet_list = item.get("diet", [])
            diet_veg = "veg" in diet_list
            diet_egg = "egg" in diet_list
            diet_nv = "nv" in diet_list
            
            # Map goals list to distinct flags
            goals_list = item.get("goals", [])
            goal_wl = "wl" in goals_list
            goal_wg = "wg" in goals_list
            goal_mg = "mg" in goals_list
            goal_m = "m" in goals_list
            goal_db = "db" in goals_list
            
            # Serialize list fields to JSON
            ingredients_json = json.dumps(item.get("ingredients", []))
            vitamins_json = json.dumps([])  # Curated database defaults
            minerals_json = json.dumps([])
            
            # Construct model instance
            meal = Meal(
                name=item["name"],
                source_type="curated",
                diet_veg=diet_veg,
                diet_egg=diet_egg,
                diet_nv=diet_nv,
                goal_wl=goal_wl,
                goal_wg=goal_wg,
                goal_mg=goal_mg,
                goal_m=goal_m,
                goal_db=goal_db,
                meal_type=item.get("type"),
                calories=float(item.get("cal", 0)),
                protein=float(item.get("pro", 0)),
                carbohydrates=float(item.get("carbs", 0)),
                fat=float(item.get("fat", 0)),
                fiber=float(item.get("fiber", 0)),
                vitamins=vitamins_json,
                minerals=minerals_json,
                ingredients=ingredients_json,
                health_benefits=item.get("why", ""),
            )
            
            db.add(meal)
            inserted_count += 1
            
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"Error during seeding: {e}")
        raise e
    finally:
        db.close()
        
    print("\n--- Seeding Verification Summary ---")
    print(f"Database Path:      {DATABASE_URL}")
    print(f"Total Seed Records: {total_records}")
    print(f"Inserted Records:   {inserted_count}")
    print(f"Skipped Duplicates: {skipped_count}")

if __name__ == "__main__":
    seed_database()
