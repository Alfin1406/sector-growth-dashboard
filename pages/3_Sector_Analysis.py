
import pandas as pd
import plotly.express as px
import streamlit as st

from utils.db import fetch_dataframe

# Modul AI Summary milik Alfin.
try:
    from fitur_ai_summary import render_fitur_ai_summary
    MODUL_AI_TERSEDIA = True
except ImportError:
    MODUL_AI_TERSEDIA = False

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

# --------------------------------------------------
# QUERY DISTRIBUSI KATEGORI
# --------------------------------------------------

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


# --------------------------------------------------
# CACHE DATA
# --------------------------------------------------

@st.cache_data(ttl=300, show_spinner=False)
def load_category_data(
    source: str,
    dimension: str,
    limit: int,
) -> pd.DataFrame:
    """Mengambil jumlah artikel berdasarkan kategori."""
    query = QUERIES[source][dimension]
    return fetch_dataframe(query, params={"limit": limit})


@st.cache_data(ttl=600, show_spinner=False)
def load_raw_ai_data_for_summary(
    dimension: str,
    limit: int,
) -> pd.DataFrame:
    """Mengambil sampel berita AI untuk modul AI Summary Alfin."""

    if dimension == "Technology Tag":
        query = """
            SELECT
                judul,
                sumber,
                ringkasan_ai,
                tech.value AS subtopic
            FROM public.tabel_berita_ai
            CROSS JOIN LATERAL
                unnest(teknologi_dibahas) AS tech(value)
            WHERE teknologi_dibahas IS NOT NULL
            LIMIT :limit
        """
    elif dimension == "Business Category":
        query = """
            SELECT
                judul,
                sumber,
                ringkasan_ai,
                kategori_bisnis AS subtopic
            FROM public.tabel_berita_ai
            LIMIT :limit
        """
    else:
        query = """
            SELECT
                judul,
                sumber,
                ringkasan_ai,
                sumber AS subtopic
            FROM public.tabel_berita_ai
            LIMIT :limit
        """

    # Mengambil sampel lebih besar untuk modul AI.
    return fetch_dataframe(
        query,
        params={"limit": limit * 50},
    )


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

# Inisialisasi agar variabel selalu tersedia.
df_ai_raw = pd.DataFrame()

# --------------------------------------------------
# AMBIL DATA
# --------------------------------------------------

try:
    with st.spinner("Mengambil data kategori dari Neon DB..."):
        df = load_category_data(
            selected_source,
            selected_dimension,
            top_n,
        )

        if selected_source == "AI News" and MODUL_AI_TERSEDIA:
            df_ai_raw = load_raw_ai_data_for_summary(
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

# --------------------------------------------------
# KPI
# --------------------------------------------------

df["total"] = pd.to_numeric(
    df["total"],
    errors="raise",
).astype(int)

df = (
    df.sort_values("total", ascending=False)
    .reset_index(drop=True)
)

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

# --------------------------------------------------
# GRAFIK DISTRIBUSI
# --------------------------------------------------

st.divider()

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
    cliponaxis=False,
)

fig.update_layout(
    xaxis_title="Jumlah Artikel",
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
# MODUL AI SUMMARY ALFIN
# --------------------------------------------------

if selected_source == "AI News":
    if MODUL_AI_TERSEDIA:
        if not df_ai_raw.empty:
            st.divider()
            st.subheader("AI Summary")

            list_topik_terpilih = df["category"].tolist()

            render_fitur_ai_summary(
                df_ai_raw,
                list_topik_terpilih,
            )
        else:
            st.info(
                "Data berita AI untuk AI Summary belum tersedia."
            )
    else:
        st.info(
            "Modul AI Summary belum tersedia. "
            "Pastikan file fitur_ai_summary.py ada di lokasi "
            "yang dapat diimpor oleh aplikasi."
        )

# --------------------------------------------------
# DETAIL DISTRIBUSI
# --------------------------------------------------

st.divider()
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

if (
    selected_source == "AI News"
    and selected_dimension == "Technology Tag"
):
    st.caption(
        "Satu artikel dapat memiliki beberapa tag teknologi. "
        "Jumlah per tag menghitung kemunculan tag pada artikel, "
        "sehingga kategori tidak saling eksklusif."
    )
