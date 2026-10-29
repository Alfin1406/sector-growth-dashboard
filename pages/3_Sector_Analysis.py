
import pandas as pd
import plotly.express as px
import streamlit as st

from utils.db import fetch_dataframe

st.set_page_config(
    page_title="Sector Analysis | Sector Growth",
    page_icon="📊",
    layout="wide",
)

st.title("📊 Sector Analysis")
st.caption("Analisis distribusi kategori dari data berita aktual.")

st.info(
    "Jumlah pada grafik menunjukkan jumlah artikel per kategori, "
    "bukan tingkat pertumbuhan ekonomi atau bisnis. "
    "Kategori dan jumlahnya mengikuti sumber data yang dipilih."
)

# Semua nama tabel dan kolom bersifat tetap dan sudah diperiksa.
# User hanya memilih opsi yang telah didefinisikan di sini.
QUERIES = {
    "Sector 3": {
        "Topic": """
            SELECT
                COALESCE(topic, '(NULL)') AS category,
                COUNT(*)::int AS total
            FROM public.sector3_articles
            GROUP BY topic
            ORDER BY total DESC, category
            LIMIT :limit
        """,
        "Subtopic": """
            SELECT
                COALESCE(subtopic, '(NULL)') AS category,
                COUNT(*)::int AS total
            FROM public.sector3_articles
            GROUP BY subtopic
            ORDER BY total DESC, category
            LIMIT :limit
        """,
        "Industry": """
            SELECT
                COALESCE(industry, '(NULL)') AS category,
                COUNT(*)::int AS total
            FROM public.sector3_articles
            GROUP BY industry
            ORDER BY total DESC, category
            LIMIT :limit
        """,
        "Publisher": """
            SELECT
                COALESCE(source, '(NULL)') AS category,
                COUNT(*)::int AS total
            FROM public.sector3_articles
            GROUP BY source
            ORDER BY total DESC, category
            LIMIT :limit
        """,
        "Content Status": """
            SELECT
                COALESCE(content_status, '(NULL)') AS category,
                COUNT(*)::int AS total
            FROM public.sector3_articles
            GROUP BY content_status
            ORDER BY total DESC, category
            LIMIT :limit
        """,
    },
    "Data Center News": {
        "Sector": """
            SELECT
                COALESCE(sector, '(NULL)') AS category,
                COUNT(*)::int AS total
            FROM public.data_center_news
            WHERE record_type = 'ARTICLE'
            GROUP BY sector
            ORDER BY total DESC, category
            LIMIT :limit
        """,
        "Topic": """
            SELECT
                COALESCE(topic, '(NULL)') AS category,
                COUNT(*)::int AS total
            FROM public.data_center_news
            WHERE record_type = 'ARTICLE'
            GROUP BY topic
            ORDER BY total DESC, category
            LIMIT :limit
        """,
        "Publisher": """
            SELECT
                COALESCE(source, '(NULL)') AS category,
                COUNT(*)::int AS total
            FROM public.data_center_news
            WHERE record_type = 'ARTICLE'
            GROUP BY source
            ORDER BY total DESC, category
            LIMIT :limit
        """,
        "Relevance": """
            SELECT
                COALESCE(relevance, '(NULL)') AS category,
                COUNT(*)::int AS total
            FROM public.data_center_news
            WHERE record_type = 'ARTICLE'
            GROUP BY relevance
            ORDER BY total DESC, category
            LIMIT :limit
        """,
    },
    "AI News": {
        "Business Category": """
            SELECT
                COALESCE(kategori_bisnis, '(NULL)') AS category,
                COUNT(*)::int AS total
            FROM public.tabel_berita_ai
            GROUP BY kategori_bisnis
            ORDER BY total DESC, category
            LIMIT :limit
        """,
        "Publisher": """
            SELECT
                COALESCE(sumber, '(NULL)') AS category,
                COUNT(*)::int AS total
            FROM public.tabel_berita_ai
            GROUP BY sumber
            ORDER BY total DESC, category
            LIMIT :limit
        """,
        "Technology Tag": """
            SELECT
                COALESCE(tech.value, '(NULL)') AS category,
                COUNT(*)::int AS total
            FROM public.tabel_berita_ai
            CROSS JOIN LATERAL
                unnest(teknologi_dibahas) AS tech(value)
            WHERE teknologi_dibahas IS NOT NULL
            GROUP BY tech.value
            ORDER BY total DESC, category
            LIMIT :limit
        """,
    },
}


@st.cache_data(ttl=300, show_spinner=False)
def load_category_data(
    source: str,
    dimension: str,
    limit: int,
) -> pd.DataFrame:
    """Mengambil agregasi kategori dari sumber yang dipilih."""
    query = QUERIES[source][dimension]
    return fetch_dataframe(query, params={"limit": limit})


# --------------------------------------------------
# FILTER
# --------------------------------------------------

filter_col1, filter_col2 = st.columns(2)

with filter_col1:
    selected_source = st.selectbox(
        "Pilih sumber data",
        list(QUERIES.keys()),
    )

with filter_col2:
    selected_dimension = st.selectbox(
        "Analisis berdasarkan",
        list(QUERIES[selected_source].keys()),
    )

top_n = st.selectbox(
    "Jumlah kategori teratas",
    options=[10, 15, 20, 30],
    index=1,
)

try:
    with st.spinner("Mengambil data kategori dari Neon DB..."):
        df = load_category_data(
            selected_source,
            selected_dimension,
            top_n,
        )

except Exception as exc:
    st.error(
        "Kategori belum berhasil dimuat dari Neon DB. "
        "Periksa koneksi dan konfigurasi query."
    )
    st.caption(f"Jenis error: {type(exc).__name__}")
    st.stop()


if df.empty:
    st.warning("Tidak ada kategori yang tersedia untuk pilihan ini.")
    st.stop()


df["total"] = pd.to_numeric(
    df["total"],
    errors="raise",
).astype(int)

df = df.sort_values(
    "total",
    ascending=False,
).reset_index(drop=True)


# --------------------------------------------------
# KPI
# --------------------------------------------------

top_category = df.iloc[0]

col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        "Kategori Ditampilkan",
        len(df),
    )

with col2:
    st.metric(
        "Kategori Teratas",
        str(top_category["category"]),
    )

with col3:
    st.metric(
        "Artikel pada Kategori Teratas",
        f"{int(top_category['total']):,}",
    )


st.divider()


# --------------------------------------------------
# CHART
# --------------------------------------------------

st.subheader(
    f"Distribusi {selected_dimension} — {selected_source}"
)

chart_df = df.sort_values(
    "total",
    ascending=True,
)

fig = px.bar(
    chart_df,
    x="total",
    y="category",
    orientation="h",
    text="total",
    labels={
        "total": "Jumlah Artikel",
        "category": selected_dimension,
    },
    title=f"Jumlah Artikel per {selected_dimension}",
)

fig.update_traces(
    textposition="outside",
)

fig.update_layout(
    xaxis_title="Jumlah artikel",
    yaxis_title=selected_dimension,
    yaxis=dict(
        categoryorder="array",
        categoryarray=chart_df["category"].tolist(),
    ),
    xaxis_rangemode="tozero",
)

st.plotly_chart(
    fig,
    width="stretch",
)


# --------------------------------------------------
# TABLE
# --------------------------------------------------

st.subheader("Detail Distribusi")

display_df = df.rename(
    columns={
        "category": "Kategori",
        "total": "Jumlah Artikel",
    }
)

st.dataframe(
    display_df,
    hide_index=True,
    width="stretch",
)

st.download_button(
    label="Unduh distribusi CSV",
    data=display_df.to_csv(index=False).encode("utf-8"),
    file_name="sector_analysis_distribution.csv",
    mime="text/csv",
)

if selected_source == "AI News" and selected_dimension == "Technology Tag":
    st.caption(
        "Satu artikel dapat memiliki beberapa tag teknologi. "
        "Jumlah per tag menghitung kemunculan tag pada artikel, "
        "sehingga kategori tidak saling eksklusif."
    )

if selected_source == "Data Center News":
    st.caption(
        "Hanya record dengan record_type = 'ARTICLE' yang dihitung. "
        "Record ringkasan AI tidak disertakan."
    )
