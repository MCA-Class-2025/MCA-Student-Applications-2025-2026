from pydantic import BaseModel
from typing import Dict, Any

class SystemHealthResponse(BaseModel):
    status: str
    app_name: str
    version: str
    database_connected: bool
    ollama_connected: bool
    ollama_model: str
    system_info: Dict[str, Any]
