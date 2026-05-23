import streamlit as st

def render_role_card(title: str, description: str, icon: str, role_value: str, login_page_path: str = "pages/Login.py"):
    with st.container(border=True):
        st.markdown(f"### {icon} {title}")
        st.markdown(f"<div style='min-height: 60px;'>{description}</div>", unsafe_allow_html=True)
        
        if st.button(f"Masuk sebagai {title}", key=f"btn_{role_value}", use_container_width=True):
            st.session_state["login_role_preselect"] = role_value
            try:
                st.switch_page(login_page_path)
            except Exception as e:
                st.error(f"Halaman login belum tersedia di {login_page_path}")