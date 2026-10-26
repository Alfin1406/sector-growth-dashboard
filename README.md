# Sector Growth Dashboard

Dashboard Streamlit gabungan (multipage) untuk proyek Sector Growth Insight (PLN Icon Plus).
Pipeline dan migrasi database ada di repo terpisah: **sector-growth-pipeline**.

## Aturan
- Satu halaman per orang/sumber di folder `pages/`, setiap halaman membaca tabelnya sendiri.
- Jangan commit `.streamlit/secrets.toml` atau kredensial apa pun.
- Setiap orang bekerja di branch sendiri (`alfin`, `arza`, `atha`), digabung ke `develop`.
  `main` dipakai untuk deployment ke Streamlit Community Cloud.