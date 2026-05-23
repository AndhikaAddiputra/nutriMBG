import streamlit as st
import time
from utils.session import save_session, check_auth_redirect, get_redirect_target, manage_sidebar_visibility
from utils.api import login, AuthError

st.set_page_config(page_title="Login | NutriMBG", page_icon="🔐", layout="centered")
manage_sidebar_visibility()

check_auth_redirect()

st.markdown("<h2 style='text-align: center;'>Masuk ke NutriMBG</h2>", unsafe_allow_html=True)

preselect_val = st.session_state.get("login_role_preselect", "koordinator")
default_idx = 0 if preselect_val == "koordinator" else 1

st.markdown("<div style='text-align:center; margin-bottom: 10px;'>Pilih Peran Akses:</div>", unsafe_allow_html=True)
selected_tab = st.radio(
    "Peran", 
    ["👨‍🏫 Koordinator", "⚙️ Administrator"], 
    index=default_idx, 
    horizontal=True,
    label_visibility="collapsed"
)

if "Koordinator" in selected_tab:
    active_role = "koordinator"
    accent_color = "#28a745"
    btn_label = "Masuk sebagai Koordinator"
    demo_hint = "Hint: koor@nutrimbg.go.id | pass: koor123"
else:
    active_role = "administrator"
    accent_color = "#007bff"
    btn_label = "Masuk sebagai Administrator"
    demo_hint = "Hint: admin@nutrimbg.go.id | pass: admin123"

st.markdown(f"""
    <style>
        div[data-testid="stForm"] {{
            border-top: 4px solid {accent_color} !important;
            border-radius: 10px;
        }}
    </style>
""", unsafe_allow_html=True)

with st.form("login_form"):
    st.markdown(f"#### {selected_tab}")
    email_input = st.text_input("Alamat Email", placeholder="contoh@nutrimbg.go.id")
    pass_input = st.text_input("Kata Sandi", type="password")
    
    submit_btn = st.form_submit_button(btn_label, use_container_width=True)

    if submit_btn:
        try:
            res = login(email_input, pass_input, active_role)
            save_session(
                token=res['token'],
                user_id=res['user']['id'],
                role=active_role,
                name=res['user']['name'],
                district=res['user']['district']
            )
            
            target_path = get_redirect_target(active_role)
            st.switch_page(target_path)
            
        except AuthError as e:
            st.error(f"❌ Login Gagal: {str(e)}")

st.caption(demo_hint) # Baris ini dihapus saat di production

st.info("Lupa kata sandi? Hubungi administrator wilayah Anda.")