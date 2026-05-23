import asyncio
from datetime import datetime, timedelta, timezone
from pathlib import Path
import sys

from sqlalchemy import select

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.db.session import AsyncSessionLocal
from app.models.entities import FoodItem, MenuAnalysis, MenuIngredient, Recommendation, User


# Day 0 = 7 days ago, Day 6 = today
# Varying scores to make the trend chart interesting
DAILY_MENUS = [
    {
        "menu_text": "Nasi putih, ayam goreng, tumis kangkung, pisang",
        "score_total": 72.0,
        "ingredients": [
            ("Nasi Putih", 150.0),
            ("Ayam Goreng", 80.0),
            ("Kangkung", 60.0),
            ("Pisang", 90.0),
        ],
        "recommendation": "Tambah tahu 50g untuk protein nabati tambahan.",
        "projected_score": 80.0,
    },
    {
        "menu_text": "Nasi putih, tempe goreng, bayam bening",
        "score_total": 68.0,
        "ingredients": [
            ("Nasi Putih", 150.0),
            ("Tempe", 75.0),
            ("Bayam", 70.0),
        ],
        "recommendation": "Tambahkan lauk hewani seperti telur untuk protein lengkap.",
        "projected_score": 76.0,
    },
    {
        "menu_text": "Nasi putih, telur dadar, wortel rebus",
        "score_total": 55.0,
        "ingredients": [
            ("Nasi Putih", 120.0),
            ("Telur Ayam", 60.0),
            ("Wortel", 50.0),
        ],
        "recommendation": "Kurangi porsi nasi, tambah sayur hijau dan sumber zat besi.",
        "projected_score": 68.0,
    },
    {
        "menu_text": "Nasi putih, ikan lele goreng, tumis bayam, tempe",
        "score_total": 62.0,
        "ingredients": [
            ("Nasi Putih", 130.0),
            ("Ikan Lele", 90.0),
            ("Bayam", 65.0),
            ("Tempe", 40.0),
        ],
        "recommendation": "Tambah buah pisang sebagai pencuci mulut untuk serat tambahan.",
        "projected_score": 72.0,
    },
    {
        "menu_text": "Nasi putih, ayam goreng, wortel, pisang, tahu",
        "score_total": 78.0,
        "ingredients": [
            ("Nasi Putih", 140.0),
            ("Ayam Goreng", 85.0),
            ("Wortel", 55.0),
            ("Pisang", 100.0),
            ("Tahu", 50.0),
        ],
        "recommendation": "Ganti nasi putih dengan nasi merah sesekali untuk serat lebih.",
        "projected_score": 86.0,
    },
    {
        "menu_text": "Nasi putih, kangkung tumis, pisang goreng",
        "score_total": 45.0,
        "ingredients": [
            ("Nasi Putih", 200.0),
            ("Kangkung", 50.0),
            ("Pisang", 80.0),
        ],
        "recommendation": "Kekurangan protein dan lemak, tambahkan telur atau tempe pada menu.",
        "projected_score": 62.0,
    },
    {
        "menu_text": "Nasi putih, lele goreng, tumis kangkung, tahu",
        "score_total": 71.0,
        "ingredients": [
            ("Nasi Putih", 150.0),
            ("Ikan Lele", 85.0),
            ("Kangkung", 70.0),
            ("Tahu", 50.0),
        ],
        "recommendation": "Tambahkan buah segar seperti pepaya untuk vitamin A tambahan.",
        "projected_score": 79.0,
    },
    {
        "menu_text": "Nasi putih, tempe orek, bayam, wortel, pisang",
        "score_total": 74.0,
        "ingredients": [
            ("Nasi Putih", 130.0),
            ("Tempe", 60.0),
            ("Bayam", 60.0),
            ("Wortel", 45.0),
            ("Pisang", 80.0),
        ],
        "recommendation": "Menu sudah cukup baik, pertahankan variasi sayur dan lauk.",
        "projected_score": 82.0,
    },
    {
        "menu_text": "Nasi putih, telur ceplok, tumis kangkung",
        "score_total": 60.0,
        "ingredients": [
            ("Nasi Putih", 150.0),
            ("Telur Ayam", 55.0),
            ("Kangkung", 65.0),
        ],
        "recommendation": "Kurang sumber karbohidrat kompleks, tambahkan kacang-kacangan.",
        "projected_score": 70.0,
    },
    {
        "menu_text": "Nasi putih, ayam goreng, bayam, tahu, wortel",
        "score_total": 76.0,
        "ingredients": [
            ("Nasi Putih", 140.0),
            ("Ayam Goreng", 80.0),
            ("Bayam", 60.0),
            ("Tahu", 45.0),
            ("Wortel", 40.0),
        ],
        "recommendation": "Menu bergizi seimbang, tambahkan buah untuk vitamin tambahan.",
        "projected_score": 84.0,
    },
    {
        "menu_text": "Nasi putih, tempe bacem, tumis bayam, pisang",
        "score_total": 66.0,
        "ingredients": [
            ("Nasi Putih", 150.0),
            ("Tempe", 70.0),
            ("Bayam", 55.0),
            ("Pisang", 85.0),
        ],
        "recommendation": "Tambahkan lauk hewani untuk meningkatkan protein dan zat besi.",
        "projected_score": 74.0,
    },
    {
        "menu_text": "Nasi putih, lele goreng, wortel rebus, tahu goreng",
        "score_total": 70.0,
        "ingredients": [
            ("Nasi Putih", 140.0),
            ("Ikan Lele", 90.0),
            ("Wortel", 60.0),
            ("Tahu", 50.0),
        ],
        "recommendation": "Tambahkan sayuran hijau seperti bayam untuk serat lebih.",
        "projected_score": 78.0,
    },
    {
        "menu_text": "Nasi putih, telur balado, kangkung tumis, tempe",
        "score_total": 73.0,
        "ingredients": [
            ("Nasi Putih", 140.0),
            ("Telur Ayam", 60.0),
            ("Kangkung", 70.0),
            ("Tempe", 45.0),
        ],
        "recommendation": "Pertahankan komposisi ini, tambahkan buah segar.",
        "projected_score": 80.0,
    },
    {
        "menu_text": "Nasi putih, ayam goreng, tumis kangkung, tahu goreng, pisang",
        "score_total": 81.0,
        "ingredients": [
            ("Nasi Putih", 140.0),
            ("Ayam Goreng", 85.0),
            ("Kangkung", 65.0),
            ("Tahu", 50.0),
            ("Pisang", 90.0),
        ],
        "recommendation": "Menu sangat baik, lengkap dengan protein hewani-nabati dan serat.",
        "projected_score": 88.0,
    },
]


async def seed_mock_analyses() -> None:
    async with AsyncSessionLocal() as session:
        # Fetch coordinator user
        result = await session.execute(select(User).where(User.email == "koor@nutrimbg.go.id"))
        user = result.scalar_one_or_none()
        if not user:
            print("ERROR: Koordinator user not found. Run seed_dummy_data.py first.")
            return

        # Fetch food items
        result = await session.execute(select(FoodItem))
        food_items: list[FoodItem] = result.scalars().all()
        food_by_name = {fi.name: fi for fi in food_items}

        # Delete existing analysis data to allow re-run
        await session.execute(
            Recommendation.__table__.delete().where(
                Recommendation.analysis_id.in_(select(MenuAnalysis.id))
            )
        )
        await session.execute(MenuIngredient.__table__.delete())
        await session.execute(MenuAnalysis.__table__.delete())

        now = datetime.now(timezone.utc)
        total_menus = len(DAILY_MENUS)

        # Distribute menus across 7 days (2 menus per day, except last day = 0 menus or 0... depends)
        # We have 14 menus for exactly 7 days (2 per day)
        menus_per_day = 2
        day_count = 7

        for day_offset in range(day_count):
            day_date = now - timedelta(days=day_count - 1 - day_offset)
            day_date_midday = day_date.replace(hour=9, minute=0, second=0, microsecond=0)

            for slot in range(menus_per_day):
                idx = day_offset * menus_per_day + slot
                if idx >= total_menus:
                    break

                menu = DAILY_MENUS[idx]
                created_at = day_date_midday + timedelta(hours=3 * slot)  # 09:00 and 12:00

                analysis = MenuAnalysis(
                    user_id=user.id,
                    menu_text=menu["menu_text"],
                    education_level="SMP",
                    score_total=menu["score_total"],
                    created_at=created_at,
                )
                session.add(analysis)
                await session.flush()

                # Add ingredients
                ingredients = []
                for ing_name, weight in menu["ingredients"]:
                    fi = food_by_name.get(ing_name)
                    if fi:
                        ingredients.append(
                            MenuIngredient(
                                analysis_id=analysis.id,
                                food_item_id=fi.id,
                                input_name=ing_name.lower(),
                                weight_gram=weight,
                            )
                        )
                session.add_all(ingredients)

                # Add recommendation
                session.add(
                    Recommendation(
                        analysis_id=analysis.id,
                        title="Rekomendasi perbaikan menu",
                        projected_score=menu["projected_score"],
                        notes=menu["recommendation"],
                    )
                )

        await session.commit()
        print(f"Seeded {total_menus} mock analyses across {day_count} days successfully.")


if __name__ == "__main__":
    asyncio.run(seed_mock_analyses())
