from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.api.dashboard_api import router as dashboard_router
from backend.api.upload_api import router as upload_router


# Create app first
app = FastAPI(title="Conversational BI Dashboard API")


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):

    return JSONResponse(
        status_code=500,
        content={"error": str(exc)}
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