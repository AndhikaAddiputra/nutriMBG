import streamlit as st

def check_auth_redirect():
    if "user_role" in st.session_state and st.session_state["user_role"]:
        role = st.session_state["user_role"]
        
        if role == "koordinator":
            st.switch_page("pages/GiziMeter.py") 
        elif role == "administrator":
            st.switch_page("pages/GiziMeter.py")

def logout():
    keys_to_clear = ["user_role", "username", "login_role_preselect"]
    for key in keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]
    
    st.switch_page("00_Beranda.py")

def manage_sidebar_visibility():
    is_logged_in = "user_role" in st.session_state and st.session_state["user_role"]
    
    if is_logged_in:
        st.markdown(
            """
            <style>
            /* Menyembunyikan link yang mengandung kata 'login' dan 'Beranda' */
            [data-testid="stSidebarNav"] ul li a[href*="Login"] { display: none !important; }
            [data-testid="stSidebarNav"] ul li a[href*="00_Beranda"] { display: none !important; }
            </style>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            """
            <style>
            [data-testid="stSidebarNav"] ul li a[href*="Dashboard"] { display: none !important; }
            </style>
            """,
            unsafe_allow_html=True,
        )