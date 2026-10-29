
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

# Semua query menggunakan nama tabel yang sudah diverifikasi.
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
    """,

    # Tambahan Arza: tren publikasi Data Center & Cloud.
    "Tren Publikasi Data Center (Arza)": """
        SELECT
            date_trunc('month', published_date)::date AS month,
            COUNT(*)::int AS total_articles
        FROM public.data_center_news
        WHERE record_type = 'ARTICLE'
          AND published_date IS NOT NULL
        GROUP BY 1
        ORDER BY 1
    """,
}


@st.cache_data(ttl=300, show_spinner=False)
def load_monthly_data(source: str) -> pd.DataFrame:
    """Mengambil agregasi publikasi dari sumber yang dipilih."""
    return fetch_dataframe(QUERIES[source])


# --------------------------------------------------
# GRAFIK UTAMA: FITUR EXISTING
# --------------------------------------------------

# Query khusus tren Arza ditampilkan sebagai grafik tambahan
# di bawah, bukan sebagai pilihan pada grafik utama.
main_sources = [
    source
    for source in QUERIES
    if source != "Tren Publikasi Data Center (Arza)"
]

selected_source = st.selectbox(
    "Pilih sumber data",
    main_sources,
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

total_articles = int(df["total_articles"].sum())
average_articles = df["total_articles"].mean()
peak_row = df.loc[df["total_articles"].idxmax()]

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Total Artikel", f"{total_articles:,}")

with col2:
    st.metric(
        "Rata-rata per Periode",
        f"{average_articles:,.1f}",
    )

with col3:
    date_format = (
        "%d %b %Y"
        if "Mingguan" in selected_source
        else "%b %Y"
    )
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
        tickformat=(
            "%d %b %Y"
            if "Mingguan" in selected_source
            else "%b %Y"
        ),
        title="Waktu Publikasi",
        showgrid=False,
    ),
    yaxis=dict(
        rangemode="tozero",
        title="Jumlah Artikel",
        fixedrange=True,
    ),
    hovermode="x unified",
    margin=dict(l=0, r=0, t=30, b=0),
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
display_df["month"] = display_df["month"].dt.strftime(
    "%Y-%m-%d"
    if "Mingguan" in selected_source
    else "%Y-%m"
)
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

# --------------------------------------------------
# TAMBAHAN ARZA: TREN PUBLIKASI DATA CENTER & CLOUD
# --------------------------------------------------

st.divider()
st.subheader("Tren Publikasi Data Center & Cloud")
st.caption(
    "Grafik tambahan untuk melihat jumlah artikel Data Center "
    "per bulan beserta perubahan dibandingkan bulan sebelumnya."
)

try:
    with st.spinner("Mengambil tren publikasi Data Center..."):
        df_tren = fetch_dataframe(
            QUERIES["Tren Publikasi Data Center (Arza)"]
        )

except Exception as exc:
    st.error(
        "Gagal mengambil tren publikasi Data Center. "
        f"Jenis error: {type(exc).__name__}."
    )
    df_tren = pd.DataFrame()

if df_tren.empty:
    st.warning(
        "Belum ada data Data Center untuk ditampilkan "
        "atau data belum berhasil diambil."
    )
else:
    df_tren["month"] = pd.to_datetime(df_tren["month"])
    df_tren["total_articles"] = pd.to_numeric(
        df_tren["total_articles"],
        errors="raise",
    )
    df_tren = df_tren.sort_values("month").reset_index(drop=True)

    # Persentase perubahan dibandingkan bulan sebelumnya.
    df_tren["change_pct"] = (
        df_tren["total_articles"]
        .pct_change(fill_method=None)
        .mul(100)
    )

    total_dc = int(df_tren["total_articles"].sum())
    latest_row = df_tren.iloc[-1]
    latest_month = latest_row["month"].strftime("%b %Y")
    latest_count = int(latest_row["total_articles"])

    metric1, metric2, metric3 = st.columns(3)

    with metric1:
        st.metric(
            "Total Publikasi Data Center",
            f"{total_dc:,}",
        )

    with metric2:
        st.metric(
            "Publikasi Bulan Terakhir",
            f"{latest_count:,}",
            help=f"Periode: {latest_month}",
        )

    with metric3:
        change_pct = latest_row["change_pct"]

        if pd.isna(change_pct):
            st.metric(
                "Perubahan dari Bulan Sebelumnya",
                "N/A",
                help="Belum ada data bulan sebelumnya untuk dibandingkan.",
            )
        else:
            st.metric(
                "Perubahan dari Bulan Sebelumnya",
                f"{change_pct:+.1f}%",
                help=(
                    "Persentase perubahan jumlah artikel dibandingkan "
                    "bulan publikasi sebelumnya."
                ),
            )

    fig_tren = px.line(
        df_tren,
        x="month",
        y="total_articles",
        markers=True,
        labels={
            "month": "Bulan",
            "total_articles": "Jumlah Artikel",
        },
        title="Tren Publikasi Data Center & Cloud per Bulan",
    )

    fig_tren.update_traces(
        line=dict(width=3),
        marker=dict(size=8),
    )

    fig_tren.update_layout(
        xaxis=dict(
            title="Bulan Publikasi",
            tickformat="%b %Y",
            showgrid=False,
        ),
        yaxis=dict(
            title="Jumlah Artikel",
            rangemode="tozero",
            fixedrange=True,
        ),
        hovermode="x unified",
        margin=dict(l=0, r=0, t=40, b=0),
    )

    st.plotly_chart(
        fig_tren,
        use_container_width=True,
    )

    tren_display = df_tren[
        ["month", "total_articles", "change_pct"]
    ].copy()

    tren_display["month"] = tren_display["month"].dt.strftime("%Y-%m")
    tren_display["change_pct"] = tren_display["change_pct"].map(
        lambda value: (
            "N/A" if pd.isna(value) else f"{value:+.1f}%"
        )
    )

    tren_display = tren_display.rename(
        columns={
            "month": "Bulan",
            "total_articles": "Jumlah Artikel",
            "change_pct": "Perubahan Bulanan",
        }
    )

    st.dataframe(
        tren_display,
        hide_index=True,
        width="stretch",
    )

    st.caption(
        "Persentase perubahan dihitung dari jumlah artikel per bulan, "
        "bukan pertumbuhan ekonomi atau bisnis. Bulan berjalan mungkin "
        "belum mencakup satu bulan penuh."
    )
