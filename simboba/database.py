"""Database configuration and session management."""

import os
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase


class Base(DeclarativeBase):
    pass


def get_default_db_path() -> Path:
    """Get the default database path, searching for boba-evals/ directory."""
    from simboba.config import find_boba_evals_dir

    evals_dir = find_boba_evals_dir()
    if evals_dir:
        return evals_dir / "simboba.db"

    # Fallback: check if we're already inside a boba-evals folder
    cwd = Path.cwd()
    if cwd.name == "boba-evals":
        return cwd / "simboba.db"

    # Last resort: create in cwd (for tests or edge cases)
    return cwd / "simboba.db"


def get_database_url(db_path: Path | None = None) -> str:
    """Get the SQLite database URL."""
    if db_path:
        path = db_path
    elif os.environ.get("SIMBOBA_DB_PATH"):
        path = Path(os.environ["SIMBOBA_DB_PATH"])
    else:
        path = get_default_db_path()
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
