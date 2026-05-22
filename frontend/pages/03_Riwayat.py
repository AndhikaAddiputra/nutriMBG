import streamlit as st
import requests
import datetime

# ... (Existing imports and setup)

st.header("Laporan Gizi Mingguan")

col1, col2 = st.columns([2, 1])

with col1:
    # Set default to the monday of the current week
    today = datetime.date.today()
    monday = today - datetime.timedelta(days=today.weekday())
    selected_week_start = st.date_input("Tanggal Mulai Minggu (Senin)", value=monday)
    sppg_name = st.text_input("Nama SPPG", value="SPPG Jakarta")

with col2:
    st.write("") # Spacing
    st.write("")
    
    # We load the PDF from the backend endpoint
    if st.button("Generate Laporan"):
        with st.spinner("Memproses PDF dalam <10 detik..."):
            backend_url = f"http://localhost:8000/reports/weekly" # adjust port/url based on docker-compose
            params = {
                "week_start": selected_week_start.strftime("%Y-%m-%d"),
                "sppg_name": sppg_name
            }
            
            try:
                response = requests.get(backend_url, params=params)
                if response.status_code == 200:
                    filename = f"laporan_mingguan_{sppg_name.replace(' ', '_')}_{selected_week_start}.pdf"
                    st.success("Laporan berhasil dibuat!")
                    
                    # Display the Streamlit native download button
                    st.download_button(
                        label="Unduh Laporan Mingguan (PDF)",
                        data=response.content,
                        file_name=filename,
                        mime="application/pdf",
                        type="primary"
                    )
                else:
                    st.error(f"Gagal mengambil laporan dari server. (Code: {response.status_code})")
            except requests.exceptions.RequestException as e:
                st.error("Koneksi ke backend gagal.")