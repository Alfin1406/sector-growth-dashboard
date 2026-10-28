
import os
from collections.abc import Mapping
from pathlib import Path

import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine, make_url


PROJECT_ROOT = Path(__file__).resolve().parents[1]

# Fallback configuration untuk development lokal.
# Variabel environment yang sudah tersedia tidak ditimpa.
load_dotenv(PROJECT_ROOT / ".env", override=False)


def _get_secrets_database_url() -> str | None:
    """Baca DATABASE_URL dari st.secrets terlebih dahulu."""

    try:
        database_url = st.secrets.get("DATABASE_URL")

        if database_url:
            return str(database_url).strip()

        database_section = st.secrets.get("database", {})

        if isinstance(database_section, Mapping):
            database_url = (
                database_section.get("url")
                or database_section.get("DATABASE_URL")
            )

            if database_url:
                return str(database_url).strip()

    except (FileNotFoundError, KeyError):
        # Secrets lokal belum tersedia atau key tidak ditemukan.
        pass

    return None


def get_database_url() -> str:
    """Prioritas: st.secrets, lalu environment/.env lokal."""

    secrets_url = _get_secrets_database_url()

    if secrets_url:
        return secrets_url

    local_url = os.getenv("DATABASE_URL", "").strip()

    if local_url:
        return local_url

    raise RuntimeError(
        "DATABASE_URL belum dikonfigurasi. "
        "Gunakan st.secrets untuk deployment atau "
        ".env untuk development lokal."
    )


@st.cache_resource(show_spinner=False)
def _create_engine(database_url: str) -> Engine:
    """Buat engine SQLAlchemy yang dapat digunakan ulang."""

    try:
        db_url = make_url(database_url)
    except Exception as exc:
        raise ValueError(
            "Format DATABASE_URL tidak valid. "
            "Periksa connection string PostgreSQL."
        ) from exc

    if db_url.drivername in {"postgres", "postgresql"}:
        db_url = db_url.set(
            drivername="postgresql+psycopg2"
        )

    if db_url.drivername != "postgresql+psycopg2":
        raise ValueError(
            "Gunakan PostgreSQL dengan driver psycopg2."
        )

    # Neon mewajibkan koneksi SSL.
    if db_url.host and db_url.host.endswith(".neon.tech"):
        query_params = dict(db_url.query)
        query_params.setdefault("sslmode", "require")
        db_url = db_url.set(query=query_params)

    return create_engine(
        db_url,
        pool_pre_ping=True,
        pool_recycle=300,
        connect_args={"connect_timeout": 10},
        hide_parameters=True,
    )


def get_engine() -> Engine:
    """Ambil engine menggunakan sumber konfigurasi prioritas."""
    return _create_engine(get_database_url())


def check_database_connection() -> bool:
    """Uji koneksi PostgreSQL dengan query sederhana."""

    with get_engine().connect() as connection:
        connection.execute(text("SELECT 1"))

    return True


def fetch_dataframe(
    query: str,
    params: dict | None = None,
) -> pd.DataFrame:
    """Jalankan query baca dan kembalikan DataFrame."""

    with get_engine().connect() as connection:
        return pd.read_sql_query(
            text(query),
            connection,
            params=params or {},
        )
