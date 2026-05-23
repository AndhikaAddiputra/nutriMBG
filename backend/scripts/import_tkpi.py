"""
import_tkpi.py
==============
Import TKPI (Tabel Komposisi Pangan Indonesia) CSV into food_items table.

Usage:
    .venv/bin/python scripts/import_tkpi.py
"""

from __future__ import annotations

import asyncio
import csv
import re
import sys
from pathlib import Path
from typing import Any, Dict, List

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.settings import settings

_STOP_PHRASES = [
    "segar", "segar,", "kering", "kering,", "mentah", "mentah,", "utuh",
    "giling", "rebus", "sangrai", "goreng", "panggang",
]
_UNIT_WORDS = {"gr", "gram", "g", "kg", "ml", "liter", "butir", "buah", "sdm", "sdt", "gelas", "mangkok", "ekor", "potong", "iris"}
_COOKING_WORDS = {"bakar", "rebus", "goreng", "kukus", "tumis", "sangrai", "panggang", "rebus", "mentah", "segar", "kering"}


def normalize(value: str) -> str:
    text = value.lower().strip()
    text = re.sub(r"\([^)]*\)", " ", text)
    for phrase in _STOP_PHRASES:
        text = text.replace(phrase, " ")
    text = re.sub(r"[^a-z\s]", " ", text)
    tokens = [
        t for t in text.split()
        if t not in _UNIT_WORDS and t not in _COOKING_WORDS and len(t) > 1
    ]
    return " ".join(tokens).strip()


def parse_float(val: str) -> float:
    val = val.strip()
    if not val or val == "-":
        return 0.0
    try:
        return float(val)
    except ValueError:
        return 0.0


def read_csv(path: Path) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    with path.open(encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        for i, row in enumerate(reader):
            if i < 4:
                continue
            name = row[1].strip()
            if not name:
                continue
            rows.append({
                "name": name,
                "source": row[2].strip(),
                "protein": parse_float(row[5]),
                "fat": parse_float(row[6]),
                "carbohydrate": parse_float(row[7]),
                "fiber": parse_float(row[8]),
                "iron": parse_float(row[12]),
                "vitamin_a": parse_float(row[19]),
            })
    return rows


async def main():
    dataset_dir = Path(settings.dataset_dir)
    tkpi_path = dataset_dir / "kandungan-gizi" / "TKPI.csv"
    if not tkpi_path.exists():
        print(f"TKPI file not found: {tkpi_path}")
        sys.exit(1)

    rows = read_csv(tkpi_path)
    print(f"Read {len(rows)} items from TKPI CSV")

    engine = create_async_engine(settings.database_url, pool_size=2)
    inserted = 0
    updated = 0
    skipped = 0

    async with engine.connect() as conn:
        for item in rows:
            norm = normalize(item["name"])
            if not norm:
                skipped += 1
                continue

            result = await conn.execute(
                text("SELECT id FROM food_items WHERE normalized_name = :norm"),
                {"norm": norm},
            )
            existing = result.fetchone()

            if existing:
                await conn.execute(
                    text("""
                        UPDATE food_items
                        SET name = :name, source = :source,
                            protein = :protein, carbohydrate = :carbohydrate,
                            fat = :fat, fiber = :fiber, iron = :iron,
                            vitamin_a = :vitamin_a, is_active = TRUE
                        WHERE id = :id
                    """),
                    {"id": existing[0], "name": item["name"], "source": item["source"],
                     "protein": item["protein"], "carbohydrate": item["carbohydrate"],
                     "fat": item["fat"], "fiber": item["fiber"], "iron": item["iron"],
                     "vitamin_a": item["vitamin_a"]},
                )
                updated += 1
            else:
                await conn.execute(
                    text("""
                        INSERT INTO food_items
                            (name, normalized_name, source,
                             protein, carbohydrate, fat, fiber, iron, vitamin_a,
                             is_active)
                        VALUES
                            (:name, :norm, :source,
                             :protein, :carbohydrate, :fat, :fiber, :iron, :vitamin_a,
                             TRUE)
                    """),
                    {"name": item["name"], "norm": norm, "source": item["source"],
                     "protein": item["protein"], "carbohydrate": item["carbohydrate"],
                     "fat": item["fat"], "fiber": item["fiber"], "iron": item["iron"],
                     "vitamin_a": item["vitamin_a"]},
                )
                inserted += 1

        await conn.commit()

    await engine.dispose()

    print(f"Inserted: {inserted}")
    print(f"Updated:  {updated}")
    print(f"Skipped:  {skipped}")
    print(f"Total:    {inserted + updated + skipped}")
    print("Done.")


if __name__ == "__main__":
    asyncio.run(main())
