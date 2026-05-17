from datetime import datetime, timedelta
from app.utils.pdf_generator import create_weekly_report_pdf

def get_status(score: int) -> str:
    if score >= 80: return "Cukup"
    if score >= 60: return "Perlu Perhatian"
    return "Defisien"

def generate_weekly_report(week_start_str: str, sppg_name: str) -> bytes:
    # 1. TODO: Fetch actual data from DB using week_start_str
    # Here we mock the data format that pdf_generator expects
    start_date = datetime.strptime(week_start_str, "%Y-%m-%d")
    
    daily_menus = []
    # Mocking 7 days of data
    for i in range(7):
        current = start_date + timedelta(days=i)
        score = 85 - (i * 5) # Mock declining score
        daily_menus.append({
            "date": current.strftime("%Y-%m-%d"),
            "menu": f"Menu Variasi {i+1}",
            "score": score,
            "status": get_status(score)
        })

    report_data = {
        "sppg_name": sppg_name,
        "district": "Jakarta Selatan",
        "period": f"{week_start_str} s/d {(start_date + timedelta(days=6)).strftime('%Y-%m-%d')}",
        "daily_menus": daily_menus,
        "top_deficiencies": [
            "Kalsium (Terjadi pada 4 hari)",
            "Vitamin C (Terjadi pada 3 hari)",
            "Zat Besi (Terjadi pada 2 hari)"
        ],
        "recommendations": [
            "Tambahkan porsi sayuran hijau gelap seperti bayam untuk meningkatkan Zat Besi.",
            "Ganti camilan manis dengan buah jeruk/pepaya untuk asupan Vitamin C.",
            "Sertakan susu atau olahan kedelai (tahu/tempe) sebagai sumber Kalsium."
        ]
    }

    # 2. Generate PDF bytes
    return create_weekly_report_pdf(report_data)