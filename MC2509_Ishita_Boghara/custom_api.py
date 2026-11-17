from fastapi import FastAPI, HTTPException, Security
from fastapi.security import APIKeyHeader
import os
from external_apis import BookMuseFusion

app = FastAPI(
    title="BookMuse Custom Fusion API",
    description="Combines multiple book information APIs",
    version="1.0"
)

fusion = BookMuseFusion()

API_KEY = os.getenv("BOOKMUSE_API_KEY", "bookmuse-demo-key-2026")

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def verify_api_key(api_key: str = Security(api_key_header)):
    if api_key != API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API Key")
    return api_key

@app.get("/")
def home():
    return {
        "message": "BookMuse Custom API is running",
        "version": "1.0"
    }


@app.get("/api/book/{title}")
def get_book(title: str, author: str = "", api_key: str = Security(verify_api_key)):
    result = fusion.get_book_intelligence(title, author)

    successful = [
    name for name in [
        "wikipedia",
        "open_library",
        "gutendex",
        "wikidata",
        "internet_archive"
    ]
        if result[name].get("success")
    ]

    if not successful:
        raise HTTPException(
            status_code=404,
            detail="Book not found in available sources"
        )

    return {
        "success": True,
        "book": title,
        "sources_used": successful,
        "source_count": len(successful),
        "data": result
    }