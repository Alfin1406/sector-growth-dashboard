import pandas as pd
import plotly.express as px
import streamlit as st
from google import genai
from utils.db import fetch_dataframe

st.set_page_config(page_title="Overview | Sector Growth", page_icon="📊", layout="wide")
st.title("📊 Overview & Laporan Eksekutif AI")

api_key = st.secrets.get("GEMINI_API_KEY", "")

# NAMA SUMBER DIUBAH MENYESUAIKAN TEMA RESMI
OVERVIEW_QUERY = """
    SELECT
        source,
        article_count,
        latest_publication
    FROM (
        SELECT 'Digital Transformation & IT Enterprise'::text AS source, COUNT(*)::bigint AS article_count, MAX(published_at)::date AS latest_publication FROM public.atha_sector3_articles
        UNION ALL
        SELECT 'Data Center & Infrastruktur'::text AS source, COUNT(*)::bigint AS article_count, MAX(published_date)::date AS latest_publication FROM public.arza_data_center_news WHERE record_type = 'ARTICLE'
        UNION ALL
        SELECT 'AI & Data'::text AS source, COUNT(*)::bigint AS article_count, MAX(tanggal)::date AS latest_publication FROM public.alfin_berita_ai
    ) AS source_summary
    ORDER BY CASE source
        WHEN 'Digital Transformation & IT Enterprise' THEN 1
        WHEN 'Data Center & Infrastruktur' THEN 2
        WHEN 'AI & Data' THEN 3
        ELSE 4
    END
"""
df_kpi = fetch_dataframe(OVERVIEW_QUERY)

st.subheader("Key Performance Indicators")
col1, col2, col3 = st.columns(3)
kpi_dict = dict(zip(df_kpi['source'], df_kpi['article_count']))
# LABEL METRIK DIUBAH
col1.metric("Digital Transformation & IT Enterprise", f"{kpi_dict.get('Digital Transformation & IT Enterprise', 0):,}")
col2.metric("Data Center & Infrastruktur", f"{kpi_dict.get('Data Center & Infrastruktur', 0):,}")
col3.metric("AI & Data", f"{kpi_dict.get('AI & Data', 0):,}")

st.divider()

# ==========================================
# 1. FITUR AI SUMMARY DINAMIS
# ==========================================
st.subheader("🤖 Laporan Eksekutif AI (14 Hari Terakhir)")
st.caption("Pilih sektor untuk mendapatkan ringkasan analitik AI dari berita terbaru.")

# LABEL DROPDOWN DIUBAH
opsi_sektor = {
    "Semua Tema": """
        SELECT title AS judul, insight_summary AS ringkasan FROM public.atha_sector3_articles WHERE published_at >= CURRENT_DATE - INTERVAL '14 days'
        UNION ALL
        SELECT title AS judul, summary AS ringkasan FROM public.arza_data_center_news WHERE record_type = 'ARTICLE' AND published_date >= CURRENT_DATE - INTERVAL '14 days'
        UNION ALL
        SELECT judul, ringkasan_ai AS ringkasan FROM public.alfin_berita_ai WHERE tanggal >= CURRENT_DATE - INTERVAL '14 days'
        LIMIT 30
    """,
    "Digital Transformation & IT Enterprise": "SELECT title AS judul, insight_summary AS ringkasan FROM public.atha_sector3_articles WHERE published_at >= CURRENT_DATE - INTERVAL '14 days' ORDER BY published_at DESC LIMIT 15",
    "Data Center & Infrastruktur": "SELECT title AS judul, summary AS ringkasan FROM public.arza_data_center_news WHERE record_type = 'ARTICLE' AND published_date >= CURRENT_DATE - INTERVAL '14 days' ORDER BY published_date DESC LIMIT 15",
    "AI & Data": "SELECT judul, ringkasan_ai AS ringkasan FROM public.alfin_berita_ai WHERE tanggal >= CURRENT_DATE - INTERVAL '14 days' ORDER BY tanggal DESC LIMIT 15"
}

fokus_laporan = st.selectbox("Pilih Fokus Tema untuk Laporan AI:", list(opsi_sektor.keys()))

@st.dialog("✨ Laporan Eksekutif AI")
def popup_laporan_ai(dataframe, fokus):
    cache_key = f"laporan_ai_{fokus}"
    
    if cache_key in st.session_state:
        st.info(f"Menampilkan laporan tersimpan dari ranah {fokus}...")
        st.write(st.session_state[cache_key])
        st.caption("✅ Menggunakan hasil cache (menghemat token API).")
        return

    st.info(f"Menganalisis {len(dataframe)} berita terbaru dari ranah {fokus}...")
    if not api_key:
        st.error("API Key Gemini belum diatur di secrets.toml.")
        return
    
    client = genai.Client(api_key=api_key)
    teks_berita = "".join([f"- {row['judul']}: {str(row.get('ringkasan', ''))}\n" for idx, row in dataframe.iterrows()])
    
    prompt = f"""Kamu adalah Analis Bisnis Senior PLN Icon Plus. 
    Buat Laporan Eksekutif singkat dari ringkasan berita 14 HARI TERAKHIR di sektor: {fokus}.
    Berita: {teks_berita}
    Format 2 poin: 1. Tren AI & Data Terkini (2 kalimat) 2. Rekomendasi Peluang Bisnis (bullet points)."""
    
    try:
        response = client.models.generate_content(
            model='gemini-3.5-flash-lite',
            contents=prompt
        )
        hasil_teks = response.text
        
        st.session_state[cache_key] = hasil_teks
        st.write(hasil_teks)
    except Exception as e:
        st.error(f"Gagal menghasilkan laporan: {e}")

if st.button("🤖 Generate Laporan AI", type="primary"):
    df_ai = fetch_dataframe(opsi_sektor[fokus_laporan])
    if df_ai.empty:
        st.warning("Tidak ada berita dalam 14 hari terakhir untuk tema ini.")
    else:
        popup_laporan_ai(df_ai, fokus_laporan)


st.divider()

# ==========================================
# 2. GRAFIK & TABEL SUMBER DATA
# ==========================================
st.subheader("Jumlah Artikel per Tema")

fig = px.bar(
    df_kpi,
    x="source",
    y="article_count",
    text="article_count",
    labels={
        "source": "Tema Data",
        "article_count": "Jumlah Artikel",
    },
)

fig.update_traces(textposition="outside")
fig.update_layout(
    xaxis_title="Tema Data",
    yaxis_title="Jumlah Artikel",
    yaxis_rangemode="tozero",
)

st.plotly_chart(fig, use_container_width=True)

st.caption("Perbandingan ini menunjukkan jumlah artikel per tema/tabel. Artikel yang sama mungkin tercatat di lebih dari satu sumber.")

st.divider()

st.subheader("Ringkasan Pengumpulan Data")

display_df = df_kpi.copy()
display_df["latest_publication"] = (
    pd.to_datetime(display_df["latest_publication"], errors="coerce")
    .dt.strftime("%Y-%m-%d")
    .fillna("Belum tersedia")
)

display_df = display_df.rename(
    columns={
        "source": "Tema Data",
        "article_count": "Jumlah Artikel",
        "latest_publication": "Publikasi Terbaru",
    }
)

st.dataframe(display_df, hide_index=True, use_container_width=True)
st.caption("Ringkasan dimuat dari Neon DB dan diperbarui melalui cache setiap lima menit.")