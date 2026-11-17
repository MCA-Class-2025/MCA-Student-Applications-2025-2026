from fastapi import Request, status
from fastapi.responses import JSONResponse

class PrepGeniusException(Exception):
    def __init__(self, message: str, status_code: int = status.HTTP_400_BAD_REQUEST, details: dict = None):
        self.message = message
        self.status_code = status_code
        self.details = details or {}

async def prepgenius_exception_handler(request: Request, exc: PrepGeniusException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "message": exc.message,
                "details": exc.details,
                "path": str(request.url.path)
            }
        }
    )

async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error": {
                "message": "An unexpected internal server error occurred.",
                "details": str(exc),
                "path": str(request.url.path)
            }
        }
    )
