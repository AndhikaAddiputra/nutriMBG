"""
api/admin/nutrition_akg.py
==========================
Admin CRUD endpoints for NutritionAKG reference values.

All routes require a valid JWT with role='admin'.

Endpoints
---------
POST  /api/admin/nutrition-akg        – create or upsert by (education_level, nutrient_code)
GET   /api/admin/nutrition-akg        – list all (optional ?education_level= filter)
PUT   /api/admin/nutrition-akg/{id}   – update target_value / unit / source
"""

from __future__ import annotations

from typing import Annotated, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import TokenPayload, require_admin
from app.crud.crud_akg import get_akg, list_akg, update_akg, upsert_akg
from app.db.session import AsyncSessionLocal
from app.schemas.akg_schemas import AKGCreate, AKGOut, AKGUpdate

router = APIRouter(prefix="/api/admin/nutrition-akg", tags=["admin – nutrition AKG"])


async def get_db() -> AsyncSession:  # type: ignore[return]
    async with AsyncSessionLocal() as session:
        yield session


# ---------------------------------------------------------------------------
# POST /api/admin/nutrition-akg  (upsert)
# ---------------------------------------------------------------------------


@router.post(
    "",
    response_model=AKGOut,
    summary="Buat atau perbarui nilai AKG (upsert)",
)
async def upsert_akg_endpoint(
    payload: AKGCreate,
    _admin: Annotated[TokenPayload, Depends(require_admin)],
    db: AsyncSession = Depends(get_db),
) -> AKGOut:
    """
    Buat atau perbarui entri AKG berdasarkan kombinasi
    `education_level` + `nutrient_code`.

    Jika kombinasi sudah ada → update nilai & kembalikan HTTP 200.
    Jika belum ada          → insert baru & kembalikan HTTP 201.

    *HTTP status* dikembalikan sebagai **200** agar klien tidak perlu
    membedakan create vs. update saat melakukan sinkronisasi massal.
    """
    row, _created = await upsert_akg(db, payload)
    return AKGOut.model_validate(row)


# ---------------------------------------------------------------------------
# GET /api/admin/nutrition-akg
# ---------------------------------------------------------------------------


@router.get(
    "",
    response_model=List[AKGOut],
    summary="Daftar semua nilai AKG",
)
async def list_akg_endpoint(
    _admin: Annotated[TokenPayload, Depends(require_admin)],
    db: AsyncSession = Depends(get_db),
    education_level: Optional[str] = Query(
        default=None,
        description="Filter berdasarkan jenjang: SD_1_3 | SD_4_6 | SMP | SMA",
    ),
) -> List[AKGOut]:
    """Kembalikan semua entri AKG, diurutkan per jenjang lalu kode nutrien."""
    rows = await list_akg(db, education_level=education_level)
    return [AKGOut.model_validate(r) for r in rows]


# ---------------------------------------------------------------------------
# PUT /api/admin/nutrition-akg/{id}
# ---------------------------------------------------------------------------


@router.put(
    "/{akg_id}",
    response_model=AKGOut,
    summary="Perbarui nilai AKG berdasarkan ID",
)
async def update_akg_endpoint(
    akg_id: int,
    payload: AKGUpdate,
    _admin: Annotated[TokenPayload, Depends(require_admin)],
    db: AsyncSession = Depends(get_db),
) -> AKGOut:
    """
    Perbarui `target_value`, `unit`, dan/atau `source` dari entri AKG.
    Field `education_level` dan `nutrient_code` bersifat immutable —
    gunakan POST (upsert) untuk membuat kombinasi baru.
    """
    row = await get_akg(db, akg_id)
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Entri AKG dengan id={akg_id} tidak ditemukan.",
        )
    updated = await update_akg(db, row, payload)
    return AKGOut.model_validate(updated)