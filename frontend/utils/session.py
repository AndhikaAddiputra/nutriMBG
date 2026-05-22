import streamlit as st

def manage_sidebar_visibility():
    is_logged_in = "user_role" in st.session_state and st.session_state["user_role"]
    
    if is_logged_in:
        st.markdown(
            """
            <style>
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
            [data-testid="stSidebarNav"] ul li a[href*="Login"] { display: none !important; }
            [data-testid="stSidebarNav"] ul li a[href*="Dashboard"] { display: none !important; }
            </style>
            """,
            unsafe_allow_html=True,
        )

def save_session(token, user_id, role, name, district):
    st.session_state["auth_token"] = token
    st.session_state["user_id"] = user_id
    st.session_state["user_role"] = role
    st.session_state["user_name"] = name
    st.session_state["user_district"] = district

def clear_session():
    keys = ["auth_token", "user_id", "user_role", "user_name", "user_district"]
    for key in keys:
        if key in st.session_state:
            del st.session_state[key]

def logout():
    clear_session()
    if "login_role_preselect" in st.session_state:
        del st.session_state["login_role_preselect"]
    
    st.success("Anda telah berhasil keluar.")
    st.switch_page("00_Beranda.py")

def get_redirect_target(role):
    if role == "koordinator":
        return "pages/GiziMeter.py"
    elif role == "administrator":
        return "pages/Dashboard.py"
    return None

def check_auth_redirect():
    if "auth_token" in st.session_state and st.session_state.get("user_role"):
        target = get_redirect_target(st.session_state["user_role"])
        if target:
            st.switch_page(target)

def require_auth(allowed_roles=None):
    if "auth_token" not in st.session_state:
        st.warning("Anda harus login untuk mengakses halaman ini.")
        st.switch_page("pages/01_Login.py")
    
    current_role = st.session_state.get("user_role")
    
    if allowed_roles and current_role not in allowed_roles:
        st.error("Anda tidak memiliki akses ke halaman ini.")
        target = get_redirect_target(current_role)
        if target:
            st.switch_page(target)
        else:
            st.stop()