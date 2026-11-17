from fastapi import APIRouter, HTTPException

from app.schemas.ml_schema import (
    GroceryPredictionRequest,
    ElectronicsPredictionRequest
)

from app.services.ml_prediction_service import (
    MLPredictionService
)


router = APIRouter(
    prefix="/api/ml",
    tags=["Machine Learning"]
)


# ============================================================
# GROCERY PRICE PREDICTION
# ============================================================

@router.post("/predict/grocery")
async def predict_grocery_price(
    request: GroceryPredictionRequest
):

    try:

        result = (
            MLPredictionService
            .predict_grocery(
                request
            )
        )

        return result

    except FileNotFoundError as error:

        raise HTTPException(
            status_code=404,
            detail=str(error)
        )

    except Exception as error:

        print(
            "GROCERY ML ERROR:",
            repr(error)
        )

        raise HTTPException(
            status_code=500,
            detail=str(error)
        )


# ============================================================
# ELECTRONICS PRICE PREDICTION
# ============================================================

@router.post("/predict/electronics")
async def predict_electronics_price(
    request: ElectronicsPredictionRequest
):

    try:

        result = (
            MLPredictionService
            .predict_electronics(
                request
            )
        )

        return result

    except FileNotFoundError as error:

        raise HTTPException(
            status_code=404,
            detail=str(error)
        )

    except Exception as error:

        print(
            "ELECTRONICS ML ERROR:",
            repr(error)
        )

        raise HTTPException(
            status_code=500,
            detail=str(error)
        )