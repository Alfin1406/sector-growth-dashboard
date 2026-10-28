
import streamlit as st


def render_placeholder_kpis() -> None:
    """Menampilkan empat KPI placeholder untuk mockup dashboard."""

    metrics = [
        ("Total Records", "—"),
        ("Sectors Analyzed", "—"),
        ("Latest Period", "—"),
        ("Average Growth", "—"),
    ]

    columns = st.columns(4)

    for column, (label, value) in zip(columns, metrics):
        with column:
            st.metric(label=label, value=value)
