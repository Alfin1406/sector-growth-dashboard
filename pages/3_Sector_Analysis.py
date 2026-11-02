import pandas as pd
import plotly.express as px
import streamlit as st
import re
from google import genai
from utils.db import fetch_dataframe

st.set_page_config(page_title="Sector Analysis | Sector Growth", page_icon="📊", layout="wide")
st.title("📊 Sector Analysis")

api_key = st.secrets.get("GEMINI_API_KEY", "")

# 1. PETA QUERY SQL KE DATABASE NEON DENGAN NAMA TEMA RESMI
QUERIES = {
    "Digital Transformation & IT Enterprise": {
        "Topic": "SELECT COALESCE(topic, '(NULL)') AS category, COUNT(*)::int AS total FROM public.sector3_articles WHERE published_at::date >= :start_date AND published_at::date <= :end_date GROUP BY topic ORDER BY total DESC",
        "Subtopic": "SELECT COALESCE(subtopic, '(NULL)') AS category, COUNT(*)::int AS total FROM public.sector3_articles WHERE published_at::date >= :start_date AND published_at::date <= :end_date GROUP BY subtopic ORDER BY total DESC",
        "Industry": "SELECT COALESCE(industry, '(NULL)') AS category, COUNT(*)::int AS total FROM public.sector3_articles WHERE published_at::date >= :start_date AND published_at::date <= :end_date GROUP BY industry ORDER BY total DESC",
        "Publisher": "SELECT COALESCE(source, '(NULL)') AS category, COUNT(*)::int AS total FROM public.sector3_articles WHERE published_at::date >= :start_date AND published_at::date <= :end_date GROUP BY source ORDER BY total DESC",
        "Sunburst Hierarchy": "SELECT 'Digital Transformation & IT Enterprise' AS main_topic, COALESCE(topic, 'Uncategorized') AS category, COALESCE(subtopic, 'Unknown') AS subcategory, COUNT(*)::int AS total FROM public.sector3_articles WHERE published_at::date >= :start_date AND published_at::date <= :end_date GROUP BY topic, subtopic"
    },
    "Data Center & Cloud": {
        "Sector": "SELECT COALESCE(sector, '(NULL)') AS category, COUNT(*)::int AS total FROM public.data_center_news WHERE record_type = 'ARTICLE' AND published_date::date >= :start_date AND published_date::date <= :end_date GROUP BY sector ORDER BY total DESC",
        "Topic": "SELECT COALESCE(topic, '(NULL)') AS category, COUNT(*)::int AS total FROM public.data_center_news WHERE record_type = 'ARTICLE' AND published_date::date >= :start_date AND published_date::date <= :end_date GROUP BY topic ORDER BY total DESC",
        "Subtopic": "SELECT COALESCE(subtopic, '(NULL)') AS category, COUNT(*)::int AS total FROM public.data_center_news WHERE record_type = 'ARTICLE' AND published_date::date >= :start_date AND published_date::date <= :end_date GROUP BY subtopic ORDER BY total DESC",
        "Publisher": "SELECT COALESCE(source, '(NULL)') AS category, COUNT(*)::int AS total FROM public.data_center_news WHERE record_type = 'ARTICLE' AND published_date::date >= :start_date AND published_date::date <= :end_date GROUP BY source ORDER BY total DESC",
        "Relevance": "SELECT COALESCE(relevance, '(NULL)') AS category, COUNT(*)::int AS total FROM public.data_center_news WHERE record_type = 'ARTICLE' AND published_date::date >= :start_date AND published_date::date <= :end_date GROUP BY relevance ORDER BY total DESC",
        "Company Mentions": "SELECT COALESCE(company, '(NULL)') AS category, COUNT(*)::int AS total FROM public.data_center_news WHERE record_type = 'ARTICLE' AND company IS NOT NULL AND company != '' AND published_date::date >= :start_date AND published_date::date <= :end_date GROUP BY company ORDER BY total DESC"
    },
    "AI & Data": {
        "Business Category": "SELECT COALESCE(kategori_bisnis, '(NULL)') AS category, COUNT(*)::int AS total FROM public.tabel_berita_ai WHERE tanggal::date >= :start_date AND tanggal::date <= :end_date GROUP BY kategori_bisnis ORDER BY total DESC",
        "Publisher": "SELECT COALESCE(sumber, '(NULL)') AS category, COUNT(*)::int AS total FROM public.tabel_berita_ai WHERE tanggal::date >= :start_date AND tanggal::date <= :end_date GROUP BY sumber ORDER BY total DESC",
        "Technology Tag": "SELECT COALESCE(tech.value, '(NULL)') AS category, COUNT(*)::int AS total FROM public.tabel_berita_ai CROSS JOIN LATERAL unnest(teknologi_dibahas) AS tech(value) WHERE teknologi_dibahas IS NOT NULL AND tanggal::date >= :start_date AND tanggal::date <= :end_date GROUP BY tech.value ORDER BY total DESC"
    }
}

COLUMN_MAP = {
    "Digital Transformation & IT Enterprise": {"Subtopic": "subtopic"},
    "Data Center & Cloud": {"Subtopic": "subtopic"},
    "AI & Data": {"Technology Tag": "teknologi_dibahas"}
}

col1, col2, col3 = st.columns([1, 1, 1])
with col1: 
    selected_source = st.selectbox("Pilih Tema", list(QUERIES.keys()))
with col2: 
    selected_dimension = st.selectbox("Analisis berdasarkan", list(QUERIES[selected_source].keys()))
with col3:
    default_start = pd.to_datetime('2024-01-01').date()
    default_end = pd.to_datetime('today').date()
    
    rentang_tanggal = st.date_input(
        "Limit by Tanggal",
        value=(default_start, default_end),
        min_value=default_start,
        max_value=default_end
    )

if len(rentang_tanggal) != 2:
    st.info("Pilih rentang awal dan akhir tanggal untuk memuat data.")
    st.stop()

start_date, end_date = rentang_tanggal

try:
    df = fetch_dataframe(QUERIES[selected_source][selected_dimension], params={"start_date": start_date, "end_date": end_date})
except Exception as exc:
    st.error(f"Gagal memuat data: {exc}")
    st.stop()

if df.empty:
    st.warning("Tidak ada data untuk kombinasi ini pada rentang tanggal tersebut.")
    st.stop()

st.divider()
st.subheader(f"Analisis {selected_dimension} — {selected_source}")

# --- RENDER VISUALISASI UTAMA ---
if selected_dimension == "Sunburst Hierarchy":
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

# --- FITUR AI PER-SUBTOPIC ---
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
        cache_key = f"ai_summary_{selected_source.replace(' ', '_')}_{selected_dimension}_{chosen_category}"
        
        if st.button(f"✨ Generate Laporan AI untuk '{chosen_category}'", type="primary"):
            if cache_key in st.session_state:
                st.info(st.session_state[cache_key])
                st.caption("✅ Menggunakan hasil cache (menghemat token API).")
            else:
                if not api_key:
                    st.error("API Key Gemini belum diatur di secrets.toml.")
                else:
                    with st.spinner(f"Mengambil berita '{chosen_category}' (14 Hari Terakhir) dan menganalisis..."):
                        nama_kolom = COLUMN_MAP[selected_source][selected_dimension]
                        
                        if selected_source == "Digital Transformation & IT Enterprise":
                            q_raw = f"SELECT title AS judul, insight_summary AS ringkasan FROM public.sector3_articles WHERE {nama_kolom} = :cat AND published_at >= CURRENT_DATE - INTERVAL '14 days' ORDER BY published_at DESC LIMIT 15"
                        elif selected_source == "Data Center & Cloud":
                            q_raw = f"SELECT title AS judul, summary AS ringkasan FROM public.data_center_news WHERE {nama_kolom} = :cat AND record_type = 'ARTICLE' AND published_date >= CURRENT_DATE - INTERVAL '14 days' ORDER BY published_date DESC LIMIT 15"
                        elif selected_dimension == "Technology Tag":
                            q_raw = "SELECT judul, ringkasan_ai AS ringkasan FROM public.tabel_berita_ai WHERE :cat = ANY(teknologi_dibahas) AND tanggal >= CURRENT_DATE - INTERVAL '14 days' ORDER BY tanggal DESC LIMIT 15"
                        
                        df_raw = fetch_dataframe(q_raw, params={"cat": chosen_category})
                        
                        if df_raw.empty:
                            st.warning(f"Tidak ada berita mentah untuk subtopik '{chosen_category}' dalam 14 hari terakhir.")
                        else:
                            client = genai.Client(api_key=api_key)
                            teks_berita = "".join([f"- {row['judul']}: {str(row.get('ringkasan', ''))}\n" for idx, row in df_raw.iterrows()])
                            
                            prompt = f"""Kamu adalah Analis Bisnis. Buat ringkasan singkat dari kumpulan berita 14 HARI TERAKHIR berikut yang secara spesifik membahas tentang subtopik '{chosen_category}'.
                            Berita: {teks_berita}
                            Format: 1. Ringkasan Utama 2. Insight Menarik (Bullet points)."""
                            
                            try:
                                response = client.models.generate_content(
                                    model='gemini-3.5-flash-lite',
                                    contents=prompt
                                )
                                hasil_teks = response.text
                                st.session_state[cache_key] = hasil_teks
                                st.info(hasil_teks)
                            except Exception as e:
                                st.error(f"Gagal menghasilkan laporan: {e}")

st.divider()

# ==========================================
# 3. ANALITIK SPESIFIK INDIVIDU (SUB-SECTION)
# ==========================================
st.subheader(f"🔍 Analisis Khusus: {selected_source}")

# ---------------------------------------------------------
# 1. RUANG KERJA ARZA (DATA CENTER & CLOUD)
# ---------------------------------------------------------
if selected_source == "Data Center & Cloud":
    st.markdown("### Business Insights & Market Signals")
    
    query_arza = """
    SELECT topic, technology, investment_value, capacity, company, project_location, organization 
    FROM public.data_center_news 
    WHERE record_type = 'ARTICLE' 
    AND published_date::date >= :start_date AND published_date::date <= :end_date
    """
    
    try:
        df_arza = fetch_dataframe(query_arza, params={"start_date": start_date, "end_date": end_date})
        
        def get_list_counts(series, limit=10):
            values = []
            for item in series.dropna().astype(str):
                values.extend([part.strip() for part in re.split(r"[;,]", item) if part.strip() and part.strip().lower() not in {"nan", "none"}])
            if not values: return pd.DataFrame(columns=["Nama", "Jumlah"])
            counts = pd.Series(values).value_counts().head(limit)
            return pd.DataFrame({"Nama": counts.index, "Jumlah": counts.values})
            
        def parse_investment_range(val):
            if not val or pd.isna(val): return None
            val = str(val).lower().replace(',', '.')
            matches = re.findall(r'([\d.]+)\s*(triliun|miliar|juta|t|m)?', val)
            if not matches: return None

            total_idr = 0
            for num_str, unit in matches:
                try:
                    num = float(num_str)
                    if unit in ['triliun', 't']: num *= 1e12
                    elif unit in ['miliar', 'm']: num *= 1e9
                    elif unit == 'juta': num *= 1e6
                    
                    if 'us$' in val or 'usd' in val or '$' in val:
                        num *= 15500 
                        
                    total_idr += num
                except: pass

            if total_idr == 0: return None
            elif total_idr <= 100e6: return "0 - 100 Juta Rupiah"
            elif total_idr <= 1e9: return "100 Juta - 1 Miliar Rupiah"
            elif total_idr <= 100e9: return "1 Miliar - 100 Miliar Rupiah"
            elif total_idr <= 1e12: return "100 Miliar - 1 Triliun Rupiah"
            else: return "> 1 Triliun Rupiah"

        def parse_capacity_range(val):
            if not val or pd.isna(val): return None
            val = str(val).lower().replace(',', '.')
            matches = re.findall(r'([\d.]+)\s*(gw|mw|kw)', val)
            if not matches: return None

            total_mw = 0
            for num_str, unit in matches:
                try:
                    num = float(num_str)
                    if unit == 'gw': num *= 1000
                    elif unit == 'kw': num /= 1000
                    total_mw += num
                except: pass

            if total_mw == 0: return None
            elif total_mw < 10: return "< 10 MW"
            elif total_mw <= 50: return "10 MW - 50 MW"
            elif total_mw <= 100: return "50 MW - 100 MW"
            elif total_mw <= 500: return "100 MW - 500 MW"
            else: return "> 500 MW"
            
        df_arza["investment_range"] = df_arza["investment_value"].apply(parse_investment_range)
        df_arza["capacity_range"] = df_arza["capacity"].apply(parse_capacity_range)

        col_t1, col_t2 = st.columns(2)
        with col_t1:
            st.markdown("**Topics Being Discussed**")
            st.dataframe(get_list_counts(df_arza["topic"], 10), hide_index=True, use_container_width=True)
        with col_t2:
            st.markdown("**Technologies Detected**")
            st.dataframe(get_list_counts(df_arza["technology"], 10), hide_index=True, use_container_width=True)
            
        st.markdown("<br>", unsafe_allow_html=True)
            
        col_i1, col_i2 = st.columns(2)
        with col_i1:
            st.markdown("**Investment Signals (Estimasi Nilai)**")
            inv_counts = df_arza["investment_range"].dropna().value_counts().reset_index()
            inv_counts.columns = ["Sinyal (Rentang Harga)", "Jumlah Artikel"]
            if inv_counts.empty: st.caption("Belum ada data nilai investasi.")
            else: st.dataframe(inv_counts, hide_index=True, use_container_width=True)
                
        with col_i2:
            st.markdown("**Capacity Signals (Estimasi Kapasitas)**")
            cap_counts = df_arza["capacity_range"].dropna().value_counts().reset_index()
            cap_counts.columns = ["Sinyal (Rentang MW)", "Jumlah Artikel"]
            if cap_counts.empty: st.caption("Belum ada data kapasitas daya/server.")
            else: st.dataframe(cap_counts, hide_index=True, use_container_width=True)

        st.markdown("<br>", unsafe_allow_html=True)

        col_e1, col_e2, col_e3 = st.columns(3)
        with col_e1:
            st.markdown("**Companies Mentioned**")
            st.dataframe(get_list_counts(df_arza["company"], 10), hide_index=True, use_container_width=True)
        with col_e2:
            st.markdown("**Project Locations**")
            st.dataframe(get_list_counts(df_arza["project_location"], 10), hide_index=True, use_container_width=True)
        with col_e3:
            st.markdown("**Organizations Mentioned**")
            st.dataframe(get_list_counts(df_arza["organization"], 10), hide_index=True, use_container_width=True)

    except Exception as e:
        st.error(f"Gagal memuat analitik spesifik Data Center: {e}")

# ---------------------------------------------------------
# 2. RUANG KERJA ALFIN (AI & DATA)
# ---------------------------------------------------------
elif selected_source == "AI & Data":
    st.markdown("### Analitik Lisensi & Distribusi Portal")
    
    query_alfin = "SELECT sumber, kategori_lisensi, teknologi_dibahas FROM public.tabel_berita_ai WHERE tanggal::date >= :start_date AND tanggal::date <= :end_date"
    try:
        df_alfin = fetch_dataframe(query_alfin, params={"start_date": start_date, "end_date": end_date})
        
        def parse_topik(x):
            if isinstance(x, list): return x
            if isinstance(x, str):
                x = x.strip('{}[]').replace('"', '').replace("'", "")
                return [i.strip() for i in x.split(',')] if x else []
            return []
            
        df_alfin['teknologi_dibahas_list'] = df_alfin['teknologi_dibahas'].apply(parse_topik)
        
        col_al1, col_al2 = st.columns([1, 2])
        
        with col_al1:
            st.markdown("**Sebaran Lisensi Penggunaan**")
            lisensi_count = df_alfin['kategori_lisensi'].value_counts().reset_index()
            lisensi_count.columns = ['Lisensi', 'Jumlah']
            if lisensi_count.empty:
                st.caption("Tidak ada data lisensi pada rentang ini.")
            else:
                fig_pie = px.pie(lisensi_count, names='Lisensi', values='Jumlah', hole=0.5, color_discrete_sequence=['#3b82f6', '#10b981', '#f59e0b'])
                fig_pie.update_layout(margin=dict(t=10, b=10, l=10, r=10))
                st.plotly_chart(fig_pie, use_container_width=True)
            
        with col_al2:
            st.markdown("**Top Portal Sumber Berita AI**")
            sumber_count = df_alfin['sumber'].value_counts().reset_index().head(10)
            sumber_count.columns = ['Portal Media', 'Artikel']
            if sumber_count.empty:
                 st.caption("Tidak ada data sumber berita pada rentang ini.")
            else:
                fig_bar = px.bar(sumber_count, x='Artikel', y='Portal Media', orientation='h', text='Artikel', color_discrete_sequence=['#3b82f6'])
                fig_bar.update_layout(yaxis={'categoryorder':'total ascending'}, margin=dict(t=10, b=10, l=10, r=10))
                st.plotly_chart(fig_bar, use_container_width=True)
            
    except Exception as e:
        st.error(f"Gagal memuat analitik spesifik AI: {e}")

# ---------------------------------------------------------
# 3. RUANG KERJA ATHA (IT ENTERPRISE & DIGITAL TRANSFORMATION)
# ---------------------------------------------------------
elif selected_source == "Digital Transformation & IT Enterprise":
    st.markdown("### Jenis peristiwa, sumber, dan konteks bisnis")
    
    query_atha = "SELECT event_type, industry, technology, source FROM public.sector3_articles WHERE published_at::date >= :start_date AND published_at::date <= :end_date"
    try:
        df_atha = fetch_dataframe(query_atha, params={"start_date": start_date, "end_date": end_date})
        
        def clean_text(value):
            if value is None or pd.isna(value): return ""
            return " ".join(str(value).replace("\xa0", " ").split()).strip()
            
        def split_csv_values(value):
            text = clean_text(value)
            if not text or text.lower() in {"nan", "none", "null", "not detected"}: return []
            return list(dict.fromkeys(part.strip() for part in text.split(",") if part.strip()))
            
        df_atha["event_type"] = df_atha["event_type"].map(clean_text)
        df_atha["source"] = df_atha["source"].map(clean_text)
        df_atha["industry_items"] = df_atha["industry"].map(split_csv_values)
        df_atha["technology_items"] = df_atha["technology"].map(split_csv_values)
        
        # BARIS 1: Jenis Peristiwa & Sumber
        event_col, source_col = st.columns(2)
        
        with event_col:
            st.markdown("**Jenis peristiwa**")
            events = df_atha[df_atha["event_type"] != ""]["event_type"].value_counts().head(8).sort_values(ascending=True).reset_index()
            events.columns = ["Jenis Peristiwa", "Artikel"]
            if not events.empty:
                fig_ev = px.bar(events, x="Artikel", y="Jenis Peristiwa", orientation="h", text="Artikel")
                fig_ev.update_traces(marker_color="#a879ff")
                fig_ev.update_layout(margin=dict(l=10, r=10, t=10, b=10))
                st.plotly_chart(fig_ev, use_container_width=True)
            else:
                st.caption("Tidak ada data jenis peristiwa.")
                
        with source_col:
            st.markdown("**Distribusi sumber**")
            sources = df_atha[df_atha["source"] != ""]["source"].value_counts().reset_index()
            sources.columns = ["Sumber", "Artikel"]
            if not sources.empty:
                fig_src = px.pie(sources, names="Sumber", values="Artikel", hole=0.62)
                fig_src.update_traces(textposition="inside", textinfo="percent+value")
                fig_src.update_layout(margin=dict(l=10, r=10, t=10, b=10))
                st.plotly_chart(fig_src, use_container_width=True)
            else:
                st.caption("Tidak ada data sumber.")
                
        st.markdown("<br>", unsafe_allow_html=True)
                
        # BARIS 2: Industri & Teknologi
        industry_col, tech_col = st.columns(2)
        
        with industry_col:
            st.markdown("**Industri yang disebut**")
            st.caption("Satu artikel dapat menyebut lebih dari satu industri.")
            all_industries = []
            for items in df_atha["industry_items"].tolist():
                all_industries.extend(items)
            
            if all_industries:
                ind_counts = pd.Series(all_industries).value_counts().head(8).sort_values(ascending=True).reset_index()
                ind_counts.columns = ["Industri", "Jumlah Penyebutan"]
                fig_ind = px.bar(ind_counts, x="Jumlah Penyebutan", y="Industri", orientation="h", text="Jumlah Penyebutan")
                fig_ind.update_traces(marker_color="#ff5ce1")
                fig_ind.update_layout(margin=dict(l=10, r=10, t=10, b=10))
                st.plotly_chart(fig_ind, use_container_width=True)
            else:
                st.info("Belum ada data industri yang dapat ditampilkan.")
                
        with tech_col:
            st.markdown("**Teknologi / vendor yang disebut**")
            st.caption("Penyebutan tidak otomatis berarti teknologi tersebut merupakan penyebab atau solusi utama artikel.")
            all_techs = []
            for items in df_atha["technology_items"].tolist():
                all_techs.extend(items)
            
            if all_techs:
                tech_counts = pd.Series(all_techs).value_counts().head(8).sort_values(ascending=True).reset_index()
                tech_counts.columns = ["Teknologi", "Jumlah Penyebutan"]
                fig_tech = px.bar(tech_counts, x="Jumlah Penyebutan", y="Teknologi", orientation="h", text="Jumlah Penyebutan")
                fig_tech.update_traces(marker_color="#b6ff6d")
                fig_tech.update_layout(margin=dict(l=10, r=10, t=10, b=10))
                st.plotly_chart(fig_tech, use_container_width=True)
            else:
                st.info("Belum ada data teknologi yang dapat ditampilkan.")
                
    except Exception as e:
        st.error(f"Gagal memuat analitik spesifik IT Enterprise: {e}")