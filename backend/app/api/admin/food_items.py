"""
api/admin/food_items.py
=======================
Admin CRUD endpoints for the FoodItem (DKBM) database.

All routes require a valid JWT with role='admin'
(enforced via Depends(require_admin)).

Endpoints
---------
POST   /api/admin/food-items            – create
GET    /api/admin/food-items            – list (paginated, searchable)
PUT    /api/admin/food-items/{id}       – update (partial)
DELETE /api/admin/food-items/{id}       – soft-delete (is_active=False)
"""

from __future__ import annotations

from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import TokenPayload, require_admin
from app.crud.crud_food_item import (
    create_food_item,
    get_food_item,
    list_food_items,
    soft_delete_food_item,
    update_food_item,
)
from app.db.session import AsyncSessionLocal
from app.schemas.food_item_schemas import FoodItemCreate, FoodItemOut, FoodItemPage, FoodItemUpdate

router = APIRouter(prefix="/api/admin/food-items", tags=["admin – food items"])


# ---------------------------------------------------------------------------
# Shared DB dependency
# ---------------------------------------------------------------------------


async def get_db() -> AsyncSession:  # type: ignore[return]
    async with AsyncSessionLocal() as session:
        yield session


# ---------------------------------------------------------------------------
# POST /api/admin/food-items
# ---------------------------------------------------------------------------


@router.post(
    "",
    response_model=FoodItemOut,
    status_code=status.HTTP_201_CREATED,
    summary="Tambah bahan makanan baru",
)
async def create_food_item_endpoint(
    payload: FoodItemCreate,
    _admin: Annotated[TokenPayload, Depends(require_admin)],
    db: AsyncSession = Depends(get_db),
) -> FoodItemOut:
    """
    Buat entri bahan makanan baru di database DKBM.
    Nama bahan harus unik (case-insensitive).
    """
    try:
        item = await create_food_item(db, payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    return FoodItemOut.model_validate(item)


# ---------------------------------------------------------------------------
# GET /api/admin/food-items
# ---------------------------------------------------------------------------


@router.get(
    "",
    response_model=FoodItemPage,
    summary="Daftar bahan makanan (paginasi + pencarian)",
)
async def list_food_items_endpoint(
    response: Response,
    _admin: Annotated[TokenPayload, Depends(require_admin)],
    db: AsyncSession = Depends(get_db),
    page: int = Query(default=1, ge=1, description="Nomor halaman (mulai dari 1)"),
    per_page: int = Query(default=20, ge=1, le=100, description="Jumlah item per halaman"),
    search: Optional[str] = Query(default=None, description="Filter nama (partial match)"),
    include_inactive: bool = Query(
        default=False, description="Sertakan item yang sudah di-soft-delete"
    ),
) -> FoodItemPage:
    """
    Kembalikan daftar bahan makanan dengan paginasi.
    Header `X-Total-Count` berisi total item yang cocok dengan filter.
    """
    items, total = await list_food_items(
        db,
        page=page,
        per_page=per_page,
        search=search,
        include_inactive=include_inactive,
    )
    response.headers["X-Total-Count"] = str(total)
    return FoodItemPage(
        items=[FoodItemOut.model_validate(i) for i in items],
        total=total,
        page=page,
        per_page=per_page,
    )


# ---------------------------------------------------------------------------
# PUT /api/admin/food-items/{id}
# ---------------------------------------------------------------------------


@router.put(
    "/{item_id}",
    response_model=FoodItemOut,
    summary="Perbarui bahan makanan",
)
async def update_food_item_endpoint(
    item_id: int,
    payload: FoodItemUpdate,
    _admin: Annotated[TokenPayload, Depends(require_admin)],
    db: AsyncSession = Depends(get_db),
) -> FoodItemOut:
    """
    Perbarui satu atau lebih field bahan makanan.
    Semua field bersifat opsional (partial update).
    """
    item = await get_food_item(db, item_id)
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bahan makanan tidak ditemukan.")
    try:
        updated = await update_food_item(db, item, payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    return FoodItemOut.model_validate(updated)


# ---------------------------------------------------------------------------
# DELETE /api/admin/food-items/{id}
# ---------------------------------------------------------------------------


@router.delete(
    "/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Soft-delete bahan makanan",
)
async def delete_food_item_endpoint(
    item_id: int,
    _admin: Annotated[TokenPayload, Depends(require_admin)],
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    Tandai bahan makanan sebagai tidak aktif (is_active=False).
    Data tidak dihapus secara permanen dari database.
    """
    item = await get_food_item(db, item_id)
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bahan makanan tidak ditemukan.")
    await soft_delete_food_item(db, item)