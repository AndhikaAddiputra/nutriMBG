import os
from typing import Any, Dict, List, Optional

import requests
import streamlit as st
from utils.session import manage_sidebar_visibility
from components.top_bar import render_top_bar


API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

EDUCATION_LEVELS = {
    "SD Kelas 1-3": "SD_1_3",
    "SD Kelas 4-6": "SD_4_6",
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


def normalize_name(value: str) -> str:
    return value.strip().lower()


def fetch_akg(level_code: str) -> List[Dict[str, Any]]:
    response = requests.get(f"{API_BASE_URL}/api/v1/reference/akg/{level_code}", timeout=10)
    response.raise_for_status()
    return response.json()


def fetch_foods(kabupaten: Optional[str]) -> List[Dict[str, Any]]:
    params = {}
    if kabupaten and kabupaten != "Semua Kabupaten":
        params["kabupaten"] = kabupaten
    response = requests.get(f"{API_BASE_URL}/api/v1/reference/foods", params=params, timeout=10)
    response.raise_for_status()
    return response.json()


def parse_menu(text: str) -> List[Dict[str, Any]]:
    response = requests.post(
        f"{API_BASE_URL}/api/v1/ai/parse",
        json={"text": text},
        timeout=20,
    )
    response.raise_for_status()
    payload = response.json()
    return payload.get("items", [])


def recommend_menu(deficiencies: Dict[str, str], local_catalog: List[str], count: int) -> List[str]:
    response = requests.post(
        f"{API_BASE_URL}/api/v1/ai/recommend",
        json={"deficiencies": deficiencies, "local_catalog": local_catalog, "count": count},
        timeout=20,
    )
    response.raise_for_status()
    payload = response.json()
    return payload.get("recommendations", [])


def find_food_match(item_name: str, foods: List[Dict[str, Any]], foods_by_norm: Dict[str, Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    normalized = normalize_name(item_name)
    if normalized in foods_by_norm:
        return foods_by_norm[normalized]
    for food in foods:
        food_norm = normalize_name(food["name"])
        if normalized in food_norm or food_norm in normalized:
            return food
    return None


def build_nutrient_totals(items: List[Dict[str, Any]], foods: List[Dict[str, Any]]) -> Dict[str, float]:
    totals = {nutrient: 0.0 for nutrient in NUTRIENT_LABELS}
    foods_by_norm = {normalize_name(food["name"]): food for food in foods}
    for item in items:
        match = find_food_match(item["name"], foods, foods_by_norm)
        if not match:
            continue
        factor = float(item.get("weight_gram", 0)) / 100.0
        for nutrient in totals:
            totals[nutrient] += float(match.get(nutrient, 0.0)) * factor
    return totals


def label_deficiency(intake: float, target: float) -> str:
    if target <= 0:
        return "N/A"
    ratio = intake / target
    if ratio >= 1.0:
        return "Cukup"
    if ratio >= 0.8:
        return "Perlu Perhatian"
    return "Defisien"


st.set_page_config(page_title="NutriMBG", page_icon="🥗", layout="centered", initial_sidebar_state="collapsed")
manage_sidebar_visibility()

if "user_role" not in st.session_state or not st.session_state["user_role"]:
    st.warning("Anda tidak memiliki akses ke halaman ini. Silakan login kembali.")
    st.stop()

render_top_bar()

st.title("NutriMBG")
st.write("Prototype validasi dan rekomendasi gizi untuk MBG.")

menu_text = st.text_area("Deskripsi menu harian", max_chars=500, height=160)
jenjang_label = st.selectbox("Jenjang pendidikan", list(EDUCATION_LEVELS.keys()))
kabupaten = st.selectbox("Kabupaten", KABUPATEN_OPTIONS)
recommend_count = st.slider("Jumlah rekomendasi menu", min_value=1, max_value=5, value=3)

if st.button("Analisa Menu"):
    if not menu_text.strip():
        st.warning("Masukkan deskripsi menu terlebih dahulu.")
    else:
        try:
            with st.spinner("Memproses menu..."):
                parsed_items = parse_menu(menu_text)
                foods = fetch_foods(kabupaten)
                akg_targets = fetch_akg(EDUCATION_LEVELS[jenjang_label])
        except requests.RequestException as exc:
            st.error(f"Gagal memproses data backend: {exc}")
        else:
            st.subheader("Hasil parsing menu")
            if parsed_items:
                st.table(parsed_items)
            else:
                st.info("Tidak ada item yang terdeteksi dari menu.")

            foods_by_norm = {normalize_name(food["name"]): food for food in foods}
            unmatched = [
                item["name"]
                for item in parsed_items
                if not find_food_match(item["name"], foods, foods_by_norm)
            ]
            if unmatched:
                st.warning(
                    "Item belum ditemukan di katalog lokal sehingga tidak dihitung pada analisa: "
                    + ", ".join(unmatched)
                )

            totals = build_nutrient_totals(parsed_items, foods)
            akg_by_nutrient = {row["nutrient_code"]: row for row in akg_targets}
            deficiencies: Dict[str, str] = {}
            rows = []
            for nutrient, label in NUTRIENT_LABELS.items():
                target_row = akg_by_nutrient.get(nutrient)
                target_value = float(target_row["target_value"]) if target_row else 0.0
                unit = target_row["unit"] if target_row else ""
                intake = totals.get(nutrient, 0.0)
                status = label_deficiency(intake, target_value)
                deficiencies[nutrient] = status
                rows.append(
                    {
                        "Nutrien": label,
                        "Asupan (estimasi)": round(intake, 2),
                        "Target": target_value,
                        "Unit": unit,
                        "Status": status,
                    }
                )

            st.subheader("Ringkasan kecukupan gizi")
            st.table(rows)

            try:
                recommendations = recommend_menu(
                    deficiencies=deficiencies,
                    local_catalog=[food["name"] for food in foods],
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
