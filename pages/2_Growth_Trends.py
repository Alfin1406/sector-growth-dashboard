import pandas as pd
import plotly.express as px
import streamlit as st
from utils.db import fetch_dataframe

st.set_page_config(page_title="Growth Trends | Sector Growth", page_icon="📈", layout="wide")
st.title("📈 Growth Trends")
st.caption("Tren publikasi artikel berdasarkan waktu.")

# --- KONTROL FILTER ---
col_res, col_src, col_opt = st.columns([1, 1, 1.5])
with col_res: 
    time_resolution = st.radio("Resolusi Waktu", ["Bulanan", "Mingguan"], horizontal=True)
with col_src: 
    selected_source = st.selectbox("Pilih sumber data", ["Sector 3", "Data Center & Cloud", "AI News"])
with col_opt:
    st.write("") # Spacer agar sejajar
    st.write("")
    exclude_current = st.checkbox("Sembunyikan periode berjalan (belum selesai)", value=False, help="Centang ini agar grafik tidak menukik tajam di akhir periode karena bulan/minggu yang belum genap.")

sql_trunc = "month" if time_resolution == "Bulanan" else "week"

queries = {
    "Sector 3": f"SELECT date_trunc('{sql_trunc}', published_at)::date AS month, COUNT(*)::int AS total_articles FROM public.sector3_articles WHERE published_at IS NOT NULL GROUP BY 1 ORDER BY 1",
    "Data Center & Cloud": f"SELECT date_trunc('{sql_trunc}', published_date)::date AS month, COUNT(*)::int AS total_articles FROM public.data_center_news WHERE record_type = 'ARTICLE' AND published_date IS NOT NULL GROUP BY 1 ORDER BY 1",
    "AI News": f"SELECT date_trunc('{sql_trunc}', tanggal)::date AS month, COUNT(*)::int AS total_articles FROM public.tabel_berita_ai WHERE tanggal IS NOT NULL GROUP BY 1 ORDER BY 1"
}

try:
    df = fetch_dataframe(queries[selected_source])
except Exception as exc:
    st.error(f"Gagal mengambil data: {exc}")
    st.stop()

if df.empty:
    st.warning("Belum ada data publikasi untuk sumber ini.")
    st.stop()

# --- PEMROSESAN DATA ---
df["month"] = pd.to_datetime(df["month"])
df["total_articles"] = pd.to_numeric(df["total_articles"])
df = df.sort_values("month").reset_index(drop=True)

# Logika Checkbox: Memotong baris paling terakhir jika dicentang
if exclude_current and len(df) > 1:
    df = df.iloc[:-1]

df["change_pct"] = df["total_articles"].pct_change(fill_method=None).mul(100)

# --- METRIK ---
total_articles = int(df["total_articles"].sum())
average_articles = df["total_articles"].mean()
peak_row = df.loc[df["total_articles"].idxmax()]
latest_row = df.iloc[-1]
date_format = "%d %b %Y" if time_resolution == "Mingguan" else "%b %Y"

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Artikel", f"{total_articles:,}")
col2.metric("Rata-rata / Periode", f"{average_articles:,.1f}")
col3.metric("Puncak Publikasi", peak_row["month"].strftime(date_format), help=f"{int(peak_row['total_articles']):,} artikel")

change_pct = latest_row["change_pct"]
val_change = "N/A" if pd.isna(change_pct) else f"{change_pct:+.1f}%"
col4.metric(f"Periode Terakhir ({latest_row['month'].strftime(date_format)})", f"{int(latest_row['total_articles']):,}", val_change)

st.divider()

# --- GRAFIK ---
fig = px.line(df, x="month", y="total_articles", markers=True, title=f"Pergerakan Publikasi: {selected_source}")
fig.update_traces(line=dict(width=3), marker=dict(size=8))
fig.update_layout(xaxis_title="Periode", yaxis_title="Jumlah Artikel", xaxis=dict(tickformat=date_format), hovermode="x unified")
st.plotly_chart(fig, use_container_width=True)

# --- TABEL & UNDUH CSV ---
with st.expander("Lihat Data Tabular & Unduh", expanded=False):
    display_df = df.copy()
    display_df["month"] = display_df["month"].dt.strftime("%Y-%m-%d" if time_resolution == "Mingguan" else "%Y-%m")
    display_df["change_pct"] = display_df["change_pct"].map(lambda x: "N/A" if pd.isna(x) else f"{x:+.1f}%")
    display_df = display_df.rename(columns={"month": "Periode", "total_articles": "Jumlah Artikel", "change_pct": "Perubahan"})
    
    st.dataframe(display_df, hide_index=True, use_container_width=True)
    
    csv = display_df.to_csv(index=False).encode('utf-8')
    st.download_button(label="📥 Unduh Data (CSV)", data=csv, file_name=f"trend_{selected_source.lower().replace(' ', '_')}.csv", mime="text/csv")