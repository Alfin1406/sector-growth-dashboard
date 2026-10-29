import pandas as pd
import plotly.express as px
import streamlit as st

from utils.db import fetch_dataframe

st.set_page_config(
    page_title="Overview | Sector Growth",
    page_icon="📊",
    layout="wide",
)

st.title("📊 Overview")
st.caption("Ringkasan publikasi berita dari database tim.")

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


@st.cache_data(ttl=300, show_spinner=False)
def load_overview_data() -> pd.DataFrame:
    """Mengambil ringkasan aktual dari ketiga sumber berita."""
    return fetch_dataframe(OVERVIEW_QUERY)


try:
    with st.spinner("Mengambil ringkasan dari Neon DB..."):
        df = load_overview_data()

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


# Pastikan jumlah artikel diperlakukan sebagai bilangan bulat.
df["article_count"] = pd.to_numeric(
    df["article_count"],
    errors="raise",
).astype(int)

summary = df.set_index("source")

sector3_count = int(
    summary.loc["Sector 3", "article_count"]
)

data_center_count = int(
    summary.loc["Data Center News", "article_count"]
)

ai_news_count = int(
    summary.loc["AI News", "article_count"]
)


# --------------------------------------------------
# KPI
# --------------------------------------------------

st.subheader("Key Performance Indicators")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        "Artikel Sector 3",
        f"{sector3_count:,}",
    )

with col2:
    st.metric(
        "Artikel Data Center",
        f"{data_center_count:,}",
    )

with col3:
    st.metric(
        "Artikel AI News",
        f"{ai_news_count:,}",
    )


st.divider()


# --------------------------------------------------
# PERBANDINGAN JUMLAH ARTIKEL PER SUMBER
# --------------------------------------------------

st.subheader("Jumlah Artikel per Sumber")

fig = px.bar(
    df,
    x="source",
    y="article_count",
    text="article_count",
    labels={
        "source": "Sumber Data",
        "article_count": "Jumlah Artikel",
    },
    title="Jumlah Record Artikel pada Setiap Tabel",
)

fig.update_traces(
    textposition="outside",
)

fig.update_layout(
    xaxis_title="Sumber Data",
    yaxis_title="Jumlah Artikel",
    yaxis_rangemode="tozero",
)

st.plotly_chart(
    fig,
    width="stretch",
)

st.caption(
    "Perbandingan ini menunjukkan jumlah artikel per tabel. "
    "Artikel yang sama mungkin tercatat di lebih dari satu sumber."
)


st.divider()


# --------------------------------------------------
# TANGGAL PUBLIKASI TERBARU
# --------------------------------------------------

st.subheader("Ringkasan Sumber Data")

display_df = df.copy()

display_df["latest_publication"] = (
    pd.to_datetime(
        display_df["latest_publication"],
        errors="coerce",
    )
    .dt.strftime("%Y-%m-%d")
    .fillna("Belum tersedia")
)

display_df = display_df.rename(
    columns={
        "source": "Sumber",
        "article_count": "Jumlah Artikel",
        "latest_publication": "Publikasi Terbaru",
    }
)

st.dataframe(
    display_df,
    hide_index=True,
    width="stretch",
)


st.caption(
    "Ringkasan dimuat dari Neon DB dan diperbarui melalui cache "
    "setiap lima menit."
)