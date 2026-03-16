from typing import Any, Optional, List, Dict
from pydantic import BaseModel

class ApiResponse(BaseModel):
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    meta: Optional[Dict[str, Any]] = None

def format_success(data: Any, meta: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    return {
        "success": True,
        "data": data,
        "error": None,
        "meta": meta
    }

def format_error(error_message: str, data: Optional[Any] = None) -> Dict[str, Any]:
    return {
        "success": False,
        "data": data,
        "error": error_message,
        "meta": None
    }
