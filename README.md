
# Sector Growth Dashboard

Dashboard Streamlit multipage untuk proyek Sector Growth Insight (PLN Icon Plus).

Pipeline pengolahan data dan migrasi database berada di repository terpisah: **sector-growth-pipeline**.

## Status Pengembangan

Frontend saat ini menyediakan empat halaman mockup:
- Overview
- Growth Trends
- Sector Analysis
- Data Explorer

Data yang ditampilkan masih berupa ilustrasi dan belum terhubung ke Neon DB.

## Teknologi

- Python 3.12
- Streamlit 1.66.1
- Pandas
- Plotly
- SQLAlchemy
- psycopg2-binary
- python-dotenv

## Struktur Proyek

- `app.py`: halaman utama dashboard.
- `pages/`: halaman multipage.
- `components/`: komponen UI yang digunakan kembali.
- `utils/db.py`: helper koneksi PostgreSQL.
- `assets/`: aset visual.
- `.streamlit/config.toml`: konfigurasi tema.
- `tests/`: lokasi pengujian.
- `requirements.txt`: daftar dependensi Python.

## Menjalankan Secara Lokal

Gunakan Python 3.12.

Buat virtual environment:

```powershell
py -3.12 -m venv .venv
```

Aktifkan di PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Instal dependensi:

```powershell
python -m pip install -r requirements.txt
```

Jalankan aplikasi:

```powershell
python -m streamlit run app.py
```

## Konfigurasi Database

Helper database dirancang untuk memprioritaskan `st.secrets`, kemudian menggunakan variabel lingkungan lokal sebagai fallback.

Untuk development lokal, gunakan file `.env` dengan variabel `DATABASE_URL`. Untuk deployment Streamlit Community Cloud, konfigurasi rahasia disimpan melalui pengaturan Secrets aplikasi.

File `.env` dan `.streamlit/secrets.toml` tidak boleh di-commit.

Integrasi database belum diaktifkan. Tunggu konfirmasi skema dan kredensial resmi dari tim backend sebelum menjalankan query ke Neon DB.

## Aturan Kerja Tim

- Satu halaman per orang atau sumber di folder `pages/`.
- Jangan commit `.streamlit/secrets.toml` atau kredensial apa pun.
- Setiap anggota bekerja pada branch masing-masing (`alfin`, `arza`, `atha`), kemudian mengajukan perubahan untuk digabungkan ke `develop`.
- Branch `main` digunakan untuk deployment ke Streamlit Community Cloud.
- Perubahan pada branch bersama harus melalui proses review sesuai kesepakatan tim.
