"""
db.py
-----
Tiny SQLite helper. The database file lives in instance/waste.db
(or the path in the DATABASE_PATH environment variable).

Tables
  users        - id, username, email, password_hash, is_admin, created_at
  predictions  - one row per classification, linked to the user who made it
"""
import os
import sqlite3

from flask import current_app, g

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    username      TEXT NOT NULL UNIQUE COLLATE NOCASE,
    email         TEXT NOT NULL UNIQUE COLLATE NOCASE,
    password_hash TEXT NOT NULL,
    is_admin      INTEGER NOT NULL DEFAULT 0,
    created_at    TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS predictions (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id        INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    material_type  TEXT NOT NULL,
    wet_or_dry     TEXT NOT NULL,
    texture        TEXT NOT NULL,
    biodegradable  TEXT NOT NULL,
    final_category TEXT NOT NULL,
    decision_tree  TEXT NOT NULL,
    random_forest  TEXT NOT NULL,
    svm            TEXT NOT NULL,
    naive_bayes    TEXT NOT NULL,
    confidence     REAL,
    is_uncertain   INTEGER NOT NULL DEFAULT 0,
    image_filename TEXT,
    created_at     TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS feedback (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    prediction_id  INTEGER NOT NULL REFERENCES predictions(id) ON DELETE CASCADE,
    user_id        INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    is_correct     INTEGER NOT NULL,
    actual_category TEXT,
    comment        TEXT,
    created_at     TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_pred_user ON predictions(user_id);
CREATE INDEX IF NOT EXISTS idx_pred_created ON predictions(created_at);
CREATE INDEX IF NOT EXISTS idx_feedback_pred ON feedback(prediction_id);
CREATE INDEX IF NOT EXISTS idx_feedback_user ON feedback(user_id);
"""


def db_path():
    return current_app.config["DATABASE"]


def get_db():
    """One connection per request."""
    if "db" not in g:
        g.db = sqlite3.connect(db_path())
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


def close_db(_exc=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    os.makedirs(os.path.dirname(db_path()), exist_ok=True)
    db = sqlite3.connect(db_path())
    db.executescript(SCHEMA)
    db.commit()
    db.close()


def init_app(app):
    app.teardown_appcontext(close_db)
    with app.app_context():
        init_db()
