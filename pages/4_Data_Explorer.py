from datetime import date, timedelta
import pandas as pd
import streamlit as st
from utils.db import fetch_dataframe

st.set_page_config(
    page_title="Data Explorer | Sector Growth",
    page_icon="🗂️",
    layout="wide",
)

# --- CSS INJECTION ALFIN UNTUK TOMBOL PAGINASI ---
st.markdown("""
<style>
div[data-testid="column"] button { margin-top: 5px; margin-bottom: 5px; }
.pagination-caption { text-align: center; color: #888; font-size: 14px; margin-bottom: 15px; }
</style>
""", unsafe_allow_html=True)

st.title("🗂️ Data Explorer")
st.caption("Pencarian dan eksplorasi artikel dari Neon DB.")

st.info(
    "Data diambil langsung dari database. "
    "Jumlah artikel antar-tabel belum dideduplikasi, "
    "sehingga hasilnya bukan jumlah berita unik lintas sumber."
)

SOURCE_SPECS = {
    "Sector 3": {
        "select_sql": """
            published_at::date AS "Tanggal", title AS "Judul", source AS "Sumber",
            COALESCE(topic, '(NULL)') AS "Kategori", COALESCE(subtopic, '(NULL)') AS "Subkategori / Teknologi",
            COALESCE(content_status, '(NULL)') AS "Status / Skor", url AS "URL"
        """,
        "from_sql": "public.sector3_articles", "date_column": "published_at",
        "search_expression": "concat_ws(' ', title, source, topic, subtopic, industry, technology, business_action, impact, insight_summary)",
        "fixed_conditions": [],
    },
    "Data Center News": {
        "select_sql": """
            published_date AS "Tanggal", title AS "Judul", source AS "Sumber",
            COALESCE(sector, '(NULL)') AS "Kategori", COALESCE(topic, '(NULL)') AS "Subkategori / Teknologi",
            COALESCE(relevance, '(NULL)') AS "Status / Skor", article_url AS "URL"
        """,
        "from_sql": "public.data_center_news", "date_column": "published_date",
        "search_expression": "concat_ws(' ', title, source, sector, topic, technology, company, organization, summary)",
        "fixed_conditions": ["record_type = 'ARTICLE'"],
    },
    "AI News": {
        "select_sql": """
            tanggal AS "Tanggal", judul AS "Judul", sumber AS "Sumber",
            COALESCE(kategori_bisnis, '(NULL)') AS "Kategori",
            COALESCE(array_to_string(teknologi_dibahas, ', '), '(NULL)') AS "Subkategori / Teknologi",
            COALESCE(skor_relevansi_it::text, '(NULL)') AS "Status / Skor", link AS "URL"
        """,
        "from_sql": "public.tabel_berita_ai", "date_column": "tanggal",
        "search_expression": "concat_ws(' ', judul, sumber, kategori_bisnis, array_to_string(teknologi_dibahas, ', '), kategori_lisensi, ringkasan_ai)",
        "fixed_conditions": [],
    },
}

@st.cache_data(ttl=300, show_spinner=False)
def load_records(source: str, search_term: str, start_date: date | None, end_date: date | None, limit: int) -> pd.DataFrame:
    spec = SOURCE_SPECS[source]
    conditions = list(spec["fixed_conditions"])
    params = {"limit": limit}

    if start_date is not None and end_date is not None:
        conditions.append(f"{spec['date_column']}::date BETWEEN :start_date AND :end_date")
        params["start_date"] = start_date
        params["end_date"] = end_date

    if search_term.strip():
        conditions.append(f"{spec['search_expression']} ILIKE :search_pattern")
        params["search_pattern"] = f"%{search_term.strip()}%"

    where_clause = " AND ".join(conditions) if conditions else "TRUE"
    query = f"SELECT {spec['select_sql']} FROM {spec['from_sql']} WHERE {where_clause} ORDER BY {spec['date_column']} DESC NULLS LAST LIMIT :limit"
    return fetch_dataframe(query, params=params)


# --- FILTER CONTROLS ---
source = st.selectbox("Pilih sumber data", list(SOURCE_SPECS.keys()))
search_term = st.text_input("Cari artikel", placeholder="Masukkan judul, sumber, kategori, teknologi, atau kata kunci...")
limit = st.selectbox("Maksimum record yang ditarik", options=[100, 250, 500, 1000], index=1)
use_date_filter = st.checkbox("Batasi rentang tanggal", value=False)

start_date, end_date = None, None
if use_date_filter:
    today = date.today()
    date_range = st.date_input("Rentang tanggal publikasi", value=(today - timedelta(days=180), today), max_value=today)
    if not isinstance(date_range, (tuple, list)) or len(date_range) != 2:
        st.warning("Pilih tanggal mulai dan akhir."); st.stop()
    start_date, end_date = date_range
    if start_date > end_date:
        st.error("Tanggal mulai melewati tanggal akhir."); st.stop()

# --- LOAD DATA ---
try:
    with st.spinner("Mengambil artikel dari Neon DB..."):
        df = load_records(source, search_term, start_date, end_date, limit)
except Exception as exc:
    st.error("Gagal mengambil data. Periksa koneksi.")
    st.stop()

col1, col2, col3 = st.columns(3)
with col1: st.metric("Record Ditampilkan", f"{len(df):,}")
with col2: st.metric("Kategori Ditemukan", f"{int(df['Kategori'].nunique()) if not df.empty else 0:,}")
with col3: st.metric("Sumber Berita", f"{int(df['Sumber'].nunique()) if not df.empty else 0:,}")
st.divider()

# ==========================================
# RENDER ARSIP GRID 3 KOLOM ALFIN
# ==========================================
st.subheader("📰 Eksplorasi Arsip Berita")

if df.empty:
    st.warning("Tidak ada artikel yang sesuai dengan filter. Coba ubah kata kunci.")
else:
    # Tampilan Toggle (Mau bentuk Kartu Visual atau Tabel Data)
    view_mode = st.radio("Mode Tampilan:", ["Kartu Visual (Grid)", "Tabel Data (Klasik)"], horizontal=True)
    
    if view_mode == "Kartu Visual (Grid)":
        ITEM_PER_HALAMAN = 21  
        total_item = len(df)
        total_halaman = max(1, (total_item - 1) // ITEM_PER_HALAMAN + 1)
        
        if 'hal_explorer' not in st.session_state: st.session_state.hal_explorer = 1
        def ganti_halaman_exp(nomor): st.session_state.hal_explorer = nomor
        if st.session_state.hal_explorer > total_halaman: st.session_state.hal_explorer = 1

        idx_awal = (st.session_state.hal_explorer - 1) * ITEM_PER_HALAMAN
        idx_akhir = idx_awal + ITEM_PER_HALAMAN
        df_halaman_ini = df.iloc[idx_awal:idx_akhir]

        st.markdown(f"<p class='pagination-caption'>Menampilkan {idx_awal + 1}–{min(idx_akhir, total_item)} dari total {total_item} artikel</p>", unsafe_allow_html=True)

        # Loop Grid 3 Kolom
        baris_berita = [df_halaman_ini.iloc[i:i+3] for i in range(0, len(df_halaman_ini), 3)]
        for baris in baris_berita:
            kolom = st.columns(3)
            for idx, (_, row) in enumerate(baris.iterrows()):
                with kolom[idx]:
                    with st.container(border=True): 
                        # Placeholder gambar karena struktur tabel general tidak semuanya punya image_url
                        st.image("https://via.placeholder.com/400x200?text=News+Article", use_container_width=True)
                        
                        st.markdown(f"**{row['Judul']}**")
                        tgl = pd.to_datetime(row['Tanggal']).strftime('%d %b %Y') if pd.notna(row['Tanggal']) else '-'
                        st.caption(f"📅 {tgl} | 🏢 **{row['Sumber']}**")
                        
                        st.markdown("<hr style='margin: 10px 0;'>", unsafe_allow_html=True)
                        st.markdown(f"<span style='font-size: 12px; color: #555;'>🏷️ **Kat**: {row['Kategori']}</span>", unsafe_allow_html=True)
                        st.markdown(f"<span style='font-size: 11px; color: #888;'>📌 **Sub**: {str(row['Subkategori / Teknologi'])[:40]}...</span>", unsafe_allow_html=True)
                        st.markdown(f"<br><a href='{row['URL']}' target='_blank' style='color:#3b82f6; text-decoration:none; font-weight:bold;'>🔗 Baca Artikel Asli ➔</a>", unsafe_allow_html=True)

        # Tombol Navigasi
        st.markdown("<br>", unsafe_allow_html=True)
        col_nav_kiri, col_nav_tengah, col_nav_kanan = st.columns([1, 4, 1]) 
        with col_nav_tengah:
            hal_skrg = st.session_state.hal_explorer
            start_hal, end_hal = max(1, hal_skrg - 2), min(total_halaman, max(1, hal_skrg - 2) + 4)
            start_hal = max(1, end_hal - 4)
            
            deret_halaman = range(start_hal, end_hal + 1)
            baris_tombol = st.columns(len(deret_halaman) + 4)
            
            with baris_tombol[0]: st.button("«", disabled=(hal_skrg == 1), on_click=ganti_halaman_exp, args=(1,), key="btn_first")
            with baris_tombol[1]: st.button("❮", disabled=(hal_skrg == 1), on_click=ganti_halaman_exp, args=(hal_skrg - 1,), key="btn_prev")
            for i, no_hal in enumerate(deret_halaman):
                with baris_tombol[i + 2]:
                    st.button(str(no_hal), on_click=ganti_halaman_exp, args=(no_hal,), type="primary" if no_hal == hal_skrg else "secondary", key=f"btn_hal_{no_hal}")
            with baris_tombol[-2]: st.button("❯", disabled=(hal_skrg == total_halaman), on_click=ganti_halaman_exp, args=(hal_skrg + 1,), key="btn_next")
            with baris_tombol[-1]: st.button("»", disabled=(hal_skrg == total_halaman), on_click=ganti_halaman_exp, args=(total_halaman,), key="btn_last")

    else:
        # Tampilan Tabel Klasik (Bawaan Atha)
        st.dataframe(
            df, hide_index=True, width="stretch",
            column_config={"URL": st.column_config.LinkColumn("Artikel", display_text="Buka artikel")},
        )
        st.download_button("Unduh hasil sebagai CSV", data=df.to_csv(index=False).encode("utf-8"), file_name="sector_growth_articles.csv", mime="text/csv")