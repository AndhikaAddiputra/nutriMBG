from __future__ import annotations

from typing import Any, Dict, List, Optional

import streamlit as st

from utils.api_client import get_dkbm_food_names


ROWS_STATE_KEY = "manual_ingredient_rows"
NEXT_ID_STATE_KEY = "manual_ingredient_next_id"


def _ensure_state() -> None:
    if ROWS_STATE_KEY not in st.session_state:
        st.session_state[ROWS_STATE_KEY] = [{"id": 1}]
    if NEXT_ID_STATE_KEY not in st.session_state:
        st.session_state[NEXT_ID_STATE_KEY] = 2


def _add_row() -> None:
    _ensure_state()
    next_id = st.session_state[NEXT_ID_STATE_KEY]
    st.session_state[ROWS_STATE_KEY].append({"id": next_id})
    st.session_state[NEXT_ID_STATE_KEY] = next_id + 1


def _remove_row(row_id: int) -> None:
    _ensure_state()
    rows = [row for row in st.session_state[ROWS_STATE_KEY] if row["id"] != row_id]
    st.session_state[ROWS_STATE_KEY] = rows or [{"id": 1}]


def _row_keys(row_id: int) -> Dict[str, str]:
    return {
        "name": f"manual_ingredient_name_{row_id}",
        "weight": f"manual_ingredient_weight_{row_id}",
    }


def _collect_rows() -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for row in st.session_state[ROWS_STATE_KEY]:
        row_id = row["id"]
        keys = _row_keys(row_id)
        name = st.session_state.get(keys["name"], "")
        weight_g = st.session_state.get(keys["weight"], 0.0)
        if name and name != "Pilih bahan":
            rows.append({"name": name, "weight_g": float(weight_g)})
    return rows


def show_fallback_form(kabupaten: str | None = None) -> Optional[List[Dict[str, Any]]]:
    _ensure_state()
    try:
        food_names = get_dkbm_food_names(kabupaten)
    except Exception:
        food_names = []
        st.warning("Daftar DKBM tidak dapat dimuat. Anda masih dapat mengetik nama bahan secara manual.")

    st.markdown("### Input bahan manual")
    st.caption("Gunakan daftar bahan DKBM berikut untuk pencarian cepat.")

    for index, row in enumerate(list(st.session_state[ROWS_STATE_KEY])):
        row_id = row["id"]
        keys = _row_keys(row_id)
        st.markdown(f"**Baris bahan #{index + 1}**")
        col_name, col_weight, col_action = st.columns([3, 2, 1])
        with col_name:
            if food_names:
                st.selectbox(
                    "Nama bahan",
                    options=["Pilih bahan"] + food_names,
                    key=keys["name"],
                    label_visibility="collapsed",
                )
            else:
                st.text_input("Nama bahan", key=keys["name"], label_visibility="collapsed")
        with col_weight:
            st.number_input(
                "Berat (gram)",
                min_value=0.0,
                step=1.0,
                key=keys["weight"],
                label_visibility="collapsed",
            )
        with col_action:
            can_remove = len(st.session_state[ROWS_STATE_KEY]) > 1
            if st.button("Hapus", key=f"remove_manual_row_{row_id}", disabled=not can_remove):
                _remove_row(row_id)
                st.rerun()

    col_add, col_submit = st.columns([1, 2])
    with col_add:
        if st.button("Tambah Bahan", use_container_width=True):
            _add_row()
            st.rerun()

    with col_submit:
        submitted = st.button("Hitung dari Input Manual", type="primary", use_container_width=True)

    if submitted:
        rows = _collect_rows()
        if len(rows) < 1:
            st.error("Minimal harus ada satu bahan.")
            return None
        invalid_rows = [row for row in rows if not row.get("name") or row.get("weight_g", 0.0) <= 0]
        if invalid_rows:
            st.error("Setiap bahan harus memiliki nama dan berat lebih dari 0 gram.")
            return None
        return rows

    return None
