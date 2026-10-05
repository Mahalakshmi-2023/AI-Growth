"""SQLite setup. We use Python's built-in sqlite3 so there is nothing extra to install."""
import os
import sqlite3
from contextlib import contextmanager

# The database file lives in the backend/ folder.
DB_PATH = os.getenv(
    "DB_PATH",
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "growthos.db"),
)

SCHEMA = """
CREATE TABLE IF NOT EXISTS students (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    name          TEXT NOT NULL,
    email         TEXT NOT NULL UNIQUE,
    phone         TEXT NOT NULL,
    college       TEXT NOT NULL,
    branch        TEXT NOT NULL,
    year          TEXT NOT NULL,
    ai_level      TEXT NOT NULL,
    career_goal   TEXT NOT NULL,
    channel       TEXT NOT NULL DEFAULT 'Direct',   -- where the student came from
    referral_code TEXT NOT NULL UNIQUE,             -- this student's own ambassador code
    referred_by   TEXT,                             -- code of the ambassador who referred them
    score         INTEGER,                          -- AI lead score 0-100
    category      TEXT,                             -- High / Medium / Low Intent
    score_reason  TEXT,
    persona       TEXT,                             -- JSON: profile, pain_point, motivation
    outreach      TEXT,                             -- JSON: whatsapp, email_subject, email_body
    ai_source     TEXT,                             -- 'gemini' or 'fallback'
    is_demo       INTEGER NOT NULL DEFAULT 0,       -- 1 = seeded demo row
    created_at    TEXT NOT NULL DEFAULT (datetime('now'))
);

-- One row per landing-page visit. Needed to compute a real conversion rate.
CREATE TABLE IF NOT EXISTS visits (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    channel    TEXT NOT NULL DEFAULT 'Direct',
    ref        TEXT,                                -- referral code in the link, if any
    is_demo    INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_students_referred_by ON students(referred_by);
CREATE INDEX IF NOT EXISTS idx_visits_ref ON visits(ref);
"""


def init_db() -> None:
    """Create tables if they do not exist yet. Safe to call on every startup."""
    with get_db() as db:
        db.executescript(SCHEMA)


@contextmanager
def get_db():
    """Open a connection, commit on success, always close."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # lets us access columns by name
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
