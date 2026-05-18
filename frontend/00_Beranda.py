import streamlit as st
import os
from utils.session import check_auth_redirect, manage_sidebar_visibility
from components.role_selector_card import render_role_card
from components.top_bar import render_top_bar

st.set_page_config(page_title="Beranda | NutriMBG", page_icon="🥗", layout="centered", initial_sidebar_state="collapsed")
manage_sidebar_visibility()

is_logged_in = "user_role" in st.session_state and st.session_state["user_role"]
if is_logged_in:
    render_top_bar()

# --- CSS Injection Tambahan (Opsional) ---
st.markdown("""
    <style>
        #MainMenu {visibility: hidden;}
        header {visibility: hidden;}
        footer {visibility: hidden;}
        /* Memastikan footer custom tetap di bawah */
        .custom-footer {
            text-align: center;
            color: #6c757d;
            font-size: 0.85rem;
            margin-top: 50px;
            padding-top: 20px;
            border-top: 1px solid #dee2e6;
        }
    </style>
""", unsafe_allow_html=True)

col_logo, col_text = st.columns([1, 4])
with col_logo:
    logo_path = "assets/logo_nutrimbg.png"
    if os.path.exists(logo_path):
        st.image(logo_path, width=80)
    else:
        st.markdown("<h1>🥗</h1>", unsafe_allow_html=True)

with col_text:
    st.title("NutriMBG")
    st.markdown("**Sistem Manajemen Gizi Cerdas Terintegrasi**")

st.markdown("""
Selamat datang di NutriMBG. Platform ini didesain khusus untuk mendukung **Program Makan Bergizi Gratis (MBG)** melalui pendekatan berbasis data. 
Kami membantu memastikan setiap sajian memenuhi standar gizi yang optimal secara efisien dan transparan.
""")

st.divider()

if not is_logged_in:
    st.subheader("Masuk ke Sistem")
    col_role1, col_role2 = st.columns(2)

    with col_role1:
        render_role_card(
            title="Koordinator SPPG",
            description="Akses untuk mengelola operasional harian, memantau distribusi, dan pelaporan SPPG di lapangan.",
            icon="👨‍🏫",
            role_value="koordinator"
        )

    with col_role2:
        render_role_card(
            title="Administrator",
            description="Akses penuh manajemen sistem, konfigurasi master data gizi, dan pemantauan menyeluruh.",
            icon="⚙️",
            role_value="administrator"
        )
else:
    role_aktif = st.session_state['user_role']
    st.success(f"Anda saat ini telah masuk ke dalam sistem sebagai **{role_aktif.title()}**.")
    
    if st.button("🚀 Buka Dashboard Saya", use_container_width=True, type="primary"):
        st.switch_page("pages/GiziMeter.py")

st.divider()

st.subheader("Fitur Unggulan")
f_col1, f_col2 = st.columns(2)

with f_col1:
    with st.container(border=True):
        st.markdown("#### 🤖 Parser AI")
        st.markdown("Otomatisasi ekstraksi dan pembacaan data gizi dari berbagai format dokumen untuk efisiensi input.")
    
    with st.container(border=True):
        st.markdown("#### 📊 Klasifikasi Gizi")
        st.markdown("Pemetaan instan dan akurat bahan makanan sesuai dengan standar gizi yang ditetapkan regulator.")

with f_col2:
    with st.container(border=True):
        st.markdown("#### 🍱 Rekomendasi Menu")
        st.markdown("Algoritma penyusunan menu cerdas berdasarkan ketersediaan bahan, target kalori, dan variasi harian.")
    
    with st.container(border=True):
        st.markdown("#### 📑 Ekspor Laporan")
        st.markdown("Pembuatan laporan siap unduh yang terstandardisasi untuk kebutuhan audit dan pemangku kepentingan.")

st.markdown(
    """
    <div class="custom-footer">
        Referensi Regulasi: <strong><a href="https://www.google.com/url?sa=t&source=web&rct=j&opi=89978449&url=https://peraturan.bpk.go.id/Download/129886/Permenkes%2520Nomor%252028%2520Tahun%25202019.pdf&ved=2ahUKEwjLkrKbtsKUAxV-T2wGHVRRJz0QFnoECBwQAQ&usg=AOvVaw06XxziNG6htDQEtdqMFV7_">Permenkes RI No. 28/2019</a></strong> tentang Angka Kecukupan Gizi (AKG) yang Dianjurkan untuk Masyarakat Indonesia
    </div>
    """, 
    unsafe_allow_html=True
)