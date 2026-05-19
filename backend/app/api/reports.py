from fastapi import APIRouter, Response, Query
from app.services.report_service import generate_weekly_report

router = APIRouter(prefix="/reports", tags=["reports"])

@router.get("/weekly")
def get_weekly_report(
    week_start: str = Query(..., description="Start date of the week in YYYY-MM-DD"),
    sppg_name: str = Query("SPPG_Pusat", description="Name of the SPPG")
):
    # Generate the PDF bytes
    pdf_bytes = generate_weekly_report(week_start, sppg_name)
    
    # Format filename securely
    safe_name = sppg_name.replace(" ", "_").replace("/", "_")
    filename = f"laporan_mingguan_{safe_name}_{week_start}.pdf"
    
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"'
        }
    )