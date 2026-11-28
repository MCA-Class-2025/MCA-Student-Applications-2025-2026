from sqlalchemy import Column, Integer, String, Boolean, Float, Text, DateTime, func
from backend.database import Base

class Meal(Base):
    __tablename__ = "meals"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(255), unique=True, index=True, nullable=False)
    source_type = Column(String(50), nullable=False, default="curated")
    
    # Diet Compliances
    diet_veg = Column(Boolean, default=False, nullable=False)
    diet_egg = Column(Boolean, default=False, nullable=False)
    diet_nv = Column(Boolean, default=False, nullable=False)
    
    # Goals
    goal_wl = Column(Boolean, default=False, nullable=False)
    goal_wg = Column(Boolean, default=False, nullable=False)
    goal_mg = Column(Boolean, default=False, nullable=False)
    goal_m = Column(Boolean, default=False, nullable=False)
    goal_db = Column(Boolean, default=False, nullable=False)
    
    meal_type = Column(String(50), nullable=True)
    
    # Macros
    calories = Column(Float, nullable=True)
    protein = Column(Float, nullable=True)
    carbohydrates = Column(Float, nullable=True)
    fat = Column(Float, nullable=True)
    fiber = Column(Float, nullable=True)
    
    # Micronutrients and details (Stored as serialized JSON strings for robustness)
    vitamins = Column(Text, nullable=True)
    minerals = Column(Text, nullable=True)
    ingredients = Column(Text, nullable=True)
    
    health_benefits = Column(Text, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class ProgressLog(Base):
    __tablename__ = "progress_logs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    date = Column(String(10), unique=True, index=True, nullable=False)  # format: YYYY-MM-DD
    goal = Column(String(100), nullable=False)
    calories = Column(Float, nullable=False)
    protein = Column(Float, nullable=False)
    fiber = Column(Float, nullable=False)
    health_score = Column(Float, nullable=False)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class HydrationLog(Base):
    __tablename__ = "hydration_logs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    date = Column(String(10), index=True, nullable=False)  # format: YYYY-MM-DD
    amount_ml = Column(Float, nullable=False)
    target_ml = Column(Float, nullable=False, default=2000.0)
    reminder_interval_mins = Column(Integer, nullable=False, default=60)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


