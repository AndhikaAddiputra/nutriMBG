"""
pages/04_Admin.py
==================
Administrator page with a "Katalog Bahan Lokal" tab.

Features:
- District selector to choose which kabupaten to manage
- Filterable, paginated table of food items with availability toggle
- Seasonal unavailability month picker
- Bulk-save via the /api/admin/local-catalog/bulk endpoint
- Single-row toggle via PUT /api/admin/local-catalog/{district_id}/{food_item_id}

Requires: Streamlit ≥ 1.23 (for st.data_editor)
"""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

import requests
import streamlit as st

from utils.session import manage_sidebar_visibility, require_auth

st.set_page_config(
    page_title="Admin – NutriMBG",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="expanded",
)
manage_sidebar_visibility()
require_auth(allowed_roles=["administrator"])

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

MONTH_LABELS = {
    1: "Jan", 2: "Feb", 3: "Mar", 4: "Apr",
    5: "Mei", 6: "Jun", 7: "Jul", 8: "Agu",
    9: "Sep", 10: "Okt", 11: "Nov", 12: "Des",
}

KNOWN_DISTRICTS = [
    "Kabupaten Bandung",
    "Kabupaten Sleman",
    "Kabupaten Bogor",
    "Kabupaten Sidoarjo",
    "Kabupaten Gowa",
]


def _admin_headers() -> Dict[str, str]:
    token = st.session_state.get("auth_token", "")
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# API helpers
# ---------------------------------------------------------------------------


@st.cache_data(ttl=60, show_spinner=False)
def fetch_districts() -> List[str]:
    try:
        resp = requests.get(
            f"{API_BASE_URL}/api/admin/local-catalog/districts",
            headers=_admin_headers(),
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        # Merge with known districts so admin can set up new ones
        return sorted(set(data + KNOWN_DISTRICTS))
    except Exception:
        return sorted(KNOWN_DISTRICTS)


@st.cache_data(ttl=30, show_spinner=False)
def fetch_all_food_items() -> List[Dict[str, Any]]:
    """Fetch all active food items via public reference endpoint."""
    try:
        resp = requests.get(
            f"{API_BASE_URL}/api/v1/reference/foods",
            params={"limit": 500},
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json() 
    except Exception:
        return []


@st.cache_data(ttl=30, show_spinner=False)
def fetch_catalog(district_id: str) -> List[Dict[str, Any]]:
    """Fetch existing catalog entries for a district."""
    try:
        resp = requests.get(
            f"{API_BASE_URL}/api/admin/local-catalog",
            headers=_admin_headers(),
            params={"district_id": district_id, "include_unavailable": True, "per_page": 200},
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json()
    except Exception:
        return []


def toggle_single_item(
    district_id: str,
    food_item_id: int,
    is_available: bool,
    unavailable_months: Optional[List[int]],
) -> bool:
    """PUT a single catalog entry. Returns True on success."""
    try:
        resp = requests.put(
            f"{API_BASE_URL}/api/admin/local-catalog/{district_id}/{food_item_id}",
            headers=_admin_headers(),
            json={
                "is_available": is_available,
                "unavailable_months": unavailable_months or [],
            },
            timeout=10,
        )
        resp.raise_for_status()
        return True
    except Exception as exc:
        st.error(f"Gagal menyimpan perubahan: {exc}")
        return False


def bulk_save(district_id: str, items: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """POST bulk update. Returns response JSON or None on error."""
    try:
        resp = requests.post(
            f"{API_BASE_URL}/api/admin/local-catalog/bulk",
            headers=_admin_headers(),
            json={"district_id": district_id, "items": items},
            timeout=20,
        )
        resp.raise_for_status()
        return resp.json()
    except Exception as exc:
        st.error(f"Gagal menyimpan bulk update: {exc}")
        return None


# ---------------------------------------------------------------------------
# Page layout
# ---------------------------------------------------------------------------

st.title("⚙️ Administrasi NutriMBG")

tabs = st.tabs(["📋 Katalog Bahan Lokal", "ℹ️ Informasi Sistem"])

# ===========================================================================
# TAB 1 — Katalog Bahan Lokal
# ===========================================================================

with tabs[0]:
    st.subheader("Katalog Bahan Lokal per District")
    st.markdown(
        "Kelola ketersediaan bahan makanan untuk setiap kabupaten/kota. "
        "Perubahan di sini langsung mempengaruhi rekomendasi menu yang diterima koordinator."
    )

    # --- District selector ---
    col_district, col_refresh = st.columns([4, 1])
    with col_district:
        districts = fetch_districts()
        selected_district = st.selectbox(
            "Pilih Kabupaten/Kota",
            options=districts,
            index=0,
            key="catalog_district_selector",
        )
    with col_refresh:
        st.write("")
        if st.button("🔄 Refresh", use_container_width=True):
            st.cache_data.clear()
            st.rerun()

    st.divider()

    if not selected_district:
        st.info("Pilih kabupaten/kota untuk melihat dan mengelola katalog bahan.")
        st.stop()

    # --- Load data ---
    with st.spinner("Memuat data..."):
        all_foods = fetch_all_food_items()
        existing_catalog = fetch_catalog(selected_district)

    if not all_foods:
        st.warning(
            "Tidak ada data bahan makanan. Tambahkan bahan terlebih dahulu "
            "melalui endpoint admin food-items atau seed data."
        )
        st.stop()

    # Build lookup: food_item_id → catalog entry
    catalog_by_food_id: Dict[int, Dict[str, Any]] = {
        entry["food_item_id"]: entry for entry in existing_catalog
    }

    # --- Search / filter ---
    col_search, col_filter = st.columns([3, 1])
    with col_search:
        search_query = st.text_input(
            "🔍 Cari bahan", placeholder="Ketik nama bahan...", key="catalog_search"
        )
    with col_filter:
        show_only_available = st.checkbox("Tampilkan tersedia saja", value=False)

    # Build table rows
    table_rows = []
    for food in all_foods:
        name: str = food["name"]
        food_id: int = food["id"]

        if search_query and search_query.lower() not in name.lower():
            continue

        catalog_entry = catalog_by_food_id.get(food_id)
        is_available = catalog_entry["is_available"] if catalog_entry else True
        unavailable_months: List[int] = (
            catalog_entry.get("unavailable_months") or [] if catalog_entry else []
        )

        if show_only_available and not is_available:
            continue

        table_rows.append(
            {
                "food_item_id": food_id,
                "Nama Bahan": name,
                "Tersedia": is_available,
                "Bulan Tidak Tersedia": ", ".join(
                    MONTH_LABELS[m] for m in sorted(unavailable_months)
                ) if unavailable_months else "–",
                "_unavailable_months": unavailable_months,
            }
        )

    total_items = len(table_rows)
    st.caption(f"Menampilkan **{total_items}** bahan untuk district: **{selected_district}**")

    if not table_rows:
        st.info("Tidak ada bahan yang cocok dengan filter.")
        st.stop()

    # --- st.data_editor for bulk toggle ---
    st.markdown("#### Tabel Ketersediaan Bahan")
    st.caption(
        "Centang kolom **Tersedia** untuk mengaktifkan/menonaktifkan bahan. "
        "Klik **Simpan Semua Perubahan** untuk menerapkan."
    )

    import pandas as pd

    display_df = pd.DataFrame(
        [
            {
                "food_item_id": row["food_item_id"],
                "Nama Bahan": row["Nama Bahan"],
                "Tersedia": row["Tersedia"],
                "Bulan Tidak Tersedia (info)": row["Bulan Tidak Tersedia"],
            }
            for row in table_rows
        ]
    )

    edited_df = st.data_editor(
        display_df,
        column_config={
            "food_item_id": st.column_config.NumberColumn(
                "ID", disabled=True, width="small"
            ),
            "Nama Bahan": st.column_config.TextColumn(
                "Nama Bahan", disabled=True, width="large"
            ),
            "Tersedia": st.column_config.CheckboxColumn(
                "Tersedia ✓",
                help="Centang untuk menandai bahan ini tersedia di district yang dipilih",
                width="small",
            ),
            "Bulan Tidak Tersedia (info)": st.column_config.TextColumn(
                "Musiman (info)",
                disabled=True,
                width="medium",
                help="Bulan tidak tersedia – edit via panel di bawah",
            ),
        },
        hide_index=True,
        use_container_width=True,
        key="catalog_editor",
    )

    # --- Seasonal months editor (for a single selected item) ---
    st.divider()
    st.markdown("#### Atur Bulan Tidak Tersedia (Musiman)")
    st.caption(
        "Pilih bahan dan centang bulan-bulan di mana bahan tersebut tidak tersedia. "
        "Ini berguna untuk bahan musiman (misalnya buah tropis tertentu)."
    )

    food_name_to_id = {food["name"]: food["id"] for food in all_foods}
    display_names = [row["Nama Bahan"] for row in table_rows]

    selected_food_name = st.selectbox(
        "Pilih bahan untuk atur musiman",
        options=display_names,
        key="seasonal_food_selector",
    )

    if selected_food_name:
        sel_food_id = food_name_to_id.get(selected_food_name)
        sel_catalog = catalog_by_food_id.get(sel_food_id, {})
        current_unavailable = sel_catalog.get("unavailable_months") or []

        month_cols = st.columns(6)
        selected_unavailable_months: List[int] = []
        for i, (month_num, month_label) in enumerate(MONTH_LABELS.items()):
            col = month_cols[i % 6]
            checked = col.checkbox(
                month_label,
                value=month_num in current_unavailable,
                key=f"month_{month_num}_{sel_food_id}",
            )
            if checked:
                selected_unavailable_months.append(month_num)

        if st.button(
            f"💾 Simpan Musiman untuk '{selected_food_name}'",
            key="save_seasonal",
            type="secondary",
        ):
            # Determine current availability from the edited df
            matching_rows = edited_df[edited_df["food_item_id"] == sel_food_id]
            is_avail = bool(
                matching_rows["Tersedia"].values[0]
                if not matching_rows.empty
                else sel_catalog.get("is_available", True)
            )
            if toggle_single_item(
                selected_district,
                sel_food_id,
                is_avail,
                selected_unavailable_months,
            ):
                st.success(f"Pengaturan musiman untuk '{selected_food_name}' berhasil disimpan.")
                st.cache_data.clear()
                st.rerun()

    # --- Bulk save button ---
    st.divider()
    col_save, col_info = st.columns([2, 3])
    with col_save:
        save_all = st.button(
            "💾 Simpan Semua Perubahan",
            type="primary",
            use_container_width=True,
            key="bulk_save_btn",
        )
    with col_info:
        st.info(
            "Simpan Semua akan menerapkan perubahan toggle **Tersedia** "
            "ke seluruh bahan yang ditampilkan. Pengaturan musiman tetap terjaga."
        )

    if save_all:
        # Build bulk payload — merge edited availability with existing seasonal data
        food_id_to_seasonal: Dict[int, List[int]] = {
            row["food_item_id"]: row["_unavailable_months"] for row in table_rows
        }
        bulk_items = []
        for _, row in edited_df.iterrows():
            fid = int(row["food_item_id"])
            bulk_items.append(
                {
                    "food_item_id": fid,
                    "is_available": bool(row["Tersedia"]),
                    "unavailable_months": food_id_to_seasonal.get(fid) or [],
                }
            )

        with st.spinner("Menyimpan perubahan..."):
            result = bulk_save(selected_district, bulk_items)

        if result:
            errors = result.get("errors", [])
            st.success(
                f"✅ Berhasil: {result.get('updated', 0)} diperbarui, "
                f"{result.get('created', 0)} dibuat baru."
            )
            if errors:
                st.warning("Beberapa item gagal diproses:")
                for err in errors:
                    st.caption(f"• {err}")
            st.cache_data.clear()
            st.rerun()

    # --- Current catalog summary ---
    st.divider()
    st.markdown("#### Ringkasan Katalog")
    total_available = sum(1 for r in table_rows if r["Tersedia"])
    total_unavailable = total_items - total_available
    total_seasonal = sum(1 for r in table_rows if r["_unavailable_months"])

    m1, m2, m3 = st.columns(3)
    m1.metric("Total Bahan", total_items)
    m2.metric("Tersedia", total_available, delta=None)
    m3.metric("Tidak Tersedia", total_unavailable, delta=None)
    if total_seasonal:
        st.caption(f"ℹ️ {total_seasonal} bahan memiliki pembatasan musiman.")

# ===========================================================================
# TAB 2 — System Info
# ===========================================================================

with tabs[1]:
    st.subheader("Informasi Sistem")
    st.markdown(
        """
        **NutriMBG** – Sistem Validasi dan Rekomendasi Gizi untuk Program Makan Bergizi Gratis.

        | Komponen | Status |
        |---|---|
        | Backend (FastAPI) | Terhubung |
        | Database (PostgreSQL) | Terkelola via Docker |
        | AI Parser | Gemini API |
        | Recommender | Gemini API + Filter Katalog Lokal |
        | ML Classifier | RandomForest (joblib) |

        **F16 – Filter Rekomendasi Berdasarkan Katalog Lokal**: ✅ Aktif
        - Rekomendasi menu hanya menggunakan bahan yang tersedia di district koordinator.
        - Filter musiman: bahan tidak akan direkomendasikan pada bulan tidak tersedia.

        **F23 – Manajemen Katalog Bahan Lokal (Admin)**: ✅ Aktif
        - Admin dapat toggle ketersediaan per bahan per district.
        - Mendukung bulk update dan pembatasan musiman (bulan 1–12).
        """
    )

    with st.expander("API Endpoints – Local Catalog"):
        st.code(
            """
GET  /api/admin/local-catalog/districts
GET  /api/admin/local-catalog?district_id=Kabupaten+Bandung
PUT  /api/admin/local-catalog/{district_id}/{food_item_id}
POST /api/admin/local-catalog/bulk
""",
            language="text",
        )
