"""SQLite-Datenbank: Ordner -> Kartensets -> Karten.

Ein Kartenset kann in einem Ordner liegen, muss aber nicht (folder_id darf NULL sein).
Wird ein Ordner gelöscht, bleiben seine Sets erhalten und sind danach ohne Ordner.
"""
import csv
import sqlite3
from pathlib import Path

from flask import g

BASE_DIR = Path(__file__).parent
DB_FILE = BASE_DIR / "karteikarten.db"
LEGACY_CSV = BASE_DIR.parent / "data" / "flashcards.csv"

SCHEMA_VERSION = 1

CARD_SETS_TABLE = """
CREATE TABLE IF NOT EXISTS {name} (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    folder_id   INTEGER REFERENCES folders(id) ON DELETE SET NULL,
    name        TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    created_at  TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
"""

SCHEMA = """
CREATE TABLE IF NOT EXISTS folders (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    name       TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
""" + CARD_SETS_TABLE.format(name="card_sets") + """
CREATE TABLE IF NOT EXISTS cards (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    set_id     INTEGER NOT NULL REFERENCES card_sets(id) ON DELETE CASCADE,
    question   TEXT NOT NULL,
    answer     TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
"""


def connect():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def get_db():
    """Eine Verbindung pro Request (wird in app.teardown geschlossen)."""
    if "db" not in g:
        g.db = connect()
    return g.db


def close_db(_exc=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    """Tabellen anlegen, alte Datenbanken umstellen, beim ersten Start die CSV importieren."""
    conn = connect()
    try:
        version = conn.execute("PRAGMA user_version").fetchone()[0]
        had_tables = conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'card_sets'"
        ).fetchone()
        if had_tables and version < 1:
            migrate_to_v1(conn)

        conn.executescript(SCHEMA)
        conn.execute(f"PRAGMA user_version = {SCHEMA_VERSION}")

        is_empty = conn.execute(
            "SELECT (SELECT COUNT(*) FROM folders) + (SELECT COUNT(*) FROM card_sets)"
        ).fetchone()[0] == 0
        if is_empty and LEGACY_CSV.exists():
            import_legacy_csv(conn)
        conn.commit()
    finally:
        conn.close()


def migrate_to_v1(conn):
    """Version 0 -> 1: folder_id von card_sets wird optional (vorher NOT NULL + CASCADE).

    SQLite kann Spalten-Constraints nicht ändern, also wird die Tabelle neu aufgebaut.
    """
    conn.commit()
    conn.execute("PRAGMA foreign_keys = OFF")
    conn.executescript(
        "BEGIN;"
        + CARD_SETS_TABLE.format(name="card_sets_new")
        + """
        INSERT INTO card_sets_new (id, folder_id, name, description, created_at)
            SELECT id, folder_id, name, description, created_at FROM card_sets;
        DROP TABLE card_sets;
        ALTER TABLE card_sets_new RENAME TO card_sets;
        COMMIT;
        """
    )
    conn.execute("PRAGMA foreign_keys = ON")


def import_legacy_csv(conn):
    """Liest data/flashcards.csv (Zeilen im Format 'Frage;Antwort')."""
    with open(LEGACY_CSV, encoding="utf-8", newline="") as f:
        rows = list(csv.reader(f, delimiter=";"))

    pairs = [(r[0].strip(), r[1].strip()) for r in rows[1:] if len(r) >= 2]
    if not pairs:
        return

    folder_id = conn.execute(
        "INSERT INTO folders (name) VALUES (?)", ("Französisch",)
    ).lastrowid
    set_id = conn.execute(
        "INSERT INTO card_sets (folder_id, name, description) VALUES (?, ?, ?)",
        (folder_id, "Grundwortschatz", "Importiert aus data/flashcards.csv"),
    ).lastrowid
    conn.executemany(
        "INSERT INTO cards (set_id, question, answer) VALUES (?, ?, ?)",
        [(set_id, q, a) for q, a in pairs],
    )
