import streamlit as st

st.set_page_config(
    page_title="Sector Growth & Market Intelligence",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Injeksi CSS Tema Neon
st.markdown("""
    <style>
      .stApp {
        color: #ecf7ff;
        background: linear-gradient(145deg, #060914 0%, #080d1d 52%, #090817 100%);
      }
      [data-testid="stHeader"] { background: rgba(5, 9, 22, .72); }
      [data-testid="stSidebar"] {
        background: linear-gradient(180deg, rgba(10, 17, 37, .98), rgba(15, 11, 35, .97));
        border-right: 1px solid rgba(55, 243, 255, .24);
      }
      .hero-title { font-size: clamp(1.7rem, 3.1vw, 2.65rem); font-weight: 850; text-shadow: 0 0 22px rgba(55,243,255,.16); }
    </style>
""", unsafe_allow_html=True)

st.markdown('<div class="hero-title">📈 Sector Growth & Market Intelligence</div>', unsafe_allow_html=True)
st.caption("Business Sector Intelligence, AI News Analysis, and Cloud Data Center Monitoring.")
st.divider()

st.markdown("""
    ### Selamat Datang di Pusat Intelijen Bisnis
    Dashboard ini adalah hasil kolaborasi untuk memantau pergerakan sektor bisnis, 
    infrastruktur data center, dan berita kecerdasan buatan (AI) secara otonom.
    
    **Navigasi Modul:**
    *   **📊 1. Overview:** Ringkasan KPI global dan Laporan Eksekutif berbasis AI.
    *   **📈 2. Growth Trends:** Analisis pergerakan publikasi artikel (*Month-over-Month*).
    *   **📊 3. Sector Analysis:** Taksonomi hierarki, intelijen kompetitor, dan AI per-subtopik.
    *   **🗂️ 4. Data Explorer:** Perpustakaan arsip berita dengan fitur pencarian dan tampilan Grid.
""")
st.divider()
st.caption("Kolaborasi: Alfin, Arza, & Atha - 2026")