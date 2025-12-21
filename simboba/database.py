"""Database configuration and session management."""

import os
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

DEFAULT_DB_PATH = Path.cwd() / "boba-evals" / "simboba.db"


class Base(DeclarativeBase):
    pass


def get_database_url(db_path: Path | None = None) -> str:
    """Get the SQLite database URL."""
    path = db_path or Path(os.environ.get("SIMBOBA_DB_PATH", DEFAULT_DB_PATH))
    # Ensure parent directory exists
    path.parent.mkdir(parents=True, exist_ok=True)
    # Ensure .gitignore exists to ignore db files
    gitignore = path.parent / ".gitignore"
    if not gitignore.exists():
        gitignore.write_text("# boba database\n*.db\n")
    return f"sqlite:///{path}"


def create_db_engine(db_path: Path | None = None):
    """Create a SQLAlchemy engine."""
    url = get_database_url(db_path)
    return create_engine(url, connect_args={"check_same_thread": False})


def get_session_factory(db_path: Path | None = None):
    """Get a session factory for the database."""
    engine = create_db_engine(db_path)
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db(db_path: Path | None = None):
    """Initialize the database, creating all tables."""
    from simboba.models import Dataset, EvalCase  # noqa: F401

    engine = create_db_engine(db_path)
    Base.metadata.create_all(bind=engine)
    return engine
