from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from services.travel_planner import create_travel_plan
from services.travel_data_service import get_destination_context


# ========================================
# Create FastAPI application
# ========================================

app = FastAPI(
    title="AI Travel Planner API",
    description="Backend API for AI Travel Planner",
    version="1.0.0"
)


# ========================================
# CORS
# ========================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ========================================
# Request Model
# ========================================

class TravelRequest(BaseModel):

    destination: str
    days: int = 3
    budget: float = 80000


# ========================================
# Home
# ========================================

@app.get("/")
def home():

    return {
        "message": "AI Travel Planner API is running!"
    }


# ========================================
# Generate Travel Plan
# ========================================

@app.post("/plan")
def generate_plan(request: TravelRequest):

    # Get project data
    context = get_destination_context(
        request.destination
    )

    # If destination doesn't exist
    if context is None:

        return {
            "destination": request.destination,
            "days": request.days,
            "budget": request.budget,
            "travel_plan": (
                f"Sorry, no travel data was found "
                f"for {request.destination}."
            ),
            "context": None
        }

    # Generate AI plan
    travel_plan = create_travel_plan(
        destination=request.destination,
        days=request.days,
        budget=request.budget
    )

    return {
        "destination": context["destination"],
        "days": request.days,
        "budget": request.budget,

        "travel_plan": travel_plan,

        # Structured project data
        "context": context
    }