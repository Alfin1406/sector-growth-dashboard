
import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(
    page_title="Growth Trends | Sector Growth",
    page_icon="📈",
    layout="wide",
)

st.title("📈 Growth Trends")
st.caption("Eksplorasi tren pertumbuhan dari waktu ke waktu")

st.warning(
    "Halaman ini menggunakan data dummy untuk mockup UI. "
    "Angka di bawah bukan data pertumbuhan aktual."
)

# Data ilustrasi untuk menguji tampilan grafik dan filter.
df = pd.DataFrame(
    {
        "Period": [
            "Q1 2025",
            "Q2 2025",
            "Q3 2025",
            "Q4 2025",
            "Q1 2026",
            "Q2 2026",
            "Q3 2026",
        ],
        "Illustrative Index": [
            100, 104, 109, 115, 118, 123, 128
        ],
        "Year": [
            2025, 2025, 2025, 2025,
            2026, 2026, 2026
        ],
    }
)

# Filter periode
selected_period = st.selectbox(
    "Pilih periode analisis",
    ["Semua periode", "2025", "2026"],
)

if selected_period == "2025":
    chart_df = df[df["Year"] == 2025]
elif selected_period == "2026":
    chart_df = df[df["Year"] == 2026]
else:
    chart_df = df.copy()

# Ringkasan
col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Periode Ditampilkan", len(chart_df))

with col2:
    st.metric("Titik Data", len(chart_df))

with col3:
    st.metric(
        "Indeks Akhir (Dummy)",
        int(chart_df["Illustrative Index"].iloc[-1]),
    )

st.divider()

# Grafik tren
st.subheader("Illustrative Growth Trend")

fig = px.line(
    chart_df,
    x="Period",
    y="Illustrative Index",
    markers=True,
    title="Indeks Ilustratif per Periode",
    labels={
        "Period": "Periode",
        "Illustrative Index": "Indeks Ilustratif",
    },
)

fig.update_traces(line=dict(width=3), marker=dict(size=8))

st.plotly_chart(fig, width="stretch")

st.caption(
    "Seluruh nilai indeks merupakan data dummy untuk pengembangan UI."
)

st.divider()

# Tabel pendukung
st.subheader("Data Periode")

st.dataframe(
    chart_df.drop(columns=["Year"]),
    hide_index=True,
    width="stretch",
)

st.download_button(
    label="Unduh data mockup CSV",
    data=chart_df.drop(columns=["Year"]).to_csv(
        index=False
    ).encode("utf-8"),
    file_name="growth_trends_mockup.csv",
    mime="text/csv",
)
