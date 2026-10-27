"""SQLite connection and explicit, versioned migrations."""
import sqlite3
from pathlib import Path

MIGRATIONS = Path(__file__).resolve().parent.parent / "migrations"


def connect(path):
    conn = sqlite3.connect(path)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def migrate(conn):
    """Apply pending migrations in filename order and record each version."""
    conn.execute("CREATE TABLE IF NOT EXISTS schema_migrations (version TEXT PRIMARY KEY)")
    applied = {row[0] for row in conn.execute("SELECT version FROM schema_migrations")}
    for script in sorted(MIGRATIONS.glob("*.sql")):
        if script.stem in applied:
            continue
        conn.executescript(script.read_text(encoding="utf-8"))
        conn.execute("INSERT INTO schema_migrations (version) VALUES (?)", (script.stem,))
        conn.commit()
