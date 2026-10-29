
import streamlit as st

st.set_page_config(
    page_title="Sector Growth Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Header dashboard
st.title("📈 Sector Growth Dashboard")
st.caption("Business Sector Intelligence & Growth Analytics")

st.divider()

# Status proyek
st.info(
    "Frontend prototype aktif. "
    "Integrasi database Neon DB belum dilakukan."
)

# KPI placeholder
st.subheader("Key Performance Indicators")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Total Records", "—")

with col2:
    st.metric("Sectors Analyzed", "—")

with col3:
    st.metric("Latest Period", "—")

with col4:
    st.metric("Average Growth", "—")

st.divider()

# Bagian visualisasi
left, right = st.columns(2)

with left:
    st.subheader("Growth Trends")
    st.info("Visualisasi tren akan dibuat pada halaman Growth Trends.")

with right:
    st.subheader("Sector Analysis")
    st.info("Analisis sektor akan dibuat pada halaman Sector Analysis.")

st.divider()

st.subheader("About This Dashboard")

st.markdown(
    """
    Dashboard ini dirancang untuk membantu tim memantau
    dan menganalisis pertumbuhan sektor bisnis.

    **Status pengembangan:**
    - Frontend: tahap mockup.
    - Database: menunggu konfigurasi Neon DB.
    - Data: belum terhubung dengan database produksi.
    """
)

st.caption("Sector Growth Dashboard · Development Prototype")
