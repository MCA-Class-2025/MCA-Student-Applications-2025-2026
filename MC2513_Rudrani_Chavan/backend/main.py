"""
NutriMate Custom FastAPI APIs
=============================
Provides production-grade REST APIs for:
1. Nutrition Analysis API (POST /api/nutrition/analyze) — delegates to rag_pipeline functions.
2. Nutrition Database API (GET /api/foods, GET /api/foods/{food_name}, POST /api/foods) — CRUD on SQLite database.
3. Food Recognition API (POST /api/foods/recognize) — delegates to analyze_food_image vision pipeline.
4. Allergen Detection API (POST /api/foods/allergens) — hybrid allergen detection and dietary suitability analysis.
5. Healthy Substitution API (POST /api/foods/substitutions) — goal-tailored ingredient substitution recommendations.
6. Food Comparison API (POST /api/foods/compare) — comparative nutrition analysis between two food items.
7. Cheat Meal Impact API (POST /api/foods/cheat-meal-impact) — goal-aware cheat meal budget analysis.
"""

import os
import sys
import json
import re
from pathlib import Path
from typing import Optional, List
from datetime import datetime

# ── Ensure project root is importable ──────────────────────────────────
_PROJECT_ROOT = str(Path(__file__).resolve().parent.parent)
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

# Force PyTorch-only backend (skip TensorFlow / Keras checks)
os.environ.setdefault("USE_TF", "0")
os.environ.setdefault("USE_TORCH", "1")

from fastapi import FastAPI, HTTPException, Depends, Query, UploadFile, File, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import func, or_

# Database & Models
from backend.database import get_db, engine, Base
from backend.models import Meal, ProgressLog, HydrationLog

# Initialize database tables programmatically (ensures progress_logs table is created)
Base.metadata.create_all(bind=engine)

# Reuse existing NutriMate analysis functions — NO duplicate LLM/vision logic
from rag_pipeline import extract_recipe_info, analyze_recipe, analyze_food_image, get_llm

# ── FastAPI Application ────────────────────────────────────────────────

app = FastAPI(
    title="NutriMate FastAPI Services",
    description=(
        "Production-grade APIs for nutritional analysis, dynamic database CRUD operations, "
        "image food recognition, allergen detection, healthy substitution recommendations, "
        "and food comparison analysis."
    ),
    version="1.0.0",
)


# ── 1. NUTRITION ANALYSIS SCHEMAS ──────────────────────────────────────

class NutritionAnalysisRequest(BaseModel):
    """Input payload for the nutrition-analysis endpoint."""

    food_name: str = Field(
        ...,
        min_length=1,
        description="Name of the food, dish, or recipe to analyze",
        json_schema_extra={"example": "Paneer Tikka"},
    )
    recipe_text: Optional[str] = Field(
        None,
        description="Optional recipe instructions or background text",
        json_schema_extra={"example": "Marinate paneer cubes in yogurt and spices, then grill on skewers."},
    )
    ingredients: Optional[List[str]] = Field(
        None,
        description="Optional list of ingredients",
        json_schema_extra={"example": ["Paneer", "Yogurt", "Tandoori Masala", "Capsicum", "Onion"]},
    )
    serving_size: Optional[str] = Field(
        None,
        description="Optional target serving size (e.g. '1 plate', '100 g')",
        json_schema_extra={"example": "1 plate"},
    )


class NutritionAnalysisResponse(BaseModel):
    """Normalized nutrition data returned by the analysis endpoint."""

    food_name: str = Field(..., json_schema_extra={"example": "Paneer Tikka"})
    serving_size: str = Field(..., json_schema_extra={"example": "1 plate (approx 150 g)"})
    calories: str = Field(..., json_schema_extra={"example": "280 kcal"})
    protein: str = Field(..., json_schema_extra={"example": "16 g"})
    carbohydrates: str = Field(..., json_schema_extra={"example": "12 g"})
    fat: str = Field(..., json_schema_extra={"example": "18 g"})
    fiber: str = Field(..., json_schema_extra={"example": "3 g"})
    vitamins: str = Field(..., json_schema_extra={"example": "Vitamin A, Vitamin C, Vitamin B12"})
    minerals: str = Field(..., json_schema_extra={"example": "Calcium, Iron, Phosphorus"})
    ingredients: List[str] = Field(..., json_schema_extra={"example": ["Paneer", "Yogurt", "Tandoori Masala"]})
    health_benefits: str = Field(..., json_schema_extra={"example": "High in protein, supports muscle repair."})
    consume_in_moderation: str = Field(..., json_schema_extra={"example": "Saturated fat from dairy and oil."})
    diet_type: str = Field(
        ...,
        description="Classification: 'veg', 'egg', or 'nv'",
        json_schema_extra={"example": "veg"},
    )
    confidence_score: int = Field(..., json_schema_extra={"example": 85})
    source_type: str = Field("api_analysis", json_schema_extra={"example": "api_analysis"})


# ── 2. NUTRITION DATABASE SCHEMAS ──────────────────────────────────────

class FoodItemResponse(BaseModel):
    """Output schema for a food record in the database."""

    id: int
    name: str
    source_type: str
    diet_veg: bool
    diet_egg: bool
    diet_nv: bool
    goal_wl: bool
    goal_wg: bool
    goal_mg: bool
    goal_m: bool
    goal_db: bool
    meal_type: Optional[str] = None
    calories: Optional[float] = None
    protein: Optional[float] = None
    carbohydrates: Optional[float] = None
    fat: Optional[float] = None
    fiber: Optional[float] = None
    vitamins: List[str] = Field(default_factory=list)
    minerals: List[str] = Field(default_factory=list)
    ingredients: List[str] = Field(default_factory=list)
    health_benefits: Optional[str] = None
    created_at: Optional[str] = None


class FoodItemCreate(BaseModel):
    """Input schema to save a new food item into the database."""

    name: str = Field(..., min_length=1, description="Unique name of the food dish", json_schema_extra={"example": "Vegetable Biryani"})
    source_type: str = Field("user_entry", description="Entry source: 'curated', 'api_analysis', or 'user_entry'", json_schema_extra={"example": "api_analysis"})
    diet_type: str = Field("veg", description="Diet classification: 'veg', 'egg', or 'nv'", json_schema_extra={"example": "veg"})
    goals: Optional[List[str]] = Field(default_factory=list, description="Target goals e.g. ['weight_loss', 'muscle_gain']", json_schema_extra={"example": ["weight_loss", "muscle_gain"]})
    meal_type: Optional[str] = Field("Lunch", description="Meal category, e.g. 'Breakfast', 'Lunch', 'Dinner', 'Snack'", json_schema_extra={"example": "Lunch"})
    calories: Optional[float] = Field(None, json_schema_extra={"example": 380.0})
    protein: Optional[float] = Field(None, json_schema_extra={"example": 18.0})
    carbohydrates: Optional[float] = Field(None, json_schema_extra={"example": 45.0})
    fat: Optional[float] = Field(None, json_schema_extra={"example": 12.0})
    fiber: Optional[float] = Field(None, json_schema_extra={"example": 6.0})
    vitamins: Optional[List[str]] = Field(default_factory=list, json_schema_extra={"example": ["Vitamin A", "Vitamin C"]})
    minerals: Optional[List[str]] = Field(default_factory=list, json_schema_extra={"example": ["Calcium", "Iron"]})
    ingredients: Optional[List[str]] = Field(default_factory=list, json_schema_extra={"example": ["Basmati Rice", "Mixed Vegetables", "Saffron"]})
    health_benefits: Optional[str] = Field(None, json_schema_extra={"example": "Rich in dietary fiber and essential vitamins."})


# ── 3. FOOD RECOGNITION SCHEMAS ───────────────────────────────────────

class FoodRecognitionResponse(BaseModel):
    """Output schema for food recognition API."""

    detected_food_name: str = Field(..., description="Name of the detected dish", json_schema_extra={"example": "Paneer Tikka"})
    confidence_score: int = Field(..., ge=0, le=100, description="Recognition confidence score (0-100)", json_schema_extra={"example": 85})
    is_food: bool = Field(..., description="True if the image contains an identifiable food dish", json_schema_extra={"example": True})
    detected_category: str = Field(..., description="Broad food category", json_schema_extra={"example": "Prepared Dish"})
    message: str = Field(..., description="Status summary message", json_schema_extra={"example": "Food dish successfully identified."})


# ── 4. ALLERGEN DETECTION SCHEMAS ──────────────────────────────────────

class AllergenAnalysisRequest(BaseModel):
    """Input payload for allergen detection API."""

    food_name: str = Field(..., min_length=1, description="Name of the food item or recipe", json_schema_extra={"example": "Paneer Tikka"})
    ingredients: Optional[List[str]] = Field(default_factory=list, description="Optional list of ingredients", json_schema_extra={"example": ["Paneer", "Yogurt", "Capsicum"]})
    recipe_text: Optional[str] = Field(None, description="Optional recipe description", json_schema_extra={"example": "Marinate paneer cubes in yogurt..."})


class AllergenAnalysisResponse(BaseModel):
    """Output schema for allergen analysis API."""

    food_name: str = Field(..., json_schema_extra={"example": "Paneer Tikka"})
    detected_allergens: List[str] = Field(default_factory=list, json_schema_extra={"example": ["Milk / Dairy"]})
    allergen_count: int = Field(..., json_schema_extra={"example": 1})
    warning_level: str = Field(..., description="'None', 'Low', 'Medium', or 'High'", json_schema_extra={"example": "Low"})
    explanation: str = Field(..., json_schema_extra={"example": "Contains Paneer and Yogurt which are dairy products."})
    safe_for_vegetarian: bool = Field(..., json_schema_extra={"example": True})
    safe_for_eggetarian: bool = Field(..., json_schema_extra={"example": True})
    safe_for_vegan: bool = Field(..., json_schema_extra={"example": False})
    confidence_score: int = Field(..., ge=0, le=100, json_schema_extra={"example": 95})


# ── 5. HEALTHY SUBSTITUTION SCHEMAS ────────────────────────────────────

class SubstitutionItem(BaseModel):
    """Single ingredient substitution recommendation."""

    original_ingredient: str = Field(..., json_schema_extra={"example": "Heavy Cream"})
    replacement: str = Field(..., json_schema_extra={"example": "Low-fat Greek Yogurt"})
    reason: str = Field(..., json_schema_extra={"example": "Reduces saturated fat while maintaining creamy texture."})
    estimated_nutrition_impact: str = Field(..., json_schema_extra={"example": "May reduce saturated fat and overall calories."})
    suitable_for_goal: str = Field(..., json_schema_extra={"example": "weight_loss"})


class HealthySubstitutionRequest(BaseModel):
    """Input payload for healthy substitution API."""

    food_name: str = Field(..., min_length=1, description="Name of the food dish or recipe", json_schema_extra={"example": "Paneer Butter Masala"})
    ingredients: Optional[List[str]] = Field(default_factory=list, description="Optional list of ingredients", json_schema_extra={"example": ["Paneer", "Butter", "Heavy Cream"]})
    recipe_text: Optional[str] = Field(None, description="Optional recipe text", json_schema_extra={"example": "Cook paneer in butter and cream..."})
    goal: Optional[str] = Field(None, description="Health goal: 'weight_loss', 'muscle_gain', 'weight_gain', 'diabetic_friendly', 'maintenance'", json_schema_extra={"example": "weight_loss"})


class HealthySubstitutionResponse(BaseModel):
    """Output schema for healthy substitution API."""

    food_name: str = Field(..., json_schema_extra={"example": "Paneer Butter Masala"})
    target_goal: str = Field(..., json_schema_extra={"example": "weight_loss"})
    substitutions: List[SubstitutionItem] = Field(default_factory=list)
    substitution_count: int = Field(..., json_schema_extra={"example": 1})
    summary: str = Field(..., json_schema_extra={"example": "1 healthier substitution identified to align with your weight_loss goal."})
    confidence_score: int = Field(..., ge=0, le=100, json_schema_extra={"example": 95})


# ── 6. FOOD COMPARISON SCHEMAS ─────────────────────────────────────────

class NutritionComparisonDetail(BaseModel):
    """Differences between food_1 and food_2 (food_1 - food_2)."""

    calories_diff: float = Field(..., description="food_1 calories minus food_2 calories", json_schema_extra={"example": 15.0})
    protein_diff: float = Field(..., description="food_1 protein minus food_2 protein", json_schema_extra={"example": 2.0})
    carbs_diff: float = Field(..., description="food_1 carbs minus food_2 carbs", json_schema_extra={"example": -5.0})
    fat_diff: float = Field(..., description="food_1 fat minus food_2 fat", json_schema_extra={"example": 1.0})
    fiber_diff: float = Field(..., description="food_1 fiber minus food_2 fiber", json_schema_extra={"example": 0.5})


class FoodComparisonRequest(BaseModel):
    """Input payload for food comparison API."""

    food_1: str = Field(..., min_length=1, description="First food item name to compare", json_schema_extra={"example": "Poha"})
    food_2: str = Field(..., min_length=1, description="Second food item name to compare", json_schema_extra={"example": "Upma"})
    goal: Optional[str] = Field("maintenance", description="Health goal: 'weight_loss', 'muscle_gain', 'weight_gain', 'diabetic_friendly', 'maintenance'", json_schema_extra={"example": "weight_loss"})


class FoodComparisonResponse(BaseModel):
    """Output schema for food comparison API."""

    food_1: FoodItemResponse
    food_2: FoodItemResponse
    nutrition_comparison: NutritionComparisonDetail
    better_for_calories: str = Field(..., description="Dish better suited for calories under target goal, or 'Equal'", json_schema_extra={"example": "Poha with Roasted Peanuts and Sprouts"})
    better_for_protein: str = Field(..., description="Dish with higher protein content, or 'Equal'", json_schema_extra={"example": "Paneer Tikka"})
    better_for_fiber: str = Field(..., description="Dish with higher fiber content, or 'Equal'", json_schema_extra={"example": "Poha with Roasted Peanuts and Sprouts"})
    better_for_goal: str = Field(..., description="Dish best suited overall for target health goal", json_schema_extra={"example": "Poha with Roasted Peanuts and Sprouts"})
    overall_recommendation: str = Field(..., description="Comparative summary recommendation", json_schema_extra={"example": "Poha is better suited for weight_loss due to lower calories and high fiber."})
    confidence_score: int = Field(..., ge=0, le=100, json_schema_extra={"example": 95})


# ── 7. CHEAT MEAL IMPACT SCHEMAS ───────────────────────────────────────

class CheatMealImpactRequest(BaseModel):
    """Input payload for cheat meal / junk food impact endpoint."""

    food_name: str = Field(
        ...,
        min_length=1,
        description="Name of the cheat-meal / junk food item.",
        json_schema_extra={"example": "Burger"},
    )
    calories: Optional[float] = Field(
        None,
        ge=0,
        description="Calorie content of this meal (kcal). If omitted, looked up or estimated via LLM.",
        json_schema_extra={"example": 550.0},
    )
    sugar_g: Optional[float] = Field(
        None,
        ge=0,
        description="Sugar content in grams. Optional.",
        json_schema_extra={"example": 12.0},
    )
    fat_g: Optional[float] = Field(
        None,
        ge=0,
        description="Total fat content in grams. Optional.",
        json_schema_extra={"example": 30.0},
    )
    daily_calorie_target: Optional[float] = Field(
        2000.0,
        gt=0,
        description="Daily calorie budget (kcal). Defaults to 2000 kcal.",
        json_schema_extra={"example": 2000.0},
    )
    daily_sugar_target: Optional[float] = Field(
        50.0,
        gt=0,
        description="Daily sugar budget (g). Defaults to 50 g (WHO guideline).",
        json_schema_extra={"example": 50.0},
    )
    daily_fat_target: Optional[float] = Field(
        65.0,
        gt=0,
        description="Daily fat budget (g). Defaults to 65 g.",
        json_schema_extra={"example": 65.0},
    )
    goal: Optional[str] = Field(
        None,
        description="Health goal: 'weight_loss', 'muscle_gain', 'weight_gain', 'diabetic_friendly', or 'maintenance'.",
        json_schema_extra={"example": "weight_loss"},
    )


class AlternativeSuggestion(BaseModel):
    """A single healthier alternative for a cheat-meal item."""

    original: str = Field(..., json_schema_extra={"example": "Deep Frying"})
    replacement: str = Field(..., json_schema_extra={"example": "Air Frying or Baking"})
    reason: str = Field(..., json_schema_extra={"example": "Reduces excess oil absorption."})


class CheatMealImpactResponse(BaseModel):
    """Output of the cheat meal impact analysis."""

    food_name: str = Field(..., json_schema_extra={"example": "Burger"})
    estimated_calories: float = Field(
        ...,
        description="Calories used for calculations (from input, DB, or LLM estimate).",
        json_schema_extra={"example": 550.0},
    )
    calorie_budget_used_pct: float = Field(
        ...,
        description="Percentage of daily calorie budget consumed by this meal.",
        json_schema_extra={"example": 27.5},
    )
    remaining_calorie_budget: float = Field(
        ...,
        description="Remaining daily calorie allowance after this meal.",
        json_schema_extra={"example": 1450.0},
    )
    sugar_budget_used_pct: Optional[float] = Field(
        None,
        description="Percentage of daily sugar budget consumed. Null when sugar data unavailable.",
        json_schema_extra={"example": 24.0},
    )
    fat_budget_used_pct: Optional[float] = Field(
        None,
        description="Percentage of daily fat budget consumed. Null when fat data unavailable.",
        json_schema_extra={"example": 46.2},
    )
    impact_level: str = Field(
        ...,
        description="Overall impact level: 'Low', 'Moderate', or 'High'.",
        json_schema_extra={"example": "Moderate"},
    )
    recommendation: str = Field(
        ...,
        description="Goal-aware dietary recommendation (no exercise prescription).",
        json_schema_extra={
            "example": "This meal accounts for 27.5% of your daily calorie budget. "
                       "Balance remaining meals with lower-calorie, high-fiber options."
        },
    )
    alternatives: List[AlternativeSuggestion] = Field(
        default_factory=list,
        description="Up to 2 healthier food alternatives sourced from substitution rules.",
    )
    calorie_source: str = Field(
        ...,
        description="How calorie data was obtained: 'user_provided', 'database', or 'llm_estimate'.",
        json_schema_extra={"example": "llm_estimate"},
    )


# ── 8. PROGRESS LOG SCHEMAS ───────────────────────────────────────────

class ProgressLogCreate(BaseModel):
    """Input payload for progress log creation."""
    date: str = Field(
        ...,
        pattern=r"^\d{4}-\d{2}-\d{2}$",
        description="Log date in YYYY-MM-DD format",
        json_schema_extra={"example": "2026-08-14"},
    )
    goal: str = Field(
        ...,
        min_length=1,
        description="Active health goal (e.g. weight_loss, muscle_gain, etc.)",
        json_schema_extra={"example": "weight_loss"},
    )
    calories: float = Field(
        ...,
        ge=0,
        description="Daily calorie consumption in kcal",
        json_schema_extra={"example": 1850.0},
    )
    protein: float = Field(
        ...,
        ge=0,
        description="Daily protein consumption in grams",
        json_schema_extra={"example": 75.0},
    )
    fiber: float = Field(
        ...,
        ge=0,
        description="Daily fiber consumption in grams",
        json_schema_extra={"example": 25.0},
    )
    health_score: float = Field(
        ...,
        ge=0,
        le=100,
        description="Overall health score for the day (0-100)",
        json_schema_extra={"example": 82.5},
    )
    notes: Optional[str] = Field(
        None,
        description="Optional diary notes or feedback",
        json_schema_extra={"example": "Felt energetic today, adhered to diet goals."},
    )


class ProgressLogResponse(BaseModel):
    """Output schema for a logged progress record."""
    id: int
    date: str
    goal: str
    calories: float
    protein: float
    fiber: float
    health_score: float
    notes: Optional[str] = None
    created_at: str


class ProgressSummaryResponse(BaseModel):
    """Response containing computed aggregate statistics and trend indicators."""
    total_logged_days: int
    average_calories: float
    average_protein: float
    average_fiber: float
    average_health_score: float
    trend: str = Field(
        ...,
        description="Chronological health score trend: 'Improving', 'Declining', or 'Stable'",
        json_schema_extra={"example": "Improving"}
    )



# ── 9. HYDRATION SCHEMAS ──────────────────────────────────────────────

class HydrationLogCreate(BaseModel):
    """Input payload for water intake log creation."""
    date: Optional[str] = Field(
        None,
        pattern=r"^\d{4}-\d{2}-\d{2}$",
        description="Log date in YYYY-MM-DD format (defaults to today's date)",
        json_schema_extra={"example": "2026-08-14"},
    )
    amount_ml: float = Field(
        ...,
        ge=0,
        description="Amount of water consumed in ml (can be 0 to update settings)",
        json_schema_extra={"example": 250.0},
    )
    target_ml: Optional[float] = Field(
        None,
        ge=100.0,
        le=10000.0,
        description="Daily water target in ml",
        json_schema_extra={"example": 2000.0},
    )
    reminder_interval_mins: Optional[int] = Field(
        None,
        ge=10,
        le=1440,
        description="Reminder interval in minutes",
        json_schema_extra={"example": 60},
    )


class HydrationLogResponse(BaseModel):
    """Output schema for a logged water intake record."""
    id: int
    date: str
    amount_ml: float
    target_ml: float
    reminder_interval_mins: int
    created_at: str


class HydrationTodayResponse(BaseModel):
    """Current day hydration status response."""
    date: str
    target_ml: float
    consumed_ml: float
    remaining_ml: float
    completion_pct: float
    hydration_status: str
    reminder_interval_mins: int
    logs: List[HydrationLogResponse]


class HydrationDailySummary(BaseModel):
    """Summary of water intake for a single day."""
    date: str
    consumed_ml: float
    target_ml: float
    completion_pct: float
    hydration_status: str


class HydrationSummaryResponse(BaseModel):
    """Hydration history metrics summary response."""
    total_days_logged: int
    average_daily_intake: float
    average_daily_target: float
    average_completion_pct: float
    history: List[HydrationDailySummary]



# ── HELPERS & UTILITIES ────────────────────────────────────────────────


_NV_KEYWORDS = frozenset({
    "chicken", "mutton", "lamb", "goat", "beef", "pork", "bacon",
    "fish", "salmon", "tuna", "sardine", "mackerel", "pomfret", "hilsa", "rohu",
    "prawn", "prawns", "shrimp", "crab", "lobster", "squid", "octopus",
    "meat", "keema", "seekh", "tikka boti", "tandoori chicken",
    "butter chicken", "rogan josh", "biryani chicken", "fish fry",
})

_EGG_KEYWORDS = frozenset({
    "egg", "eggs", "anda", "omelette", "omelet", "egg curry",
    "egg bhurji", "egg fried rice", "scotch egg",
})


def _infer_diet_type(ingredients: list, food_name: str) -> str:
    """Classify a dish as 'veg', 'egg', or 'nv' based on ingredient keywords."""
    text = " ".join(str(i) for i in ingredients).lower() + " " + food_name.lower()
    for kw in _NV_KEYWORDS:
        if kw in text:
            return "nv"
    for kw in _EGG_KEYWORDS:
        if kw in text:
            return "egg"
    return "veg"


def _build_input_text(
    food_name: str,
    recipe_text: str | None,
    ingredients: list[str] | None,
    serving_size: str | None,
) -> str:
    parts = [food_name]
    if recipe_text:
        parts.append(f"Recipe: {recipe_text}")
    if ingredients:
        parts.append(f"Ingredients: {', '.join(ingredients)}")
    if serving_size:
        parts.append(f"Serving size: {serving_size}")
    return "\n".join(parts)


_NA = "Not Available"


def _safe_str(val, fallback: str = _NA) -> str:
    if val is None:
        return fallback
    s = str(val).strip()
    return s if s else fallback


def _parse_json_list(val: Optional[str]) -> List[str]:
    """Safely deserialize a JSON list string into a Python list of strings."""
    if not val:
        return []
    val = val.strip()
    if not val:
        return []
    try:
        parsed = json.loads(val)
        if isinstance(parsed, list):
            return [str(x) for x in parsed if x]
        elif isinstance(parsed, str):
            return [parsed] if parsed else []
    except Exception:
        pass
    return [item.strip() for item in val.split(",") if item.strip()]


def _serialize_meal_to_response(meal: Meal) -> FoodItemResponse:
    """Convert SQLAlchemy Meal model instance to FoodItemResponse."""
    return FoodItemResponse(
        id=meal.id,
        name=meal.name,
        source_type=meal.source_type,
        diet_veg=meal.diet_veg,
        diet_egg=meal.diet_egg,
        diet_nv=meal.diet_nv,
        goal_wl=meal.goal_wl,
        goal_wg=meal.goal_wg,
        goal_mg=meal.goal_mg,
        goal_m=meal.goal_m,
        goal_db=meal.goal_db,
        meal_type=meal.meal_type,
        calories=meal.calories,
        protein=meal.protein,
        carbohydrates=meal.carbohydrates,
        fat=meal.fat,
        fiber=meal.fiber,
        vitamins=_parse_json_list(meal.vitamins),
        minerals=_parse_json_list(meal.minerals),
        ingredients=_parse_json_list(meal.ingredients),
        health_benefits=meal.health_benefits,
        created_at=meal.created_at.isoformat() if meal.created_at else None
    )


# ── ALLERGEN DETECTION PATTERNS ────────────────────────────────────────

_ALLERGEN_PATTERNS = {
    "Milk / Dairy": [
        "paneer", "cheese", "butter", "ghee", "curd", "yogurt", "dahi",
        "milk", "cream", "malai", "khoya", "mawa", "whey", "casein", "lactose", "c paneer"
    ],
    "Egg": [
        "egg", "eggs", "anda", "omelette", "omelet", "yolk", "bhurji", "mayonnaise", "albumen"
    ],
    "Peanuts": [
        "peanut", "peanuts", "mungfali", "groundnut", "peanut butter", "chikki"
    ],
    "Tree Nuts": [
        "almond", "cashew", "walnut", "pistachio", "hazelnut", "macadamia", "badam", "kaju", "pista", "akhrot"
    ],
    "Soy": [
        "soy", "soya", "tofu", "edamame", "soy sauce", "soya chunks", "soybean"
    ],
    "Wheat / Gluten": [
        "wheat", "atta", "maida", "semolina", "sooji", "suji", "barley", "rye", "bread", "roti", "naan", "pasta", "noodle", "paratha"
    ],
    "Fish": [
        "fish", "salmon", "tuna", "mackerel", "sardine", "pomfret", "hilsa", "rohu", "machhli"
    ],
    "Shellfish": [
        "prawn", "prawns", "shrimp", "crab", "lobster", "squid", "octopus", "clam", "mussel"
    ],
    "Sesame": [
        "sesame", "til", "tahini", "gingelly"
    ]
}


# ── HEALTHY SUBSTITUTION RULES ─────────────────────────────────────────

_SUBSTITUTION_RULES = [
    {
        "keywords": ["heavy cream", "cream", "malai"],
        "original": "Heavy Cream",
        "replacement": "Low-fat Greek Yogurt or Blended Cashew Milk",
        "reason": "Reduces saturated fat while maintaining a creamy texture.",
        "impact": "May reduce saturated fat and overall calories",
        "goals": ["weight_loss", "diabetic_friendly", "maintenance", "muscle_gain"]
    },
    {
        "keywords": ["butter", "makhani"],
        "original": "Butter",
        "replacement": "Olive Oil or Cold-pressed Ghee in moderation",
        "reason": "Replaces saturated fats with heart-healthy unsaturated fats.",
        "impact": "May improve fat quality and lower saturated fat intake",
        "goals": ["weight_loss", "diabetic_friendly", "maintenance"]
    },
    {
        "keywords": ["white rice", "basmati rice"],
        "original": "White Rice",
        "replacement": "Brown Rice, Quinoa, or Foxtail Millet",
        "reason": "Provides higher dietary fiber and a lower glycemic index.",
        "impact": "May promote better blood sugar control and sustained satiety",
        "goals": ["weight_loss", "diabetic_friendly", "maintenance"]
    },
    {
        "keywords": ["white sugar", "sugar"],
        "original": "White Sugar",
        "replacement": "Stevia, Monk Fruit, or Jaggery in moderation",
        "reason": "Prevents rapid glucose spikes.",
        "impact": "May prevent sudden blood sugar spikes and lower empty calories",
        "goals": ["diabetic_friendly", "weight_loss", "maintenance"]
    },
    {
        "keywords": ["maida", "refined flour", "refined wheat flour"],
        "original": "Maida (Refined Flour)",
        "replacement": "Whole Wheat Atta, Oats Flour, or Multigrain Flour",
        "reason": "Retains dietary fiber and complex carbohydrates.",
        "impact": "May improve digestion and slow carbohydrate absorption",
        "goals": ["weight_loss", "diabetic_friendly", "maintenance", "muscle_gain"]
    },
    {
        "keywords": ["deep fried", "deep frying"],
        "original": "Deep Frying",
        "replacement": "Air Frying, Baking, or Pan-Searing",
        "reason": "Decreases excess oil absorption.",
        "impact": "May substantially lower overall fat absorption and calorie density",
        "goals": ["weight_loss", "diabetic_friendly", "maintenance"]
    },
    {
        "keywords": ["white potato", "aloo"],
        "original": "White Potato",
        "replacement": "Sweet Potato or Boiled Chickpeas",
        "reason": "Lower glycemic index with higher dietary fiber and beta-carotene.",
        "impact": "May stabilize glycemic response and boost micronutrient intake",
        "goals": ["diabetic_friendly", "weight_loss"]
    }
]


# ── 1. NUTRITION ANALYSIS ENDPOINT ─────────────────────────────────────

@app.post(
    "/api/nutrition/analyze",
    response_model=NutritionAnalysisResponse,
    status_code=status.HTTP_200_OK,
    summary="Analyze nutritional information of a food item",
    tags=["Nutrition Analysis"]
)
async def analyze_nutrition(payload: NutritionAnalysisRequest):
    food_name = payload.food_name.strip()
    if not food_name:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="food_name must be a non-empty string.",
        )

    recipe_text = payload.recipe_text.strip() if payload.recipe_text else None
    ingredients_in = payload.ingredients or []
    serving_size = payload.serving_size.strip() if payload.serving_size else None

    combined = _build_input_text(food_name, recipe_text, ingredients_in or None, serving_size)

    try:
        detail = extract_recipe_info(combined)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"extract_recipe_info failed: {exc}",
        )

    try:
        recipe = analyze_recipe(combined)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"analyze_recipe failed: {exc}",
        )

    if not detail.get("is_recipe") and not recipe.get("is_recipe"):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"'{food_name}' was not recognized as a food item or recipe.",
        )

    res_food = detail.get("dish_name") or recipe.get("dish_name") or food_name
    res_serving = serving_size or "1 serving (standard)"

    res_cal  = _safe_str(detail.get("calories",  recipe.get("calories")))
    res_pro  = _safe_str(detail.get("protein",   recipe.get("protein")))
    res_carb = _safe_str(
        detail.get("carbs",
        recipe.get("carbohydrates",
        recipe.get("carbs")))
    )
    res_fat  = _safe_str(detail.get("fat",  recipe.get("fat")))
    res_fib  = _safe_str(detail.get("fiber", recipe.get("fiber")))

    res_vit = _safe_str(detail.get("vitamins"))
    res_min = _safe_str(detail.get("minerals"))

    if res_vit == _NA and "vitamins_minerals" in recipe:
        res_vit = _safe_str(recipe["vitamins_minerals"])
    if res_min == _NA and "vitamins_minerals" in recipe:
        res_min = _safe_str(recipe["vitamins_minerals"])

    if ingredients_in:
        res_ings = ingredients_in
    elif isinstance(detail.get("ingredients"), list) and detail["ingredients"]:
        res_ings = detail["ingredients"]
    else:
        res_ings = [_NA]

    res_benefits = _safe_str(recipe.get("health_benefits", detail.get("summary")))
    res_moderation = _safe_str(recipe.get("consume_in_moderation"))
    res_diet = _infer_diet_type(res_ings, food_name)

    _scored_fields = [res_cal, res_pro, res_carb, res_fat, res_fib,
                      res_vit, res_min, res_benefits, res_moderation]
    filled = sum(1 for v in _scored_fields if v != _NA)
    res_conf = min(95, max(40, int(filled / len(_scored_fields) * 100)))

    return NutritionAnalysisResponse(
        food_name=res_food,
        serving_size=res_serving,
        calories=res_cal,
        protein=res_pro,
        carbohydrates=res_carb,
        fat=res_fat,
        fiber=res_fib,
        vitamins=res_vit,
        minerals=res_min,
        ingredients=res_ings,
        health_benefits=res_benefits,
        consume_in_moderation=res_moderation,
        diet_type=res_diet,
        confidence_score=res_conf,
        source_type="api_analysis",
    )


# ── 2. NUTRITION DATABASE ENDPOINTS ────────────────────────────────────

@app.get(
    "/api/foods",
    response_model=List[FoodItemResponse],
    status_code=status.HTTP_200_OK,
    summary="Get all foods with optional filters",
    tags=["Nutrition Database"]
)
def get_foods(
    diet_type: Optional[str] = Query(None, description="Filter by diet type: 'veg', 'egg', or 'nv'"),
    meal_type: Optional[str] = Query(None, description="Filter by meal type: 'Breakfast', 'Lunch', 'Dinner', 'Snack'"),
    goal: Optional[str] = Query(None, description="Filter by target goal e.g. 'weight_loss', 'muscle_gain', 'diabetic_friendly'"),
    search: Optional[str] = Query(None, description="Search keyword in food name, ingredients, or health benefits"),
    db: Session = Depends(get_db)
):
    query = db.query(Meal)

    if diet_type:
        dt = diet_type.strip().lower()
        if dt == "veg":
            query = query.filter(Meal.diet_veg == True)
        elif dt == "egg":
            query = query.filter(Meal.diet_egg == True)
        elif dt == "nv":
            query = query.filter(Meal.diet_nv == True)

    if meal_type:
        mt = meal_type.strip().lower()
        query = query.filter(func.lower(Meal.meal_type) == mt)

    if goal:
        g = goal.strip().lower()
        if g in ("wl", "weight_loss", "weight loss"):
            query = query.filter(Meal.goal_wl == True)
        elif g in ("wg", "weight_gain", "weight gain"):
            query = query.filter(Meal.goal_wg == True)
        elif g in ("mg", "muscle_gain", "muscle gain"):
            query = query.filter(Meal.goal_mg == True)
        elif g in ("m", "maintenance"):
            query = query.filter(Meal.goal_m == True)
        elif g in ("db", "diabetic", "diabetic_friendly"):
            query = query.filter(Meal.goal_db == True)

    if search:
        s = f"%{search.strip().lower()}%"
        query = query.filter(
            or_(
                func.lower(Meal.name).like(s),
                func.lower(Meal.ingredients).like(s),
                func.lower(Meal.health_benefits).like(s)
            )
        )

    meals = query.all()
    return [_serialize_meal_to_response(m) for m in meals]


@app.get(
    "/api/foods/{food_name}",
    response_model=FoodItemResponse,
    status_code=status.HTTP_200_OK,
    summary="Get complete nutrition data for one food item",
    tags=["Nutrition Database"]
)
def get_food_by_name(food_name: str, db: Session = Depends(get_db)):
    food_clean = food_name.strip()
    if not food_clean:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Food name parameter cannot be empty."
        )

    meal = db.query(Meal).filter(func.lower(Meal.name) == food_clean.lower()).first()
    if not meal:
        meal = db.query(Meal).filter(Meal.name.ilike(f"%{food_clean}%")).first()

    if not meal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Food item '{food_clean}' not found in database."
        )
    return _serialize_meal_to_response(meal)


@app.post(
    "/api/foods",
    response_model=FoodItemResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add a new food/recipe to the dynamic dataset",
    tags=["Nutrition Database"]
)
def create_food_item(payload: FoodItemCreate, db: Session = Depends(get_db)):
    name_clean = payload.name.strip()
    if not name_clean:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="name must be a non-empty string."
        )

    existing = db.query(Meal).filter(func.lower(Meal.name) == name_clean.lower()).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Food item '{name_clean}' already exists in database."
        )

    src = payload.source_type.strip().lower() if payload.source_type else "user_entry"
    if src not in ("curated", "api_analysis", "user_entry"):
        src = "user_entry"

    dt = payload.diet_type.strip().lower() if payload.diet_type else "veg"
    if dt == "nv":
        d_veg, d_egg, d_nv = False, False, True
    elif dt == "egg":
        d_veg, d_egg, d_nv = False, True, True
    else:
        d_veg, d_egg, d_nv = True, True, True

    goals_lower = [g.strip().lower() for g in (payload.goals or [])]
    g_wl = any(g in ("wl", "weight_loss", "weight loss") for g in goals_lower)
    g_wg = any(g in ("wg", "weight_gain", "weight gain") for g in goals_lower)
    g_mg = any(g in ("mg", "muscle_gain", "muscle gain") for g in goals_lower)
    g_m  = any(g in ("m", "maintenance") for g in goals_lower)
    g_db = any(g in ("db", "diabetic", "diabetic_friendly") for g in goals_lower)

    vit_str = json.dumps(payload.vitamins or [])
    min_str = json.dumps(payload.minerals or [])
    ing_str = json.dumps(payload.ingredients or [])

    new_meal = Meal(
        name=name_clean,
        source_type=src,
        diet_veg=d_veg,
        diet_egg=d_egg,
        diet_nv=d_nv,
        goal_wl=g_wl,
        goal_wg=g_wg,
        goal_mg=g_mg,
        goal_m=g_m,
        goal_db=g_db,
        meal_type=payload.meal_type or "Snack",
        calories=payload.calories,
        protein=payload.protein,
        carbohydrates=payload.carbohydrates,
        fat=payload.fat,
        fiber=payload.fiber,
        vitamins=vit_str,
        minerals=min_str,
        ingredients=ing_str,
        health_benefits=payload.health_benefits or "",
    )

    db.add(new_meal)
    db.commit()
    db.refresh(new_meal)

    return _serialize_meal_to_response(new_meal)


# ── 3. FOOD RECOGNITION ENDPOINT ───────────────────────────────────────

@app.post(
    "/api/foods/recognize",
    response_model=FoodRecognitionResponse,
    status_code=status.HTTP_200_OK,
    summary="Identify food dish from an uploaded image",
    tags=["Food Recognition"]
)
async def recognize_food(file: UploadFile = File(...)):
    filename = file.filename or "uploaded_image.jpg"
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    content_type = (file.content_type or "").lower()

    valid_exts = {"jpg", "jpeg", "png"}
    valid_types = {"image/jpeg", "image/jpg", "image/png"}

    if ext not in valid_exts and content_type not in valid_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid image file type. Only JPG, JPEG, and PNG images are supported."
        )

    try:
        image_bytes = await file.read()
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to read uploaded file: {exc}"
        )

    if not image_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded image file is empty."
        )

    try:
        result = analyze_food_image(image_bytes, filename=filename)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Vision analysis pipeline failed: {exc}"
        )

    if result.get("is_not_food_image") or not result.get("is_recipe", True):
        return FoodRecognitionResponse(
            detected_food_name="Unknown / Not Food",
            confidence_score=0,
            is_food=False,
            detected_category="Non-Food",
            message="The uploaded image does not contain an identifiable food dish."
        )

    dish_name = result.get("dish_name", filename.rsplit(".", 1)[0].replace("-", " ").replace("_", " ").title())
    if not dish_name or dish_name == "Not Available":
        dish_name = "Nutritious Food Dish"

    _NA = "Not Available"
    fields = [result.get("calories"), result.get("protein"), result.get("carbs"), result.get("fat")]
    filled = sum(1 for f in fields if f and f != _NA)
    confidence = min(95, max(60, 60 + filled * 8))

    return FoodRecognitionResponse(
        detected_food_name=dish_name,
        confidence_score=confidence,
        is_food=True,
        detected_category="Prepared Dish",
        message="Food dish successfully identified."
    )


# ── 4. ALLERGEN DETECTION ENDPOINT ─────────────────────────────────────

@app.post(
    "/api/foods/allergens",
    response_model=AllergenAnalysisResponse,
    status_code=status.HTTP_200_OK,
    summary="Detect common food allergens and evaluate dietary suitability",
    tags=["Allergen Detection"]
)
async def detect_allergens(payload: AllergenAnalysisRequest):
    food_name = payload.food_name.strip()
    if not food_name:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="food_name must be a non-empty string."
        )

    ingredients = payload.ingredients or []
    recipe_text = payload.recipe_text.strip() if payload.recipe_text else ""
    combined_text = f"{food_name} {' '.join(ingredients)} {recipe_text}".lower()

    detected = []

    for allergen_category, keywords in _ALLERGEN_PATTERNS.items():
        for kw in keywords:
            pattern = r'\b' + re.escape(kw) + r'\b'
            if re.search(pattern, combined_text):
                detected.append(allergen_category)
                break

    if not detected and not ingredients and len(food_name.split()) <= 3:
        try:
            llm_info = extract_recipe_info(food_name)
            if llm_info and isinstance(llm_info.get("ingredients"), list):
                extracted_ings = " ".join(llm_info["ingredients"]).lower()
                for allergen_category, keywords in _ALLERGEN_PATTERNS.items():
                    if allergen_category not in detected:
                        for kw in keywords:
                            if re.search(r'\b' + re.escape(kw) + r'\b', extracted_ings):
                                detected.append(allergen_category)
                                break
        except Exception:
            pass

    allergen_count = len(detected)

    if allergen_count == 0:
        warning_level = "None"
        explanation = "No major common allergens detected in this food item."
    elif allergen_count == 1:
        warning_level = "Low"
        explanation = f"Contains {detected[0]} which is a common food allergen."
    elif allergen_count == 2:
        warning_level = "Medium"
        explanation = f"Contains multiple allergens: {', '.join(detected)}."
    else:
        warning_level = "High"
        explanation = f"High allergen alert! Contains: {', '.join(detected)}."

    has_dairy = "Milk / Dairy" in detected
    has_egg = "Egg" in detected
    has_fish = "Fish" in detected
    has_shellfish = "Shellfish" in detected

    safe_veg = not (has_egg or has_fish or has_shellfish)
    safe_egg = not (has_fish or has_shellfish)
    safe_vegan = not (has_dairy or has_egg or has_fish or has_shellfish)

    confidence = 95 if allergen_count > 0 or ingredients else 90

    return AllergenAnalysisResponse(
        food_name=food_name,
        detected_allergens=detected,
        allergen_count=allergen_count,
        warning_level=warning_level,
        explanation=explanation,
        safe_for_vegetarian=safe_veg,
        safe_for_eggetarian=safe_egg,
        safe_for_vegan=safe_vegan,
        confidence_score=confidence
    )


# ── 5. HEALTHY SUBSTITUTION ENDPOINT ───────────────────────────────────

@app.post(
    "/api/foods/substitutions",
    response_model=HealthySubstitutionResponse,
    status_code=status.HTTP_200_OK,
    summary="Suggest goal-tailored healthy ingredient substitutions",
    tags=["Healthy Substitution"]
)
async def suggest_substitutions(payload: HealthySubstitutionRequest):
    food_name = payload.food_name.strip()
    if not food_name:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="food_name must be a non-empty string."
        )

    ingredients = payload.ingredients or []
    recipe_text = payload.recipe_text.strip() if payload.recipe_text else ""
    target_goal = (payload.goal.strip().lower() if payload.goal else "general_health")

    combined_text = f"{food_name} {' '.join(ingredients)} {recipe_text}".lower()

    substitutions = []

    for rule in _SUBSTITUTION_RULES:
        if target_goal != "general_health" and target_goal not in rule["goals"]:
            continue

        for kw in rule["keywords"]:
            pattern = r'\b' + re.escape(kw) + r'\b'
            if re.search(pattern, combined_text):
                substitutions.append(
                    SubstitutionItem(
                        original_ingredient=rule["original"],
                        replacement=rule["replacement"],
                        reason=rule["reason"],
                        estimated_nutrition_impact=rule["impact"],
                        suitable_for_goal=target_goal
                    )
                )
                break

    if not substitutions and len(food_name.split()) <= 4:
        try:
            llm_info = extract_recipe_info(food_name)
            if llm_info and isinstance(llm_info.get("ingredients"), list):
                llm_ings_text = " ".join(llm_info["ingredients"]).lower()
                for rule in _SUBSTITUTION_RULES:
                    if target_goal != "general_health" and target_goal not in rule["goals"]:
                        continue
                    for kw in rule["keywords"]:
                        if re.search(r'\b' + re.escape(kw) + r'\b', llm_ings_text):
                            substitutions.append(
                                SubstitutionItem(
                                    original_ingredient=rule["original"],
                                    replacement=rule["replacement"],
                                    reason=rule["reason"],
                                    estimated_nutrition_impact=rule["impact"],
                                    suitable_for_goal=target_goal
                                )
                            )
                            break
        except Exception:
            pass

    sub_count = len(substitutions)

    if sub_count == 0:
        summary = (
            f"This meal ('{food_name}') already consists of whole, nutrient-dense ingredients. "
            "No immediate substitutions are required."
        )
        confidence = 95
    else:
        summary = (
            f"Found {sub_count} healthier ingredient substitution(s) for '{food_name}' "
            f"tailored to your {target_goal} goal."
        )
        confidence = 90

    return HealthySubstitutionResponse(
        food_name=food_name,
        target_goal=target_goal,
        substitutions=substitutions,
        substitution_count=sub_count,
        summary=summary,
        confidence_score=confidence
    )


# ── 6. FOOD COMPARISON ENDPOINT ────────────────────────────────────────

def _fetch_meal_or_404(food_name: str, db: Session) -> Meal:
    """Helper to query database for a food item by exact name or substring."""
    clean = food_name.strip()
    if not clean:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Food name cannot be empty."
        )

    # 1. Exact case-insensitive match
    meal = db.query(Meal).filter(func.lower(Meal.name) == clean.lower()).first()

    # 2. Substring match fallback
    if not meal:
        meal = db.query(Meal).filter(Meal.name.ilike(f"%{clean}%")).first()

    if not meal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Food item '{clean}' not found in database."
        )
    return meal


@app.post(
    "/api/foods/compare",
    response_model=FoodComparisonResponse,
    status_code=status.HTTP_200_OK,
    summary="Compare nutritional profiles of two food items",
    tags=["Food Comparison"]
)
def compare_foods(payload: FoodComparisonRequest, db: Session = Depends(get_db)):
    """
    Retrieves two foods from the database and performs a goal-aware nutrition comparison.
    Does NOT modify the database.
    """
    f1_clean = payload.food_1.strip() if payload.food_1 else ""
    f2_clean = payload.food_2.strip() if payload.food_2 else ""

    if not f1_clean or not f2_clean:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Both food_1 and food_2 must be non-empty strings."
        )

    target_goal = (payload.goal.strip().lower() if payload.goal else "maintenance")

    # Retrieve from database
    meal1 = _fetch_meal_or_404(f1_clean, db)
    meal2 = _fetch_meal_or_404(f2_clean, db)

    resp1 = _serialize_meal_to_response(meal1)
    resp2 = _serialize_meal_to_response(meal2)

    # Macro values
    c1, c2 = meal1.calories or 0.0, meal2.calories or 0.0
    p1, p2 = meal1.protein or 0.0, meal2.protein or 0.0
    cb1, cb2 = meal1.carbohydrates or 0.0, meal2.carbohydrates or 0.0
    ft1, ft2 = meal1.fat or 0.0, meal2.fat or 0.0
    fb1, fb2 = meal1.fiber or 0.0, meal2.fiber or 0.0

    comp_detail = NutritionComparisonDetail(
        calories_diff=round(c1 - c2, 1),
        protein_diff=round(p1 - p2, 1),
        carbs_diff=round(cb1 - cb2, 1),
        fat_diff=round(ft1 - ft2, 1),
        fiber_diff=round(fb1 - fb2, 1),
    )

    # Goal-aware calorie comparison
    if abs(c1 - c2) <= 10.0:
        better_calories = "Equal"
    elif target_goal in ("weight_gain", "wg", "muscle_gain", "mg"):
        better_calories = meal1.name if c1 > c2 else meal2.name
    else:  # weight_loss, diabetic_friendly, maintenance default
        better_calories = meal1.name if c1 < c2 else meal2.name

    # Protein comparison
    if abs(p1 - p2) <= 0.8:
        better_protein = "Equal"
    elif p1 > p2:
        better_protein = meal1.name
    else:
        better_protein = meal2.name

    # Fiber comparison
    if abs(fb1 - fb2) <= 0.5:
        better_fiber = "Equal"
    elif fb1 > fb2:
        better_fiber = meal1.name
    else:
        better_fiber = meal2.name

    # Goal suitability scoring
    score1, score2 = 0.0, 0.0

    if target_goal in ("weight_loss", "wl"):
        # Lower calories, higher fiber, higher protein
        score1 += (1000 - c1) * 0.4 + fb1 * 20.0 + p1 * 5.0
        score2 += (1000 - c2) * 0.4 + fb2 * 20.0 + p2 * 5.0
    elif target_goal in ("muscle_gain", "mg"):
        # Higher protein, higher calories
        score1 += p1 * 30.0 + c1 * 0.2
        score2 += p2 * 30.0 + c2 * 0.2
    elif target_goal in ("weight_gain", "wg"):
        # Higher calories, higher protein
        score1 += c1 * 0.5 + p1 * 10.0
        score2 += c2 * 0.5 + p2 * 10.0
    elif target_goal in ("diabetic_friendly", "db"):
        # Higher fiber, lower carbs, lower calories
        score1 += fb1 * 30.0 + (500 - cb1) * 0.5 + (1000 - c1) * 0.2
        score2 += fb2 * 30.0 + (500 - cb2) * 0.5 + (1000 - c2) * 0.2
    else:  # maintenance
        score1 += p1 * 10.0 + fb1 * 15.0 + (1000 - c1) * 0.1
        score2 += p2 * 10.0 + fb2 * 15.0 + (1000 - c2) * 0.1

    if abs(score1 - score2) < (max(score1, score2) * 0.05):
        better_goal = "Both are equally suitable"
        rec = f"Both '{meal1.name}' and '{meal2.name}' present balanced nutritional profiles for {target_goal}."
    elif score1 > score2:
        better_goal = meal1.name
        rec = f"'{meal1.name}' is better recommended for {target_goal}."
    else:
        better_goal = meal2.name
        rec = f"'{meal2.name}' is better recommended for {target_goal}."

    return FoodComparisonResponse(
        food_1=resp1,
        food_2=resp2,
        nutrition_comparison=comp_detail,
        better_for_calories=better_calories,
        better_for_protein=better_protein,
        better_for_fiber=better_fiber,
        better_for_goal=better_goal,
        overall_recommendation=rec,
        confidence_score=95
    )


# ── 7. CHEAT MEAL IMPACT HELPERS ───────────────────────────────────────

def _parse_numeric_value(raw: Optional[str]) -> Optional[float]:
    """
    Extract the first numeric value from a string like '280 kcal', '16 g', '~12-18 g'.
    Returns None if nothing parseable is found.
    """
    if raw is None:
        return None
    # Strip common prefixes/ranges and extract first number
    clean = re.sub(r"[~<>≈]", "", str(raw))
    # Handle ranges like '12-18' → take average
    range_match = re.search(r"(\d+(?:\.\d+)?)\s*[-–]\s*(\d+(?:\.\d+)?)", clean)
    if range_match:
        lo, hi = float(range_match.group(1)), float(range_match.group(2))
        return round((lo + hi) / 2, 1)
    # Single number
    single_match = re.search(r"(\d+(?:\.\d+)?)", clean)
    if single_match:
        return float(single_match.group(1))
    return None


async def _cheat_meal_alternatives(food_name: str, goal: Optional[str] = None) -> List[AlternativeSuggestion]:
    """
    Return up to 2 healthier alternatives by calling the existing Healthy Substitution API
    internally. Falls back to generic junk-food swaps when no specific rule matches.
    """
    suggestions: List[AlternativeSuggestion] = []
    name_lower = food_name.lower()

    try:
        sub_req = HealthySubstitutionRequest(food_name=food_name, goal=goal)
        sub_res = await suggest_substitutions(sub_req)
        for item in sub_res.substitutions:
            suggestions.append(
                AlternativeSuggestion(
                    original=item.original_ingredient,
                    replacement=item.replacement,
                    reason=item.reason
                )
            )
    except Exception:
        pass

    # Generic junk-food alternatives when no specific rule matched
    if not suggestions:
        junk_keywords = [
            "burger", "pizza", "fries", "chips", "fried", "nugget",
            "cola", "soda", "cold drink", "aerated", "soft drink",
            "chocolate", "candy", "cake", "pastry", "donut", "doughnut",
            "samosa", "pakoda", "vada pav",
        ]
        matched_generic = any(kw in name_lower for kw in junk_keywords)
        if matched_generic:
            suggestions.append(
                AlternativeSuggestion(
                    original=food_name,
                    replacement="Grilled or baked version of a similar dish",
                    reason="Reduces oil and refined-carb content while preserving the general flavour profile.",
                )
            )
            suggestions.append(
                AlternativeSuggestion(
                    original=food_name,
                    replacement="Fresh fruit salad, yogurt parfait, or a whole-grain snack",
                    reason="Provides natural sugars, dietary fiber, and micronutrients with significantly fewer empty calories.",
                )
            )

    return suggestions[:2]


def _cheat_meal_recommendation(
    food_name: str,
    cal_pct: float,
    impact: str,
    goal: Optional[str],
    remaining_cal: float,
) -> str:
    """
    Build a concise, goal-aware dietary recommendation.
    Never prescribes exercise or implies that exercise 'burns off' food.
    """
    goal_norm = (goal or "maintenance").strip().lower()

    base = (
        f"'{food_name}' uses {cal_pct:.1f}% of your daily calorie budget, "
        f"leaving approximately {remaining_cal:.0f} kcal for the rest of the day."
    )

    if impact == "Low":
        impact_note = "This is a relatively minor indulgence."
    elif impact == "Moderate":
        impact_note = (
            "This is a meaningful portion of your daily budget. "
            "Keep remaining meals lighter and nutrient-dense."
        )
    else:  # High
        impact_note = (
            "This meal is a significant part of your daily budget. "
            "Prioritise vegetables, lean protein, and whole grains for the remaining meals today."
        )

    if goal_norm in ("weight_loss", "wl"):
        goal_note = (
            "For weight loss, focus remaining meals on high-fiber, high-protein, "
            "low-calorie options such as salads, lentils, or grilled vegetables."
        )
    elif goal_norm in ("diabetic_friendly", "db"):
        goal_note = (
            "For blood sugar management, avoid additional high-sugar or high-GI foods today "
            "and choose fiber-rich, low-GI options for remaining meals."
        )
    elif goal_norm in ("muscle_gain", "mg"):
        goal_note = (
            "For muscle gain, ensure remaining meals are rich in lean protein "
            "(e.g., eggs, legumes, paneer, or chicken) to meet your daily protein target."
        )
    elif goal_norm in ("weight_gain", "wg"):
        goal_note = (
            "For weight gain, complement this meal with nutrient-dense, calorie-rich whole foods "
            "such as nuts, dairy, whole grains, and legumes."
        )
    else:  # maintenance / general
        goal_note = (
            "For balanced nutrition, ensure remaining meals include a variety of vegetables, "
            "whole grains, and adequate protein to meet your daily micronutrient needs."
        )

    return f"{base} {impact_note} {goal_note}"


# ── 7. CHEAT MEAL IMPACT ENDPOINT ──────────────────────────────────────

@app.post(
    "/api/foods/cheat-meal-impact",
    response_model=CheatMealImpactResponse,
    status_code=status.HTTP_200_OK,
    summary="Analyse the daily-budget impact of a cheat meal or junk food item",
    description=(
        "Calculates calorie, sugar, and fat budget usage for a cheat meal. "
        "Returns impact level (Low / Moderate / High), remaining calorie budget, "
        "a goal-aware dietary recommendation, and up to 2 healthier alternatives. "
        "Calorie data is sourced from: (1) user-provided value, (2) NutriMate database, "
        "or (3) LLM estimation via analyze_recipe — in that priority order."
    ),
    tags=["Cheat Meal Impact"],
)
async def cheat_meal_impact(payload: CheatMealImpactRequest, db: Session = Depends(get_db)):

    food_name = payload.food_name.strip()
    if not food_name:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="food_name must be a non-empty string.",
        )

    # ── Retrieve / estimate calorie value ───────────────────────────────
    meal_calories: Optional[float] = None
    sugar_g: Optional[float] = payload.sugar_g
    fat_g: Optional[float] = payload.fat_g
    calorie_source: str = "user_provided"

    # Priority 1: user-provided calories
    if payload.calories is not None:
        meal_calories = payload.calories
        calorie_source = "user_provided"

    # Priority 2: NutriMate database lookup
    if meal_calories is None:
        try:
            db_meal = db.query(Meal).filter(
                func.lower(Meal.name) == food_name.lower()
            ).first()
            if not db_meal:
                db_meal = db.query(Meal).filter(
                    Meal.name.ilike(f"%{food_name}%")
                ).first()
            if db_meal and db_meal.calories is not None:
                meal_calories = float(db_meal.calories)
                calorie_source = "database"
                # Also pick up fat from DB if not user-supplied
                if fat_g is None and db_meal.fat is not None:
                    fat_g = float(db_meal.fat)
        except Exception:
            pass

    # Priority 3: LLM estimation — analyze_recipe first, then extract_recipe_info fallback
    if meal_calories is None:
        try:
            llm_data = analyze_recipe(food_name)
            # Some short common names (e.g. 'Burger') return is_recipe=False from analyze_recipe.
            # Retry with a more descriptive prompt before falling back to extract_recipe_info.
            if not llm_data.get("is_recipe"):
                llm_data = analyze_recipe(
                    f"{food_name} - common food item, estimate nutritional values per serving"
                )
            if llm_data.get("is_recipe"):
                cal_raw = llm_data.get("calories")
                parsed_cal = _parse_numeric_value(str(cal_raw)) if cal_raw else None
                if parsed_cal is not None:
                    meal_calories = parsed_cal
                    calorie_source = "llm_estimate"
                # Extract fat if still missing
                if fat_g is None:
                    fat_raw = llm_data.get("fat")
                    if fat_raw:
                        fat_g = _parse_numeric_value(str(fat_raw))
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"LLM estimation failed: {exc}",
            )

    # Priority 4: extract_recipe_info fallback (catches short names like 'Burger', 'Pizza')
    if meal_calories is None:
        try:
            ei_data = extract_recipe_info(food_name)
            if ei_data and ei_data.get("is_recipe"):
                cal_raw = ei_data.get("calories")
                parsed_cal = _parse_numeric_value(str(cal_raw)) if cal_raw else None
                if parsed_cal is not None:
                    meal_calories = parsed_cal
                    calorie_source = "llm_estimate"
                if fat_g is None:
                    fat_raw = ei_data.get("fat")
                    if fat_raw:
                        fat_g = _parse_numeric_value(str(fat_raw))
        except Exception:
            pass  # Silently skip; 422 raised below if still None


    # If still no calorie data, raise a clear error
    if meal_calories is None or meal_calories < 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                f"Could not determine calorie content for '{food_name}'. "
                "Please provide the 'calories' field explicitly."
            ),
        )

    # ── Budget calculations ──────────────────────────────────────────────
    daily_cal   = payload.daily_calorie_target or 2000.0
    daily_sugar = payload.daily_sugar_target   or 50.0
    daily_fat   = payload.daily_fat_target     or 65.0

    cal_pct       = round((meal_calories / daily_cal) * 100, 1)
    remaining_cal = round(daily_cal - meal_calories, 1)

    sugar_pct: Optional[float] = None
    if sugar_g is not None:
        sugar_pct = round((sugar_g / daily_sugar) * 100, 1)

    fat_pct: Optional[float] = None
    if fat_g is not None:
        fat_pct = round((fat_g / daily_fat) * 100, 1)

    # ── Impact level ─────────────────────────────────────────────────────
    # Driven by calorie % alone; secondary signals (fat/sugar) can elevate it.
    if cal_pct < 20:
        impact_level = "Low"
    elif cal_pct < 40:
        impact_level = "Moderate"
    else:
        impact_level = "High"

    # Elevate impact when fat > 50% or sugar >= 75% of daily budget
    if impact_level == "Low" and (
        (fat_pct is not None and fat_pct > 50)
        or (sugar_pct is not None and sugar_pct >= 75)
    ):
        impact_level = "Moderate"
    elif impact_level == "Moderate" and (
        (fat_pct is not None and fat_pct > 80)
        or (sugar_pct is not None and sugar_pct > 100)
    ):
        impact_level = "High"

    # ── Recommendation ───────────────────────────────────────────────────
    recommendation = _cheat_meal_recommendation(
        food_name=food_name,
        cal_pct=cal_pct,
        impact=impact_level,
        goal=payload.goal,
        remaining_cal=remaining_cal,
    )

    # ── Healthier alternatives ───────────────────────────────────────────
    alternatives = await _cheat_meal_alternatives(food_name, payload.goal)

    return CheatMealImpactResponse(
        food_name=food_name,
        estimated_calories=round(meal_calories, 1),
        calorie_budget_used_pct=cal_pct,
        remaining_calorie_budget=remaining_cal,
        sugar_budget_used_pct=sugar_pct,
        fat_budget_used_pct=fat_pct,
        impact_level=impact_level,
        recommendation=recommendation,
        alternatives=alternatives,
        calorie_source=calorie_source,
    )


# ── 8. PROGRESS TRACKING ENDPOINTS ──────────────────────────────────────

@app.post(
    "/api/progress/log",
    response_model=ProgressLogResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Log daily health and nutrition progress",
    tags=["Progress Tracking"]
)
def log_progress_endpoint(payload: ProgressLogCreate, db: Session = Depends(get_db)):
    # Check for duplicate date
    existing = db.query(ProgressLog).filter(ProgressLog.date == payload.date).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Progress log already exists for date '{payload.date}'."
        )

    log_item = ProgressLog(
        date=payload.date,
        goal=payload.goal.strip(),
        calories=payload.calories,
        protein=payload.protein,
        fiber=payload.fiber,
        health_score=payload.health_score,
        notes=payload.notes.strip() if payload.notes else None
    )

    db.add(log_item)
    try:
        db.commit()
        db.refresh(log_item)
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database commit failed: {e}"
        )

    return ProgressLogResponse(
        id=log_item.id,
        date=log_item.date,
        goal=log_item.goal,
        calories=log_item.calories,
        protein=log_item.protein,
        fiber=log_item.fiber,
        health_score=log_item.health_score,
        notes=log_item.notes,
        created_at=log_item.created_at.isoformat() if log_item.created_at else ""
    )


@app.get(
    "/api/progress",
    response_model=List[ProgressLogResponse],
    status_code=status.HTTP_200_OK,
    summary="Retrieve progress logs with optional filters",
    tags=["Progress Tracking"]
)
def get_progress_endpoint(
    start_date: Optional[str] = Query(None, pattern=r"^\d{4}-\d{2}-\d{2}$", description="Filter from date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, pattern=r"^\d{4}-\d{2}-\d{2}$", description="Filter to date (YYYY-MM-DD)"),
    goal: Optional[str] = Query(None, description="Filter by goal name"),
    db: Session = Depends(get_db)
):
    query = db.query(ProgressLog)

    if start_date:
        query = query.filter(ProgressLog.date >= start_date)
    if end_date:
        query = query.filter(ProgressLog.date <= end_date)
    if goal:
        query = query.filter(ProgressLog.goal.ilike(f"%{goal.strip()}%"))

    # Sort chronological ascending
    logs = query.order_by(ProgressLog.date.asc()).all()

    return [
        ProgressLogResponse(
            id=item.id,
            date=item.date,
            goal=item.goal,
            calories=item.calories,
            protein=item.protein,
            fiber=item.fiber,
            health_score=item.health_score,
            notes=item.notes,
            created_at=item.created_at.isoformat() if item.created_at else ""
        )
        for item in logs
    ]


@app.get(
    "/api/progress/summary",
    response_model=ProgressSummaryResponse,
    status_code=status.HTTP_200_OK,
    summary="Get aggregated progress summary and trends",
    tags=["Progress Tracking"]
)
def get_progress_summary_endpoint(db: Session = Depends(get_db)):
    logs = db.query(ProgressLog).order_by(ProgressLog.date.asc()).all()

    if not logs:
        return ProgressSummaryResponse(
            total_logged_days=0,
            average_calories=0.0,
            average_protein=0.0,
            average_fiber=0.0,
            average_health_score=0.0,
            trend="Stable"
        )

    total_days = len(logs)
    avg_cal = sum(item.calories for item in logs) / total_days
    avg_pro = sum(item.protein for item in logs) / total_days
    avg_fib = sum(item.fiber for item in logs) / total_days
    avg_hs  = sum(item.health_score for item in logs) / total_days

    # Calculate trend using health_score linear regression slope
    if total_days < 2:
        trend = "Stable"
    else:
        # X is time index: 0, 1, 2, ..., N-1
        # Y is health_score
        N = total_days
        sum_x = sum(i for i in range(N))
        sum_y = sum(item.health_score for item in logs)
        sum_xx = sum(i * i for i in range(N))
        sum_xy = sum(i * item.health_score for i, item in enumerate(logs))

        denom = N * sum_xx - sum_x * sum_x
        if denom == 0:
            trend = "Stable"
        else:
            slope = (N * sum_xy - sum_x * sum_y) / denom
            if slope > 0.05:
                trend = "Improving"
            elif slope < -0.05:
                trend = "Declining"
            else:
                trend = "Stable"

    return ProgressSummaryResponse(
        total_logged_days=total_days,
        average_calories=round(avg_cal, 1),
        average_protein=round(avg_pro, 1),
        average_fiber=round(avg_fib, 1),
        average_health_score=round(avg_hs, 1),
        trend=trend
    )


# ── 9. HYDRATION TRACKING ENDPOINTS ──────────────────────────────────────

@app.post(
    "/api/hydration/log",
    response_model=HydrationLogResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Log water intake or update hydration target/reminder settings",
    tags=["Hydration Tracking"]
)
def log_hydration_endpoint(payload: HydrationLogCreate, db: Session = Depends(get_db)):
    log_date = payload.date.strip() if payload.date else datetime.now().date().strftime("%Y-%m-%d")
    
    # Resolve target_ml and reminder_interval_mins
    target_ml = payload.target_ml
    reminder_interval = payload.reminder_interval_mins
    
    # If not provided, try to copy over preferences from the latest log
    if target_ml is None or reminder_interval is None:
        latest_log = db.query(HydrationLog).order_by(HydrationLog.date.desc(), HydrationLog.id.desc()).first()
        if latest_log:
            if target_ml is None:
                target_ml = latest_log.target_ml
            if reminder_interval is None:
                reminder_interval = latest_log.reminder_interval_mins
        
        # Fallbacks to defaults
        if target_ml is None:
            target_ml = 2000.0
        if reminder_interval is None:
            reminder_interval = 60

    log_item = HydrationLog(
        date=log_date,
        amount_ml=payload.amount_ml,
        target_ml=target_ml,
        reminder_interval_mins=reminder_interval
    )

    db.add(log_item)
    try:
        db.commit()
        db.refresh(log_item)
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database commit failed: {e}"
        )

    return HydrationLogResponse(
        id=log_item.id,
        date=log_item.date,
        amount_ml=log_item.amount_ml,
        target_ml=log_item.target_ml,
        reminder_interval_mins=log_item.reminder_interval_mins,
        created_at=log_item.created_at.isoformat() if log_item.created_at else ""
    )


@app.get(
    "/api/hydration/today",
    response_model=HydrationTodayResponse,
    status_code=status.HTTP_200_OK,
    summary="Get today's hydration metrics and history log",
    tags=["Hydration Tracking"]
)
def get_hydration_today_endpoint(
    date: Optional[str] = Query(None, pattern=r"^\d{4}-\d{2}-\d{2}$", description="Optional date YYYY-MM-DD"),
    db: Session = Depends(get_db)
):
    target_date = date.strip() if date else datetime.now().date().strftime("%Y-%m-%d")
    
    # Query today's logs
    logs = db.query(HydrationLog).filter(HydrationLog.date == target_date).order_by(HydrationLog.created_at.asc()).all()
    
    consumed_ml = sum(item.amount_ml for item in logs)
    
    # Target and reminder preferences resolution
    if logs:
        target_ml = logs[-1].target_ml
        reminder_interval = logs[-1].reminder_interval_mins
    else:
        # Try to find latest log in entire DB for previous dates
        latest_prev = db.query(HydrationLog).filter(HydrationLog.date < target_date).order_by(HydrationLog.date.desc(), HydrationLog.id.desc()).first()
        if latest_prev:
            target_ml = latest_prev.target_ml
            reminder_interval = latest_prev.reminder_interval_mins
        else:
            # Try to find any log (even future)
            any_log = db.query(HydrationLog).order_by(HydrationLog.id.desc()).first()
            if any_log:
                target_ml = any_log.target_ml
                reminder_interval = any_log.reminder_interval_mins
            else:
                target_ml = 2000.0
                reminder_interval = 60

    remaining_ml = max(0.0, target_ml - consumed_ml)
    completion_pct = round((consumed_ml / target_ml) * 100.0, 1) if target_ml > 0 else 0.0
    
    if completion_pct < 50.0:
        status_str = "Dehydrated"
    elif completion_pct < 100.0:
        status_str = "Moderately Hydrated"
    else:
        status_str = "Well Hydrated"

    return HydrationTodayResponse(
        date=target_date,
        target_ml=target_ml,
        consumed_ml=consumed_ml,
        remaining_ml=remaining_ml,
        completion_pct=completion_pct,
        hydration_status=status_str,
        reminder_interval_mins=reminder_interval,
        logs=[
            HydrationLogResponse(
                id=item.id,
                date=item.date,
                amount_ml=item.amount_ml,
                target_ml=item.target_ml,
                reminder_interval_mins=item.reminder_interval_mins,
                created_at=item.created_at.isoformat() if item.created_at else ""
            )
            for item in logs
        ]
    )


@app.get(
    "/api/hydration/summary",
    response_model=HydrationSummaryResponse,
    status_code=status.HTTP_200_OK,
    summary="Get aggregated statistics and trends for hydration history",
    tags=["Hydration Tracking"]
)
def get_hydration_summary_endpoint(db: Session = Depends(get_db)):
    all_logs = db.query(HydrationLog).order_by(HydrationLog.date.asc(), HydrationLog.created_at.asc()).all()
    
    if not all_logs:
        return HydrationSummaryResponse(
            total_days_logged=0,
            average_daily_intake=0.0,
            average_daily_target=2000.0,
            average_completion_pct=0.0,
            history=[]
        )
    
    # Group logs by date
    logs_by_date = {}
    for log in all_logs:
        if log.date not in logs_by_date:
            logs_by_date[log.date] = []
        logs_by_date[log.date].append(log)
        
    history_summaries = []
    total_intake_sum = 0.0
    total_target_sum = 0.0
    total_completion_pct_sum = 0.0
    
    # Calculate daily summaries
    for d_str in sorted(logs_by_date.keys()):
        day_logs = logs_by_date[d_str]
        day_consumed = sum(item.amount_ml for item in day_logs)
        day_target = day_logs[-1].target_ml
        day_pct = round((day_consumed / day_target) * 100.0, 1) if day_target > 0 else 0.0
        
        if day_pct < 50.0:
            day_status = "Dehydrated"
        elif day_pct < 100.0:
            day_status = "Moderately Hydrated"
        else:
            day_status = "Well Hydrated"
            
        history_summaries.append(
            HydrationDailySummary(
                date=d_str,
                consumed_ml=day_consumed,
                target_ml=day_target,
                completion_pct=day_pct,
                hydration_status=day_status
            )
        )
        total_intake_sum += day_consumed
        total_target_sum += day_target
        total_completion_pct_sum += day_pct
        
    num_days = len(logs_by_date)
    avg_intake = total_intake_sum / num_days
    avg_target = total_target_sum / num_days
    avg_pct = total_completion_pct_sum / num_days
    
    return HydrationSummaryResponse(
        total_days_logged=num_days,
        average_daily_intake=round(avg_intake, 1),
        average_daily_target=round(avg_target, 1),
        average_completion_pct=round(avg_pct, 1),
        history=history_summaries
    )


