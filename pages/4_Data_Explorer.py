import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Data Explorer | Sector Growth",
    page_icon="🗂️",
    layout="wide",
)

st.title("🗂️ Data Explorer")
st.caption("Eksplorasi dan penyaringan data pertumbuhan sektor")

st.warning(
    "Data pada halaman ini adalah data dummy untuk mockup UI. "
    "Belum ada data yang dibaca dari Neon DB."
)

# --------------------------------------------------
# DATA DUMMY
# Ganti dengan query database setelah skema backend dikonfirmasi.
# --------------------------------------------------
df = pd.DataFrame(
    [
        {
            "Record ID": "MOCK-001",
            "Period": "2025-Q1",
            "Sector": "Sector A",
            "Indicator": "Growth",
            "Value": 8.5,
            "Unit": "%",
            "Source": "Mock Source A",
        },
        {
            "Record ID": "MOCK-002",
            "Period": "2025-Q1",
            "Sector": "Sector B",
            "Indicator": "Growth",
            "Value": 5.2,
            "Unit": "%",
            "Source": "Mock Source B",
        },
        {
            "Record ID": "MOCK-003",
            "Period": "2025-Q2",
            "Sector": "Sector C",
            "Indicator": "Growth",
            "Value": 3.7,
            "Unit": "%",
            "Source": "Mock Source A",
        },
        {
            "Record ID": "MOCK-004",
            "Period": "2025-Q2",
            "Sector": "Sector A",
            "Indicator": "Records",
            "Value": 120,
            "Unit": "records",
            "Source": "Mock Source C",
        },
        {
            "Record ID": "MOCK-005",
            "Period": "2026-Q1",
            "Sector": "Sector D",
            "Indicator": "Growth",
            "Value": -1.1,
            "Unit": "%",
            "Source": "Mock Source B",
        },
        {
            "Record ID": "MOCK-006",
            "Period": "2026-Q1",
            "Sector": "Sector E",
            "Indicator": "Growth",
            "Value": 6.4,
            "Unit": "%",
            "Source": "Mock Source A",
        },
        {
            "Record ID": "MOCK-007",
            "Period": "2026-Q2",
            "Sector": "Sector B",
            "Indicator": "Records",
            "Value": 95,
            "Unit": "records",
            "Source": "Mock Source C",
        },
        {
            "Record ID": "MOCK-008",
            "Period": "2026-Q2",
            "Sector": "Sector E",
            "Indicator": "Growth",
            "Value": 7.2,
            "Unit": "%",
            "Source": "Mock Source B",
        },
    ]
)

# --------------------------------------------------
# FILTERS
# --------------------------------------------------
st.subheader("Filter Data")

col1, col2 = st.columns(2)

with col1:
    sector_options = ["Semua sektor"] + sorted(
        df["Sector"].unique().tolist()
    )

    selected_sector = st.selectbox(
        "Pilih sektor",
        sector_options,
    )

with col2:
    period_options = ["Semua periode"] + sorted(
        df["Period"].unique().tolist()
    )

    selected_period = st.selectbox(
        "Pilih periode",
        period_options,
    )

search_text = st.text_input(
    "Cari data",
    placeholder="Cari Record ID, sektor, indikator, atau sumber...",
)

# Terapkan filter
filtered_df = df.copy()

if selected_sector != "Semua sektor":
    filtered_df = filtered_df[
        filtered_df["Sector"] == selected_sector
    ]

if selected_period != "Semua periode":
    filtered_df = filtered_df[
        filtered_df["Period"] == selected_period
    ]

if search_text.strip():
    search_mask = filtered_df.apply(
        lambda column: column.astype(str).str.contains(
            search_text.strip(),
            case=False,
            na=False,
            regex=False,
        )
    ).any(axis=1)

    filtered_df = filtered_df[search_mask]

st.divider()

# --------------------------------------------------
# SUMMARY
# --------------------------------------------------
st.subheader("Data Summary")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        "Filtered Records",
        len(filtered_df),
    )

with col2:
    st.metric(
        "Sectors Found",
        filtered_df["Sector"].nunique(),
    )

with col3:
    st.metric(
        "Periods Found",
        filtered_df["Period"].nunique(),
    )

st.divider()

# --------------------------------------------------
# TABLE
# --------------------------------------------------
st.subheader("Records Table")

if filtered_df.empty:
    st.info(
        "Tidak ada data yang cocok dengan filter. "
        "Coba ubah pilihan sektor, periode, atau kata kunci."
    )
else:
    st.dataframe(
        filtered_df,
        hide_index=True,
        width="stretch",
        column_config={
            "Value": st.column_config.NumberColumn(
                "Value",
                format="%.2f",
            ),
        },
    )

    st.download_button(
        label="Unduh hasil filter CSV",
        data=filtered_df.to_csv(
            index=False
        ).encode("utf-8"),
        file_name="sector_growth_filtered_mockup.csv",
        mime="text/csv",
    )

st.caption(
    "Seluruh record dengan ID MOCK adalah data ilustrasi, "
    "bukan data produksi."
)
