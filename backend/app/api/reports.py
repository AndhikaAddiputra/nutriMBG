from typing import Optional

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import AsyncSessionLocal
from app.services.report_service import generate_weekly_report

router = APIRouter(prefix="/reports", tags=["reports"])


async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session


@router.get("/weekly")
async def get_weekly_report(
    week_start: str = Query(..., description="Start date of the week in YYYY-MM-DD"),
    sppg_name: str = Query("SPPG_Pusat", description="Name of the SPPG"),
    district: Optional[str] = Query(None, description="District name"),
    db: AsyncSession = Depends(get_db),
):
    pdf_bytes = await generate_weekly_report(db, week_start, sppg_name, district or "")

    safe_name = sppg_name.replace(" ", "_").replace("/", "_")
    filename = f"laporan_mingguan_{safe_name}_{week_start}.pdf"

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"'
        },
    )
