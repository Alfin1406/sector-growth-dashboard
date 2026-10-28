
import pandas as pd
import plotly.express as px
import streamlit as st

from components.metrics import render_placeholder_kpis

st.set_page_config(
    page_title="Overview | Sector Growth",
    page_icon="📊",
    layout="wide",
)

st.title("📊 Overview")
st.caption("Ringkasan indikator pertumbuhan sektor bisnis")

st.warning(
    "Halaman ini masih berupa mockup. "
    "Grafik menggunakan data ilustrasi, bukan data aktual."
)

# KPI placeholder
render_placeholder_kpis()

st.divider()

# Grafik ilustrasi
st.subheader("Illustrative Growth Trend")

df = pd.DataFrame(
    {
        "Period": ["Q1 2025", "Q2 2025", "Q3 2025", "Q4 2025"],
        "Illustrative Index": [100, 104, 109, 115],
    }
)

fig = px.line(
    df,
    x="Period",
    y="Illustrative Index",
    markers=True,
    title="Contoh Tren Indeks",
)

st.plotly_chart(fig, width="stretch")

st.caption(
    "Nilai indeks hanya data dummy untuk menguji desain visual."
)

st.divider()

# Ringkasan status integrasi
left, right = st.columns(2)

with left:
    st.subheader("Database Status")
    st.info("Neon DB — menunggu koneksi dari tim backend.")

with right:
    st.subheader("Data Status")
    st.info("Data aktual belum diintegrasikan.")
