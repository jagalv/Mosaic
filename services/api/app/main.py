"""FastAPI application entrypoint.

Run locally with:
    uvicorn app.main:app --reload --port 8000
(from the services/api directory, with the venv active)
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.routers import company, health

settings = get_settings()

app = FastAPI(title="Mosaic API", version="0.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(company.router)


@app.get("/")
def root() -> dict:
    retur