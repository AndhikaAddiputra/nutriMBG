import os

import requests
import streamlit as st
from utils.session import require_auth, manage_sidebar_visibility, clear_session

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

st.set_page_config(page_title="Administrator | NutriMBG", layout="wide")
manage_sidebar_visibility()
require_auth(allowed_roles=["administrator"])


def _headers():
    token = st.session_state.get("auth_token", "")
    if token:
        return {"Authorization": f"Bearer {token}"}
    return {}


def fetch_stats():
    try:
        r = requests.get(f"{API_BASE_URL}/api/admin/stats", headers=_headers(), timeout=10)
        r.raise_for_status()
        return r.json()
    except requests.RequestException:
        return None


def fetch_users(search=""):
    params = {"page": 1, "per_page": 50}
    if search:
        params["search"] = search
    try:
        r = requests.get(f"{API_BASE_URL}/api/admin/users", params=params, headers=_headers(), timeout=10)
        r.raise_for_status()
        return r.json()
    except requests.RequestException:
        return None


col1, col2 = st.columns([8, 1])
with col1:
    st.title("Panel Administrator")
    st.write(f"Wilayah: **{st.session_state.get('user_district', '-')}**")
with col2:
    if st.button("Logout"):
        clear_session()
        st.switch_page("00_Beranda.py")

st.divider()

stats = fetch_stats()
if stats is None:
    st.error("Gagal mengambil data dari backend. Pastikan server berjalan.")
    st.stop()

row = st.columns(5)
with row[0]:
    st.metric("Total Analisa", stats["total_analyses"])
with row[1]:
    st.metric("Rata-rata Skor", f'{stats["average_score"]:.1f}')
with row[2]:
    st.metric("Analisa Hari Ini", stats["today_analyses"])
with row[3]:
    st.metric("Pengguna Aktif", stats["total_users"])
with row[4]:
    st.metric("Bahan Makanan", stats["total_foods"])

st.divider()

tab1, tab2, tab3 = st.tabs(["Analisa Terbaru", "Manajemen Pengguna", "Akses Cepat"])

with tab1:
    recent = stats.get("recent_analyses", [])
    if recent:
        table = []
        for a in recent:
            table.append({
                "ID": a["id"],
                "Menu": a["menu_text"],
                "Jenjang": a["education_level"],
                "Skor": f'{a["score_total"]:.1f}',
                "Waktu": a["created_at"][:19].replace("T", " "),
            })
        st.table(table)
    else:
        st.info("Belum ada data analisa.")

with tab2:
    st.subheader("Daftar Pengguna")

    search = st.text_input("Cari pengguna (nama/email)", key="user_search")
    users_data = fetch_users(search)
    if users_data and users_data.get("items"):
        user_table = []
        for u in users_data["items"]:
            user_table.append({
                "ID": u["id"],
                "Nama": u["full_name"],
                "Email": u["email"],
                "Peran": u["role"],
                "Provinsi": u["province"],
                "Kabupaten": u["kabupaten"],
                "Aktif": "✅" if u["is_active"] else "❌",
            })
        st.table(user_table)
        st.caption(f"Total {users_data['total']} pengguna")
    else:
        st.info("Tidak ada pengguna ditemukan.")

    st.divider()
    st.subheader("Tambah Pengguna Baru")
    with st.form("add_user_form"):
        c1, c2 = st.columns(2)
        with c1:
            full_name = st.text_input("Nama Lengkap")
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
        with c2:
            role = st.selectbox("Peran", ["coordinator", "admin"])
            province = st.text_input("Provinsi")
            kabupaten = st.text_input("Kabupaten/Kota")
        submitted = st.form_submit_button("Tambah Pengguna", use_container_width=True)
        if submitted:
            try:
                r = requests.post(
                    f"{API_BASE_URL}/api/admin/users",
                    json={
                        "full_name": full_name,
                        "email": email,
                        "password": password,
                        "role": role,
                        "province": province,
                        "kabupaten": kabupaten,
                        "default_education_level": "SMP",
                    },
                    headers=_headers(),
                    timeout=10,
                )
                if r.status_code == 201:
                    st.success("Pengguna berhasil ditambahkan!")
                    st.rerun()
                elif r.status_code == 409:
                    st.error("Email sudah terdaftar.")
                else:
                    st.error(f"Gagal: {r.text}")
            except requests.RequestException as e:
                st.error(f"Koneksi gagal: {e}")

with tab3:
    fast_cols = st.columns(3)
    with fast_cols[0]:
        st.page_link("pages/GiziMeter.py", label="🔬 Buka GiziMeter", use_container_width=True)
    with fast_cols[1]:
        st.page_link("pages/03_Riwayat.py", label="📈 Buka Riwayat", use_container_width=True)
    with fast_cols[2]:
        st.markdown("[Kelola Bahan Makanan](/#)", help="Fitur manajemen bahan segera hadir.")
