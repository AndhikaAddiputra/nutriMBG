import streamlit as st

st.set_page_config(page_title="Login | NutriMBG", page_icon="🔒", layout="centered")

selected_role = st.session_state.get("login_role_preselect", "koordinator")

if st.button("← Kembali ke Beranda"):
    st.switch_page("00_Beranda.py")

st.title("Masuk ke NutriMBG")
st.markdown(f"Silakan masukkan kredensial Anda untuk masuk sebagai **{selected_role.capitalize()}**.")

with st.form("login_form"):
    username = st.text_input("Username", placeholder="Masukkan username Anda")
    password = st.text_input("Password", type="password", placeholder="Masukkan password Anda")
    
    submitted = st.form_submit_button("Masuk", use_container_width=True)

    if submitted:
        # Nanti kamu bisa mengganti bagian ini dengan query ke database/API yang sesungguhnya
        if username == "admin" and password == "12345":
            st.success("Login berhasil! Memuat dashboard...")
            
            st.session_state["user_role"] = selected_role
            
            if selected_role == "koordinator":
                st.switch_page("pages/GiziMeter.py") 
            elif selected_role == "administrator":
                st.switch_page("pages/GiziMeter.py")
        else:
            st.error("Username atau password salah! (Hint: gunakan admin / 12345)")