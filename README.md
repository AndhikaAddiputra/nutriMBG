# nutriMBG

Prototype sistem validasi dan rekomendasi gizi berbasis AI untuk Program Makan Bergizi Gratis (MBG).

## Arsitektur singkat
- Frontend: Streamlit
- Backend: FastAPI
- Database: PostgreSQL
- AI pipeline: Parser (OpenAI), Classifier (ML), Generator (Ollama/Llama 3)

## Struktur direktori
- backend/: layanan API FastAPI dan pipeline AI
- frontend/: aplikasi Streamlit
- docker-compose.yml: database PostgreSQL lokal
- .env.example: contoh konfigurasi lingkungan

## Menjalankan lokal
1. Salin `.env.example` ke `.env` dan isi nilai yang dibutuhkan.
2. Jalankan database: `docker compose up -d`.
3. Backend: `cd backend && pip install -r requirements.txt && uvicorn app.main:app --reload`.
4. Frontend: `cd frontend && pip install -r requirements.txt && streamlit run app.py`.
