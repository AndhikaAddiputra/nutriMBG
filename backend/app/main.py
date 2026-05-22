from fastapi import FastAPI

from app.api.admin.food_items import router as admin_food_router
from app.api.admin.nutrition_akg import router as admin_akg_router
from app.api.ai import router as ai_router
from app.api.health import router as health_router
from app.api.history import router as history_router
from app.api.menu import router as menu_router
from app.api.reference import router as reference_router
from app.api.reports import router as reports_router
from app.core.settings import settings


app = FastAPI(title=settings.app_name)

app.include_router(health_router)
app.include_router(reference_router)
app.include_router(ai_router, prefix="/api/v1/ai")
app.include_router(menu_router, prefix="/api/menu")

app.include_router(ai_router)
app.include_router(reports_router)
app.include_router(history_router)
app.include_router(admin_food_router)
app.include_router(admin_akg_router)

@app.get("/")
def root() -> dict:
    return {"name": settings.app_name, "status": "ok"}
