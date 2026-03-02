"""
Database access layer — thin wrappers around sqlite3.
"""
import sqlite3
import hashlib
from flask import g, current_app


SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    name      TEXT    NOT NULL,
    email     TEXT    NOT NULL UNIQUE,
    role      TEXT    NOT NULL CHECK(role IN ('employee', 'manager')),
    password_hash TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS expenses (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER NOT NULL REFERENCES users(id),
    title       TEXT    NOT NULL,
    amount      REAL    NOT NULL CHECK(amount > 0),
    category    TEXT    NOT NULL,
    description TEXT    DEFAULT '',
    status      TEXT    NOT NULL DEFAULT 'draft'
                CHECK(status IN ('draft','submitted','approved','rejected')),
    created_at  TEXT    NOT NULL DEFAULT (datetime('now')),
    updated_at  TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS expense_status_history (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    expense_id   INTEGER NOT NULL REFERENCES expenses(id),
    from_status  TEXT,
    to_status    TEXT    NOT NULL,
    changed_by_id INTEGER NOT NULL REFERENCES users(id),
    note         TEXT    DEFAULT '',
    timestamp    TEXT    NOT NULL DEFAULT (datetime('now'))
);
"""

SEED_USERS = [
    ("Alice Employee", "alice@demo.com", "employee", "password123"),
    ("Bob Employee",   "bob@demo.com",   "employee", "password123"),
    ("Carol Manager",  "carol@demo.com", "manager",  "password123"),
]


def _hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def check_password(stored_hash: str, password: str) -> bool:
    return stored_hash == _hash_password(password)


def get_db():
    if "db" not in g:
        # For :memory: testing, reuse the same connection stored on app
        db_path = current_app.config["DATABASE"]
        if db_path == ":memory:":
            if not hasattr(current_app, "_memory_db"):
                raise RuntimeError("In-memory DB not initialized. Call init_db first.")
            g.db = current_app._memory_db
        else:
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA foreign_keys = ON")
            g.db = conn
    return g.db


def close_db(e=None):
    db = g.pop("db", None)
    # Don't close in-memory connections
    if db is not None and current_app.config["DATABASE"] != ":memory:":
        db.close()


def init_db(app):
    app.teardown_appcontext(close_db)

    db_path = app.config["DATABASE"]
    if db_path == ":memory:":
        conn = sqlite3.connect(":memory:", check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        app._memory_db = conn
    else:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")

    conn.executescript(SCHEMA)
    conn.commit()

    # Seed only if empty
    if conn.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 0:
        for name, email, role, pwd in SEED_USERS:
            conn.execute(
                "INSERT INTO users (name, email, role, password_hash) VALUES (?, ?, ?, ?)",
                (name, email, role, _hash_password(pwd)),
            )
        conn.commit()
        app.logger.info("Seeded demo users: alice@demo.com, bob@demo.com, carol@demo.com (password: password123)")

    if db_path != ":memory:":
        conn.close()
