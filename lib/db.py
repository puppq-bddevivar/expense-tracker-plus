import os
from contextlib import contextmanager

import streamlit as st
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Use environment variable for DB URL, default to local SQLite
# This allows easy switching to PostgreSQL/MySQL in production
DEFAULT_DB_PATH = os.path.join("data", "expense_tracker.db")
DB_URL = os.getenv("DATABASE_URL", f"sqlite:///{DEFAULT_DB_PATH}")

Base = declarative_base()


@st.cache_resource
def get_engine():
    # Ensure data directory exists if using default SQLite
    if DB_URL.startswith("sqlite"):
        os.makedirs("data", exist_ok=True)
        connect_args = {"check_same_thread": False}
    else:
        connect_args = {}

    return create_engine(
        DB_URL,
        connect_args=connect_args,
        pool_pre_ping=True,  # Check connection validity before usage
        pool_recycle=3600,  # Recycle connections every hour
    )


@st.cache_resource
def get_session_factory():
    engine = get_engine()
    return sessionmaker(bind=engine, autoflush=False)


def get_session():
    Session = get_session_factory()
    return Session()


@contextmanager
def provide_session():
    """
    Context manager to ensure session is closed automatically.
    Usage:
        with provide_session() as session:
            session.query(...)
    """
    session = get_session()
    try:
        yield session
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def init_db():
    engine = get_engine()
    Base.metadata.create_all(bind=engine)
