from fastapi import FastAPI
from pydantic import BaseModel
import pandas as pd
import math
from typing import Optional


# =========================================================
# APP INITIALIZATION
# =========================================================

app = FastAPI(
    title="FixAI Maharashtra Services API",
    description="Local household repair and professional services API",
    version="1.0.0"
)


# =========================================================
# LOAD SERVICE DATA
# =========================================================

DATA_FILE = "api/service_data.csv"

services_df = pd.read_csv(DATA_FILE)


# =========================================================
# RESPONSE MODEL
# =========================================================

class Service(BaseModel):

    id: int
    name: str
    service_type: str
    city: str
    area: str
    phone: str
    rating: float
    experience: int
    price_range: str
    latitude: float
    longitude: float


# =========================================================
# DISTANCE CALCULATION
# =========================================================

def calculate_distance(
    lat1,
    lon1,
    lat2,
    lon2
):

    R = 6371.0

    lat1 = math.radians(lat1)
    lat2 = math.radians(lat2)

    delta_lat = math.radians(
        lat2 - lat1
    )

    delta_lon = math.radians(
        lon2 - lon1
    )

    a = (
        math.sin(delta_lat / 2) ** 2
        +
        math.cos(lat1)
        *
        math.cos(lat2)
        *
        math.sin(delta_lon / 2) ** 2
    )

    c = 2 * math.atan2(
        math.sqrt(a),
        math.sqrt(1 - a)
    )

    return R * c


# =========================================================
# HOME
# =========================================================

@app.get("/")
def home():

    return {

        "message":
            "FixAI Maharashtra Services API is running",

        "version":
            "1.0.0",

        "total_services":
            len(services_df)
    }


# =========================================================
# GET ALL SERVICES
# =========================================================

@app.get("/api/services")
def get_services(
    city: Optional[str] = None,
    service: Optional[str] = None,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None
):

    result = services_df.copy()


    # =====================================================
    # CITY FILTER
    # =====================================================

    if city:

        result = result[
            result["city"].str.lower()
            == city.lower()
        ]


    # =====================================================
    # SERVICE FILTER
    # =====================================================

    if service:

        result = result[
            result["service_type"].str.lower()
            == service.lower()
        ]


    # =====================================================
    # DISTANCE
    # =====================================================

    if latitude is not None and longitude is not None:

        result["distance_km"] = result.apply(

            lambda row: calculate_distance(

                latitude,
                longitude,

                row["latitude"],
                row["longitude"]

            ),

            axis=1
        )

        result = result.sort_values(
            by="distance_km"
        )


    return result.to_dict(
        orient="records"
    )

# =========================================================
# GET NEARBY SERVICES
# =========================================================

@app.get(
    "/api/services/nearby",
    response_model=list[Service]
)

def get_nearby_services(

    latitude: float,

    longitude: float,

    service: Optional[str] = None,

    radius: float = 10

):

    result = services_df.copy()


    # -----------------------------------------------------
    # SERVICE FILTER
    # -----------------------------------------------------

    if service:

        result = result[
            result["service_type"]
            .astype(str)
            .str.lower()
            ==
            service.lower()
        ]


    # -----------------------------------------------------
    # CALCULATE DISTANCE
    # -----------------------------------------------------

    result["distance_km"] = result.apply(

        lambda row:

        calculate_distance(

            latitude,

            longitude,

            float(row["latitude"]),

            float(row["longitude"])

        ),

        axis=1
    )


    # -----------------------------------------------------
    # FILTER BY RADIUS
    # -----------------------------------------------------

    result = result[
        result["distance_km"]
        <=
        radius
    ]


    # -----------------------------------------------------
    # SORT BY DISTANCE
    # -----------------------------------------------------

    result = result.sort_values(
        by="distance_km"
    )


    # -----------------------------------------------------
    # REMOVE DISTANCE FOR RESPONSE MODEL
    # -----------------------------------------------------

    result = result.drop(
        columns=["distance_km"]
    )


    return result.to_dict(
        orient="records"
    )