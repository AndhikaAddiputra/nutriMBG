from fastapi import FastAPI

from app.api.ai import router as ai_router
from app.api.health import router as health_router
from app.api.history import router as history_router
from app.api.reference import router as reference_router
from app.api.reports import router as reports_router
from app.core.settings import settings


app = FastAPI(title=settings.app_name)

app.include_router(health_router)
app.include_router(reference_router)
app.include_router(ai_router)
app.include_router(reports_router)
app.include_router(history_router)

@app.get("/")
def root() -> dict:
    return {"name": settings.app_name, "status": "ok"}
