from __future__ import annotations

from typing import Any, Dict, List

import streamlit as st


def render_parser_result(items: List[Dict[str, Any]], source_label: str = "Parser AI", fallback: bool = False) -> None:
    with st.container(border=True):
        if fallback:
            st.caption(f"Mode aktif: {source_label}")
            st.info("Kartu ini berasal dari input manual, bukan hasil parser otomatis.")
        else:
            st.success(f"Hasil {source_label}")

        if items:
            st.table(items)
        else:
            st.info("Tidak ada item yang terdeteksi.")
