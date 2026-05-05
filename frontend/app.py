import os

import requests
import streamlit as st


API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

st.set_page_config(page_title="NutriMBG", layout="wide")

st.title("NutriMBG")
st.write("Prototype validasi dan rekomendasi gizi untuk MBG.")

menu_text = st.text_area("Deskripsi menu harian", max_chars=500, height=160)
jenjang = st.selectbox(
    "Jenjang pendidikan",
    ["SD Kelas 1-3", "SD Kelas 4-6", "SMP", "SMA"],
)

if st.button("Analisa Menu"):
    if not menu_text.strip():
        st.warning("Masukkan deskripsi menu terlebih dahulu.")
    else:
        try:
            response = requests.get(f"{API_BASE_URL}/health", timeout=5)
            if response.ok:
                st.success("Backend aktif. Endpoint analisa menu belum diimplementasikan.")
            else:
                st.error("Backend tidak siap. Periksa service API.")
        except requests.RequestException:
            st.error("Tidak bisa terhubung ke backend.")
