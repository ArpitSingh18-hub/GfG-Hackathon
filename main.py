from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.api.dashboard_api import router as dashboard_router
from backend.api.upload_api import router as upload_router

app = FastAPI(title="Conversational BI Dashboard API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(dashboard_router, prefix="/api")
app.include_router(upload_router, prefix="/api")

@app.get("/")
def read_root():
    return {"message": "Welcome to the Conversational BI Dashboard API."}
