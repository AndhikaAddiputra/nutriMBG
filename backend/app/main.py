from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.admin.food_items import router as admin_food_router
from app.api.admin.nutrition_akg import router as admin_akg_router
from app.api.admin.stats import router as admin_stats_router
from app.api.admin.users import router as admin_users_router
from app.api.ai import router as ai_router
from app.api.auth import router as auth_router
from app.api.health import router as health_router
from app.api.history import router as history_router
from app.api.reference import router as reference_router
from app.api.reports import router as reports_router
from sqlalchemy import text as sa_text

from app.core.settings import settings
from app.db.session import engine


app = FastAPI(title=settings.app_name)


@app.on_event("startup")
async def migrate_rate_limit_logs() -> None:
    async with engine.connect() as conn:
        await conn.execute(
            sa_text("""
                ALTER TABLE rate_limit_logs
                ADD COLUMN IF NOT EXISTS scope VARCHAR(20) NOT NULL DEFAULT 'global'
            """)
        )
        await conn.execute(
            sa_text("""
                DO $$
                BEGIN
                    IF NOT EXISTS (
                        SELECT 1 FROM pg_constraint
                        WHERE conname = 'uq_rate_limit_logs_user_scope_date'
                    ) THEN
                        ALTER TABLE rate_limit_logs
                        ADD CONSTRAINT uq_rate_limit_logs_user_scope_date
                        UNIQUE (user_id, scope, rate_date);
                    END IF;
                END $$;
            """)
        )
        await conn.commit()

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(reference_router)
app.include_router(auth_router)
app.include_router(ai_router, prefix="/api/v1/ai")
app.include_router(reports_router)
app.include_router(history_router)
app.include_router(admin_food_router)
app.include_router(admin_akg_router)
app.include_router(admin_stats_router)
app.include_router(admin_users_router)

@app.get("/")
def root() -> dict:
    return {"name": settings.app_name, "status": "ok"}
