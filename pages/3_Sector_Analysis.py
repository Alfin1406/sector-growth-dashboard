import pandas as pd
import plotly.express as px
import streamlit as st
from google import genai
from utils.db import fetch_dataframe

st.set_page_config(page_title="Sector Analysis | Sector Growth", page_icon="📊", layout="wide")
st.title("📊 Sector Analysis")

api_key = st.secrets.get("GEMINI_API_KEY", "")

# 1. PETA QUERY SQL KE DATABASE NEON
QUERIES = {
    "Sector 3": {
        "Topic": "SELECT COALESCE(topic, '(NULL)') AS category, COUNT(*)::int AS total FROM public.sector3_articles GROUP BY topic ORDER BY total DESC LIMIT :limit",
        "Subtopic": "SELECT COALESCE(subtopic, '(NULL)') AS category, COUNT(*)::int AS total FROM public.sector3_articles GROUP BY subtopic ORDER BY total DESC LIMIT :limit",
        "Industry": "SELECT COALESCE(industry, '(NULL)') AS category, COUNT(*)::int AS total FROM public.sector3_articles GROUP BY industry ORDER BY total DESC LIMIT :limit",
        "Publisher": "SELECT COALESCE(source, '(NULL)') AS category, COUNT(*)::int AS total FROM public.sector3_articles GROUP BY source ORDER BY total DESC LIMIT :limit",
        "Sunburst Hierarchy (Atha)": "SELECT 'Sector 3' AS main_topic, COALESCE(topic, 'Uncategorized') AS category, COALESCE(subtopic, 'Unknown') AS subcategory, COUNT(*)::int AS total FROM public.sector3_articles GROUP BY topic, subtopic"
    },
    "Data Center News": {
        "Sector": "SELECT COALESCE(sector, '(NULL)') AS category, COUNT(*)::int AS total FROM public.data_center_news WHERE record_type = 'ARTICLE' GROUP BY sector ORDER BY total DESC LIMIT :limit",
        "Topic": "SELECT COALESCE(topic, '(NULL)') AS category, COUNT(*)::int AS total FROM public.data_center_news WHERE record_type = 'ARTICLE' GROUP BY topic ORDER BY total DESC LIMIT :limit",
        "Subtopic": "SELECT COALESCE(subtopic, '(NULL)') AS category, COUNT(*)::int AS total FROM public.data_center_news WHERE record_type = 'ARTICLE' GROUP BY subtopic ORDER BY total DESC LIMIT :limit",
        "Publisher": "SELECT COALESCE(source, '(NULL)') AS category, COUNT(*)::int AS total FROM public.data_center_news WHERE record_type = 'ARTICLE' GROUP BY source ORDER BY total DESC LIMIT :limit",
        "Relevance": "SELECT COALESCE(relevance, '(NULL)') AS category, COUNT(*)::int AS total FROM public.data_center_news WHERE record_type = 'ARTICLE' GROUP BY relevance ORDER BY total DESC LIMIT :limit",
        "Company Mentions (Arza)": "SELECT COALESCE(company, '(NULL)') AS category, COUNT(*)::int AS total FROM public.data_center_news WHERE record_type = 'ARTICLE' AND company IS NOT NULL AND company != '' GROUP BY company ORDER BY total DESC LIMIT :limit"
    },
    "AI News": {
        "Business Category": "SELECT COALESCE(kategori_bisnis, '(NULL)') AS category, COUNT(*)::int AS total FROM public.tabel_berita_ai GROUP BY kategori_bisnis ORDER BY total DESC LIMIT :limit",
        "Publisher": "SELECT COALESCE(sumber, '(NULL)') AS category, COUNT(*)::int AS total FROM public.tabel_berita_ai GROUP BY sumber ORDER BY total DESC LIMIT :limit",
        "Technology Tag": "SELECT COALESCE(tech.value, '(NULL)') AS category, COUNT(*)::int AS total FROM public.tabel_berita_ai CROSS JOIN LATERAL unnest(teknologi_dibahas) AS tech(value) WHERE teknologi_dibahas IS NOT NULL GROUP BY tech.value ORDER BY total DESC LIMIT :limit"
    }
}

# Peta kolom asli untuk menarik data mentah saat Generate AI
COLUMN_MAP = {
    "Sector 3": {"Subtopic": "subtopic"},
    "Data Center News": {"Subtopic": "subtopic"},
    "AI News": {"Technology Tag": "teknologi_dibahas"}
}

col1, col2, col3 = st.columns([2, 2, 1])
with col1: selected_source = st.selectbox("Pilih sumber data", list(QUERIES.keys()))
with col2: selected_dimension = st.selectbox("Analisis berdasarkan", list(QUERIES[selected_source].keys()))
with col3: top_n = st.selectbox("Jumlah teratas", [10, 15, 30], index=1)

try:
    df = fetch_dataframe(QUERIES[selected_source][selected_dimension], params={"limit": top_n})
except Exception as exc:
    st.error(f"Gagal memuat data: {exc}")
    st.stop()

if df.empty:
    st.warning("Tidak ada data untuk kombinasi ini.")
    st.stop()

st.divider()
st.subheader(f"Analisis {selected_dimension} — {selected_source}")

# --- RENDER VISUALISASI ---
if selected_dimension == "Sunburst Hierarchy (Atha)":
    fig = px.sunburst(df, path=["main_topic", "category", "subcategory"], values="total", color="category")
    fig.update_traces(textinfo="label+percent parent", maxdepth=3)
    st.plotly_chart(fig, use_container_width=True)
else:
    df["total"] = pd.to_numeric(df["total"])
    chart_df = df.sort_values("total", ascending=True)
    fig = px.bar(chart_df, x="total", y="category", orientation="h", text="total")
    fig.update_traces(textposition="outside")
    fig.update_layout(xaxis_title="Jumlah Artikel", yaxis_title="Kategori")
    st.plotly_chart(fig, use_container_width=True)


# --- FITUR AI PER-SUBTOPIC (Hanya aktif untuk Subtopik/Technology Tag) ---
DIMENSI_AI = ["Subtopic", "Technology Tag"]

if selected_dimension in DIMENSI_AI:
    st.divider()
    st.subheader(f"🤖 AI Summary khusus untuk {selected_dimension}")
    st.caption("Pilih salah satu subtopik dari grafik di atas untuk dibuatkan ringkasan khusus oleh AI.")
    
    list_kategori = df['category'].tolist()
    
    if not list_kategori:
        st.warning("Tidak ada subtopik untuk dianalisis.")
    else:
        chosen_category = st.selectbox("Pilih Subtopik:", list_kategori)
        
        # MEMBUAT KUNCI CACHE UNIK
        cache_key = f"ai_summary_{selected_source}_{selected_dimension}_{chosen_category}"
        
        if st.button(f"✨ Generate Laporan AI untuk '{chosen_category}'", type="primary"):
            
            # CEK CACHE SEBELUM MEMANGGIL API
            if cache_key in st.session_state:
                st.info(st.session_state[cache_key])
                st.caption("✅ Menggunakan hasil cache (menghemat token API).")
            
            # JIKA BELUM ADA DI CACHE, PROSES API
            else:
                if not api_key:
                    st.error("API Key Gemini belum diatur di secrets.toml.")
                else:
                    with st.spinner(f"Mengambil berita '{chosen_category}' (14 Hari Terakhir) dan menganalisis..."):
                        nama_kolom = COLUMN_MAP[selected_source][selected_dimension]
                        
                        if selected_source == "Sector 3":
                            q_raw = f"SELECT title AS judul, insight_summary AS ringkasan FROM public.sector3_articles WHERE {nama_kolom} = :cat AND published_at >= CURRENT_DATE - INTERVAL '14 days' ORDER BY published_at DESC LIMIT 15"
                        elif selected_source == "Data Center News":
                            q_raw = f"SELECT title AS judul, summary AS ringkasan FROM public.data_center_news WHERE {nama_kolom} = :cat AND record_type = 'ARTICLE' AND published_date >= CURRENT_DATE - INTERVAL '14 days' ORDER BY published_date DESC LIMIT 15"
                        elif selected_dimension == "Technology Tag":
                            q_raw = "SELECT judul, ringkasan_ai AS ringkasan FROM public.tabel_berita_ai WHERE :cat = ANY(teknologi_dibahas) AND tanggal >= CURRENT_DATE - INTERVAL '14 days' ORDER BY tanggal DESC LIMIT 15"
                        
                        df_raw = fetch_dataframe(q_raw, params={"cat": chosen_category})
                        
                        if df_raw.empty:
                            st.warning(f"Tidak ada berita mentah untuk subtopik '{chosen_category}' dalam 14 hari terakhir.")
                        else:
                            # --- PERBAIKAN SDK GOOGLE GENAI DIMULAI DI SINI ---
                            client = genai.Client(api_key=api_key)
                            teks_berita = "".join([f"- {row['judul']}: {str(row.get('ringkasan', ''))}\n" for idx, row in df_raw.iterrows()])
                            
                            prompt = f"""Kamu adalah Analis Bisnis. Buat ringkasan singkat dari kumpulan berita 14 HARI TERAKHIR berikut yang secara spesifik membahas tentang subtopik '{chosen_category}'.
                            Berita: {teks_berita}
                            Format: 1. Ringkasan Utama 2. Insight Menarik (Bullet points)."""
                            
                            try:
                                # Generate hasil teks dari API menggunakan format baru
                                response = client.models.generate_content(
                                    model='gemini-3.5-flash-lite',
                                    contents=prompt
                                )
                                hasil_teks = response.text
                                
                                # Simpan ke session_state agar tidak panggil API lagi jika di-klik ulang
                                st.session_state[cache_key] = hasil_teks
                                
                                # Tampilkan ke layar
                                st.info(hasil_teks)
                            except Exception as e:
                                st.error(f"Gagal menghasilkan laporan: {e}")
                            # --- PERBAIKAN SDK SELESAI ---