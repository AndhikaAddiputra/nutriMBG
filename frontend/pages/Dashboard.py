import streamlit as st
from utils.session import require_auth, manage_sidebar_visibility, clear_session

st.set_page_config(page_title="Administrator | NutriMBG", layout="wide")
manage_sidebar_visibility()

require_auth(allowed_roles=["administrator"])

col1, col2 = st.columns([8, 1])
with col1:
    st.title("⚙️ Halaman Administrator")
    st.write(f"Sistem kontrol wilayah: **{st.session_state.get('user_district')}**")
with col2:
    if st.button("Logout"):
        clear_session()
        st.switch_page("00_Beranda.py")

st.info("Fitur manajemen admin sedang dalam pengembangan (Task Berikutnya).")