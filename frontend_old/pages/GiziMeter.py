import os
from typing import Any, Dict, List, Optional

import requests
import streamlit as st
from utils.session import manage_sidebar_visibility
from components.top_bar import render_top_bar


API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

EDUCATION_LEVELS = {
    "SD Kelas 1-3": "SD",
    "SD Kelas 4-6": "SD",
    "SMP": "SMP",
    "SMA": "SMA",
}

KABUPATEN_OPTIONS = [
    "Semua Kabupaten",
    "Kabupaten Bandung",
    "Kabupaten Sleman",
    "Kabupaten Bogor",
    "Kabupaten Sidoarjo",
    "Kabupaten Gowa",
]

NUTRIENT_LABELS = {
    "protein": "Protein",
    "carbohydrate": "Karbohidrat",
    "fat": "Lemak",
    "fiber": "Serat",
    "iron": "Zat Besi",
    "vitamin_a": "Vitamin A",
}

STATUS_COLORS = {
    "Cukup": "🟢",
    "Perlu Perhatian": "🟡",
    "Defisien": "🔴",
}


def _headers() -> Dict[str, str]:
    token = st.session_state.get("auth_token", "")
    if token:
        return {"Authorization": f"Bearer {token}"}
    return {}


def fetch_foods(kabupaten: Optional[str]) -> List[Dict[str, Any]]:
    params = {}
    if kabupaten and kabupaten != "Semua Kabupaten":
        params["kabupaten"] = kabupaten
    response = requests.get(
        f"{API_BASE_URL}/api/v1/reference/foods",
        params=params,
        headers=_headers(),
        timeout=10,
    )
    response.raise_for_status()
    return response.json()


def classify_menu(text: str, education_level: str) -> Dict[str, Any]:
    response = requests.post(
        f"{API_BASE_URL}/api/v1/ai/classify",
        json={"text": text, "education_level": education_level},
        headers=_headers(),
        timeout=30,
    )
    response.raise_for_status()
    return response.json()


def recommend_menu(deficiencies: Dict[str, str], local_catalog: List[str], count: int) -> List[str]:
    response = requests.post(
        f"{API_BASE_URL}/api/v1/ai/recommend",
        json={"deficiencies": deficiencies, "local_catalog": local_catalog, "count": count},
        headers=_headers(),
        timeout=30,
    )
    response.raise_for_status()
    payload = response.json()
    return payload.get("recommendations", [])


st.set_page_config(page_title="NutriMBG", page_icon="🥗", layout="centered", initial_sidebar_state="collapsed")
manage_sidebar_visibility()

if "user_role" not in st.session_state or not st.session_state["user_role"]:
    st.warning("Anda tidak memiliki akses ke halaman ini. Silakan login kembali.")
    st.stop()

render_top_bar()

st.title("NutriMBG")
st.write("Validasi dan rekomendasi gizi untuk MBG.")

menu_text = st.text_area("Deskripsi menu harian", max_chars=500, height=160)
jenjang_label = st.selectbox("Jenjang pendidikan", list(EDUCATION_LEVELS.keys()))
kabupaten = st.selectbox("Kabupaten", KABUPATEN_OPTIONS)
recommend_count = st.slider("Jumlah rekomendasi menu", min_value=1, max_value=5, value=3)

if st.button("Analisa Menu"):
    if not menu_text.strip():
        st.warning("Masukkan deskripsi menu terlebih dahulu.")
    else:
        try:
            with st.spinner("Menganalisa menu..."):
                level_code = EDUCATION_LEVELS[jenjang_label]
                result = classify_menu(menu_text, level_code)
                foods = fetch_foods(kabupaten)
        except requests.RequestException as exc:
            st.error(f"Gagal memproses data backend: {exc}")
        else:
            st.subheader("Hasil parsing menu")
            items = result.get("items", [])
            if items:
                st.table(items)
            else:
                st.info("Tidak ada item yang terdeteksi dari menu.")

            unmatched = result.get("unmatched_items", [])
            if unmatched:
                st.warning(
                    "Item tidak ditemukan di database TKPI sehingga tidak dihitung: "
                    + ", ".join(unmatched)
                )

            st.subheader("Ringkasan kecukupan gizi")
            labels = result.get("labels", {})
            ratios = result.get("ratios", {})
            totals = result.get("totals", {})
            rows = []
            for nutrient, label in NUTRIENT_LABELS.items():
                status = labels.get(nutrient, "N/A")
                ratio = ratios.get(nutrient, 0.0)
                rows.append(
                    {
                        "Nutrien": label,
                        "Asupan": f"{totals.get(nutrient, 0.0):.2f}",
                        "Rasio AKG": f"{ratio * 100:.1f}%",
                        "Status": f"{STATUS_COLORS.get(status, '')} {status}",
                    }
                )

            st.table(rows)

            score = result.get("score", 0.0)
            st.metric("Skor Gizi Keseluruhan", f"{score:.1f}/100")

            try:
                deficiencies = {n: labels.get(n, "N/A") for n in NUTRIENT_LABELS}
                local_catalog_names = [food["name"] for food in foods]
                recommendations = recommend_menu(
                    deficiencies=deficiencies,
                    local_catalog=local_catalog_names,
                    count=recommend_count,
                )
            except requests.RequestException as exc:
                st.error(f"Gagal meminta rekomendasi menu: {exc}")
            else:
                st.subheader("Rekomendasi menu")
                if recommendations:
                    for rec in recommendations:
                        st.write(f"- {rec}")
                else:
                    st.info("Belum ada rekomendasi yang dihasilkan.")
