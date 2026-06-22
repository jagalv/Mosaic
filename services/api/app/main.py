"""FastAPI application entrypoint.

Run locally with:
    uvicorn app.main:app --reload --port 8000
(from the services/api directory, with the venv active)
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.routers import ask, auth, company, filing, health, notes, watchlists

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
app.include_router(filing.router)
app.include_router(ask.router)
app.include_router(auth.router)
app.include_router(watchlists.router)
app.include_router(notes.router)


@app.get("/")
def root() -> dict:
    return {"service": "mosaic-api", "status": "ok"}
