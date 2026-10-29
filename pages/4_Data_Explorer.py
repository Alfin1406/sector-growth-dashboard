from html import escape
import pandas as pd
import streamlit as st
from utils.db import fetch_dataframe

st.set_page_config(page_title="Data Explorer | Sector Growth", page_icon="🗂️", layout="wide")
st.markdown("""<style>div[data-testid="column"] button { margin-top: 5px; margin-bottom: 5px; } .pagination-caption { text-align: center; color: #888; font-size: 14px; margin-bottom: 15px; }</style>""", unsafe_allow_html=True)
st.title("🗂️ Data Explorer")

# --- PERBAIKAN: Kolom 'gambar' dimasukkan ke query AI News ---
SOURCE_SPECS = {
    "Sector 3": {
        "select": """published_at::date AS "Tanggal", title AS "Judul", source AS "Sumber", COALESCE(topic, '(NULL)') AS "Kategori", COALESCE(subtopic, '(NULL)') AS "Subkategori", url AS "URL", NULL AS "Gambar" """,
        "from": "public.sector3_articles", "date": "published_at", "search": "concat_ws(' ', title, source, topic, subtopic)"
    },
    "Data Center News": {
        "select": """published_date AS "Tanggal", title AS "Judul", source AS "Sumber", COALESCE(sector, '(NULL)') AS "Kategori", COALESCE(company, '(NULL)') AS "Subkategori", article_url AS "URL", image_url AS "Gambar" """,
        "from": "public.data_center_news", "date": "published_date", "search": "concat_ws(' ', title, source, sector, company, summary)",
        "where": "record_type = 'ARTICLE'"
    },
    "AI News": {
        "select": """tanggal AS "Tanggal", judul AS "Judul", sumber AS "Sumber", COALESCE(kategori_bisnis, '(NULL)') AS "Kategori", COALESCE(array_to_string(teknologi_dibahas, ', '), '(NULL)') AS "Subkategori", link AS "URL", gambar AS "Gambar" """,
        "from": "public.tabel_berita_ai", "date": "tanggal", "search": "concat_ws(' ', judul, sumber, kategori_bisnis, ringkasan_ai)"
    }
}

col1, col2 = st.columns([1, 2])
with col1: source = st.selectbox("Pilih sumber data", list(SOURCE_SPECS.keys()))
with col2: search_term = st.text_input("Cari artikel...", placeholder="Kata kunci...")

spec = SOURCE_SPECS[source]
base_where = spec.get("where", "TRUE")
search_where = f"{spec['search']} ILIKE :search_pattern" if search_term.strip() else "TRUE"

query = f"SELECT {spec['select']} FROM {spec['from']} WHERE {base_where} AND {search_where} ORDER BY {spec['date']} DESC NULLS LAST LIMIT 100"
params = {"search_pattern": f"%{search_term.strip()}%"}

try:
    df = fetch_dataframe(query, params=params)
except Exception as exc:
    st.error(f"Gagal memuat data dari database: {exc}")
    st.stop()

st.divider()

if df.empty:
    st.warning("Tidak ada artikel yang sesuai.")
else:
    view_mode = st.radio("Mode Tampilan:", ["Kartu Visual (Grid)", "Tabel Data (Klasik)"], horizontal=True)

    if view_mode == "Kartu Visual (Grid)":
        ITEM_PER_HALAMAN = 21
        total_item = len(df)
        total_halaman = max(1, (total_item - 1) // ITEM_PER_HALAMAN + 1)

        if "hal_explorer" not in st.session_state: st.session_state.hal_explorer = 1
        
        def ganti_halaman(nomor): 
            st.session_state.hal_explorer = nomor
            
        if st.session_state.hal_explorer > total_halaman: st.session_state.hal_explorer = 1

        idx_awal = (st.session_state.hal_explorer - 1) * ITEM_PER_HALAMAN
        df_halaman_ini = df.iloc[idx_awal:idx_awal + ITEM_PER_HALAMAN]

        st.markdown(f"<p class='pagination-caption'>Menampilkan {idx_awal + 1}–{min(idx_awal + ITEM_PER_HALAMAN, total_item)} dari total {total_item} artikel</p>", unsafe_allow_html=True)

        baris_berita = [df_halaman_ini.iloc[i:i + 3] for i in range(0, len(df_halaman_ini), 3)]
        for baris in baris_berita:
            kolom = st.columns(3)
            for idx, (_, row) in enumerate(baris.iterrows()):
                with kolom[idx]:
                    with st.container(border=True):
                        # Logika render gambar 
                        img_url = str(row["Gambar"])
                        if img_url.startswith("http"): 
                            st.image(img_url, use_container_width=True)
                        else: 
                            st.image("https://via.placeholder.com/400x200?text=No+Image", use_container_width=True)
                        
                        st.markdown(f"**{escape(str(row['Judul']))}**")
                        tgl = pd.to_datetime(row["Tanggal"]).strftime("%d %b %Y") if pd.notna(row["Tanggal"]) else "-"
                        st.caption(f"📅 {tgl} | 🏢 **{row['Sumber']}**")
                        st.caption(f"🏷️ {escape(str(row['Kategori']))} | 📌 {escape(str(row['Subkategori'])[:40])}")
                        
                        if str(row.get("URL")).startswith("http"):
                            st.link_button("🔗 Baca Artikel ➔", str(row["URL"]), use_container_width=True)

        # Kontrol Navigasi Paginasi
        col_nav_kiri, col_nav_tengah, col_nav_kanan = st.columns([1, 4, 1])
        with col_nav_tengah:
            hal_skrg = st.session_state.hal_explorer
            baris_tombol = st.columns(7)
            with baris_tombol[1]: st.button("❮", disabled=(hal_skrg == 1), on_click=ganti_halaman, args=(hal_skrg - 1,))
            with baris_tombol[3]: st.button(str(hal_skrg), type="primary")
            with baris_tombol[5]: st.button("❯", disabled=(hal_skrg == total_halaman), on_click=ganti_halaman, args=(hal_skrg + 1,))
    else:
        st.dataframe(df.drop(columns=["Gambar"]), hide_index=True, use_container_width=True, column_config={"URL": st.column_config.LinkColumn("Buka Artikel")})