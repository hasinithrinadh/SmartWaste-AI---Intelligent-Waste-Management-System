"""
database.py
SQLite-backed persistence layer for SmartWaste AI.
"""

import sqlite3
import random
from datetime import datetime

import pandas as pd

DB_PATH = "smartwaste.db"

# Seed data used only the first time the database is created
_SEED_BINS = [
    ("BIN-001", "Main Street",      "General Waste", 42),
    ("BIN-002", "Central Park",     "Recyclable",     78),
    ("BIN-003", "City Mall",        "Organic",        91),
    ("BIN-004", "Riverside Ave",    "General Waste",  35),
    ("BIN-005", "Tech Park",        "E-waste",         58),
    ("BIN-006", "Railway Station",  "Recyclable",      88),
    ("BIN-007", "School Zone",      "Organic",         63),
    ("BIN-008", "Residential Block A", "General Waste", 25),
]


def _get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create tables if they don't exist and seed initial bin data."""
    conn = _get_conn()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS bins (
            bin_id TEXT PRIMARY KEY,
            location TEXT NOT NULL,
            waste_type TEXT NOT NULL,
            fill_level REAL NOT NULL,
            last_collected TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS chat_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question TEXT NOT NULL,
            response TEXT NOT NULL,
            timestamp TEXT NOT NULL
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            bin_id TEXT NOT NULL,
            message TEXT NOT NULL,
            timestamp TEXT NOT NULL
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS classification_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item TEXT NOT NULL,
            category TEXT NOT NULL,
            timestamp TEXT NOT NULL
        )
    """)

    conn.commit()

    # Seed bins only if the table is empty (first run)
    cur.execute("SELECT COUNT(*) FROM bins")
    if cur.fetchone()[0] == 0:
        now = datetime.now().isoformat()
        cur.executemany(
            "INSERT INTO bins (bin_id, location, waste_type, fill_level, last_collected) "
            "VALUES (?, ?, ?, ?, ?)",
            [(b[0], b[1], b[2], b[3], now) for b in _SEED_BINS],
        )
        conn.commit()

    conn.close()


def get_all_bins() -> pd.DataFrame:
    """Return all bins as a DataFrame."""
    conn = _get_conn()
    df = pd.read_sql_query(
        "SELECT bin_id, location, waste_type, fill_level, last_collected FROM bins ORDER BY bin_id",
        conn,
    )
    conn.close()
    return df


def mark_bin_collected(bin_id: str):
    """Reset a bin's fill level after collection and log the timestamp."""
    conn = _get_conn()
    cur = conn.cursor()
    # Fill level resets to a small random residual rather than exactly 0,
    # to keep the simulation realistic.
    residual = round(random.uniform(2, 8), 1)
    cur.execute(
        "UPDATE bins SET fill_level = ?, last_collected = ? WHERE bin_id = ?",
        (residual, datetime.now().isoformat(), bin_id),
    )
    conn.commit()
    conn.close()


def log_chat(question: str, response: str):
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO chat_log (question, response, timestamp) VALUES (?, ?, ?)",
        (question, response, datetime.now().isoformat()),
    )
    conn.commit()
    conn.close()


def log_alert(bin_id: str, message: str):
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO alerts (bin_id, message, timestamp) VALUES (?, ?, ?)",
        (bin_id, message, datetime.now().isoformat()),
    )
    conn.commit()
    conn.close()


def log_classification(item: str, category: str):
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO classification_log (item, category, timestamp) VALUES (?, ?, ?)",
        (item, category, datetime.now().isoformat()),
    )
    conn.commit()
    conn.close()


def get_classification_history(limit: int = 50) -> pd.DataFrame:
    """Return the most recent classification log entries."""
    conn = _get_conn()
    df = pd.read_sql_query(
        "SELECT item, category, timestamp FROM classification_log "
        "ORDER BY id DESC LIMIT ?",
        conn,
        params=(limit,),
    )
    conn.close()
    return df


def get_alerts(limit: int = 50) -> pd.DataFrame:
    """Return the most recent alerts (useful for debugging/admin views)."""
    conn = _get_conn()
    df = pd.read_sql_query(
        "SELECT bin_id, message, timestamp FROM alerts ORDER BY id DESC LIMIT ?",
        conn,
        params=(limit,),
    )
    conn.close()
    return df
