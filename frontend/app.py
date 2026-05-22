from __future__ import annotations

from typing import Any, Dict, List, Optional

import requests
import streamlit as st

from components.manual_input_form import show_fallback_form
from components.parser_result import render_parser_result
from components.top_bar import render_top_bar
from utils.api_client import API_BASE_URL, AnalysisAPIError, ParserAPIError, analyze_manual_items, parse_menu
from utils.session import manage_sidebar_visibility


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

MANUAL_MODE_ACTIVE_KEY = "manual_analysis_active"
MANUAL_MODE_CONTEXT_KEY = "manual_analysis_context"
MANUAL_MODE_MESSAGE_KEY = "manual_analysis_message"


def normalize_name(value: str) -> str:
    return value.strip().lower()


def fetch_akg(level_code: str) -> List[Dict[str, Any]]:
    response = requests.get(f"{API_BASE_URL}/api/v1/reference/akg/{level_code}", timeout=10)
    response.raise_for_status()
    return response.json()


def fetch_foods(kabupaten: Optional[str]) -> List[Dict[str, Any]]:
    params: Dict[str, Any] = {}
    if kabupaten and kabupaten != "Semua Kabupaten":
        params["kabupaten"] = kabupaten
    response = requests.get(f"{API_BASE_URL}/api/v1/reference/foods", params=params, timeout=10)
    response.raise_for_status()
    return response.json()


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
        factor = float(item.get("weight_gram", item.get("weight_g", 0))) / 100.0
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


def render_analysis(items: List[Dict[str, Any]], foods: List[Dict[str, Any]], akg_targets: List[Dict[str, Any]], recommend_count: int) -> None:
    render_parser_result(items, source_label="Input manual", fallback=True)

    foods_by_norm = {normalize_name(food["name"]): food for food in foods}
    unmatched = [item["name"] for item in items if not find_food_match(item["name"], foods, foods_by_norm)]
    if unmatched:
        st.warning(
            "Item belum ditemukan di katalog lokal sehingga tidak dihitung pada analisa: " + ", ".join(unmatched)
        )

    totals = build_nutrient_totals(items, foods)
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
        response = requests.post(
            f"{API_BASE_URL}/api/v1/ai/recommend",
            json={
                "deficiencies": deficiencies,
                "local_catalog": [food["name"] for food in foods],
                "count": recommend_count,
            },
            timeout=20,
        )
        response.raise_for_status()
        payload = response.json()
        recommendations = payload.get("recommendations", [])
    except requests.RequestException as exc:
        st.error(f"Gagal meminta rekomendasi menu: {exc}")
    else:
        st.subheader("Rekomendasi menu")
        if recommendations:
            for rec in recommendations:
                st.write(f"- {rec}")
        else:
            st.info("Belum ada rekomendasi yang dihasilkan.")


def render_manual_analysis_payload(payload: Dict[str, Any]) -> None:
    items = payload.get("items", [])
    totals = payload.get("totals", {})
    labels = payload.get("labels", {})
    unmatched = payload.get("unmatched_items", [])
    recommendations = payload.get("recommendations", [])
    score = float(payload.get("score", 0.0))

    render_parser_result(items, source_label="Input manual", fallback=True)

    if unmatched:
        st.warning(
            "Item belum ditemukan di katalog lokal sehingga tidak dihitung pada analisa: " + ", ".join(unmatched)
        )

    rows = []
    for nutrient, label in NUTRIENT_LABELS.items():
        rows.append(
            {
                "Nutrien": label,
                "Asupan (estimasi)": round(float(totals.get(nutrient, 0.0)), 2),
                "Target": "-",
                "Unit": "",
                "Status": labels.get(nutrient, "N/A"),
            }
        )

    st.subheader("Ringkasan kecukupan gizi")
    st.metric("Skor total", f"{score:.2f}")
    st.table(rows)

    st.subheader("Rekomendasi menu")
    if recommendations:
        for rec in recommendations:
            st.write(f"- {rec}")
    else:
        st.info("Belum ada rekomendasi yang dihasilkan.")


def _set_manual_mode(kabupaten: str, jenjang_label: str, recommend_count: int, message: str) -> None:
    st.session_state[MANUAL_MODE_ACTIVE_KEY] = True
    st.session_state[MANUAL_MODE_CONTEXT_KEY] = {
        "kabupaten": kabupaten,
        "jenjang_label": jenjang_label,
        "recommend_count": recommend_count,
    }
    st.session_state[MANUAL_MODE_MESSAGE_KEY] = message


def _clear_manual_mode() -> None:
    st.session_state[MANUAL_MODE_ACTIVE_KEY] = False
    st.session_state.pop(MANUAL_MODE_CONTEXT_KEY, None)
    st.session_state.pop(MANUAL_MODE_MESSAGE_KEY, None)


def main() -> None:
    st.set_page_config(page_title="GiziMeter | NutriMBG", page_icon="🥗", layout="centered", initial_sidebar_state="collapsed")
    manage_sidebar_visibility()

    if "user_role" not in st.session_state or not st.session_state["user_role"]:
        st.warning("Anda tidak memiliki akses ke halaman ini. Silakan login kembali.")
        st.stop()

    render_top_bar()

    st.title("GiziMeter")
    st.write("Prototype validasi dan rekomendasi gizi untuk MBG.")

    menu_text = st.text_area("Deskripsi menu harian", max_chars=500, height=160)
    jenjang_label = st.selectbox("Jenjang pendidikan", list(EDUCATION_LEVELS.keys()))
    kabupaten = st.selectbox("Kabupaten", KABUPATEN_OPTIONS)
    recommend_count = st.slider("Jumlah rekomendasi menu", min_value=1, max_value=5, value=3)

    if MANUAL_MODE_ACTIVE_KEY not in st.session_state:
        st.session_state[MANUAL_MODE_ACTIVE_KEY] = False

    if st.button("Analisa Menu"):
        if not menu_text.strip():
            st.warning("Masukkan deskripsi menu terlebih dahulu.")
            return

        try:
            with st.spinner("Memproses menu..."):
                parsed_items = parse_menu(menu_text)
                foods = fetch_foods(kabupaten)
                akg_targets = fetch_akg(EDUCATION_LEVELS[jenjang_label])
        except ParserAPIError as exc:
            st.warning("Parser tidak tersedia. Masukkan bahan secara manual.", icon="⚠️")
            st.caption(f"Jenis error parser: {exc.kind}")
            _set_manual_mode(kabupaten, jenjang_label, recommend_count, exc.message)
        except Exception as exc:
            st.error(f"Gagal memproses data backend: {exc}")
        else:
            render_parser_result(parsed_items, source_label="Parser AI")
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
                recommendations_response = requests.post(
                    f"{API_BASE_URL}/api/v1/ai/recommend",
                    json={
                        "deficiencies": deficiencies,
                        "local_catalog": [food["name"] for food in foods],
                        "count": recommend_count,
                    },
                    timeout=20,
                )
                recommendations_response.raise_for_status()
                recommendations_payload = recommendations_response.json()
                recommendations = recommendations_payload.get("recommendations", [])
            except requests.RequestException as exc:
                st.error(f"Gagal meminta rekomendasi menu: {exc}")
            else:
                st.subheader("Rekomendasi menu")
                if recommendations:
                    for rec in recommendations:
                        st.write(f"- {rec}")
                else:
                    st.info("Belum ada rekomendasi yang dihasilkan.")

    if st.session_state.get(MANUAL_MODE_ACTIVE_KEY):
        context = st.session_state.get(MANUAL_MODE_CONTEXT_KEY, {})
        manual_kabupaten = context.get("kabupaten", kabupaten)
        manual_jenjang_label = context.get("jenjang_label", jenjang_label)
        manual_recommend_count = int(context.get("recommend_count", recommend_count))

        manual_items = show_fallback_form(manual_kabupaten)
        if manual_items:
            try:
                analysis_payload = analyze_manual_items(
                    [
                        {"name": row["name"], "weight_gram": float(row["weight_g"])}
                        for row in manual_items
                    ],
                    EDUCATION_LEVELS[manual_jenjang_label],
                    manual_kabupaten,
                    manual_recommend_count,
                )
            except AnalysisAPIError as exc:
                st.error(f"Gagal memproses input manual di backend: {exc.message}")
            else:
                render_manual_analysis_payload(analysis_payload)
                _clear_manual_mode()


if __name__ == "__main__":
    main()
