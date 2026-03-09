"""SQLite connection manager with WAL mode enforcement."""
import sqlite3
from pathlib import Path
from contextlib import contextmanager
from config import DB_PATH


def get_connection(db_path: Path = DB_PATH) -> sqlite3.Connection:
    """Get a SQLite connection with WAL mode and row factory."""
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


@contextmanager
def get_db():
    """Context manager for database connections. Auto-commits on success, rolls back on error."""
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def checkpoint():
    """Run WAL checkpoint to flush writes to main DB file."""
    conn = get_connection()
    try:
        conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
    finally:
        conn.close()
