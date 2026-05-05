import asyncio
import sys
from pathlib import Path

from sqlalchemy import delete

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.db.base import Base
from app.db.session import AsyncSessionLocal, engine
from app.models.entities import (
    FoodItem,
    LocalCatalogItem,
    MenuAnalysis,
    MenuIngredient,
    NutritionAKG,
    Recommendation,
    User,
)


def normalize_name(name: str) -> str:
    return name.lower().strip()


async def seed() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as session:
        await session.execute(delete(Recommendation))
        await session.execute(delete(MenuIngredient))
        await session.execute(delete(MenuAnalysis))
        await session.execute(delete(LocalCatalogItem))
        await session.execute(delete(NutritionAKG))
        await session.execute(delete(FoodItem))
        await session.execute(delete(User))

        foods = [
            ("Nasi Putih", "DKBM", 2.7, 28.0, 0.3, 0.4, 0.2, 0.0),
            ("Ayam Goreng", "DKBM", 26.0, 5.0, 14.0, 0.0, 1.3, 60.0),
            ("Tempe", "DKBM", 20.8, 13.5, 8.8, 1.4, 2.7, 0.0),
            ("Bayam", "DKBM", 2.9, 3.6, 0.4, 2.2, 2.7, 470.0),
            ("Wortel", "DKBM", 0.9, 9.6, 0.2, 2.8, 0.3, 835.0),
            ("Telur Ayam", "DKBM", 12.5, 1.1, 10.8, 0.0, 1.8, 140.0),
            ("Ikan Lele", "DKBM", 17.6, 0.0, 4.8, 0.0, 1.0, 80.0),
            ("Pisang", "USDA", 1.1, 22.8, 0.3, 2.6, 0.3, 64.0),
            ("Kangkung", "DKBM", 3.4, 5.4, 0.7, 2.0, 2.5, 315.0),
            ("Tahu", "DKBM", 8.1, 1.9, 4.8, 0.3, 1.6, 0.0),
        ]

        food_rows = [
            FoodItem(
                name=name,
                normalized_name=normalize_name(name),
                source=source,
                protein=protein,
                carbohydrate=carbohydrate,
                fat=fat,
                fiber=fiber,
                iron=iron,
                vitamin_a=vitamin_a,
            )
            for name, source, protein, carbohydrate, fat, fiber, iron, vitamin_a in foods
        ]
        session.add_all(food_rows)
        await session.flush()

        food_id_by_name = {row.name: row.id for row in food_rows}
        pilot_kabupaten = [
            "Kabupaten Bandung",
            "Kabupaten Sleman",
            "Kabupaten Bogor",
            "Kabupaten Sidoarjo",
            "Kabupaten Gowa",
        ]
        unavailable_by_region = {
            "Kabupaten Bandung": {"Ikan Lele"},
            "Kabupaten Sleman": {"Kangkung"},
            "Kabupaten Bogor": {"Ayam Goreng"},
            "Kabupaten Sidoarjo": {"Wortel"},
            "Kabupaten Gowa": {"Tempe"},
        }

        catalog_rows = []
        for kabupaten in pilot_kabupaten:
            unavailable = unavailable_by_region[kabupaten]
            for food_name, food_id in food_id_by_name.items():
                catalog_rows.append(
                    LocalCatalogItem(
                        kabupaten=kabupaten,
                        food_item_id=food_id,
                        is_available=food_name not in unavailable,
                    )
                )
        session.add_all(catalog_rows)

        akg_targets = {
            "SD_1_3": {"protein": 35.0, "carbohydrate": 220.0, "fat": 62.0, "fiber": 16.0, "iron": 8.0, "vitamin_a": 500.0},
            "SD_4_6": {"protein": 50.0, "carbohydrate": 270.0, "fat": 70.0, "fiber": 20.0, "iron": 10.0, "vitamin_a": 600.0},
            "SMP": {"protein": 65.0, "carbohydrate": 300.0, "fat": 80.0, "fiber": 25.0, "iron": 13.0, "vitamin_a": 700.0},
            "SMA": {"protein": 75.0, "carbohydrate": 340.0, "fat": 90.0, "fiber": 30.0, "iron": 15.0, "vitamin_a": 700.0},
        }
        unit_by_nutrient = {
            "protein": "g",
            "carbohydrate": "g",
            "fat": "g",
            "fiber": "g",
            "iron": "mg",
            "vitamin_a": "mcg",
        }
        akg_rows = []
        for level, nutrients in akg_targets.items():
            for nutrient_code, target_value in nutrients.items():
                akg_rows.append(
                    NutritionAKG(
                        education_level=level,
                        nutrient_code=nutrient_code,
                        target_value=target_value,
                        unit=unit_by_nutrient[nutrient_code],
                    )
                )
        session.add_all(akg_rows)

        demo_user = User(
            full_name="Demo Koordinator",
            email="demo@nutrimbg.local",
            password_hash="dummy-hash",
            role="coordinator",
            province="Jawa Barat",
            kabupaten="Kabupaten Bandung",
            default_education_level="SMP",
            is_active=True,
        )
        session.add(demo_user)
        await session.flush()

        analysis = MenuAnalysis(
            user_id=demo_user.id,
            menu_text="Nasi putih, ayam goreng, bayam, pisang",
            education_level="SMP",
            score_total=68.5,
        )
        session.add(analysis)
        await session.flush()

        session.add_all(
            [
                MenuIngredient(analysis_id=analysis.id, food_item_id=food_id_by_name["Nasi Putih"], input_name="nasi putih", weight_gram=150.0),
                MenuIngredient(analysis_id=analysis.id, food_item_id=food_id_by_name["Ayam Goreng"], input_name="ayam goreng", weight_gram=80.0),
                MenuIngredient(analysis_id=analysis.id, food_item_id=food_id_by_name["Bayam"], input_name="bayam", weight_gram=60.0),
                MenuIngredient(analysis_id=analysis.id, food_item_id=food_id_by_name["Pisang"], input_name="pisang", weight_gram=90.0),
            ]
        )
        session.add(
            Recommendation(
                analysis_id=analysis.id,
                title="Tambah sayur tinggi serat",
                projected_score=78.0,
                notes="Tambahkan wortel 50g untuk meningkatkan serat dan vitamin A.",
            )
        )

        await session.commit()


if __name__ == "__main__":
    asyncio.run(seed())
    print("Dummy data seeded successfully.")
