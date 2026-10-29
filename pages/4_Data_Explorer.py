
from datetime import date, timedelta

import pandas as pd
import streamlit as st

from utils.db import fetch_dataframe

st.set_page_config(
    page_title="Data Explorer | Sector Growth",
    page_icon="🗂️",
    layout="wide",
)

st.title("🗂️ Data Explorer")
st.caption("Pencarian dan eksplorasi artikel dari Neon DB.")

st.info(
    "Data diambil langsung dari database. "
    "Jumlah artikel antar-tabel belum dideduplikasi, "
    "sehingga hasilnya bukan jumlah berita unik lintas sumber."
)

# --------------------------------------------------
# QUERY DEFINITIONS
# SQL di bawah ditetapkan oleh aplikasi. Input pengguna
# dimasukkan melalui parameter SQLAlchemy, bukan ke SQL mentah.
# --------------------------------------------------

SOURCE_SPECS = {
    "Sector 3": {
        "select_sql": """
            published_at::date AS "Tanggal",
            title AS "Judul",
            source AS "Sumber",
            COALESCE(topic, '(NULL)') AS "Kategori",
            COALESCE(subtopic, '(NULL)') AS "Subkategori / Teknologi",
            COALESCE(content_status, '(NULL)') AS "Status / Skor",
            url AS "URL"
        """,
        "from_sql": "public.sector3_articles",
        "date_column": "published_at",
        "search_expression": """
            concat_ws(
                ' ',
                title,
                source,
                topic,
                subtopic,
                industry,
                technology,
                business_action,
                impact,
                insight_summary
            )
        """,
        "fixed_conditions": [],
    },
    "Data Center News": {
        "select_sql": """
            published_date AS "Tanggal",
            title AS "Judul",
            source AS "Sumber",
            COALESCE(sector, '(NULL)') AS "Kategori",
            COALESCE(topic, '(NULL)') AS "Subkategori / Teknologi",
            COALESCE(relevance, '(NULL)') AS "Status / Skor",
            article_url AS "URL"
        """,
        "from_sql": "public.data_center_news",
        "date_column": "published_date",
        "search_expression": """
            concat_ws(
                ' ',
                title,
                source,
                sector,
                topic,
                technology,
                company,
                organization,
                summary
            )
        """,
        "fixed_conditions": ["record_type = 'ARTICLE'"],
    },
    "AI News": {
        "select_sql": """
            tanggal AS "Tanggal",
            judul AS "Judul",
            sumber AS "Sumber",
            COALESCE(kategori_bisnis, '(NULL)') AS "Kategori",
            COALESCE(
                array_to_string(teknologi_dibahas, ', '),
                '(NULL)'
            ) AS "Subkategori / Teknologi",
            COALESCE(skor_relevansi_it::text, '(NULL)') AS "Status / Skor",
            link AS "URL"
        """,
        "from_sql": "public.tabel_berita_ai",
        "date_column": "tanggal",
        "search_expression": """
            concat_ws(
                ' ',
                judul,
                sumber,
                kategori_bisnis,
                array_to_string(teknologi_dibahas, ', '),
                kategori_lisensi,
                ringkasan_ai
            )
        """,
        "fixed_conditions": [],
    },
}


@st.cache_data(ttl=300, show_spinner=False)
def load_records(
    source: str,
    search_term: str,
    start_date: date | None,
    end_date: date | None,
    limit: int,
) -> pd.DataFrame:
    """Ambil artikel dari sumber yang dipilih dengan filter aman."""

    spec = SOURCE_SPECS[source]

    conditions = list(spec["fixed_conditions"])
    params = {"limit": limit}

    if start_date is not None and end_date is not None:
        conditions.append(
            f"{spec['date_column']}::date "
            "BETWEEN :start_date AND :end_date"
        )
        params["start_date"] = start_date
        params["end_date"] = end_date

    if search_term.strip():
        conditions.append(
            f"{spec['search_expression']} ILIKE :search_pattern"
        )
        params["search_pattern"] = f"%{search_term.strip()}%"

    where_clause = (
        " AND ".join(conditions)
        if conditions
        else "TRUE"
    )

    query = f"""
        SELECT {spec['select_sql']}
        FROM {spec['from_sql']}
        WHERE {where_clause}
        ORDER BY {spec['date_column']} DESC NULLS LAST
        LIMIT :limit
    """

    return fetch_dataframe(query, params=params)


# --------------------------------------------------
# FILTER CONTROLS
# --------------------------------------------------

source = st.selectbox(
    "Pilih sumber data",
    list(SOURCE_SPECS.keys()),
)

search_term = st.text_input(
    "Cari artikel",
    placeholder="Masukkan judul, sumber, kategori, teknologi, atau kata kunci...",
)

limit = st.selectbox(
    "Maksimum record yang ditampilkan",
    options=[100, 250, 500, 1000],
    index=1,
)

use_date_filter = st.checkbox(
    "Batasi rentang tanggal",
    value=False,
)

start_date = None
end_date = None

if use_date_filter:
    today = date.today()
    default_start = today - timedelta(days=180)

    date_range = st.date_input(
        "Rentang tanggal publikasi",
        value=(default_start, today),
        max_value=today,
    )

    if not isinstance(date_range, (tuple, list)) or len(date_range) != 2:
        st.warning(
            "Pilih tanggal mulai dan tanggal akhir "
            "untuk menerapkan filter."
        )
        st.stop()

    start_date, end_date = date_range

    if start_date > end_date:
        st.error("Tanggal mulai tidak boleh melewati tanggal akhir.")
        st.stop()


# --------------------------------------------------
# LOAD DATA
# --------------------------------------------------

try:
    with st.spinner("Mengambil artikel dari Neon DB..."):
        df = load_records(
            source=source,
            search_term=search_term,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
        )

except Exception as exc:
    st.error(
        "Data Explorer gagal mengambil data. "
        "Periksa koneksi database dan struktur tabel."
    )
    st.caption(f"Jenis error: {type(exc).__name__}")
    st.stop()


# --------------------------------------------------
# SUMMARY
# --------------------------------------------------

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Record Ditampilkan", f"{len(df):,}")

with col2:
    sector_count = (
        int(df["Kategori"].nunique())
        if not df.empty
        else 0
    )
    st.metric("Kategori Ditemukan", f"{sector_count:,}")

with col3:
    source_count = (
        int(df["Sumber"].nunique())
        if not df.empty
        else 0
    )
    st.metric("Sumber Berita", f"{source_count:,}")

st.caption(
    f"Sumber aktif: {source}. "
    f"Batas tampilan: {limit:,} record."
)

st.divider()


# --------------------------------------------------
# DATA TABLE
# --------------------------------------------------

st.subheader("Daftar Artikel")

if df.empty:
    st.warning(
        "Tidak ada artikel yang sesuai dengan filter. "
        "Coba ubah kata kunci atau rentang tanggal."
    )

else:
    st.dataframe(
        df,
        hide_index=True,
        width="stretch",
        column_config={
            "URL": st.column_config.LinkColumn(
                "Artikel",
                display_text="Buka artikel",
            ),
        },
    )

    st.download_button(
        label="Unduh hasil sebagai CSV",
        data=df.to_csv(index=False).encode("utf-8"),
        file_name="sector_growth_articles.csv",
        mime="text/csv",
    )

st.caption(
    "Hasil dibatasi sesuai jumlah record yang dipilih. "
    "Data diambil menggunakan query baca saja."
)
