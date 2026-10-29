import pandas as pd
import plotly.express as px
import streamlit as st
import google.generativeai as genai

from utils.db import fetch_dataframe

# Mengambil API Key dari secrets Streamlit
api_key = st.secrets.get("GEMINI_API_KEY", "")

st.set_page_config(
    page_title="Overview | Sector Growth",
    page_icon="📊",
    layout="wide",
)

st.title("📊 Overview & Eksekutif Laporan")
st.caption("Ringkasan publikasi berita dari database tim dan analisis AI.")

st.info(
    "KPI dan grafik di bawah menggunakan data aktual dari Neon DB. "
    "Jumlah artikel antar-tabel belum dideduplikasi, sehingga "
    "tidak boleh dianggap sebagai jumlah berita unik."
)

OVERVIEW_QUERY = """
    SELECT
        source,
        article_count,
        latest_publication
    FROM (
        SELECT
            'Sector 3'::text AS source,
            COUNT(*)::bigint AS article_count,
            MAX(published_at)::date AS latest_publication
        FROM public.sector3_articles

        UNION ALL

        SELECT
            'Data Center News'::text AS source,
            COUNT(*)::bigint AS article_count,
            MAX(published_date)::date AS latest_publication
        FROM public.data_center_news
        WHERE record_type = 'ARTICLE'

        UNION ALL

        SELECT
            'AI News'::text AS source,
            COUNT(*)::bigint AS article_count,
            MAX(tanggal)::date AS latest_publication
        FROM public.tabel_berita_ai
    ) AS source_summary
    ORDER BY CASE source
        WHEN 'Sector 3' THEN 1
        WHEN 'Data Center News' THEN 2
        WHEN 'AI News' THEN 3
        ELSE 4
    END
"""

# Query khusus untuk bahan Laporan AI (14 hari terakhir)
AI_NEWS_QUERY = """
    SELECT judul, ringkasan_ai 
    FROM public.tabel_berita_ai 
    WHERE tanggal >= CURRENT_DATE - INTERVAL '14 days'
    ORDER BY tanggal DESC
    LIMIT 15
"""

@st.cache_data(ttl=300, show_spinner=False)
def load_overview_data() -> pd.DataFrame:
    """Mengambil ringkasan aktual dari ketiga sumber berita."""
    return fetch_dataframe(OVERVIEW_QUERY)

@st.cache_data(ttl=600, show_spinner=False)
def load_ai_news_data() -> pd.DataFrame:
    """Mengambil data berita AI 14 hari terakhir untuk prompt."""
    return fetch_dataframe(AI_NEWS_QUERY)

try:
    with st.spinner("Mengambil ringkasan dari Neon DB..."):
        df = load_overview_data()
        df_ai = load_ai_news_data()

except Exception as exc:
    st.error(
        "Data Overview belum berhasil dimuat. "
        "Periksa koneksi database dan konfigurasi lokal."
    )
    st.caption(f"Jenis error: {type(exc).__name__}")
    st.stop()


# Pastikan hasil query tersedia.
if df.empty:
    st.warning("Belum ada ringkasan data dari sumber yang tersedia.")
    st.stop()

# --------------------------------------------------
# LOGIKA AI SUMMARY (Buatan Alfin)
# --------------------------------------------------
@st.cache_data(show_spinner=False)
def generate_ai_summary(dataframe):
    if not api_key:
        return "⚠️ API Key Gemini belum diatur di secrets.toml. Tambahkan 'GEMINI_API_KEY' ke .streamlit/secrets.toml."
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash') # Updated ke versi model yang stabil
    
    teks_berita = "".join([f"- {row['judul']}: {str(row.get('ringkasan_ai', ''))}\n" for index, row in dataframe.iterrows()])
        
    prompt = f"""
    Kamu adalah seorang Analis Bisnis Senior di PLN Icon Plus. 
    Tugasmu adalah menganalisis kumpulan ringkasan berita teknologi dari 2 minggu terakhir berikut ini dan membuat 'Laporan Eksekutif' singkat.
    Fokuslah pada tren kecerdasan buatan (AI) dan Infrastruktur Data (seperti Data Center, Cloud).
    
    Berita terbaru (14 Hari Terakhir):
    {teks_berita}
    
    Buatlah ringkasan dalam format Markdown dengan 2 poin utama:
    1. Tren AI & Data Terkini (2 kalimat)
    2. 2 Rekomendasi Peluang Bisnis untuk PLN Icon Plus berdasarkan tren tersebut (gunakan bullet points).
    Gunakan bahasa Indonesia yang profesional dan lugas.
    """
    try:
        return model.generate_content(prompt).text
    except Exception as e:
        return f"Gagal menghasilkan laporan eksekutif. Error: {e}"

@st.dialog("✨ Laporan Eksekutif AI (Tren 14 Hari Terakhir)")
def popup_laporan_ai(dataframe):
    st.info(f"🤖 Menganalisis {len(dataframe)} berita terhangat. Mohon tunggu beberapa detik...")
    st.write(generate_ai_summary(dataframe))

# === TOMBOL AI GLOBAL (Tampil di atas metrik) ===
col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])
with col_btn2: 
    if st.button("🤖 Generate Laporan Eksekutif AI (14 Hari Terakhir)", use_container_width=True, type="primary"):
        if df_ai.empty: 
            st.warning("Tidak ada data AI News dalam 14 hari terakhir di