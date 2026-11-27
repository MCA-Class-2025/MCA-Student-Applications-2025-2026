from fastapi import FastAPI, HTTPException, Query
from typing import Optional
from pathlib import Path
import csv
import math

app = FastAPI(
    title="FixAI Professional Services API",
    description="Custom REST API used by FixAI to find household repair professionals.",
    version="1.0.0"
)

CSV_FILE = Path(__file__).parent / "professionals.csv"


def load_data():
    if not CSV_FILE.exists():
        raise FileNotFoundError(f"professionals.csv not found at {CSV_FILE}")
    with open(CSV_FILE, "r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def clean(row):
    return {
        "id": int(row["id"]),
        "name": row["name"],
        "service_type": row["service_type"],
        "city": row["city"],
        "area": row["area"],
        "phone": row["phone"],
        "rating": float(row["rating"]),
        "experience": int(row["experience"]),
        "price_range": row["price_range"],
        "latitude": float(row["latitude"]),
        "longitude": float(row["longitude"])
    }


def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp/2)**2 + math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))


@app.get("/")
def root():
    return {
        "message": "FixAI Professional Services API is running",
        "records": len(load_data()),
        "docs": "/docs"
    }


@app.get("/health")
def health():
    return {"status": "healthy", "records": len(load_data())}


@app.get("/professionals")
def professionals(
    service_type: Optional[str] = None,
    city: Optional[str] = None,
    area: Optional[str] = None,
    min_rating: Optional[float] = Query(None, ge=0, le=5),
    limit: int = Query(20, ge=1, le=100)
):
    data = [clean(x) for x in load_data()]

    if service_type:
        data = [x for x in data if x["service_type"].lower() == service_type.strip().lower()]
    if city:
        data = [x for x in data if x["city"].lower() == city.strip().lower()]
    if area:
        data = [x for x in data if x["area"].lower() == area.strip().lower()]
    if min_rating is not None:
        data = [x for x in data if x["rating"] >= min_rating]

    data.sort(key=lambda x: (-x["rating"], -x["experience"]))
    return {"count": len(data), "professionals": data[:limit]}


@app.get("/professionals/nearby")
def nearby(
    latitude: float,
    longitude: float,
    service_type: Optional[str] = None,
    radius_km: float = Query(15, gt=0, le=100),
    limit: int = Query(10, ge=1, le=50)
):
    data = [clean(x) for x in load_data()]

    if service_type:
        data = [x for x in data if x["service_type"].lower() == service_type.strip().lower()]

    for x in data:
        x["distance_km"] = round(
            haversine(latitude, longitude, x["latitude"], x["longitude"]), 2
        )

    data = [x for x in data if x["distance_km"] <= radius_km]
    data.sort(key=lambda x: (x["distance_km"], -x["rating"]))

    return {"count": len(data), "professionals": data[:limit]}


@app.get("/professionals/{professional_id}")
def professional(professional_id: int):
    for row in load_data():
        item = clean(row)
        if item["id"] == professional_id:
            return item
    raise HTTPException(status_code=404, detail="Professional not found")
