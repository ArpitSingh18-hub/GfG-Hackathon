import os
import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.api.dashboard_api import router as dashboard_router
from backend.api.upload_api import router as upload_router


# Create app first
app = FastAPI(title="Conversational BI Dashboard API")


from backend.utils.exceptions import BaseAPIException
from backend.utils.response_formatter import format_error

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    status_code = 500
    detail = str(exc)
    
    if isinstance(exc, BaseAPIException):
        status_code = exc.status_code
        detail = exc.detail
        
    return JSONResponse(
        status_code=status_code,
        content=format_error(detail)
    )


# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Routers
app.include_router(dashboard_router, prefix="/api")
app.include_router(upload_router, prefix="/api")


# Root endpoint
@app.get("/")
def read_root():
    return {"message": "Welcome to the Conversational BI Dashboard API."}


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)