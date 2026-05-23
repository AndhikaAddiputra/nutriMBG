import streamlit as st
from utils.session import logout

def render_top_bar():
    if "user_role" in st.session_state and st.session_state["user_role"]:
        col_info, col_logout = st.columns([8, 2])
        
        with col_info:
            username = st.session_state.get("user_name", "User")
            role = st.session_state.get("user_role", "").title()
            st.markdown(f"<h5 style='margin-top: 10px;'>👋 Halo, {username} ({role})</h5>", unsafe_allow_html=True)
            
        with col_logout:
            if st.button("🚪 Logout", use_container_width=True, type="secondary"):
                logout()
                
        st.divider()