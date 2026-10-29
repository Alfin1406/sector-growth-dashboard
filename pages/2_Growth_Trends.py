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
st.caption("Tren publikasi artikel berdasarkan waktu.")

st.info(
    "Visualisasi ini menghitung jumlah artikel berdasarkan "
    "tanggal publikasi. Ini bukan ukuran pertumbuhan ekonomi "
    "atau bisnis."
)

# Semua query menggunakan nama tabel tetap yang sudah diverifikasi.
# Ditambahkan date_trunc('week') untuk AI News sesuai struktur Alfin.
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
    "AI News (Bulanan)": """
        SELECT
            date_trunc('month', tanggal)::date AS month,
            COUNT(*)::int AS total_articles
        FROM public.tabel_berita_ai
        WHERE tanggal IS NOT NULL
        GROUP BY 1
        ORDER BY 1
    """,
    "AI News (Mingguan - Alfin)": """
        SELECT
            date_trunc('week', tanggal)::date AS month,
            COUNT(*)::int AS total_articles
        FROM public.tabel_berita_ai
        WHERE tanggal IS NOT NULL
        GROUP BY 1
        ORDER BY 1
    """
}

@st.cache_data(ttl=300, show_spinner=False)
def load_monthly_data(source: str) -> pd.DataFrame:
    """Ambil agregasi artikel bulanan/mingguan dari sumber yang dipilih."""
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
        "Rata-rata per Periode",
        f"{average_articles:,.1f}",
    )

with col3:
    # Penyesuaian format tanggal berdasarkan bulanan vs mingguan
    date_format = "%d %b %Y" if "Mingguan" in selected_source else "%b %Y"
    st.metric(
        "Puncak Publikasi",
        peak_row["month"].strftime(date_format),
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
        "month": "Periode",
        "total_articles": "Jumlah Artikel",
    },
    title="Jumlah Artikel per Periode (Bulan/Minggu)",
)

fig.update_traces(
    line=dict(width=3),
    marker=dict(size=8),
)

fig.update_layout(
    xaxis=dict(
        tickformat="%d %b %Y" if "Mingguan" in selected_source else "%b %Y",
        title="Waktu Publikasi",
        showgrid=False
    ),
    yaxis=dict(
        rangemode="tozero",
        title="Jumlah artikel",
        fixedrange=True
    ),
    hovermode="x unified",
    margin=dict(l=0, r=0, t=30, b=0)
)

st.plotly_chart(fig, use_container_width=True)

st.caption(
    "Periode terakhir pada data bisa belum lengkap. "
    "Jumlah publikasi juga dapat berubah ketika pipeline "
    "memasukkan atau memperbarui artikel."
)

st.divider()

st.subheader("Data Tabular")

display_df = df.copy()
display_df["month"] = display_df["month"].dt.strftime("%Y-%m-%d" if "Mingguan" in selected_source else "%Y-%m")
display_df = display_df.rename(
    columns={
        "month": "Periode",
        "total_articles": "Jumlah Artikel",
    }
)

st.dataframe(
    display_df,
    hide_index=True,
    width="stretch",
)

st.download_button(
    label="Unduh Data CSV",
    data=display_df.to_csv(index=False).encode("utf-8"),
    file_name="growth_trends_data.csv",
    mime="text/csv",
)