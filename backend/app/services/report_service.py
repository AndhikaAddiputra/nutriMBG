from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, List

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.entities import MenuAnalysis, Recommendation
from app.utils.pdf_generator import create_weekly_report_pdf


def _get_status(score: float) -> str:
    if score >= 80:
        return "Cukup"
    if score >= 60:
        return "Perlu Perhatian"
    return "Defisien"


async def generate_weekly_report(
    db: AsyncSession,
    week_start_str: str,
    sppg_name: str,
    district: str = "",
) -> bytes:
    start_date = datetime.strptime(week_start_str, "%Y-%m-%d")
    end_date = start_date + timedelta(days=7)

    result = await db.execute(
        select(MenuAnalysis)
        .where(MenuAnalysis.created_at >= start_date, MenuAnalysis.created_at < end_date)
        .order_by(MenuAnalysis.created_at.asc())
    )
    analyses = result.scalars().all()

    analysis_ids = [a.id for a in analyses]

    rec_result = await db.execute(
        select(Recommendation).where(Recommendation.analysis_id.in_(analysis_ids))
    )
    recommendations_rows = rec_result.scalars().all()

    daily_buckets: Dict[str, List[dict]] = defaultdict(list)
    for a in analyses:
        day_key = a.created_at.strftime("%Y-%m-%d") if hasattr(a.created_at, "strftime") else str(a.created_at)[:10]
        daily_buckets[day_key].append(a)

    daily_menus = []
    for i in range(7):
        current = start_date + timedelta(days=i)
        day_key = current.strftime("%Y-%m-%d")
        day_analyses = daily_buckets.get(day_key, [])

        if day_analyses:
            scores = [a.score_total for a in day_analyses]
            avg_score = sum(scores) / len(scores)
            menu_texts = [a.menu_text for a in day_analyses]
            menu_display = "; ".join(menu_texts[:3])
            if len(menu_texts) > 3:
                menu_display += f" (+{len(menu_texts)-3} lagi)"
        else:
            avg_score = 0.0
            menu_display = "-"

        daily_menus.append({
            "date": day_key,
            "menu": menu_display,
            "score": round(avg_score, 1),
            "status": _get_status(avg_score),
        })

    deficiency_counts: Dict[str, int] = defaultdict(int)
    for a in analyses:
        if a.score_total < 60:
            deficiency_counts["Skor Komposit"] += 1

    sorted_deficiencies = sorted(deficiency_counts.items(), key=lambda x: -x[1])
    top_deficiencies = [f"{name} (Terjadi pada {count} hari)" for name, count in sorted_deficiencies[:3]]

    rec_texts = [r.notes for r in recommendations_rows[:3]]
    if not rec_texts:
        rec_texts = [
            "Tambahkan porsi sayuran hijau gelap seperti bayam untuk meningkatkan Zat Besi.",
            "Ganti camilan manis dengan buah jeruk/pepaya untuk asupan Vitamin C.",
            "Sertakan susu atau olahan kedelai (tahu/tempe) sebagai sumber Kalsium.",
        ]

    period = f"{week_start_str} s/d {(start_date + timedelta(days=6)).strftime('%Y-%m-%d')}"

    report_data = {
        "sppg_name": sppg_name,
        "district": district or "Jakarta Selatan",
        "period": period,
        "daily_menus": daily_menus,
        "top_deficiencies": top_deficiencies or [
            "Belum ada data defisiensi yang tercatat.",
        ],
        "recommendations": rec_texts,
    }

    return create_weekly_report_pdf(report_data)
