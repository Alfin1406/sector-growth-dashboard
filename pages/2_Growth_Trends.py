
import pandas as pd
import plotly.express as px
import streamlit as st

from utils.db import fetch_dataframe

st.set_page_config(
    page_title="Growth Trends | Sector Growth",
    page_icon="📈",
    layout="wide",
)

st.title("📈 Growth Trends")
st.caption("Tren publikasi artikel berdasarkan bulan.")

st.info(
    "Visualisasi ini menghitung jumlah artikel berdasarkan "
    "tanggal publikasi. Ini bukan ukuran pertumbuhan ekonomi "
    "atau bisnis."
)

# Semua query menggunakan nama tabel tetap yang sudah diverifikasi.
# data_center_news difilter untuk mengecualikan record AI_SUMMARY.
QUERIES = {
    "Sector 3": """
        SELECT
            date_trunc('month', published_at)::date AS month,
            COUNT(*)::int AS total_articles
        FROM public.sector3_articles
        WHERE published_at IS NOT NULL
        GROUP BY 1
        ORDER BY 1
    """,
    "Data Center News": """
        SELECT
            date_trunc('month', published_date)::date AS month,
            COUNT(*)::int AS total_articles
        FROM public.data_center_news
        WHERE record_type = 'ARTICLE'
          AND published_date IS NOT NULL
        GROUP BY 1
        ORDER BY 1
    """,
    "AI News": """
        SELECT
            date_trunc('month', tanggal)::date AS month,
            COUNT(*)::int AS total_articles
        FROM public.tabel_berita_ai
        WHERE tanggal IS NOT NULL
        GROUP BY 1
        ORDER BY 1
    """,
}


@st.cache_data(ttl=300, show_spinner=False)
def load_monthly_data(source: str) -> pd.DataFrame:
    """Ambil agregasi artikel bulanan dari sumber yang dipilih."""
    query = QUERIES[source]
    return fetch_dataframe(query)


selected_source = st.selectbox(
    "Pilih sumber data",
    list(QUERIES.keys()),
)

try:
    with st.spinner("Mengambil data dari Neon DB..."):
        df = load_monthly_data(selected_source)

except Exception as exc:
    st.error(
        "Data belum berhasil diambil dari Neon DB. "
        f"Jenis error: {type(exc).__name__}. "
        "Periksa konfigurasi koneksi dan coba lagi."
    )
    st.stop()

if df.empty:
    st.warning("Belum ada data publikasi untuk sumber ini.")
    st.stop()

df["month"] = pd.to_datetime(df["month"])
df["total_articles"] = pd.to_numeric(
    df["total_articles"],
    errors="raise",
)
df = df.sort_values("month").reset_index(drop=True)

# Ringkasan dihitung dari hasil query aktual.
total_articles = int(df["total_articles"].sum())
average_articles = df["total_articles"].mean()
peak_row = df.loc[df["total_articles"].idxmax()]

col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        "Total Artikel",
        f"{total_articles:,}",
    )

with col2:
    st.metric(
        "Rata-rata per Bulan",
        f"{average_articles:,.1f}",
    )

with col3:
    st.metric(
        "Puncak Publikasi",
        peak_row["month"].strftime("%b %Y"),
        help=f"{int(peak_row['total_articles']):,} artikel",
    )

st.divider()

st.subheader(f"Tren Publikasi — {selected_source}")

fig = px.line(
    df,
    x="month",
    y="total_articles",
    markers=True,
    labels={
        "month": "Bulan",
        "total_articles": "Jumlah Artikel",
    },
    title="Jumlah Artikel per Bulan",
)

fig.update_traces(
    line=dict(width=3),
    marker=dict(size=8),
)

fig.update_layout(
    xaxis=dict(
        tickformat="%b %Y",
        title="Bulan publikasi",
    ),
    yaxis=dict(
        rangemode="tozero",
        title="Jumlah artikel",
    ),
    hovermode="x unified",
)

st.plotly_chart(fig, width="stretch")

st.caption(
    "Bulan terakhir pada data bisa belum lengkap. "
    "Jumlah publikasi juga dapat berubah ketika pipeline "
    "memasukkan atau memperbarui artikel."
)

st.divider()

st.subheader("Data Bulanan")

display_df = df.copy()
display_df["month"] = display_df["month"].dt.strftime("%Y-%m")
display_df = display_df.rename(
    columns={
        "month": "Bulan",
        "total_articles": "Jumlah Artikel",
    }
)

st.dataframe(
    display_df,
    hide_index=True,
    width="stretch",
)

st.download_button(
    label="Unduh Data Bulanan CSV",
    data=display_df.to_csv(index=False).encode("utf-8"),
    file_name="growth_trends_monthly.csv",
    mime="text/csv",
)
