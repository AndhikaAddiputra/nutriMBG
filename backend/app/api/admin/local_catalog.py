"""
api/admin/local_catalog.py
==========================
Admin CRUD endpoints for the LocalIngredientCatalog.

All routes require a valid JWT with role='admin'.

Endpoints
---------
GET  /api/admin/local-catalog                               – list catalog for a district
PUT  /api/admin/local-catalog/{district_id}/{food_item_id} – toggle availability / seasonal flags
POST /api/admin/local-catalog/bulk                          – bulk-update for a district
GET  /api/admin/local-catalog/districts                     – list known districts
"""

from __future__ import annotations

from typing import Annotated, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import TokenPayload, require_admin
from app.crud.crud_local_catalog import (
    bulk_upsert_catalog,
    get_catalog_entry,
    list_catalog_for_district,
    upsert_catalog_entry,
)
from app.db.session import AsyncSessionLocal
from app.models.entities import FoodItem
from app.models.local_catalog import LocalIngredientCatalog
from app.schemas.local_catalog_schemas import (
    BulkCatalogUpdateRequest,
    BulkCatalogUpdateResponse,
    LocalCatalogItemOut,
    LocalCatalogUpdate,
)

router = APIRouter(
    prefix="/api/admin/local-catalog",
    tags=["admin – local catalog"],
)


# ---------------------------------------------------------------------------
# DB dependency
# ---------------------------------------------------------------------------


async def get_db() -> AsyncSession:  # type: ignore[return]
    async with AsyncSessionLocal() as session:
        yield session


# ---------------------------------------------------------------------------
# GET /api/admin/local-catalog/districts
# ---------------------------------------------------------------------------


@router.get(
    "/districts",
    response_model=List[str],
    summary="Daftar district yang sudah memiliki entri katalog",
)
async def list_districts(
    _admin: Annotated[TokenPayload, Depends(require_admin)],
    db: AsyncSession = Depends(get_db),
) -> List[str]:
    """Return sorted list of distinct district_id values in the catalog."""
    result = await db.execute(
        select(LocalIngredientCatalog.district_id)
        .distinct()
        .order_by(LocalIngredientCatalog.district_id.asc())
    )
    return [row[0] for row in result.all()]


# ---------------------------------------------------------------------------
# GET /api/admin/local-catalog
# ---------------------------------------------------------------------------


@router.get(
    "",
    response_model=List[LocalCatalogItemOut],
    summary="Daftar katalog bahan lokal untuk suatu district",
)
async def list_catalog(
    response: Response,
    _admin: Annotated[TokenPayload, Depends(require_admin)],
    db: AsyncSession = Depends(get_db),
    district_id: str = Query(..., description="Kabupaten/Kota identifier"),
    include_unavailable: bool = Query(
        default=True,
        description="Sertakan bahan yang sedang tidak tersedia",
    ),
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=50, ge=1, le=200),
    search: Optional[str] = Query(default=None, description="Filter nama bahan"),
) -> List[LocalCatalogItemOut]:
    """
    Kembalikan katalog bahan makanan untuk suatu district (kabupaten/kota),
    dengan paginasi dan pencarian opsional.
    Header `X-Total-Count` berisi total item.
    """
    rows, total = await list_catalog_for_district(
        db,
        district_id,
        include_unavailable=include_unavailable,
        page=page,
        per_page=per_page,
        search=search,
    )
    response.headers["X-Total-Count"] = str(total)

    return [
        LocalCatalogItemOut(
            id=entry.id,
            food_item_id=entry.food_item_id,
            food_item_name=food_name,
            district_id=entry.district_id,
            is_available=entry.is_available,
            unavailable_months=entry.unavailable_months,
        )
        for entry, food_name in rows
    ]


# ---------------------------------------------------------------------------
# PUT /api/admin/local-catalog/{district_id}/{food_item_id}
# ---------------------------------------------------------------------------


@router.put(
    "/{district_id}/{food_item_id}",
    response_model=LocalCatalogItemOut,
    summary="Toggle ketersediaan / atur bulan musiman untuk satu bahan",
)
async def update_catalog_entry_endpoint(
    district_id: str,
    food_item_id: int,
    payload: LocalCatalogUpdate,
    _admin: Annotated[TokenPayload, Depends(require_admin)],
    db: AsyncSession = Depends(get_db),
) -> LocalCatalogItemOut:
    """
    Buat atau perbarui entri katalog untuk kombinasi district + food item.

    - Gunakan `is_available: false` untuk menonaktifkan bahan.
    - Gunakan `unavailable_months: [6, 7, 8]` untuk menyetel pembatasan musiman.
    - Kirim `unavailable_months: []` untuk menghapus pembatasan musiman.
    """
    # Verify food item exists
    food_result = await db.execute(
        select(FoodItem).where(FoodItem.id == food_item_id)
    )
    food = food_result.scalar_one_or_none()
    if food is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"FoodItem dengan id={food_item_id} tidak ditemukan.",
        )

    entry, _ = await upsert_catalog_entry(db, district_id, food_item_id, payload)

    return LocalCatalogItemOut(
        id=entry.id,
        food_item_id=entry.food_item_id,
        food_item_name=food.name,
        district_id=entry.district_id,
        is_available=entry.is_available,
        unavailable_months=entry.unavailable_months,
    )


# ---------------------------------------------------------------------------
# POST /api/admin/local-catalog/bulk
# ---------------------------------------------------------------------------


@router.post(
    "/bulk",
    response_model=BulkCatalogUpdateResponse,
    summary="Bulk-update ketersediaan bahan untuk suatu district",
)
async def bulk_update_catalog(
    payload: BulkCatalogUpdateRequest,
    _admin: Annotated[TokenPayload, Depends(require_admin)],
    db: AsyncSession = Depends(get_db),
) -> BulkCatalogUpdateResponse:
    """
    Perbarui banyak entri katalog sekaligus untuk satu district.
    Mendukung format JSON. Untuk CSV, konversi ke JSON sebelum dikirim.

    Contoh payload:
    ```json
    {
      "district_id": "Kabupaten Bandung",
      "items": [
        {"food_item_id": 1, "is_available": true, "unavailable_months": null},
        {"food_item_id": 2, "is_available": false, "unavailable_months": [6, 7]}
      ]
    }
    ```
    """
    updated, created, errors = await bulk_upsert_catalog(
        db, payload.district_id, payload.items
    )
    return BulkCatalogUpdateResponse(
        district_id=payload.district_id,
        updated=updated,
        created=created,
        errors=errors,
    )
