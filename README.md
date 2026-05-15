# nutriMBG

Prototype sistem validasi dan rekomendasi gizi berbasis AI untuk Program Makan Bergizi Gratis (MBG).

## Arsitektur singkat
- Frontend: Streamlit
- Backend: FastAPI
- Database: PostgreSQL
- AI pipeline: Parser (Gemini), Classifier (ML), Generator/ Recomendator (Ollama)

## Bagaimana sistem ini bekerja?
Secara garis besar, sistem ini menerima input menu harian, lalu menghitung apakah kandungan gizinya sudah sesuai target AKG untuk jenjang usia tertentu.

Alur utamanya:
1. User mengetik menu di frontend (contoh: "nasi, ayam, bayam").
2. Backend memanggil AI Parser untuk memecah teks menjadi daftar bahan + estimasi berat.
3. Setiap bahan dicocokkan ke data kandungan gizi (TKPI).
4. Sistem menghitung total nutrisi menu (protein, karbohidrat, lemak, serat, besi, vitamin A).
5. Total nutrisi dibandingkan dengan AKG (SD/SMP/SMA) untuk mendapatkan rasio kecukupan.
6. Model ML mengubah rasio tersebut menjadi skor menu, lalu sistem memberi label per nutrien (Cukup/Perlu Perhatian/Defisien).
7. Jika diperlukan, AI Generator memberi alternatif rekomendasi menu.

## Komponen utama yang perlu dipahami tim
- **Parser AI**: mengubah teks menu bebas menjadi bahan terstruktur.
- **Data referensi (TKPI + AKG)**: sumber angka gizi dan target kebutuhan.
- **Classifier ML**: menghitung skor keseluruhan menu dari fitur nutrisi.
- **Recommender AI**: membuat saran menu berdasarkan nutrien yang masih kurang.

## Struktur direktori
- backend/: layanan API FastAPI dan pipeline AI
- frontend/: aplikasi Streamlit
- docker-compose.yml: database PostgreSQL lokal
- .env.example: contoh konfigurasi lingkungan

## Menjalankan lokal
1. Isi nilai `.env` yang dibutuhkan (terutama `GEMINI_API_KEY`).
2. Jalankan database: `docker compose up -d`.
3. Backend: `cd backend && pip install -r requirements.txt && uvicorn app.main:app --reload`.
4. (Opsional) Atur target API: `export API_BASE_URL=http://localhost:8000`.
5. Frontend: `cd frontend && pip install -r requirements.txt && streamlit run app.py`.

## Setup backend & frontend (step-by-step)
Backend (FastAPI):
1. `cd backend`
2. `python3 -m venv .venv && source .venv/bin/activate`
3. `pip install -r requirements.txt`
4. Dari root repo: `cp .env.example .env` lalu isi `GEMINI_API_KEY` (opsional jika hanya pakai classifier).
5. `docker compose up -d` (jalankan PostgreSQL)
6. `uvicorn app.main:app --reload`

Frontend (Streamlit):
1. `cd frontend`
2. `python3 -m venv .venv && source .venv/bin/activate`
3. `pip install -r requirements.txt`
4. `streamlit run app.py`

## Seed dummy data (Fase Beta sementara)
1. Jalankan PostgreSQL: `docker compose up -d`.
2. Jalankan seeder: `cd backend && python3 scripts/seed_dummy_data.py`.
3. Cek endpoint referensi:
   - `GET /api/v1/reference/akg/SMP`
    - `GET /api/v1/reference/foods`
    - `GET /api/v1/reference/foods?kabupaten=Kabupaten%20Bandung`

## Endpoint AI (Gemini)
- `POST /api/menu/parse` body: `{"text":"nasi, ayam goreng, bayam"}`
- `POST /api/menu/recommend` body: `{"deficiencies":{"fiber":"Defisien"}, "local_catalog":["bayam","wortel"], "count":2}`
- `POST /api/menu/analyze` body: `{"text":"nasi, ayam goreng, bayam", "education_level":"SMP"}`
- `POST /api/v1/ai/parse` body: `{"text":"nasi, ayam goreng, bayam"}`
- `POST /api/v1/ai/recommend` body: `{"deficiencies":{"fiber":"Defisien"}, "local_catalog":["bayam","wortel"], "count":2}`
- `POST /api/v1/ai/classify` body: `{"text":"nasi, ayam goreng, bayam", "education_level":"SMP"}`

## Pipeline classifier (ML)
Dataset ini menggunakan 6 nutrien inti: protein, karbohidrat, lemak, serat, zat besi, vitamin A.

Kategori AKG yang dipakai:
- **SD**: rata-rata AKG usia 7-9 dan 10-12 tahun (untuk rentang 6-12).
- **SMP**: usia 13-15 tahun.
- **SMA**: usia 16-18 tahun.

Skor menu = rata-rata rasio asupan/AKG (per nutrien), dengan cap 1.2, lalu dikali 100.

### Proses training model ML (langkah mudah)
Tujuan training: membuat model yang bisa memprediksi **skor menu** dari data nutrisi.

1. **Siapkan data mentah** di folder `/dataset` (menu nusantara, TKPI, AKG, bahan lokal).
2. **Bangun dataset training** dengan script:
   - Membaca bahan resep dari dataset menu.
   - Mengonversi bahan menjadi total nutrisi per menu.
   - Membandingkan total nutrisi dengan target AKG SD/SMP/SMA.
   - Menghasilkan fitur rasio nutrisi + label nutrien + skor menu.
3. **Latih model** dari dataset hasil langkah 2.
4. **Simpan model** ke `backend/artifacts/classifier.joblib`.
5. Saat backend berjalan, endpoint `/api/v1/ai/classify` memakai model ini untuk prediksi skor real-time.

### Kapan perlu training ulang?
- Saat ada perubahan besar pada data menu/dataset.
- Saat menambah banyak alias bahan di `dataset/aliases.csv`.
- Saat ingin meningkatkan akurasi model.

Langkah training:
1. Pastikan semua data ada di folder `/dataset` sesuai struktur yang sudah disediakan.
2. (Opsional) Tambahkan alias bahan di `dataset/aliases.csv` untuk mapping nama masakan → bahan dasar.
3. Build dataset: `cd backend && python3 scripts/build_classifier_dataset.py`.
4. Train model: `cd backend && python3 scripts/train_classifier.py`.
5. Jalankan backend dan gunakan endpoint `/api/v1/ai/classify` (pastikan model sudah ada di `backend/artifacts/classifier.joblib`).

## Kriteria data training yang baik (untuk nanti saat scraping selesai)
- **Representatif lintas wilayah**: menu dan bahan dari banyak daerah, bukan dominan satu pola masak.
- **Label akurat & konsisten**: aturan Cukup/Perlu Perhatian/Defisien harus konsisten ke seluruh sampel.
- **Distribusi seimbang**: tiap label gizi (terutama Defisien) cukup banyak agar model tidak bias.
- **Input realistis**: variasi typo, sinonim, bahasa sehari-hari, dan variasi takaran porsi.
- **Coverage nutrien tinggi**: minim nilai kosong pada 6 nutrien inti; jika kosong harus ditandai/imputasi jelas.
- **Split data bersih**: pisahkan train/valid/test berdasarkan resep unik agar tidak leakage.
