import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(
    page_title="Sector Analysis | Sector Growth",
    page_icon="📊",
    layout="wide",
)

st.title("📊 Sector Analysis")
st.caption("Perbandingan indikator pertumbuhan antar sektor")

st.warning(
    "Halaman ini menggunakan data dummy untuk mockup UI. "
    "Nilai pertumbuhan bukan data bisnis aktual."
)

# DATA DUMMY: ganti setelah skema database dikonfirmasi.
df = pd.DataFrame(
    {
        "Sector": [
            "Sector A",
            "Sector B",
            "Sector C",
            "Sector D",
            "Sector E",
        ],
        "Illustrative Growth (%)": [
            8.5,
            5.2,
            3.7,
            -1.1,
            6.4,
        ],
        "Illustrative Records": [
            120,
            95,
            80,
            45,
            110,
        ],
    }
)

# Filter sektor
selected_sectors = st.multiselect(
    "Pilih sektor untuk dibandingkan",
    options=df["Sector"].tolist(),
    default=df["Sector"].tolist(),
)

filtered_df = df[
    df["Sector"].isin(selected_sectors)
].copy()

st.divider()

# Ringkasan KPI
col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        "Sectors Selected",
        len(filtered_df),
    )

with col2:
    if not filtered_df.empty:
        highest_sector = filtered_df.loc[
            filtered_df["Illustrative Growth (%)"].idxmax()
        ]
        st.metric(
            "Highest Growth (Dummy)",
            f"{highest_sector['Illustrative Growth (%)']:.1f}%",
            help=f"Sektor: {highest_sector['Sector']}",
        )
    else:
        st.metric("Highest Growth (Dummy)", "—")

with col3:
    if not filtered_df.empty:
        lowest_sector = filtered_df.loc[
            filtered_df["Illustrative Growth (%)"].idxmin()
        ]
        st.metric(
            "Lowest Growth (Dummy)",
            f"{lowest_sector['Illustrative Growth (%)']:.1f}%",
            help=f"Sektor: {lowest_sector['Sector']}",
        )
    else:
        st.metric("Lowest Growth (Dummy)", "—")

st.divider()

# Grafik perbandingan pertumbuhan
st.subheader("Illustrative Growth by Sector")

if filtered_df.empty:
    st.info("Pilih minimal satu sektor untuk menampilkan grafik.")
else:
    chart_df = filtered_df.sort_values(
        "Illustrative Growth (%)",
        ascending=True,
    )

    fig = px.bar(
        chart_df,
        x="Illustrative Growth (%)",
        y="Sector",
        orientation="h",
        text="Illustrative Growth (%)",
        labels={
            "Illustrative Growth (%)": "Pertumbuhan Ilustratif (%)",
            "Sector": "Sektor",
        },
        title="Perbandingan Pertumbuhan Ilustratif",
    )

    fig.update_traces(
        texttemplate="%{text:.1f}%",
        textposition="outside",
    )

    fig.add_vline(
        x=0,
        line_dash="dash",
        line_color="gray",
    )

    st.plotly_chart(fig, width="stretch")

st.caption(
    "Angka positif dan negatif hanya contoh untuk menguji visualisasi."
)

st.divider()

# Tabel perbandingan
st.subheader("Sector Comparison Table")

st.dataframe(
    filtered_df,
    hide_index=True,
    width="stretch",
)

# Ekspor data mockup
st.download_button(
    label="Unduh data mockup CSV",
    data=filtered_df.to_csv(index=False).encode("utf-8"),
    file_name="sector_analysis_mockup.csv",
    mime="text/csv",
)
